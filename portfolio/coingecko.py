import json
import logging
import time
import hashlib
import requests
from typing import List, Dict
from django.core.cache import cache
from django_redis.exceptions import ConnectionInterrupted

logger = logging.getLogger(__name__)

CACHE_TTL = 180           # Cache duration in seconds
LOCK_TIMEOUT = 10         # Lock timeout
POLL_INTERVAL = 0.5       # Poll every 500ms
MAX_WAIT_TIME = LOCK_TIMEOUT + 2  # Max wait for cache population

class CoinGeckoService:
    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self):
        self.session = requests.Session()

    def get_prices(self, coin_ids: List[str]) -> Dict:
        sorted_ids = sorted(coin_ids)
        key_hash = hashlib.md5(",".join(sorted_ids).encode()).hexdigest()
        cache_key = f"cached_crypto_prices:{key_hash}"
        lock_key = f"{cache_key}:lock"

        try:
            cached = cache.get(cache_key)
            if cached:
                logger.info("✅ Using cached CoinGecko prices")
                return cached
        except ConnectionInterrupted:
            logger.warning("⚠️ Redis unavailable while reading cache.")

        if cache.add(lock_key, "locked", LOCK_TIMEOUT):
            try:
                query_ids = ",".join(sorted_ids)
                direct_url = (
                    f"{self.BASE_URL}/simple/price?"
                    f"ids={query_ids}&vs_currencies=usd"
                    f"&include_24hr_change=true&include_last_updated_at=true"
                )
                proxy_url = f"https://api.allorigins.win/get?url={requests.utils.quote(direct_url)}"
                logger.info(f"🌐 Fetching CoinGecko data via proxy: {proxy_url}")

                response = self.session.get(proxy_url, timeout=10)
                if response.status_code != 200:
                    logger.warning(f"🚨 Proxy response failed: {response.status_code}")
                    return {}

                raw = response.json()
                if "contents" not in raw:
                    logger.warning("🚨 Missing 'contents' in proxy response")
                    return {}

                prices = json.loads(raw["contents"])
                if "status" in prices and "error_code" in prices["status"]:
                    logger.warning(f"🚨 API error (not caching): {prices}")
                    return {}

                logger.info(f"🔍 Prices fetched: {prices}")
                try:
                    cache.set(cache_key, prices, timeout=CACHE_TTL)
                except ConnectionInterrupted:
                    logger.warning("⚠️ Redis unavailable while writing cache.")

                return prices

            except Exception as e:
                logger.warning(f"🚨 Proxy fetch error: {e}")
                return {}

            finally:
                cache.delete(lock_key)

        logger.info("⏳ Waiting for another request to populate cache...")
        waited = 0
        while waited < MAX_WAIT_TIME:
            try:
                fallback = cache.get(cache_key)
                if fallback:
                    logger.info("✅ Fetched from cache after waiting")
                    return fallback
            except ConnectionInterrupted:
                logger.warning("⚠️ Redis unavailable during polling.")
                break

            time.sleep(POLL_INTERVAL)
            waited += POLL_INTERVAL

        logger.warning("⏰ Timeout waiting for cache.")
        return {}

# Singleton
coingecko_service = CoinGeckoService()
