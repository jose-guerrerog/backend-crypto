import requests
import time
import json
import logging
from django.core.cache import cache
from typing import List, Dict

logger = logging.getLogger(__name__)

CACHE_KEY = "cached_crypto_prices"
CACHE_TTL = 60  # seconds

class CoinGeckoService:
    BASE_URL = "https://api.coingecko.com/api/v3"
    PROXY_BASE = "https://api.allorigins.win/get"

    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0

    def get_prices(self, coin_ids: List[str]) -> Dict:
        cached = cache.get(CACHE_KEY)
        if cached:
            logger.info("✅ Using cached CoinGecko prices")
            return cached

        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < 1.3:
            time.sleep(1.3 - elapsed)

        endpoint = f"{self.BASE_URL}/simple/price"
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_last_updated_at": "true"
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        full_url = f"{endpoint}?{query}"
        proxy_url = f"{self.PROXY_BASE}?url={requests.utils.quote(full_url)}"

        try:
            logger.info(f"🌐 Requesting CoinGecko via proxy: {proxy_url}")
            response = self.session.get(proxy_url, timeout=10)
            self.last_request_time = time.time()

            if response.status_code == 200:
                wrapper = response.json()
                if 'contents' in wrapper:
                    prices = json.loads(wrapper['contents'])
                    if 'status' in prices and prices['status'].get('error_code') == 429:
                        raise Exception("Rate limited")
                    cache.set(CACHE_KEY, prices, timeout=CACHE_TTL)
                    return prices
        except Exception as e:
            logger.warning(f"🛑 CoinGecko error: {e}")

        return cache.get(CACHE_KEY, {})

coingecko_service = CoinGeckoService()