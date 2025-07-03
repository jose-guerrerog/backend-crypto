import json
import logging
import time
import requests
from typing import List, Dict
from django.core.cache import cache
from django_redis.exceptions import ConnectionInterrupted

logger = logging.getLogger(__name__)

CACHE_KEY = "cached_crypto_prices"
CACHE_TTL = 60  # seconds

class CoinGeckoService:
    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self):
        self.session = requests.Session()

    def get_prices(self, coin_ids: List[str]) -> Dict:
        # Try cache first
        try:
            cached = cache.get(CACHE_KEY)
        except ConnectionInterrupted:
            logger.warning("⚠️ Redis unavailable while reading cache.")
            cached = None

        if cached:
            logger.info("✅ Using cached CoinGecko prices")
            return cached

        # Build proxy-wrapped URL
        query_ids = ",".join(coin_ids)
        target_url = (
            f"{self.BASE_URL}/simple/price?"
            f"ids={query_ids}&vs_currencies=usd"
            f"&include_24hr_change=true&include_last_updated_at=true"
        )
        proxy_url = f"https://api.allorigins.win/get?url={requests.utils.quote(target_url)}"

        try:
            logger.info(f"🌐 Fetching CoinGecko data via proxy: {proxy_url}")
            response = self.session.get(proxy_url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"🚨 Proxy response failed: {response.status_code}")
                return cache.get(CACHE_KEY, {}) or {}

            raw = response.json()

            # Parse the actual JSON payload from `contents`
            if "contents" not in raw:
                logger.warning("🚨 Missing 'contents' in proxy response")
                return cache.get(CACHE_KEY, {}) or {}

            prices = json.loads(raw["contents"])

            if "status" in prices and "error_code" in prices["status"]:
                logger.warning(f"🚨 CoinGecko error response (not caching): {prices}")
                return cache.get(CACHE_KEY, {}) or {}

            logger.info(f"🔍 CoinGecko prices fetched: {prices}")
            try:
                cache.set(CACHE_KEY, prices, timeout=CACHE_TTL)
            except ConnectionInterrupted:
                logger.warning("⚠️ Redis unavailable while writing cache.")

            return prices

        except Exception as e:
            logger.warning(f"🚨 CoinGecko fetch error: {e}")
            return cache.get(CACHE_KEY, {}) or {}

coingecko_service = CoinGeckoService()
