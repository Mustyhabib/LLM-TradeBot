# 🔮 PredictAgent (The Prophet)

> Prediction Prophet - ML-driven price trend prediction

## Overview

PredictAgent is the prediction engine of the multi-Agent framework, using a LightGBM machine learning model to predict the probability of a price increase in the next 30 minutes, providing data-driven signals for the decision layer.

## Core Responsibilities

1. **Probability Prediction** - Output the probability of a price increase in the next 30 minutes (0.0 ~ 1.0)
2. **Dual-Mode Support** - ML model first, falls back to rule scoring when no model is available
3. **Feature Engineering** - Process 80+ technical features
4. **Auto Training** - Automatically retrain the model every 2 hours

## Data Flow

```text
┌─────────────────────────────────────────────────────────────────┐
│                        PredictAgent                              │
├─────────────────────────────────────────────────────────────────┤
│ Input: features Dict (from TechnicalFeatureEngineer)             │
│   - 80+ technical features                                      │
│   - Price position, trend strength, momentum, volatility, volume│
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Preprocessing: _preprocess_features                       │   │
│  │   • Handle NaN/Inf outliers                              │   │
│  │   • Feature default value filling                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           │                                      │
│              ┌────────────┴────────────┐                        │
│              ▼                         ▼                        │
│  ┌───────────────────┐    ┌───────────────────┐                │
│  │   ML Model Pred.   │    │   Rule Score Pred. │                │
│  │  (LightGBM)       │    │   (Fallback)      │                │
│  │                   │    │                   │                │
│  │ predict_proba()   │    │ Weighted rule sys │                │
│  └───────────────────┘    └───────────────────┘                │
│              │                         │                        │
│              └────────────┬────────────┘                        │
│                           ▼                                      │
├─────────────────────────────────────────────────────────────────┤
│ Output: PredictResult                                            │
│   - probability_up: Upside probability (0.0 ~ 1.0)              │
│   - probability_down: Downside probability                       │
│   - confidence: Confidence level                                 │
│   - signal: "bullish" / "bearish" / "neutral"                   │
│   - factors: Top 5 important features                            │
└─────────────────────────────────────────────────────────────────┘
```

## Key Data Structures

### PredictResult

```python
@dataclass
class PredictResult:
    probability_up: float      # Upside probability (0.0 ~ 1.0)
    probability_down: float    # Downside probability
    confidence: float          # Confidence level
    horizon: str               # Prediction horizon (default "30m")
    factors: Dict[str, float]  # Important features and contributions
    model_type: str            # "ml_lightgbm" / "rule_based"
    timestamp: datetime
```
    @property
    def signal(self) -> str:
        if self.probability_up > 0.55:
            return "bullish"
        elif self.probability_up < 0.45:
            return "bearish"
        return "neutral"
```

## ML Model Training

### Label Generation (LabelGenerator)

```python
# Core parameters
horizon_minutes = 30   # Predict 30 minutes ahead
up_threshold = 0.001   # Upside threshold 0.1%

# Label calculation
future_price = df['close'].shift(-6)  # 6 x 5m candles = 30 minutes
returns = (future_price - current_price) / current_price
label = 1 if returns > 0.001 else 0
```

### Feature Engineering (TechnicalFeatureEngineer)

| Feature Category | Count | Example |
|----------|------|------|
| Price Relative Position | 8 | `price_to_sma20_pct`, `bb_position` |
| Trend Strength | 10 | `ema_cross_strength`, `macd_momentum` |
| Momentum | 8 | `rsi_divergence`, `rsi_slope` |
| Volatility | 8 | `atr_ratio`, `volatility_breakout` |
| Volume | 8 | `volume_surge`, `vwap_deviation` |
| Composite Features | 8+ | `trend_confirmation_score` |

### Auto Training (ProphetAutoTrainer)

```python
# Configuration
interval_hours = 2.0     # Train every 2 hours
training_days = 7        # Use 7 days of historical data

# Training flow
1. Fetch historical K-lines (~2016 entries)
2. Calculate technical indicators
3. Build features
4. Generate labels
5. 80/20 train/validation split
6. LightGBM training
7. Save model to models/prophet_lgb_{symbol}.pkl
8. Reload into PredictAgent
```

## Multi-Symbol Support

Each trading pair has an independent PredictAgent and model file:

```
models/
├── prophet_lgb_BTCUSDT.pkl
├── prophet_lgb_ETHUSDT.pkl
├── prophet_lgb_SOLUSDT.pkl
└── prophet_lgb_BNBUSDT.pkl
```

## Dependencies

```text
PredictAgent
├── ProphetMLModel (src/models/prophet_model.py)
├── TechnicalFeatureEngineer (src/features/technical_features.py)
└── ProphetAutoTrainer (auto training)
```

## Configuration

| Parameter | Default | Description |
|-----------|--------|-------------|
| horizon | "30m" | Prediction time range |
| symbol | "BTCUSDT" | Trading pair |
| model_path | Auto-generated | Model file path |

## Usage Example

```python
from src.agents.predict_agent import PredictAgent

# Initialize (auto-load model)
agent = PredictAgent(horizon='30m', symbol='BTCUSDT')

# Predict
result = await agent.predict(features)

print(f"Upside probability: {result.probability_up:.2%}")
print(f"Signal: {result.signal}")
print(f"Confidence: {result.confidence:.2%}")
```

## Log Output

Dashboard log format:

```
🔮 PredictAgent (The Prophet): 📈 P(Up)=56.5% | Signal: bullish | Conf: 65%
```

Symbol legend:

- 📈 P(Up) > 55%
- 📉 P(Up) < 45%
- ➡️ Other
