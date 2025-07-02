#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
航班控制器
處理與航班相關的API請求
"""
import logging
from uuid import UUID
from flask import Blueprint, request
from marshmallow import ValidationError
from werkzeug.exceptions import NotFound, BadRequest

from ..services.flight_search_service import FlightSearchService
from ..services.flight_details_service import FlightDetailsService
from ..utils.api_helper import api_response
from ..schemas.flight_schema import FlightSchema, FlightSearchArgsSchema

# 創建藍圖
flight_bp = Blueprint('flights', __name__)
logger = logging.getLogger(__name__)

# 實例化 Schema
flight_search_args_schema = FlightSearchArgsSchema()
flight_schema = FlightSchema()
flights_schema = FlightSchema(many=True)


@flight_bp.route("/search", methods=['GET'])
async def search_flights():
    """
    異步搜索航班。
    ---
    tags:
      - Flights
    parameters:
      - name: departure_code
        in: query
        type: string
        required: true
        description: 出發機場 IATA 代碼 (例如 'TPE')
      - name: arrival_code
        in: query
        type: string
        required: true
        description: 抵達機場 IATA 代碼 (例如 'NRT')
      - name: date_str
        in: query
        type: string
        format: date
        required: true
        description: 出發日期 (YYYY-MM-DD)
      - name: passengers
        in: query
        type: integer
        default: 1
        description: 成人乘客數量
      - name: max_results
        in: query
          type: integer
        default: 10
        description: 最大返回結果數量
    responses:
      200:
        description: 成功返回航班
      400:
        description: 請求參數錯誤
      500:
        description: 伺服器內部錯誤
    """
    try:
        # 使用 Marshmallow 進行參數驗證和反序列化
        args = flight_search_args_schema.load(request.args)
    except ValidationError as err:
        logger.warning(f"搜索航班參數驗證失敗: {err.messages}")
        return api_response(success=False, message=err.messages, status_code=400)

    try:
        result = await FlightSearchService.search_flights(**args)
        
        return api_response(
            success=True,
            message=f"成功處理了 {len(result.get('departure', []))} 筆去程航班。",
            data=result
        )
    except Exception as e:
        logger.error(f"異步搜索航班時出錯: {e}", exc_info=True)
        return api_response(success=False, message="搜尋航班時發生內部錯誤", status_code=500)


@flight_bp.route("/<string:flight_id>", methods=['GET'])
async def get_flight_details(flight_id: str):
    """異步獲取單個航班的詳細資訊"""
    try:
        # 驗證 flight_id 是否為有效的 UUID
        valid_flight_id = UUID(flight_id)
    except ValueError:
        return api_response(success=False, message="無效的航班ID格式", status_code=400)

    try:
        flight_details = await FlightDetailsService.get_flight_details_by_id(str(valid_flight_id))
        
        if not flight_details:
            return api_response(success=False, message=f"找不到ID為 {flight_id} 的航班", status_code=404)
        
        # 使用 Schema 序列化結果 - flight_details 已經是 dict，不需 dump
        return api_response(
            success=True,
            message="成功獲取航班詳細資訊",
            data=flight_details
        )
    except Exception as e:
        logger.error(f"異步獲取航班詳情時發生未知錯誤: {e}", exc_info=True)
        return api_response(success=False, message="伺服器內部錯誤", status_code=500)


@flight_bp.route("/from-taiwan", methods=['GET'])
async def get_flights_from_taiwan():
    """
    異步獲取從台灣任一機場出發的航班。
    """
    # 這裡的參數驗證可以簡化，或同樣使用 Schema
    date_str = request.args.get('date')
    if not date_str:
        return api_response(success=False, message="缺少 'date' 參數", status_code=400)
    
    try:
        limit = int(request.args.get('limit', 50))
    except (ValueError, TypeError):
        limit = 50

    try:
        # 注意：search_flights_from_taiwan 需要一個 date 物件
        from datetime import datetime
        flight_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        flights = await FlightSearchService.search_flights_from_taiwan(
            date=flight_date,
            max_results=limit
        )
        
        # flights 已經是格式化好的 dict list，不需再用 schema dump
        return api_response(
            success=True,
            message=f"成功獲取 {len(flights)} 筆從台灣出發的航班",
            data=flights
        )
    except ValueError:
        return api_response(success=False, message="日期格式錯誤，應為 YYYY-MM-DD", status_code=400)
    except Exception as e:
        logger.error(f"異步獲取從台灣出發航班時出錯: {e}", exc_info=True)
        return api_response(success=False, message="伺服器內部錯誤", status_code=500)