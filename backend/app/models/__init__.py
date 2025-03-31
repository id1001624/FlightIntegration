"""
模型初始化模塊

此模塊導入所有數據模型，確保它們在應用啟動時被加載
"""
from .base import db
from .airport import Airport
from .airline import Airline
from .flight import Flight
from .user import User
from .ticket_price import TicketPrice
from .price_history import PriceHistory
from .weather import Weather
from .user_search_history import UserSearchHistory
from .common_phrase import CommonPhrase
from .user_query import UserQuery
from .flight_prediction import FlightPrediction

# 導出所有模型，方便直接從models模塊導入
__all__ = [
    'db',
    'Airport',
    'Airline',
    'Flight',
    'User',
    'TicketPrice',
    'PriceHistory',
    'Weather',
    'UserSearchHistory',
    'CommonPhrase',
    'UserQuery',
    'FlightPrediction',
    'FlightDelay'
]
