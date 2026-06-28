from dataclasses import dataclass
from datetime import datetime

@dataclass
class TradeRecord:
    """Trade record"""
    symbol: str
    action: str
    timestamp: datetime
    pnl: float = 0.0
