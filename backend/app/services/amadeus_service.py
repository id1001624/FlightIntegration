import os
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class AmadeusService:
    def __init__(self):
        self.base_url = "https://test.api.amadeus.com"
        self.api_key = os.environ.get("AMADEUS_API_KEY")
        self.api_secret = os.environ.get("AMADEUS_API_SECRET")
        if not self.api_key or not self.api_secret:
            raise ValueError("AMADEUS_API_KEY and AMADEUS_API_SECRET must be set in .env file")
        self._access_token = None
        self._session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """獲取或創建一個 aiohttp ClientSession。"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close_session(self):
        """關閉 aiohttp ClientSession。"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _get_access_token(self):
        """異步獲取或刷新 Amadeus API 的 access token。"""
        url = f"{self.base_url}/v1/security/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret
        }
        try:
            session = await self._get_session()
            async with session.post(url, headers=headers, data=body) as response:
                response.raise_for_status()
                data = await response.json()
                self._access_token = data.get("access_token")
                logger.info("Successfully retrieved Amadeus access token.")
            return self._access_token
        except aiohttp.ClientError as e:
            logger.error(f"Failed to get Amadeus access token: {e}")
            return None

    async def get_airlines_by_codes(self, airline_codes: List[str]) -> List[Dict[str, Any]]:
        """根據 IATA 代碼列表異步獲取航空公司資訊。"""
        token = await self._get_access_token()
        if not token:
            return []

        url = f"{self.base_url}/v1/reference-data/airlines"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"airlineCodes": ",".join(airline_codes)}

        try:
            session = await self._get_session()
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                result = await response.json()
                logger.info(f"Successfully fetched details for {len(result.get('data', []))} airlines.")
                return result.get('data', [])
        except aiohttp.ClientError as e:
            logger.error(f"Failed to get airline details: {e}")
            return []

    async def search_flight_destinations(self, origin_iata_code, max_price=None):
        """異步查詢從指定機場出發的航班目的地。"""
        token = await self._get_access_token()
        if not token:
            return None

        url = f"{self.base_url}/v1/shopping/flight-destinations"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"origin": origin_iata_code}
        if max_price:
            params["maxPrice"] = max_price

        try:
            session = await self._get_session()
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                logger.info(f"Successfully fetched flight destinations for {origin_iata_code}.")
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Failed to search flight destinations: {e}")
            response_json = await response.json() if response else "No response"
            return {"error": str(e), "details": response_json}

    async def search_flight_offers(self, origin, destination, departure_date, adults=1, max_results=10):
        """異步查詢具體航班報價。"""
        token = await self._get_access_token()
        if not token:
            return None

        url = f"{self.base_url}/v2/shopping/flight-offers"
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "nonStop": "false",
            "currencyCode": "TWD",
            "max": max_results
        }

        try:
            session = await self._get_session()
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                logger.info(f"Successfully fetched flight offers for {origin}->{destination} on {departure_date}. Count: {len(data.get('data', []))}")
                return data
        except aiohttp.ClientError as e:
            logger.error(f"Failed to search flight offers: {e}")
            response_json = await response.json() if response else "No response"
            return {"error": str(e), "details": response_json}

    async def get_airport_destinations(self, departure_airport_code: str, max_results: int = 100) -> Dict[str, Any]:
        """
        異步獲取從指定機場出發的所有直達目的地。
        使用 Amadeus Airport Routes API。
        
        Args:
            departure_airport_code: 出發機場的 IATA 代碼 (如: 'TPE')
            max_results: 最大返回結果數量 (預設: 100)
            
        Returns:
            Dict: 包含目的地資訊的字典
        """
        token = await self._get_access_token()
        if not token:
            return {"error": "Failed to get access token"}

        url = f"{self.base_url}/v1/airport/direct-destinations"
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "departureAirportCode": departure_airport_code,
            "max": max_results
        }

        try:
            session = await self._get_session()
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                logger.info(f"Successfully fetched {len(data.get('data', []))} destinations for airport {departure_airport_code}")
                return data
        except aiohttp.ClientError as e:
            logger.error(f"Failed to get airport destinations for {departure_airport_code}: {e}")
            # 嘗試獲取響應內容以獲得更詳細的錯誤信息
            try:
                if response.status != 200:
                    error_data = await response.json()
                    return {"error": str(e), "details": error_data}
            except Exception:
                pass
            return {"error": str(e), "details": "No additional error details available"}

# 創建一個單例實例
amadeus_service = AmadeusService() 