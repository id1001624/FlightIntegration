"""
Flask應用啟動腳本
"""
import os
import asyncio

# 加載環境變量（必須在其他導入前完成）
from dotenv import load_dotenv
# 查找並加載 .env 文件
load_dotenv()

from app import create_app
from flask import jsonify
from asgiref.wsgi import WsgiToAsgi
from hypercorn.asyncio import serve
from hypercorn.config import Config as HyperConfig

# 打印環境變量進行檢查
print(f"Database URL: {os.getenv('DATABASE_URL', '未設置')}")

# 創建Flask應用
app = create_app()

# 添加測試路由檢查可用航班
@app.route('/api/debug/flights', methods=['GET'])
async def debug_flights():
    """列出資料庫中所有航班的基本信息，用於偵錯"""
    from app.database.db import get_db, release_db
    
    db = await get_db()
    try:
        # 使用 asyncpg 直接查詢
        query = """
        SELECT 
            f.flight_id, 
            f.flight_number, 
            f.scheduled_departure, 
            f.status,
            dep.airport_id as dep_id, 
            dep.airport_id as dep_code, 
            dep.name_zh as dep_name,
            arr.airport_id as arr_id, 
            arr.airport_id as arr_code, 
            arr.name_zh as arr_name,
            al.airline_id as airline_code, 
            al.name_zh as airline_name
        FROM 
            flights f
        JOIN 
            airports dep ON f.departure_airport_id = dep.airport_id
        JOIN 
            airports arr ON f.arrival_airport_id = arr.airport_id
        JOIN 
            airlines al ON f.airline_id = al.airline_id
        LIMIT 10
        """
        
        flights = await db.fetch(query)
        result = []
        
        for flight in flights:
            result.append({
                'flight_id': str(flight['flight_id']),
                'flight_number': flight['flight_number'],
                'departure': {
                    'airport_id': str(flight['dep_id']),
                    'code': flight['dep_code'],
                    'name': flight['dep_name']
                },
                'arrival': {
                    'airport_id': str(flight['arr_id']),
                    'code': flight['arr_code'],
                    'name': flight['arr_name']
                },
                'airline': {
                    'code': flight['airline_code'],
                    'name': flight['airline_name']
                },
                'departure_time': flight['scheduled_departure'].isoformat() if flight['scheduled_departure'] else None,
                'status': flight['status']
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        await release_db(db)

@app.route('/api/debug/airports', methods=['GET'])
async def debug_airports():
    """列出資料庫中所有機場，用於偵錯"""
    from app.database.db import get_db, release_db
    
    db = await get_db()
    try:
        # 使用 asyncpg 直接查詢
        query = """
        SELECT 
            airport_id, 
            airport_id as iata_code, 
            name_zh, 
            name_en, 
            city, 
            country
        FROM 
            airports
        LIMIT 20
        """
        
        airports = await db.fetch(query)
        result = [{
            'airport_id': str(airport['airport_id']),
            'iata_code': airport['iata_code'],
            'name_zh': airport['name_zh'],
            'name_en': airport['name_en'],
            'city': airport['city'],
            'country': airport['country']
        } for airport in airports]
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        await release_db(db)

async def run_async_app():
    """運行異步 Flask 應用"""
    config = HyperConfig()
    config.bind = [f"0.0.0.0:{int(os.environ.get('PORT', 5000))}"]
    config.use_reloader = True
    
    # 如果是開發環境，開啟調試模式
    if os.environ.get('FLASK_ENV', 'development') == 'development':
        config.debug = True
    
    # 將 WSGI 應用轉換為 ASGI 應用
    asgi_app = WsgiToAsgi(app)
    
    # 運行應用
    await serve(asgi_app, config)

if __name__ == '__main__':
    # 獲取端口，如果環境變量中沒有設置，使用默認值5000
    port = int(os.environ.get('PORT', 5000))
    
    # 檢查是否使用異步模式
    use_async = os.environ.get('USE_ASYNC', 'true').lower() == 'true'
    
    if use_async:
        # 運行異步應用
        print(f"啟動異步 Flask 應用，端口: {port}")
        asyncio.run(run_async_app())
    else:
        # 運行同步應用
        print(f"啟動同步 Flask 應用，端口: {port}")
        app.run(host='0.0.0.0', port=port, debug=True)

