# portfolio/services.py
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

    def get_coin_data(self, coin_ids: List[str]) -> Dict[str, CoinData]:
        if not coin_ids:
            return {}

        coin_ids_sorted = sorted(coin_ids[:250])
        coin_ids_str = ",".join(coin_ids_sorted)
        cache_key = f"coin_data:{coin_ids_str}"

        try:
            cached = cache.get(cache_key)
        except Exception as e:
            print(f"⚠️ Redis cache error: {e}")
            cached = None

        if cached:
            print(f"✅ Using cached data for: {coin_ids_str}")
            return cached

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
            'vs_currency': 'usd',  # ✅ This is the correct param
            'order': 'market_cap_desc',
            'per_page': 250,
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '24h'
        }

        data = self._make_request("/coins/markets", params)
        print(f"📊 Raw API response: {data}")
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

    def search_coins(self, query: str) -> List[Dict]:
        params = {'query': query}
        data = self._make_request("/search", params)
        if data and 'coins' in data:
            return data['coins'][:20]
        return []

class PortfolioAnalytics:
    def __init__(self, coingecko_service: CoinGeckoService):
        self.coingecko = coingecko_service

    def calculate_portfolio_metrics(self, portfolio: Portfolio) -> PortfolioMetrics:
        transactions = portfolio.transactions.all()
        print(f"📊 Retrieved {transactions.count()} transactions for portfolio {portfolio.id}")

        if not transactions.exists():
            print(f"⚠️ No transactions found for portfolio {portfolio.id}")
            return PortfolioMetrics(
                total_value=0,
                total_cost=0,
                total_profit_loss=0,
                profit_loss_percentage=0,
                best_performer=None,
                worst_performer=None,
                asset_allocation={}
            )

        coin_ids = list(set(t.coin_id for t in transactions))
        current_prices = self.coingecko.get_detailed_coin_data(coin_ids)

        holdings = {}

        for transaction in transactions:
            coin_id = transaction.coin_id
            if coin_id not in holdings:
                holdings[coin_id] = {
                    'amount': 0,
                    'cost_basis': 0,
                    'coin_name': transaction.coin_name,
                    'coin_symbol': transaction.coin_symbol
                }

            if transaction.transaction_type == 'buy':
                holdings[coin_id]['amount'] += transaction.amount
                holdings[coin_id]['cost_basis'] += transaction.amount * transaction.price_usd
            else:
                holdings[coin_id]['amount'] -= transaction.amount
                holdings[coin_id]['cost_basis'] -= transaction.amount * transaction.price_usd

        holdings = {k: v for k, v in holdings.items() if v['amount'] > 0}

        print(f"✅ Current prices: {current_prices}")
        print(f"🪙 Holdings: {holdings}")

        total_value = 0
        total_cost = 0
        best_performer = None
        worst_performer = None
        asset_allocation = {}

        for coin_id, holding in holdings.items():
            current_price = current_prices.get(coin_id)
            if current_price:
                current_value = holding['amount'] * current_price.current_price
                cost_basis = holding['cost_basis']
                profit_loss = current_value - cost_basis
                profit_loss_pct = (profit_loss / cost_basis * 100) if cost_basis > 0 else 0

                holding['current_value'] = current_value
                holding['profit_loss'] = profit_loss
                holding['profit_loss_percentage'] = profit_loss_pct
                holding['current_price'] = current_price.current_price

                total_value += current_value
                total_cost += cost_basis

                if best_performer is None or profit_loss_pct > best_performer['profit_loss_percentage']:
                    best_performer = {
                        'coin_id': coin_id,
                        'coin_name': holding['coin_name'],
                        'coin_symbol': holding['coin_symbol'],
                        'profit_loss_percentage': profit_loss_pct,
                        'profit_loss': profit_loss
                    }

                if worst_performer is None or profit_loss_pct < worst_performer['profit_loss_percentage']:
                    worst_performer = {
                        'coin_id': coin_id,
                        'coin_name': holding['coin_name'],
                        'coin_symbol': holding['coin_symbol'],
                        'profit_loss_percentage': profit_loss_pct,
                        'profit_loss': profit_loss
                    }

        for coin_id, holding in holdings.items():
            if 'current_value' in holding and total_value > 0:
                allocation_pct = (holding['current_value'] / total_value) * 100
                asset_allocation[f"{holding['coin_symbol']} ({holding['coin_name']})"] = allocation_pct

        total_profit_loss = total_value - total_cost
        profit_loss_percentage = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0

        return PortfolioMetrics(
            total_value=total_value,
            total_cost=total_cost,
            total_profit_loss=total_profit_loss,
            profit_loss_percentage=profit_loss_percentage,
            best_performer=best_performer,
            worst_performer=worst_performer,
            asset_allocation=asset_allocation
        )

coingecko_service = CoinGeckoService()
portfolio_analytics = PortfolioAnalytics(coingecko_service)
