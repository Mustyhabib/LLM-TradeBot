from dataclasses import dataclass

@dataclass
class SignalWeight:
    """Signal weight configuration
    
    Note: All weights should sum to 1.0 (excluding dynamic sentiment)
    Optimized config (2026-01-07): Further optimized based on backtest analysis
    - Increased 1h weight, reduced short-period noise
    - Reduced prophet weight, more reliance on technical indicators
    """
    # Trend signals (total 0.45) - increased long-period weight
    trend_5m: float = 0.03   # Reduced 5m noise impact
    trend_15m: float = 0.12  # Slightly increased
    trend_1h: float = 0.30   # Increased 1h weight (core trend judgment)
    # Oscillator signals (total 0.20)
    oscillator_5m: float = 0.03  # Reduced 5m noise
    oscillator_15m: float = 0.07
    oscillator_1h: float = 0.10  # Increased 1h weight
    # Prophet ML prediction weight - further reduced
    prophet: float = 0.05  # Reduced ML weight to avoid overfitting
    # Sentiment signal (dynamic weight)
    sentiment: float = 0.25
    # Other extended signals (e.g., LLM)
    llm_signal: float = 0.0  # To be integrated
