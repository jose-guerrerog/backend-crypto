from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class Performer:
    coin_id: str
    coin_name: str
    coin_symbol: str
    profit_loss_percentage: float
    profit_loss: float

@dataclass
class PortfolioMetrics:
    total_value: float
    total_cost: float
    total_profit_loss: float
    profit_loss_percentage: float
    best_performer: Optional[Performer]
    worst_performer: Optional[Performer]
    asset_allocation: Dict[str, float]