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
        """獲取或創建一個 aiohttp ClientSession，配置適當的連接參數。"""
        if self._session is None or self._session.closed:
            # 配置連接器以優化連接管理
            connector = aiohttp.TCPConnector(
                limit=30,  # 總連接池大小
                limit_per_host=10,  # 每個主機的連接數限制
                ttl_dns_cache=300,  # DNS 緩存 5 分鐘
                use_dns_cache=True,
                keepalive_timeout=60,  # 保持連接 60 秒
                enable_cleanup_closed=True
            )
            
            # 配置超時設置
            timeout = aiohttp.ClientTimeout(
                total=120,  # 總超時 2 分鐘
                connect=30,  # 連接超時 30 秒
                sock_read=60  # 讀取超時 60 秒
            )
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                raise_for_status=False  # 手動處理 HTTP 錯誤
            )
        return self._session

    async def close_session(self):
        """關閉 aiohttp ClientSession。"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _get_access_token(self):
        """異步獲取或刷新 Amadeus API 的 access token。"""
        # 如果已經有 token，直接返回（Amadeus token 通常有效期 30 分鐘）
        if self._access_token:
            return self._access_token
            
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

    async def get_supported_destinations(self, origin_code: str) -> List[Dict[str, Any]]:
        """
        獲取指定出發地的 Amadeus 支援目的地，並結合本地資料庫的中文名稱
        
        Args:
            origin_code: 出發機場的 IATA 代碼
            
        Returns:
            List[Dict]: 包含機場代碼、中文名稱和英文名稱的目的地列表
        """
        # 首先從 Amadeus 獲取直達目的地
        amadeus_response = await self.get_airport_destinations(origin_code)
        
        if "error" in amadeus_response:
            logger.error(f"Failed to get destinations from Amadeus: {amadeus_response['error']}")
            return []
        
        amadeus_destinations = amadeus_response.get('data', [])
        if not amadeus_destinations:
            return []
        
        # 提取機場代碼
        airport_codes = [dest['iataCode'] for dest in amadeus_destinations if 'iataCode' in dest]
        
        if not airport_codes:
            return []
        
        # 從本地資料庫獲取中文名稱
        from ..services.airport_service import airport_service
        
        enriched_destinations = []
        for code in airport_codes:
            # 查詢本地資料庫中的機場資訊
            local_airport = await airport_service.get_airport_by_iata(code)
            
            if local_airport:
                # 使用本地資料庫的中文名稱
                enriched_destinations.append({
                    'code': code,
                    'name': local_airport.get('name_zh') or local_airport.get('name_en', code),
                    'name_en': local_airport.get('name_en', ''),
                    'name_zh': local_airport.get('name_zh', ''),
                    'city': local_airport.get('city', ''),
                    'country': local_airport.get('country', '')
                })
            else:
                # 如果本地資料庫沒有，使用機場代碼作為顯示名稱
                enriched_destinations.append({
                    'code': code,
                    'name': code,
                    'name_en': '',
                    'name_zh': '',
                    'city': '',
                    'country': '',
                    'needs_manual_update': True  # 標記需要手動更新
                })
        
        logger.info(f"Successfully enriched {len(enriched_destinations)} destinations for {origin_code}")
        return enriched_destinations

# 創建一個單例實例
amadeus_service = AmadeusService() 