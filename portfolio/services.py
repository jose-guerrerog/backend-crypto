import requests
import time
from django.core.cache import cache
from typing import Dict, List, Optional
from datetime import datetime
from .models import Portfolio

from dataclasses import dataclass

@dataclass
class CoinData:
    id: str
    symbol: str
    name: str
    current_price: float
    market_cap: float
    price_change_24h: float
    price_change_percentage_24h: float
    volume_24h: float
    last_updated: datetime

@dataclass
class PortfolioMetrics:
    total_value: float
    total_cost: float
    total_profit_loss: float
    profit_loss_percentage: float
    best_performer: Optional[Dict]
    worst_performer: Optional[Dict]
    asset_allocation: Dict[str, float]

class CoinGeckoService:
    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0
        self.rate_limit_delay = 1.2

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)

        try:
            url = f"{self.BASE_URL}{endpoint}"
            response = self.session.get(url, params=params or {}, timeout=10)
            self.last_request_time = time.time()
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ API Error {response.status_code}: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None

    def get_coin_data(self, coin_ids: List[str]) -> Dict[str, CoinData]:
        if not coin_ids:
            return {}

        coin_ids_sorted = sorted(coin_ids[:250])
        coin_ids_str = ",".join(coin_ids_sorted)
        cache_key = f"coin_data:{coin_ids_str}"
        cached_data = cache.get(cache_key)
        if cached_data:
            print(f"✅ Using cached data for: {coin_ids_str}")
            return cached_data

        params = {
            'ids': coin_ids_str,
            'vs_currencies': 'usd',
            'include_market_cap': 'true',
            'include_24hr_vol': 'true',
            'include_24hr_change': 'true',
            'include_last_updated_at': 'true'
        }

        data = self._make_request("/simple/price", params)
        if not data:
            return {}

        result = {}
        for coin_id, coin_data in data.items():
            result[coin_id] = CoinData(
                id=coin_id,
                symbol="",
                name="",
                current_price=coin_data.get('usd', 0),
                market_cap=coin_data.get('usd_market_cap', 0),
                price_change_24h=0,
                price_change_percentage_24h=coin_data.get('usd_24h_change', 0),
                volume_24h=coin_data.get('usd_24h_vol', 0),
                last_updated=datetime.now()
            )

        cache.set(cache_key, result, timeout=300)
        print(f"📦 Cached data for: {coin_ids_str}")

        return result

    def get_detailed_coin_data(self, coin_ids: List[str]) -> Dict[str, CoinData]:
        if not coin_ids:
            return {}

        coin_ids_sorted = sorted(coin_ids[:250])
        coin_ids_str = ",".join(coin_ids_sorted)
        cache_key = f"detailed_data:{coin_ids_str}"

        cached = cache.get(cache_key)
        if cached:
            print(f"✅ Using cached detailed data for: {coin_ids_str}")
            return cached

        params = {
            'ids': coin_ids_str,
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 250,
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '24h'
        }

        data = self._make_request("/coins/markets", params)
        if not data:
            print(f"⚠️ CoinGecko returned no data for: {coin_ids_str}")
            return {}

        result = {}
        for coin in data:
            result[coin['id']] = CoinData(
                id=coin['id'],
                symbol=coin['symbol'].upper(),
                name=coin['name'],
                current_price=coin['current_price'] or 0,
                market_cap=coin['market_cap'] or 0,
                price_change_24h=coin.get('price_change_24h', 0) or 0,
                price_change_percentage_24h=coin.get('price_change_percentage_24h', 0) or 0,
                volume_24h=coin.get('total_volume', 0) or 0,
                last_updated=datetime.now()
            )

        cache.set(cache_key, result, timeout=300)
        print(f"📦 Cached detailed data for: {coin_ids_str}")
        return result

    def search_coins(self, query: str) -> List[Dict]:
        params = {'query': query}
        data = self._make_request("/search", params)
        if data and 'coins' in data:
            return data['coins'][:20]
        return []
