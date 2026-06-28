# 🕵️ DataSyncAgent (The Oracle)

> Data Oracle - Asynchronous data acquisition and dual-view construction

## Overview

DataSyncAgent is the data entry point of the multi-Agent framework, responsible for asynchronously fetching market data from Binance and external quantitative APIs, and constructing dual-view (Stable + Live) data structures for downstream Agents to use.

## Core Responsibilities

1. **Asynchronous Concurrent Requests** - Use `asyncio.gather` to fetch multi-timeframe K-line data concurrently
2. **Dual-View Data Structure** - Separate completed candles (stable) and current incomplete candles (live)
3. **Timestamp Alignment Validation** - Ensure time consistency across multi-timeframe data
4. **External Data Integration** - Get institutional fund flow, OI, and other quantitative indicators

## Data Flow

```text
┌─────────────────────────────────────────────────────────────────┐
│                      DataSyncAgent                               │
├─────────────────────────────────────────────────────────────────┤
│ Input:                                                           │
│   - symbol: Trading pair (e.g. BTCUSDT)                          │
│   - limit: Number of K-lines (default 300)                       │
├─────────────────────────────────────────────────────────────────┤
│ Concurrent requests:                                              │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│   │ 5m K-lines │  │15m K-lines │  │ 1h K-lines │                │
│   └────────────┘  └────────────┘  └────────────┘                │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│   │ Quant API  │  │Funding Rate│  │    OI      │                │
│   └────────────┘  └────────────┘  └────────────┘                │
├─────────────────────────────────────────────────────────────────┤
│ Output: MarketSnapshot                                           │
│   - stable_5m/15m/1h: Completed K-line DataFrame                 │
│   - live_5m/15m/1h: Current K-line Dict                         │
│   - quant_data: External quantitative data                      │
│   - binance_funding: Funding rate                                │
│   - binance_oi: Open interest                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Key Data Structures

### MarketSnapshot

```python
@dataclass
class MarketSnapshot:
    # 5m data
    stable_5m: pd.DataFrame  # Completed candles (iloc[:-1])
    live_5m: Dict            # Current candle (iloc[-1])
    
    # 15m data
    stable_15m: pd.DataFrame
    live_15m: Dict
    
    # 1h data
    stable_1h: pd.DataFrame
    live_1h: Dict
    
    # Metadata
    timestamp: datetime
    alignment_ok: bool       # Alignment status
    fetch_duration: float    # Fetch duration (seconds)
    
    # Quantitative data
    quant_data: Dict
    binance_funding: Dict
    binance_oi: Dict
```

## Core Methods

### `fetch_all_timeframes(symbol, limit)`

Asynchronously fetch all timeframe data concurrently.

**Optimization points**:

- Uses `asyncio.gather` for concurrent requests, saving ~60% IO time
- Alignment validation tolerance: 15m data allows 15min difference, 1h data allows 1h difference

### `_to_dataframe(klines)`

Convert raw K-line data to Pandas DataFrame, including:

- Timestamp converted to datetime index
- Numeric column type conversion

### `_check_alignment(k5m, k15m, k1h)`

Check time alignment of multi-timeframe data:

- 5m vs 15m: 15min difference allowed
- 5m vs 1h: 1h difference allowed

## Dependencies

```text
DataSyncAgent
├── BinanceClient (src/api/binance_client.py)
├── QuantClient (src/api/quant_client.py)
└── OITracker (src/utils/oi_tracker.py)
```

## Configuration

| Parameter | Default | Description |
|-----------|--------|-------------|
| symbol | BTCUSDT | Trading pair |
| limit | 300 | Number of K-lines to fetch |

## Usage Example

```python
from src.agents.data_sync_agent import DataSyncAgent

agent = DataSyncAgent()
snapshot = await agent.fetch_all_timeframes("BTCUSDT", limit=300)

# Get live price
live_price = agent.get_live_price("5m")

# Get stable DataFrame
df_5m = agent.get_stable_dataframe("5m")
```

## Log Output

Dashboard log format:

```
🕵️ DataSyncAgent (The Oracle): Action=Fetch[5m,15m,1h] | Snapshot=$96000.00
```
