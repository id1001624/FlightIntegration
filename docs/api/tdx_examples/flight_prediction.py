#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TDX 航空 API 範例 - 航班延誤預測
此範例展示如何獲取航班資訊，並基於簡單邏輯進行延誤預測分析
"""

import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split

class TDXAuth:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        self.token = None
        self.token_expire_time = None
        
    def get_token(self):
        """取得 TDX API 的 Access Token，含過期時間管理"""
        # 如果已有未過期的 token，直接返回
        if self.token and self.token_expire_time and datetime.now() < self.token_expire_time:
            return self.token
            
        # 準備取得 token 的請求資料
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        # 發送請求取得 token
        response = requests.post(self.auth_url, headers=headers, data=data)
        
        # 檢查回應狀態
        if response.status_code != 200:
            raise Exception(f"取得 token 失敗: {response.status_code} {response.text}")
            
        # 解析回應並儲存 token
        response_data = json.loads(response.text)
        self.token = response_data.get("access_token")
        
        # 設置 token 過期時間 (預留 10 分鐘緩衝)
        expires_in = response_data.get("expires_in", 3600)  # 預設 1 小時
        self.token_expire_time = datetime.now() + timedelta(seconds=expires_in - 600)
        
        return self.token
    
    def get_auth_header(self):
        """取得用於 API 請求的認證 header"""
        token = self.get_token()
        return {
            "authorization": f"Bearer {token}",
            "Accept-Encoding": "gzip"  # 建議加入，可減少回傳資料量
        }

class FlightPredictor:
    def __init__(self, auth):
        self.auth = auth
        self.base_url = "https://tdx.transportdata.tw/api/basic/v2/Air"
        self.model = None
        self.encoder = None
        
    def get_historical_data(self, start_date, end_date, airport_code="TPE"):
        """獲取歷史航班資料
        
        注意：實際 TDX API 可能沒有直接提供過去的歷史資料，
        此函數僅作為示範，實際使用時可能需要長期收集資料建立自己的歷史數據庫
        
        Args:
            start_date: 開始日期，格式為 "YYYY-MM-DD"
            end_date: 結束日期，格式為 "YYYY-MM-DD"
            airport_code: 機場 IATA 代碼
            
        Returns:
            歷史航班資料的 DataFrame
        """
        # 將日期範圍轉換為日期列表
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        date_list = [(start + timedelta(days=x)).strftime("%Y-%m-%d") 
                     for x in range((end - start).days + 1)]
        
        all_data = []
        
        for date in date_list:
            try:
                # 獲取抵達航班資料
                url = f"{self.base_url}/FIDS/Airport/Arrival/{airport_code}/{date}?$format=JSON"
                response = requests.get(url, headers=self.auth.get_auth_header())
                
                if response.status_code == 200:
                    arrivals = json.loads(response.text)
                    all_data.extend(arrivals)
                else:
                    print(f"獲取 {date} 的抵達航班資料失敗: {response.status_code}")
                
                # 限制 API 呼叫頻率，避免達到限制
                import time
                time.sleep(1)
                
            except Exception as e:
                print(f"處理 {date} 的資料時發生錯誤: {str(e)}")
        
        # 將資料轉換為 DataFrame
        if not all_data:
            return pd.DataFrame()
            
        df = pd.DataFrame(all_data)
        
        # 處理延誤資訊
        if 'ScheduleArrivalTime' in df.columns and 'ActualArrivalTime' in df.columns:
            df['ScheduleArrival'] = pd.to_datetime(df['ScheduleArrivalTime'])
            df['ActualArrival'] = pd.to_datetime(df['ActualArrivalTime'])
            df['DelayMinutes'] = (df['ActualArrival'] - df['ScheduleArrival']).dt.total_seconds() / 60
            df['IsDelayed'] = df['DelayMinutes'] > 15  # 超過 15 分鐘視為延誤
        
        return df
    
    def prepare_features(self, df):
        """準備模型訓練所需的特徵
        
        Args:
            df: 航班資料的 DataFrame
            
        Returns:
            特徵矩陣 X 和標籤 y
        """
        if df.empty or 'IsDelayed' not in df.columns:
            raise ValueError("資料不足或缺少延誤資訊")
            
        # 選擇特徵列
        features = ['AirlineID', 'FlightNumber', 'DepartureAirportID', 'ArrivalAirportID']
        
        # 確保所有特徵列都存在
        for feature in features:
            if feature not in df.columns:
                raise ValueError(f"缺少特徵列: {feature}")
        
        # 擷取時間相關特徵
        if 'ScheduleArrivalTime' in df.columns:
            df['ArrivalHour'] = pd.to_datetime(df['ScheduleArrivalTime']).dt.hour
            df['ArrivalDayOfWeek'] = pd.to_datetime(df['ScheduleArrivalTime']).dt.dayofweek
            features.extend(['ArrivalHour', 'ArrivalDayOfWeek'])
        
        # 使用 OneHotEncoder 處理類別型特徵
        categorical_features = ['AirlineID', 'DepartureAirportID', 'ArrivalAirportID']
        cat_features = df[categorical_features]
        
        self.encoder = OneHotEncoder(sparse=False, handle_unknown='ignore')
        encoded_features = self.encoder.fit_transform(cat_features)
        
        # 選取數值型特徵
        numerical_features = [f for f in features if f not in categorical_features]
        num_features = df[numerical_features].fillna(0)
        
        # 合併特徵
        X = np.hstack([encoded_features, num_features])
        y = df['IsDelayed'].astype(int).values
        
        return X, y
    
    def train_model(self, X, y):
        """訓練預測模型
        
        Args:
            X: 特徵矩陣
            y: 標籤
            
        Returns:
            訓練好的模型
        """
        # 分割訓練集和測試集
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # 使用隨機森林分類器
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)
        
        # 評估模型
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        print(f"模型訓練完成：")
        print(f"訓練集準確率: {train_score:.4f}")
        print(f"測試集準確率: {test_score:.4f}")
        
        return self.model
    
    def predict_delays(self, flight_data):
        """使用訓練好的模型預測航班延誤
        
        Args:
            flight_data: 航班資料的 DataFrame 或 dict
            
        Returns:
            航班延誤預測結果
        """
        if self.model is None or self.encoder is None:
            raise ValueError("模型尚未訓練，請先呼叫 train_model")
            
        # 轉換輸入資料為 DataFrame
        if isinstance(flight_data, dict):
            df = pd.DataFrame([flight_data])
        else:
            df = flight_data
            
        # 準備特徵
        categorical_features = ['AirlineID', 'DepartureAirportID', 'ArrivalAirportID']
        cat_features = df[categorical_features]
        encoded_features = self.encoder.transform(cat_features)
        
        # 選取數值型特徵
        if 'ScheduleArrivalTime' in df.columns:
            df['ArrivalHour'] = pd.to_datetime(df['ScheduleArrivalTime']).dt.hour
            df['ArrivalDayOfWeek'] = pd.to_datetime(df['ScheduleArrivalTime']).dt.dayofweek
        
        numerical_features = ['FlightNumber', 'ArrivalHour', 'ArrivalDayOfWeek']
        num_features = df[numerical_features].fillna(0)
        
        # 合併特徵
        X = np.hstack([encoded_features, num_features])
        
        # 預測延誤概率
        delay_proba = self.model.predict_proba(X)[:, 1]
        
        # 加入預測結果
        df['DelayProbability'] = delay_proba
        df['PredictedDelayed'] = delay_proba > 0.5
        
        return df[['AirlineID', 'FlightNumber', 'DepartureAirportID', 'ArrivalAirportID',
                   'DelayProbability', 'PredictedDelayed']]

def main():
    # 請替換為您的 Client ID 和 Client Secret
    client_id = "YOUR_CLIENT_ID"
    client_secret = "YOUR_CLIENT_SECRET"
    
    # 創建認證實例
    auth = TDXAuth(client_id, client_secret)
    
    # 創建航班預測器
    predictor = FlightPredictor(auth)
    
    # 設定時間範圍
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    try:
        print(f"獲取 {start_date} 至 {end_date} 的航班歷史資料...")
        historical_data = predictor.get_historical_data(start_date, end_date)
        
        if historical_data.empty:
            print("無法獲取足夠的歷史資料，無法進行模型訓練")
            return
            
        print(f"成功獲取 {len(historical_data)} 筆歷史資料")
        print("準備特徵資料...")
        X, y = predictor.prepare_features(historical_data)
        
        print("訓練航班延誤預測模型...")
        predictor.train_model(X, y)
        
        print("獲取今日航班並進行延誤預測...")
        today = datetime.now().strftime("%Y-%m-%d")
        url = f"{predictor.base_url}/FIDS/Airport/Arrival/TPE/{today}?$format=JSON"
        response = requests.get(url, headers=auth.get_auth_header())
        
        if response.status_code == 200:
            today_flights = json.loads(response.text)
            today_df = pd.DataFrame(today_flights)
            
            # 必須包含延誤預測所需的特徵
            if not {'AirlineID', 'FlightNumber', 'DepartureAirportID', 'ArrivalAirportID'}.issubset(today_df.columns):
                print("今日航班資料缺少必要的特徵資訊")
                return
                
            if 'ScheduleArrivalTime' in today_df.columns:
                today_df['ArrivalHour'] = pd.to_datetime(today_df['ScheduleArrivalTime']).dt.hour
                today_df['ArrivalDayOfWeek'] = pd.to_datetime(today_df['ScheduleArrivalTime']).dt.dayofweek
            
            prediction_results = predictor.predict_delays(today_df)
            
            # 儲存預測結果
            prediction_results.to_csv(f'flight_delay_predictions_{today}.csv', index=False)
            print(f"延誤預測結果已儲存至 flight_delay_predictions_{today}.csv")
            
            # 輸出高延誤風險航班
            high_risk = prediction_results[prediction_results['DelayProbability'] > 0.7]
            if not high_risk.empty:
                print("\n高延誤風險航班:")
                for _, flight in high_risk.iterrows():
                    print(f"{flight['AirlineID']}{flight['FlightNumber']} ({flight['DepartureAirportID']} -> {flight['ArrivalAirportID']}): {flight['DelayProbability']*100:.1f}% 延誤機率")
            else:
                print("沒有偵測到高延誤風險航班")
                
        else:
            print(f"獲取今日航班資料失敗: {response.status_code}")
            
    except Exception as e:
        print(f"發生錯誤: {str(e)}")

if __name__ == "__main__":
    main() 