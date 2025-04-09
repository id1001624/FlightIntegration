import requests
import json
import sys

try:
    # API URL - 請確保這是正確的端點
    url = "http://127.0.0.1:5000/api/flight/search"
    
    # 嘗試不同的API路徑
    alternative_urls = [
        "http://127.0.0.1:5000/api/flights/search",
        "http://127.0.0.1:5000/api/v1/flights/search",
        "http://127.0.0.1:5000/api/v1/flight/search",
        "http://127.0.0.1:5000/flight/search"
    ]

    # 查詢參數
    params = {
        "departure": "TPE",
        "arrival": "DPS",
        "date": "2025-04-07"
    }

    # 發送請求
    print(f"正在嘗試 {url}...")
    response = requests.get(url, params=params)
    print(f"Status code: {response.status_code}")
    
    # 如果失敗，嘗試其他可能的URL
    if response.status_code != 200:
        for alt_url in alternative_urls:
            print(f"嘗試替代 URL: {alt_url}")
            try:
                response = requests.get(alt_url, params=params)
                print(f"Status code: {response.status_code}")
                if response.status_code == 200:
                    print("成功找到正確的API端點！")
                    break
            except Exception as e:
                print(f"該端點請求失敗: {str(e)}")

    # 如果成功，打印響應
    if response.status_code == 200:
        data = response.json()
        print("資料結構：")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"發生錯誤: {str(e)}")
    import traceback
    traceback.print_exc()