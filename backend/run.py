"""
Flask應用啟動腳本
"""
import os
import asyncio
import logging
# import click # <-- 移除 click 導入
from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_cors import CORS
from flask_caching import Cache
from dotenv import load_dotenv

# 加載環境變量
load_dotenv()

from app import create_app
from flask import jsonify
from asgiref.wsgi import WsgiToAsgi
from hypercorn.asyncio import serve
from hypercorn.config import Config as HyperConfig
import traceback  # 導入 traceback 用於獲取詳細錯誤信息

# 打印環境變量進行檢查
print(f"Database URL: {os.getenv('DATABASE_URL', '未設置')}")

# 創建Flask應用
app = create_app()

# --- 移除頂層導入 CLI 相關模塊的嘗試 ---
# _crm_module = None
# try:
#     # ... (移除 try-except 塊)
# except Exception as e:
#     print(f"[run.py top level] 導入 create_rich_menu 模塊時發生其他錯誤: {e}")

# --- 移除 Flask CLI 命令註冊 --- 
# @app.cli.group()
# def scripts():
#     pass
# 
# @scripts.command("setup-rich-menu")
# @click.option(...)
# @click.option(...)
# def setup_rich_menu_command(image_path, frontend_url):
#     # ... (移除整個函數)

# --- 結束移除 CLI 命令註冊 ---

# 添加測試路由檢查可用航班
@app.route('/api/debug/flights', methods=['GET'])
async def debug_flights():
    """列出資料庫中所有航班的基本信息，用於偵錯"""
    from app.database.db import get_pool  # 改用get_pool而不是init_asyncpg_pool
    
    try:
        # 獲取連接池
        pool = await get_pool()  # 改用get_pool()
        
        # 使用連接池獲取連接
        async with pool.acquire() as conn:
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
            
            flights = await conn.fetch(query)
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
                    'departure_time': flight['scheduled_departure'].isoformat() if flight['scheduled_departure'] else None
                })
            
            return jsonify(result)
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"Debug flights 錯誤: {str(e)}\n{error_traceback}")
        return jsonify({
            'error': str(e),
            'type': type(e).__name__,
            'trace': error_traceback
        }), 500

@app.route('/api/debug/airports', methods=['GET'])
async def debug_airports():
    """列出資料庫中所有機場，用於偵錯"""
    from app.database.db import get_pool  # 改用get_pool而不是init_asyncpg_pool
    
    try:
        # 獲取連接池
        pool = await get_pool()  # 改用get_pool()
        
        # 使用連接池獲取連接
        async with pool.acquire() as conn:
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
            
            airports = await conn.fetch(query)
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
        error_traceback = traceback.format_exc()
        print(f"Debug airports 錯誤: {str(e)}\n{error_traceback}")
        return jsonify({
            'error': str(e),
            'type': type(e).__name__,
            'trace': error_traceback
        }), 500

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
        # 注意：直接運行 app.run 在生產環境中不推薦，應使用 Gunicorn/Hypercorn
        # 但對於本地開發和 Render (通常會接管啟動過程) 是可以的
        app.run(host='0.0.0.0', port=port, debug=(os.environ.get('FLASK_ENV', 'development') == 'development'))

