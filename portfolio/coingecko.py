import os
import time
import json
import logging
import requests
from typing import List, Dict
from django.core.cache import cache
from django_redis.exceptions import ConnectionInterrupted

logger = logging.getLogger(__name__)

CACHE_KEY = "cached_crypto_prices"
CACHE_TTL = 60  # Cache time in seconds

class CoinGeckoService:
    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0
        self.api_key = os.getenv("COINGECKO_API_KEY")

    def get_prices(self, coin_ids: List[str]) -> Dict:
        # Try to get from cache
        try:
            cached = cache.get(CACHE_KEY)
        except ConnectionInterrupted:
            logger.warning("⚠️ Redis unavailable while trying to read cache.")
            cached = None

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

        headers = {
            "x-cg-demo-api-key": self.api_key  # Use 'x-cg-pro-api-key' if on paid plan
        }

        try:
            logger.info(f"🌐 Requesting CoinGecko API: {endpoint} with {params}")
            response = self.session.get(endpoint, params=params, headers=headers, timeout=10)
            self.last_request_time = time.time()

            if response.status_code == 200:
                prices = response.json()
                logger.info(f"🔍 CoinGecko prices fetched: {prices}")
                try:
                    cache.set(CACHE_KEY, prices, timeout=CACHE_TTL)
                except ConnectionInterrupted:
                    logger.warning("⚠️ Redis unavailable while trying to write cache.")
                return prices
            else:
                logger.warning(f"🚨 CoinGecko API error: {response.status_code} - {response.text}")
        except Exception as e:
            logger.warning(f"🚨 CoinGecko fetch error: {e}")

        # Fallback to old cache
        try:
            return cache.get(CACHE_KEY, {})
        except ConnectionInterrupted:
            logger.warning("⚠️ Redis unavailable on fallback.")
            return {}

coingecko_service = CoinGeckoService()
