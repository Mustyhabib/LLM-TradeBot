# 👨‍🔬 QuantAnalystAgent (The Strategist)

> Quantitative Strategist - Multi-dimensional market signal analysis

## Overview

QuantAnalystAgent is the analysis engine of the multi-Agent framework, composed of three sub-Agents responsible for trend, oscillator, and sentiment analysis respectively, outputting standardized quantitative scores for the decision layer.

## Core Responsibilities

1. **Trend Analysis** - Calculate multi-timeframe trend scores based on EMA/MACD
2. **Oscillator Analysis** - Detect overbought/oversold conditions based on RSI
3. **Sentiment Analysis** - Integrate market sentiment indicators like fund flow, funding rate, OI
4. **Comprehensive Assessment** - Weighted summary to generate composite market score

## Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                    QuantAnalystAgent                             │
├─────────────────────────────────────────────────────────────────┤
│ Input: MarketSnapshot (from DataSyncAgent)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │TrendSubAgent │  │OscillatorSub │  │SentimentSub  │          │
│  │  (Trend)     │  │  (Oscillator)│  │  (Sentiment) │          │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤          │
│  │ • EMA cross  │  │ • RSI OB     │  │ • Fund flow  │          │
│  │ • MACD mom.  │  │ • RSI OS     │  │ • Funding    │          │
│  │ • Realtime   │  │ • Multi-RSI  │  │ • OI change  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│        │                  │                  │                  │
│        └──────────────────┴──────────────────┘                  │
│                           │                                      │
│                    Composite Weighted Score                       │
│             (Trend 40% + Oscillator 30% + Sentiment 30%)         │
├─────────────────────────────────────────────────────────────────┤
│ Output: quant_analysis Dict                                      │
│   - trend: Trend analysis result                                 │
│   - oscillator: Oscillator analysis result                       │
│   - sentiment: Sentiment analysis result                         │
│   - comprehensive: Comprehensive assessment                      │
└─────────────────────────────────────────────────────────────────┘
```

## Sub-Agent Details

### TrendSubAgent (Trend Analyst)

**Score Logic** (-100 ~ +100):

- 1h EMA golden cross → +40 pts (main trend)
- 15m MACD expansion → ±30 pts (mid-term confirmation)
- Real-time candle correction → ±20 pts (short-term momentum)

**Output Fields**:

```python
{
    'score': int,                # Total score
    'trend_1h_score': int,       # 1h trend score
    'trend_15m_score': int,      # 15m trend score
    'trend_5m_score': int,       # 5m/realtime correction score
    'details': {
        '1h_trend': str,         # "up" / "down"
        '1h_ema12': float,
        '1h_ema26': float,
        '15m_trend': str,
        '15m_macd_diff': float,
        'live_correction': str
    }
}
```

### OscillatorSubAgent (Oscillator Analyst)

**Score Logic**:

- RSI > 75 → -80 (severely overbought)
- RSI < 25 → +80 (severely oversold)
- Weight: 5m 30%, 15m 30%, 1h 40%

**Output Fields**:

```python
{
    'score': int,
    'osc_5m_score': int,
    'osc_15m_score': int,
    'osc_1h_score': int,
    'rsi_5m': float,          # For dashboard display
    'rsi_15m': float,
    'rsi_1h': float,
    'details': {...}
}
```

### SentimentSubAgent (Sentiment Analyst)

**Data Sources**:

1. **Institutional Fund Flow** - From external quantitative API
2. **Funding Rate** - Binance native data (contrarian indicator)
3. **OI Change Rate** - From OITracker historical tracking

**Score Logic**:

- Institutional net inflow 1h > 0 → +30 pts
- Funding rate > 0.03% → -30 pts (long crowding)
- OI 24h change > 10% → +10 pts (market active)

**Output Fields**:

```python
{
    'score': int,
    'oi_change_24h_pct': float,   # 24h OI change rate
    'total_sentiment_score': int,
    'details': {
        'inst_netflow_1h': float,
        'binance_funding_rate': float,
        'funding_signal': str,
        'binance_oi_value': float
    }
}
```

## Comprehensive Assessment

```python
composite_score = (trend * 0.4) + (oscillator * 0.3) + (sentiment * 0.3)
```

Signal mapping:

- score > 30 → "buy"
- score < -30 → "sell"
- else → "neutral"

## Dependencies

```text
QuantAnalystAgent
├── TrendSubAgent
├── OscillatorSubAgent
├── SentimentSubAgent
│   └── OITracker (src/utils/oi_tracker.py)
└── MarketSnapshot (from DataSyncAgent)
```

## Usage Example

```python
from src.agents.quant_analyst_agent import QuantAnalystAgent

agent = QuantAnalystAgent()
analysis = await agent.analyze_all_timeframes(snapshot)

# Access scores per dimension
trend_score = analysis['trend']['score']
oscillator_score = analysis['oscillator']['score']
sentiment_score = analysis['sentiment']['score']
composite = analysis['comprehensive']['score']
```

## Log Output

Dashboard log format:

```
👨‍🔬 QuantAnalystAgent (The Strategist): Trend(up,-40) | Osc(RSI:43,0) | Sent(OI:0.1%,-10) => Score: -19/100
```
