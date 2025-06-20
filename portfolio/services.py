import requests
import time
import json
import logging
from typing import Dict, Optional, List
from .models import Portfolio, Transaction
from .schemas import PortfolioMetrics, Performer

logger = logging.getLogger(__name__)

class CoinGeckoService:
    BASE_URL = "https://api.coingecko.com/api/v3"
    PROXY_BASE = "https://api.allorigins.win/get"

    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0

    def _proxy_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        try:
            now = time.time()
            elapsed = now - self.last_request_time
            if elapsed < 1.3:
                time.sleep(1.3 - elapsed)

            url = f"{self.BASE_URL}{endpoint}"
            param_str = "&".join(f"{key}={value}" for key, value in params.items())
            full_url = f"{url}?{param_str}"
            proxy_url = f"{self.PROXY_BASE}?url={requests.utils.quote(full_url)}"

            logger.info(f"🌐 Requesting CoinGecko via proxy: {proxy_url}")
            response = self.session.get(proxy_url, timeout=10)
            self.last_request_time = time.time()

            if response.status_code == 200:
                wrapper = response.json()
                if 'contents' in wrapper:
                    return json.loads(wrapper['contents'])
                else:
                    logger.warning("Proxy response missing 'contents'")
            else:
                logger.warning(f"Proxy request failed with {response.status_code}")
        except Exception as e:
            logger.error(f"Proxy request failed: {e}")
        return None

    def get_current_prices(self, coin_ids: List[str]) -> Dict[str, float]:
        endpoint = "/simple/price"
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd"
        }

        # Try proxy request
        prices = self._proxy_request(endpoint, params)
        if prices:
            logger.info(f"✅ CoinGecko prices fetched: {prices}")
            return prices

        logger.warning(f"⚠️ CoinGecko returned no usable data for: {','.join(coin_ids)}")
        return {}

coingecko_service = CoinGeckoService()

class PortfolioAnalytics:
    def __init__(self, price_service: CoinGeckoService):
        self.price_service = price_service

    def calculate_portfolio_metrics(self, portfolio: Portfolio) -> PortfolioMetrics:
        transactions = portfolio.transactions.all()
        logger.info(f"🧠 Portfolio: {portfolio.name} ({portfolio.id}) - {transactions.count()} transactions")

        if not transactions.exists():
            return PortfolioMetrics(
                total_value=0,
                total_cost=0,
                total_profit_loss=0,
                profit_loss_percentage=0,
                best_performer=None,
                worst_performer=None,
                asset_allocation={}
            )

        coin_ids = list(set(tx.coin_id.lower() for tx in transactions))
        prices = self.price_service.get_current_prices(coin_ids)
        logger.info(f"🔍 CoinGecko prices fetched:\n{prices}")

        if not prices:
            return PortfolioMetrics(
                total_value=0,
                total_cost=0,
                total_profit_loss=0,
                profit_loss_percentage=0,
                best_performer=None,
                worst_performer=None,
                asset_allocation={}
            )

        performance = {}

        for tx in transactions:
            current_price = prices.get(tx.coin_id.lower(), {}).get("usd", 0)
            value = tx.amount * current_price
            cost = tx.amount * tx.price_usd

            if tx.coin_id not in performance:
                performance[tx.coin_id] = {
                    "cost": 0,
                    "value": 0,
                    "name": tx.coin_name,
                    "symbol": tx.coin_symbol
                }

            performance[tx.coin_id]["cost"] += cost
            performance[tx.coin_id]["value"] += value

        total_cost = sum(p["cost"] for p in performance.values())
        total_value = sum(p["value"] for p in performance.values())
        profit_loss = total_value - total_cost
        profit_loss_pct = (profit_loss / total_cost * 100) if total_cost else 0

        best = None
        worst = None
        best_pct = float('-inf')
        worst_pct = float('inf')

        for coin_id, data in performance.items():
            if data["cost"] == 0:
                continue
            pct = ((data["value"] - data["cost"]) / data["cost"]) * 100
            if pct > best_pct:
                best_pct = pct
                best = Performer(
                    coin_id=coin_id,
                    coin_name=data["name"],
                    coin_symbol=data["symbol"],
                    profit_loss_percentage=pct,
                    profit_loss=data["value"] - data["cost"]
                )
            if pct < worst_pct:
                worst_pct = pct
                worst = Performer(
                    coin_id=coin_id,
                    coin_name=data["name"],
                    coin_symbol=data["symbol"],
                    profit_loss_percentage=pct,
                    profit_loss=data["value"] - data["cost"]
                )

        asset_allocation = {
            data["name"]: (data["value"] / total_value * 100 if total_value else 0)
            for data in performance.values()
        }

        return PortfolioMetrics(
            total_value=total_value,
            total_cost=total_cost,
            total_profit_loss=profit_loss,
            profit_loss_percentage=profit_loss_pct,
            best_performer=best,
            worst_performer=worst,
            asset_allocation=asset_allocation
        )

portfolio_analytics = PortfolioAnalytics(coingecko_service)
