# services.py
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

    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        try:
            now = time.time()
            elapsed = now - self.last_request_time
            if elapsed < 1.3:
                time.sleep(1.3 - elapsed)

            target_url = f"{self.BASE_URL}{endpoint}"
            logger.info(f"🌐 Requesting CoinGecko directly: {target_url} with {params}")
            response = self.session.get(target_url, params=params, timeout=10)
            self.last_request_time = time.time()

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"⚠️ CoinGecko direct request failed with status {response.status_code}")
                return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception while calling CoinGecko directly: {e}")
            return None
        # try:
        #     now = time.time()
        #     elapsed = now - self.last_request_time
        #     if elapsed < 1.3:
        #         time.sleep(1.3 - elapsed)

        #     target_url = f"{self.BASE_URL}{endpoint}"
        #     logger.info(f"🌐 Requesting CoinGecko directly: {target_url} with {params}")

        #     # param_str = "&".join(f"{key}={value}" for key, value in params.items())

        #     # proxy_url = f"https://api.allorigins.win/get?url={requests.utils.quote(target_url + '?' + param_str)}"

        #     # logger.info(f"Requesting CoinGecko (via proxy): {proxy_url}")
        #     # response = self.session.get(proxy_url, timeout=10)
        #     response = self.session.get(target_url, params=params, timeout=10)

        #     # response = self.session.get(target_url, params=params, timeout=10)

        #     self.last_request_time = time.time()

        #     if response.status_code == 200:
        #         proxy_data = response.json()
        #         if 'contents' in proxy_data:
        #             try:
        #                 return json.loads(proxy_data['contents'])
        #             except json.JSONDecodeError as e:
        #                 logger.error(f"JSON decode error from proxy response: {e}")
        #                 return None
        #         else:
        #             logger.warning("Proxy response missing 'contents'")
        #             return None
        #     else:
        #         logger.error(f"Proxy request failed with status {response.status_code}")
        #         return None
        # except requests.exceptions.RequestException as e:
        #     logger.error(f"Request exception while calling CoinGecko: {e}")
        #     return None

    def get_current_prices(self, coin_ids: List[str]) -> Dict[str, float]:
        endpoint = "/simple/price"
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd"
        }
        result = self._make_request(endpoint, params)
        if result is None:
            logger.warning(f"⚠️ CoinGecko returned no usable data for: {','.join(coin_ids)}")
            return {}
        return result

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

        # Normalize coin_ids
        coin_ids = list(set(tx.coin_id.lower() for tx in transactions))
        prices = self.price_service.get_current_prices(coin_ids)
        print("📉 CoinGecko prices:", prices)
        print("🪙 Coin IDs being used:", coin_ids)
        logger.info(f"🔍 CoinGecko prices fetched:\n{json.dumps(prices, indent=2)}")

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
            coin_id = tx.coin_id.lower()
            current_price = prices.get(coin_id, {}).get("usd", 0)
            value = tx.amount * current_price
            cost = tx.amount * tx.price_usd

            logger.debug(f"📈 {coin_id}: current_price={current_price}, amount={tx.amount}, value={value}, cost={cost}")

            if coin_id not in performance:
                performance[coin_id] = {
                    "cost": 0,
                    "value": 0,
                    "name": tx.coin_name,
                    "symbol": tx.coin_symbol
                }

            performance[coin_id]["cost"] += cost
            performance[coin_id]["value"] += value

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

        logger.debug(f"📊 Final Asset Allocation:\n{json.dumps(asset_allocation, indent=2)}")

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
