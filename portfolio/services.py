from .coingecko import coingecko_service
from .schemas import PortfolioMetrics, Performer
import logging

logger = logging.getLogger(__name__)

class PortfolioAnalytics:
    def __init__(self):
        self.price_service = coingecko_service

    def calculate_portfolio_metrics(self, portfolio):
        from .models import Portfolio, Transaction  # lazy import

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
        prices = self.price_service.get_prices(coin_ids)
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

            profit = data["value"] - data["cost"]
            pct = (profit / data["cost"]) * 100

            performer = Performer(
                coin_id=coin_id,
                coin_name=data["name"],
                coin_symbol=data["symbol"],
                profit_loss_percentage=pct,
                profit_loss=profit
            )

            if pct > best_pct:
                best_pct = pct
                best = performer

            if pct < worst_pct and coin_id != best.coin_id:
                worst_pct = pct
                worst = performer

        if best and not worst:
            worst = best

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

portfolio_analytics = PortfolioAnalytics()
