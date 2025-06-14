from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import uuid

@dataclass
class Transaction:
    """Represents a single cryptocurrency transaction"""
    id: str
    coin_id: str
    coin_name: str
    coin_symbol: str
    amount: float
    price_usd: float
    transaction_type: str  # 'buy' or 'sell'
    timestamp: datetime
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

@dataclass
class Portfolio:
    """Represents a cryptocurrency portfolio"""
    id: str
    name: str
    transactions: List[Transaction]
    created_at: datetime
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.transactions:
            self.transactions = []

@dataclass
class CoinData:
    """Represents cryptocurrency market data"""
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
    """Represents calculated portfolio metrics"""
    total_value: float
    total_cost: float
    total_profit_loss: float
    profit_loss_percentage: float
    best_performer: Optional[Dict]
    worst_performer: Optional[Dict]
    asset_allocation: Dict[str, float]

# In-memory storage for portfolios (session-based)
class PortfolioStorage:
    """In-memory storage for portfolio data"""
    
    def __init__(self):
        self.portfolios: Dict[str, Portfolio] = {}
        self.session_portfolios: Dict[str, List[str]] = {}  # session_key -> portfolio_ids
    
    def create_portfolio(self, session_key: str, name: str) -> Portfolio:
        portfolio = Portfolio(
            id=str(uuid.uuid4()),
            name=name,
            transactions=[],
            created_at=datetime.now()
        )
        
        self.portfolios[portfolio.id] = portfolio
        
        if session_key not in self.session_portfolios:
            self.session_portfolios[session_key] = []
        self.session_portfolios[session_key].append(portfolio.id)
        
        return portfolio
    
    def get_portfolio(self, portfolio_id: str) -> Optional[Portfolio]:
        return self.portfolios.get(portfolio_id)
    
    def get_session_portfolios(self, session_key: str) -> List[Portfolio]:
        portfolio_ids = self.session_portfolios.get(session_key, [])
        return [self.portfolios[pid] for pid in portfolio_ids if pid in self.portfolios]
    
    def add_transaction(self, portfolio_id: str, transaction: Transaction) -> bool:
        if portfolio_id in self.portfolios:
            self.portfolios[portfolio_id].transactions.append(transaction)
            return True
        return False
    
    def remove_transaction(self, portfolio_id: str, transaction_id: str) -> bool:
        if portfolio_id in self.portfolios:
            portfolio = self.portfolios[portfolio_id]
            portfolio.transactions = [t for t in portfolio.transactions if t.id != transaction_id]
            return True
        return False
    
    def delete_portfolio(self, session_key: str, portfolio_id: str) -> bool:
        if portfolio_id in self.portfolios:
            del self.portfolios[portfolio_id]
            if session_key in self.session_portfolios:
                self.session_portfolios[session_key] = [
                    pid for pid in self.session_portfolios[session_key] 
                    if pid != portfolio_id
                ]
            return True
        return False

# Global storage instance
portfolio_storage = PortfolioStorage()