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
            if cached:
                logger.info("✅ Using cached CoinGecko prices")
                return cached
        except ConnectionInterrupted:
            logger.warning("⚠️ Redis unavailable when reading cache.")

        # Build proxied request URL
        try:
            query = f"ids={','.join(coin_ids)}&vs_currencies=usd&include_24hr_change=true&include_last_updated_at=true"
            target_url = f"{self.BASE_URL}/simple/price?{query}"
            proxy_url = f"https://api.allorigins.win/get?url={requests.utils.quote(target_url)}"

            logger.info(f"🌐 Fetching CoinGecko data via proxy: {proxy_url}")
            response = self.session.get(proxy_url, timeout=10)
            response.raise_for_status()

            # Parse the inner contents (wrapped JSON)
            content = response.json().get("contents")
            prices = json.loads(content)

            logger.info(f"✅ Prices fetched via proxy: {prices}")

            # Cache the result
            try:
                cache.set(CACHE_KEY, prices, timeout=CACHE_TTL)
            except ConnectionInterrupted:
                logger.warning("⚠️ Redis unavailable when writing to cache.")

            return prices

        except Exception as e:
            logger.warning(f"🚨 Proxy fetch error: {e}")

        # Fallback: empty result
        return {}

coingecko_service = CoinGeckoService()