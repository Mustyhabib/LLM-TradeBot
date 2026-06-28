from typing import Optional
from dataclasses import dataclass

@dataclass
class PositionInfo:
    """Position info"""
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    quantity: float
    unrealized_pnl: float
    current_price: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
