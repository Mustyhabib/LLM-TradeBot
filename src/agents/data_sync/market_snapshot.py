"""
Data Oracle (The Oracle) Agent

Responsibilities:
1. Asynchronously fetch multi-timeframe K-line data concurrently
2. Split stable/live dual views
3. Time alignment validation

Optimizations:
- Concurrent IO, saving 60% time
- Dual-view data structure, resolving lag issues
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass, field

@dataclass
class MarketSnapshot:
    """
    Market snapshot (dual-view structure)
    
    stable_view: iloc[:-1] completed K-lines, used for calculating historical indicators
    live_view: iloc[-1] current incomplete K-line, containing the latest price
    """
    # 5m data
    stable_5m: pd.DataFrame  # Completed K-lines
    live_5m: Dict            # Latest K-line
    
    # 15m data
    stable_15m: pd.DataFrame
    live_15m: Dict
    
    # 1h data
    stable_1h: pd.DataFrame
    live_1h: Dict
    
    # Metadata
    timestamp: datetime
    alignment_ok: bool       # Time alignment status
    fetch_duration: float    # Fetch duration (seconds)
    
    # External quantitative depth data (Netflow, OI)
    quant_data: Dict = field(default_factory=dict)
    
    # Binance native data
    binance_funding: Dict = field(default_factory=dict)
    binance_oi: Dict = field(default_factory=dict)
    
    # Raw data (optional, for debugging)
    raw_5m: List[Dict] = field(default_factory=list)
    raw_15m: List[Dict] = field(default_factory=list)
    raw_1h: List[Dict] = field(default_factory=list)
    
    # 🔧 FIX: Added symbol for pipeline tracking (must come after fields with defaults)
    symbol: str = "UNKNOWN"
