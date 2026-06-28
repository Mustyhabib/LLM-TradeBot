from typing import Dict, List, Optional
from dataclasses import dataclass

from .risk_level import RiskLevel

@dataclass
class RiskCheckResult:
    """Risk check result"""
    passed: bool  # Whether passed
    risk_level: RiskLevel
    blocked_reason: Optional[str] = None  # Blocking reason (if not passed)
    corrections: Optional[Dict] = None  # Auto-correction content
    warnings: List[str] = None  # Warning messages
