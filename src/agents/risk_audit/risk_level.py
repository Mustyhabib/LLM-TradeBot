from enum import Enum

class RiskLevel(Enum):
    """Risk level"""
    SAFE = "safe"
    WARNING = "warning"
    DANGER = "danger"
    FATAL = "fatal"