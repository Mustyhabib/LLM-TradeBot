# ⚖️ DecisionCoreAgent (The Critic)

> Adversarial Critic - Weighted voting and decision fusion

## Overview

DecisionCoreAgent is the decision core of the multi-Agent framework, integrating multi-dimensional signals from QuantAnalystAgent and PredictAgent to generate final trading decisions through a weighted voting mechanism.

## Core Responsibilities

1. **Weighted Voting** - Integrate multi-timeframe trend, oscillator, sentiment, and ML prediction signals
2. **Multi-Timeframe Alignment** - Detect 1h/15m/5m trend consistency
3. **Market Awareness** - Integrate position analysis and state detection
4. **Adversarial Audit** - Detect divergence between technical signals and fund flow

## Data Flow

```text
┌─────────────────────────────────────────────────────────────────┐
│                     DecisionCoreAgent                            │
├─────────────────────────────────────────────────────────────────┤
│ Input:                                                           │
│   - quant_analysis: QuantAnalystAgent output                     │
│   - predict_result: PredictAgent output                          │
│   - market_data: Raw market data                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Signal Extraction                                         │   │
│  │ trend_5m/15m/1h, oscillator_5m/15m/1h, sentiment, prophet │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Market State Analysis                                     │   │
│  │ • RegimeDetector: trending/choppy/volatile/unknown        │   │
│  │ • PositionAnalyzer: Price position percentage             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Weighted Vote Calculation                                 │   │
│  │ weighted_score = Σ(signal × weight)                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Multi-Timeframe Alignment Detection                       │   │
│  │ • Full alignment: 1h/15m/5m same direction                │   │
│  │ • Partial alignment: 1h/15m same direction                │   │
│  │ • Misaligned: Multi-timeframe divergence                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Adversarial Audit                                         │   │
│  │ • Bullish tech + institutional outflow → confidence -50%  │   │
│  │ • Bearish tech + institutional inflow → confidence -50%   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           │                                      │
├─────────────────────────────────────────────────────────────────┤
│ Output: VoteResult                                               │
│   - action: "long" / "short" / "hold"                           │
│   - confidence: 0 ~ 100                                          │
│   - weighted_score: -100 ~ +100                                  │
│   - multi_period_aligned: bool                                   │
│   - vote_details: Per-signal contribution scores                 │
│   - reason: Decision reason                                      │
│   - regime: Market state                                         │
│   - position: Price position                                     │
└─────────────────────────────────────────────────────────────────┘
```

## Signal Weight Configuration

```python
@dataclass
class SignalWeight:
    # Trend signals (total 0.45)
    trend_5m: float = 0.10
    trend_15m: float = 0.15
    trend_1h: float = 0.20
    
    # Oscillator signals (total 0.20)
    oscillator_5m: float = 0.05
    oscillator_15m: float = 0.07
    oscillator_1h: float = 0.08
    
    # ML prediction
    prophet: float = 0.15
    
    # Sentiment signal (dynamic weight)
    sentiment: float = 0.20
```

> **Note**: All weights sum to 1.0; sentiment signal weight drops to 0 when no data is available

## Key Data Structures

### VoteResult

```python
@dataclass
class VoteResult:
    action: str              # 'long', 'short', 'hold'
    confidence: float        # 0.0 ~ 100.0
    weighted_score: float    # -100 ~ +100
    vote_details: Dict       # Per-signal contribution breakdown
    multi_period_aligned: bool
    reason: str              # Decision reason description
    regime: Optional[Dict]   # Market state
    position: Optional[Dict] # Price position
```

## Decision Thresholds

| Condition | Action | Confidence |
|------|------|------|
| score > 50 && aligned | long | 85% |
| score > 30 | long | 60-75% |
| score < -50 && aligned | short | 85% |
| score < -30 | short | 60-75% |
| Other | hold | Based on score |

## Filter Logic

### Market State Filtering

```python
if regime == 'choppy' and position == 'middle':
    return "Open prohibited: Choppy market and price in middle of range"
```

### Adversarial Audit

```python
# Technical signal vs. fund flow divergence detection
if action == 'open_long' and inst_netflow_1h < -1000000:
    confidence *= 0.5  # Bullish but institutional outflow, confidence halved
```

## Auxiliary Analyzers

### RegimeDetector (Market State Detection)

| State | Description | Condition |
|------|------|------|
| trending | Trending market | ADX > 25, EMA aligned |
| choppy | Choppy market | ADX < 20, price near MA |
| volatile | High volatility | ATR/Price > threshold |
| unknown | Unclear | None of the above |

### PositionAnalyzer (Price Position Analysis)

```python
position_pct = (current_price - min) / (max - min) * 100
# 0% = range low, 100% = range high

location = "bottom" if pct < 30 else "top" if pct > 70 else "middle"
allow_long = pct < 70   # Long prohibited at high
allow_short = pct > 30  # Short prohibited at low
```

## Dependencies

```text
DecisionCoreAgent
├── SignalWeight (weight config)
├── PositionAnalyzer (src/agents/position_analyzer.py)
├── RegimeDetector (src/agents/regime_detector.py)
└── VoteResult (output structure)
```

## Usage Example

```python
from src.agents.decision_core_agent import DecisionCoreAgent

agent = DecisionCoreAgent()
result = await agent.make_decision(
    quant_analysis=quant_output,
    predict_result=predict_output,
    market_data=market_data
)

print(f"Decision: {result.action}")
print(f"Confidence: {result.confidence}%")
print(f"Weighted score: {result.weighted_score}")
print(f"Multi-timeframe aligned: {result.multi_period_aligned}")
```

## Log Output

Dashboard log format:

```
⚖️ DecisionCoreAgent (The Critic): Context(Regime=choppy, Pos=27%) => Vote: WAIT ([CHOPPY] | Weighted score: -17.2 | Period alignment: Multi-timeframe divergence(1h:-1, 15m:0, 5m:0) | sentiment: -50 | trend_1h: -40)
```
