"""
Flask應用啟動腳本
"""
import os
from app import create_app
from flask import jsonify

# 創建Flask應用
app = create_app()

# 添加測試路由檢查可用航班
@app.route('/api/debug/flights', methods=['GET'])
def debug_flights():
    """列出資料庫中所有航班的基本信息，用於偵錯"""
    from app.models import Flight, Airport, Airline
    
    flights = Flight.query.limit(10).all()
    result = []
    
    for flight in flights:
        try:
            departure_airport = Airport.query.get(flight.departure_airport_id)
            arrival_airport = Airport.query.get(flight.arrival_airport_id)
            airline = Airline.query.get(flight.airline_id)
            
            result.append({
                'flight_id': str(flight.flight_id),
                'flight_number': flight.flight_number,
                'departure': {
                    'airport_id': str(departure_airport.airport_id) if departure_airport else None,
                    'code': departure_airport.iata_code if departure_airport else None,
                    'name': departure_airport.name_zh if departure_airport else None
                },
                'arrival': {
                    'airport_id': str(arrival_airport.airport_id) if arrival_airport else None,
                    'code': arrival_airport.iata_code if arrival_airport else None,
                    'name': arrival_airport.name_zh if arrival_airport else None
                },
                'airline': {
                    'code': airline.iata_code if airline else None,
                    'name': airline.name_zh if airline else None
                },
                'departure_time': flight.scheduled_departure.isoformat() if flight.scheduled_departure else None,
                'status': flight.status
            })
        except Exception as e:
            result.append({
                'flight_id': str(flight.flight_id),
                'error': str(e)
            })
    
    return jsonify(result)

@app.route('/api/debug/airports', methods=['GET'])
def debug_airports():
    """列出資料庫中所有機場，用於偵錯"""
    from app.models import Airport
    
    airports = Airport.query.all()
    result = [{
        'airport_id': str(airport.airport_id),
        'iata_code': airport.iata_code,
        'name_zh': airport.name_zh,
        'name_en': airport.name_en,
        'city': airport.city,
        'country': airport.country
    } for airport in airports]
    
    return jsonify(result)

if __name__ == '__main__':
    # 獲取端口，如果環境變量中沒有設置，使用默認值5000
    port = int(os.environ.get('PORT', 5000))
    
    # 啟動應用
    app.run(host='0.0.0.0', port=port, debug=True)

