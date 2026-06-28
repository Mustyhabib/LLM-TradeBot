from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class VoteResult:
    """Vote result"""
    action: str  # 'open_long', 'open_short', 'close_long', 'close_short', 'wait/hold'
    confidence: float  # 0-100
    weighted_score: float  # -100 ~ +100
    vote_details: Dict[str, float]  # Contribution score of each signal
    multi_period_aligned: bool  # Whether multi-period aligned
    reason: str  # Decision reason
    regime: Optional[Dict] = None      # Market regime info
    position: Optional[Dict] = None    # Price position info
    trade_params: Optional[Dict] = None # Dynamic trading parameters (stop_loss, take_profit, leverage, etc.)
    traps: Optional[Dict] = None # Market trap info (User Experience Logic)
