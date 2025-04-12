import os
import sys
import logging
import datetime
from dotenv import load_dotenv
from app.scripts.flightstats_sync import FlightStatsApiClient

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

def test_airport_departures():
    """測試各機場出發航班"""
    client = FlightStatsApiClient()
    
    # 測試不同機場
    test_airports = ['TPE', 'TSA', 'KHH', 'MZG', 'RMQ', 'WOT', 'CMJ']
    
    for airport in test_airports:
        logger.info(f"正在測試機場 {airport} 的起飛航班...")
        now = datetime.datetime.now()
        tomorrow = now + datetime.timedelta(days=1)
        
        try:
            # 測試今天的航班
            flights = client.get_airport_departures(airport, now)
            logger.info(f"{airport} 今日航班數: {len(flights)}")
            
            # 計算各航空公司的航班數
            airlines_count = {}
            for flight in flights:
                airline = flight.get('carrierFsCode', 'Unknown')
                if airline not in airlines_count:
                    airlines_count[airline] = 0
                airlines_count[airline] += 1
            
            # 顯示各航空公司航班數
            logger.info(f"{airport} 各航空公司航班分布:")
            for airline, count in airlines_count.items():
                logger.info(f"  - {airline}: {count}航班")
                
            # 檢查目標航空公司
            target_airlines = ['BR', 'JL', 'JX', 'IT', 'CX', 'DA', 'CI', 'OZ', 'AE', 'B7']
            target_flights = [f for f in flights if f.get('carrierFsCode') in target_airlines]
            logger.info(f"{airport} 目標航空公司航班數: {len(target_flights)}/{len(flights)}")
            
            # 測試明天的航班
            tomorrow_flights = client.get_airport_departures(airport, tomorrow)
            logger.info(f"{airport} 明日航班數: {len(tomorrow_flights)}")
            
        except Exception as e:
            logger.error(f"測試 {airport} 時發生錯誤: {str(e)}")
        
        logger.info("-" * 50)

def test_airline_flights():
    """測試指定航空公司航班"""
    client = FlightStatsApiClient()
    target_airlines = ['BR', 'JL', 'JX', 'IT', 'CX', 'DA', 'CI', 'OZ', 'AE', 'B7']
    
    now = datetime.datetime.now()
    
    for airline in target_airlines:
        logger.info(f"正在測試航空公司 {airline} 的航班...")
        try:
            # 測試該航空公司在TPE的起飛航班
            flights = client.get_airline_departures_from_airport(airline, 'TPE', now)
            logger.info(f"{airline} 從 TPE 出發的航班數: {len(flights)}")
            
            # 顯示目的地分布
            destinations = {}
            for flight in flights:
                dest = flight.get('arrivalAirportFsCode', 'Unknown')
                if dest not in destinations:
                    destinations[dest] = 0
                destinations[dest] += 1
            
            logger.info(f"{airline} 目的地分布:")
            for dest, count in destinations.items():
                logger.info(f"  - {dest}: {count}航班")
                
        except Exception as e:
            logger.error(f"測試航空公司 {airline} 時發生錯誤: {str(e)}")
        
        logger.info("-" * 50)

if __name__ == "__main__":
    logger.info("開始測試 FlightStats API...")
    test_airport_departures()
    test_airline_flights()
    logger.info("測試完成")