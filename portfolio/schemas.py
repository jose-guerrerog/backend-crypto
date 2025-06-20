from typing import Optional, Dict
from dataclasses import dataclass

@dataclass
class PortfolioMetrics:
    total_value: float
    total_cost: float
    total_profit_loss: float
    profit_loss_percentage: float
    best_performer: Optional[Dict]
    worst_performer: Optional[Dict]
    asset_allocation: Dict[str, float]