import requests
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .models import CoinData, PortfolioMetrics, Portfolio

class CoinGeckoService:
    """Service to interact with CoinGecko API"""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0
        self.rate_limit_delay = 1.2  # Seconds between requests
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make rate-limited request to CoinGecko API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        try:
            url = f"{self.BASE_URL}{endpoint}"
            response = self.session.get(url, params=params or {}, timeout=10)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
    
    def get_coin_list(self) -> List[Dict]:
        """Get list of all supported coins"""
        data = self._make_request("/coins/list")
        return data if data else []
    
    def get_coin_data(self, coin_ids: List[str]) -> Dict[str, CoinData]:
        """Get current market data for specified coins"""
        if not coin_ids:
            return {}
        
        # CoinGecko allows up to 250 coins per request
        coin_ids_str = ",".join(coin_ids[:250])
        
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
                symbol="",  # Simple price endpoint doesn't include symbol
                name="",    # Simple price endpoint doesn't include name
                current_price=coin_data.get('usd', 0),
                market_cap=coin_data.get('usd_market_cap', 0),
                price_change_24h=0,  # Not available in simple endpoint
                price_change_percentage_24h=coin_data.get('usd_24h_change', 0),
                volume_24h=coin_data.get('usd_24h_vol', 0),
                last_updated=datetime.now()
            )
        
        return result
    
    def get_detailed_coin_data(self, coin_ids: List[str]) -> Dict[str, CoinData]:
        """Get detailed market data for specified coins"""
        if not coin_ids:
            return {}
        
        coin_ids_str = ",".join(coin_ids[:250])
        
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
        
        if not data:
            return {}
        
        result = {}
        for coin in data:
            result[coin['id']] = CoinData(
                id=coin['id'],
                symbol=coin['symbol'].upper(),
                name=coin['name'],
                current_price=coin['current_price'] or 0,
                market_cap=coin['market_cap'] or 0,
                price_change_24h=coin['price_change_24h'] or 0,
                price_change_percentage_24h=coin['price_change_percentage_24h'] or 0,
                volume_24h=coin['total_volume'] or 0,
                last_updated=datetime.now()
            )
        
        return result
    
    def search_coins(self, query: str) -> List[Dict]:
        """Search for coins by name or symbol"""
        params = {'query': query}
        data = self._make_request("/search", params)
        
        if data and 'coins' in data:
            return data['coins'][:20]  # Return top 20 results
        return []

class PortfolioAnalytics:
    """Service to calculate portfolio metrics and analytics"""
    
    def __init__(self, coingecko_service: CoinGeckoService):
        self.coingecko = coingecko_service
    
    def calculate_portfolio_metrics(self, portfolio: Portfolio) -> PortfolioMetrics:
        """Calculate comprehensive portfolio metrics"""
        if not portfolio.transactions:
            return PortfolioMetrics(
                total_value=0,
                total_cost=0,
                total_profit_loss=0,
                profit_loss_percentage=0,
                best_performer=None,
                worst_performer=None,
                asset_allocation={}
            )
        
        # Get current prices for all coins in portfolio
        coin_ids = list(set(t.coin_id for t in portfolio.transactions))
        current_prices = self.coingecko.get_detailed_coin_data(coin_ids)
        
        # Calculate holdings by coin
        holdings = {}  # coin_id -> {amount, cost_basis, current_value}
        
        for transaction in portfolio.transactions:
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
            else:  # sell
                holdings[coin_id]['amount'] -= transaction.amount
                holdings[coin_id]['cost_basis'] -= transaction.amount * transaction.price_usd
        
        # Filter out zero holdings
        holdings = {k: v for k, v in holdings.items() if v['amount'] > 0}
        
        # Calculate current values and metrics
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
                
                # Track best/worst performers
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
        
        # Calculate asset allocation
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

# Global service instances
coingecko_service = CoinGeckoService()
portfolio_analytics = PortfolioAnalytics(coingecko_service)