#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試控制器 - 用於測試和比較服務性能
此控制器僅用於開發環境，不應在生產環境中啟用
"""

import logging
import json
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
import asyncio

# 導入服務
from ..services import SearchService, FlightSearchService
# from ..services.price_service import PriceService 
from ..services.price_analysis_service import PriceAnalysisService

# 創建藍圖
test_bp = Blueprint('test', __name__, url_prefix='/api/test')

# 設置日誌
logger = logging.getLogger(__name__)

@test_bp.route('/status', methods=['GET'])
def service_status():
    """獲取當前服務狀態"""
    return jsonify({
        'success': True,
        'message': '系統使用新服務架構'
    })

@test_bp.route('/compare/search', methods=['POST'])
async def compare_search():
    """比較搜索服務性能"""
    data = request.json
    departure = data.get('departure', 'TSA')
    arrival = data.get('arrival', 'HND')
    date_str = data.get('date', (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'))
    cabin_class = data.get('cabin_class', '經濟艙')
    
    logger.info(f"比較搜索服務: {departure}->{arrival}, 日期: {date_str}, 艙等: {cabin_class}")
    
    try:
        # 使用 SearchService (FlightSearchService 的別名)
        old_start = datetime.now()
        old_result = await SearchService.search_flights(
            departure_code=departure,
            arrival_code=arrival,
            date_str=date_str,
            cabin_class=cabin_class
        )
        old_time = (datetime.now() - old_start).total_seconds()
        
        # 使用直接的 FlightSearchService
        new_start = datetime.now()
        new_result = await FlightSearchService.search_flights(
            departure_code=departure,
            arrival_code=arrival,
            date_str=date_str,
            cabin_class=cabin_class
        )
        new_time = (datetime.now() - new_start).total_seconds()
        
        # 比較結果（將是相同的，因為 SearchService 只是 FlightSearchService 的別名）
        old_count = len(old_result.get('departure', [])) if isinstance(old_result, dict) else 0
        new_count = len(new_result.get('departure', [])) if isinstance(new_result, dict) else 0
        
        return jsonify({
            'success': True,
            'comparison': {
                'service_alias': {
                    'time': old_time,
                    'count': old_count
                },
                'direct_service': {
                    'time': new_time,
                    'count': new_count
                },
                'time_diff_percent': ((new_time - old_time) / old_time * 100) if old_time > 0 else 0,
                'count_match': old_count == new_count
            }
        })
    except Exception as e:
        logger.error(f"比較搜索服務時出錯: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@test_bp.route('/compare/price', methods=['POST'])
async def compare_price():
    """比較新舊價格服務"""
    data = request.json
    departure = data.get('departure', 'TSA')
    arrival = data.get('arrival', 'HND')
    start_date = data.get('start_date', (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'))
    end_date = data.get('end_date', (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'))
    
    logger.info(f"比較價格服務: {departure}->{arrival}, 日期範圍: {start_date} 至 {end_date}")
    
    try:
        # 使用舊的價格服務 (現在使用 PriceAnalysisService 的同步版本)
        old_start = datetime.now()
        old_result_sync = PriceAnalysisService.get_lowest_prices_sync(
            departure_code=departure, # 修改: 參數名從 departure_iata 改為 departure_code
            arrival_code=arrival,     # 修改: 參數名從 arrival_iata 改為 arrival_code
            start_date=start_date,
            end_date=end_date,
            cabin_class='經濟艙' # 新增: 添加 cabin_class 參數以匹配方法簽名
        )
        old_time = (datetime.now() - old_start).total_seconds()
        
        # 使用新的價格服務
        new_start = datetime.now()
        new_result = await PriceAnalysisService.get_low_fare_calendar(
            departure_code=departure,
            arrival_code=arrival,
            start_date=start_date,
            end_date=end_date,
            cabin_class='經濟艙'
        )
        new_time = (datetime.now() - new_start).total_seconds()
        
        # 從新結果中提取價格映射進行比較
        new_price_map = {}
        if "data" in new_result:
            for item in new_result["data"]:
                if "price" in item and item["price"] is not None:
                    new_price_map[item["date"]] = item["price"]
        
        # 比較結果
        old_count = len(old_result_sync) if isinstance(old_result_sync, dict) else 0 # 修改: 使用 old_result_sync
        new_count = len(new_price_map)
        
        return jsonify({
            'success': True,
            'comparison': {
                'old_service': {
                    'time': old_time,
                    'count': old_count
                },
                'new_service': {
                    'time': new_time,
                    'count': new_count
                },
                'time_diff_percent': ((new_time - old_time) / old_time * 100) if old_time > 0 else 0,
                'count_match': abs(old_count - new_count) <= 5  # 允許有小的差異
            }
        })
    except Exception as e:
        logger.error(f"比較價格服務時出錯: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 