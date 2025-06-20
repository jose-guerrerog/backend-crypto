import requests
import time
import json
from django.core.cache import cache
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import urlencode, quote
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
            target_url = f"{self.BASE_URL}{endpoint}"
            if params:
                query = urlencode(params)
                target_url = f"{target_url}?{query}"

            proxy_url = f"https://api.allorigins.win/get?url={quote(target_url)}"
            response = self.session.get(proxy_url, timeout=10)
            self.last_request_time = time.time()

            if response.status_code == 200:
                proxy_data = response.json()
                if 'contents' in proxy_data:
                    try:
                        contents = proxy_data['contents'].encode('utf-8', 'surrogatepass').decode('utf-8', 'ignore')
                        return json.loads(contents)
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                        return None
                else:
                    print("⚠️ No 'contents' in AllOrigins response")
                    return None
            else:
                print(f"❌ Proxy request failed [{response.status_code}] on {proxy_url}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None

    def get_detailed_coin_data(self, coin_ids: List[str]) -> Dict[str, CoinData]:
        if not coin_ids:
            return {}

        coin_ids_sorted = sorted(coin_ids[:250])
        coin_ids_str = ",".join(coin_ids_sorted)
        cache_key = f"detailed_data:{coin_ids_str}"

        try:
            cached = cache.get(cache_key)
        except Exception as e:
            print(f"⚠️ Redis cache error: {e}")
            cached = None

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
        if not data or not isinstance(data, list):
            print(f"⚠️ CoinGecko returned no usable data for: {coin_ids_str}")
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
