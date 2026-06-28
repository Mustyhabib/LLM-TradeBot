from typing import Dict, List, Tuple
from datetime import datetime

from src.utils.logger import log
from src.utils.action_protocol import is_open_action

from .trade_record import TradeRecord

# ============================================
# Overtrading Guard
# ============================================
class OvertradingGuard:
    """
    Overtrading Guard - Prevent frequent trading and consecutive losses
    
    Rules:
    - Minimum interval cycles for same symbol
    - Maximum new positions within 6 hours
    - Cooldown after consecutive losses
    """
    
    MIN_CYCLES_SAME_SYMBOL = 4        # Minimum interval cycles for same symbol (1 hour)
    MAX_POSITIONS_6H = 2              # Maximum new positions within 6 hours (reduce overtrading)
    LOSS_STREAK_COOLDOWN = 6          # Cooldown cycles after consecutive losses (increased cooldown)
    CONSECUTIVE_LOSS_THRESHOLD = 2   # Consecutive loss threshold to trigger cooldown
    
    def __init__(self):
        self.trade_history: List[TradeRecord] = []
        self.consecutive_losses = 0
        self.last_trade_cycle: Dict[str, int] = {}  # symbol -> cycle
        self.cooldown_until_cycle: int = 0
    
    def record_trade(self, symbol: str, action: str, pnl: float = 0.0, current_cycle: int = 0):
        """Record a trade"""
        self.trade_history.append(TradeRecord(
            symbol=symbol,
            action=action,
            timestamp=datetime.now(),
            pnl=pnl
        ))
        self.last_trade_cycle[symbol] = current_cycle
        
        # Track consecutive losses
        if pnl < 0:
            self.consecutive_losses += 1
            if self.consecutive_losses >= self.CONSECUTIVE_LOSS_THRESHOLD:
                self.cooldown_until_cycle = current_cycle + self.LOSS_STREAK_COOLDOWN
                log.warning(f"⚠️ {self.consecutive_losses} consecutive losses, cooldown until cycle {self.cooldown_until_cycle}")
        else:
            self.consecutive_losses = 0
    
    def can_open_position(self, symbol: str, current_cycle: int = 0) -> Tuple[bool, str]:
        """
        Check if opening a position is allowed
        
        Returns:
            (allowed, reason)
        """
        # Check cooldown period
        if current_cycle < self.cooldown_until_cycle:
            remaining = self.cooldown_until_cycle - current_cycle
            return False, f"⛔ In consecutive loss cooldown, {remaining} cycles remaining"
        
        # Check same symbol interval
        if symbol in self.last_trade_cycle:
            cycles_since = current_cycle - self.last_trade_cycle[symbol]
            if cycles_since < self.MIN_CYCLES_SAME_SYMBOL:
                return False, f"⛔ {symbol} trading interval insufficient, need to wait {self.MIN_CYCLES_SAME_SYMBOL - cycles_since} cycles"
        
        # Check positions opened within 6 hours
        six_hours_ago = datetime.now().timestamp() - 6 * 3600
        recent_opens = sum(
            1 for t in self.trade_history 
            if t.timestamp.timestamp() > six_hours_ago and is_open_action(t.action)
        )
        if recent_opens >= self.MAX_POSITIONS_6H:
            return False, f"⛔ {recent_opens} positions opened within 6 hours, reached limit of {self.MAX_POSITIONS_6H}"
        
        return True, "✅ Position opening allowed"
    
    def get_status(self) -> Dict:
        """Get current status"""
        return {
            'consecutive_losses': self.consecutive_losses,
            'cooldown_until': self.cooldown_until_cycle,
            'recent_trades': len(self.trade_history),
            'symbols_traded': list(self.last_trade_cycle.keys())
        }
