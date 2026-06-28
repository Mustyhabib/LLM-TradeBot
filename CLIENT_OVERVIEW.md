# LLM-TradeBot — Project Overview

## What It Is

LLM-TradeBot is an automated cryptocurrency futures trading system powered by a **multi-agent adversarial decision framework**. Instead of relying on a single algorithm or a lone LLM prompt, it uses a coordinated team of specialized AI agents — each responsible for a distinct aspect of trading — that debate, validate, and collectively decide every trade.

The system is designed for **Binance Futures** (with Bybit, OKX, Hyperliquid, and others on the roadmap) and supports paper trading for risk-free testing as well as live deployment.

---

## What It Does

| Capability | Description |
|---|---|
| **Automated Futures Trading** | Places long/short entries and exits on Binance perpetual futures 24/7 |
| **Multi-Timeframe Analysis** | Simultaneously reads 5m, 15m, and 1h candles, aligned to the same snapshot moment |
| **Market Regime Detection** | Identifies whether the market is trending, ranging, or volatile — and adapts strategy accordingly |
| **Intelligent Symbol Selection** | AUTO1 scans momentum, volume, and technicals to pick the highest-conviction trading pair |
| **Adversarial Decision Core** | Multiple strategy agents vote; conflicts are resolved before execution |
| **Risk Audit & Veto** | A dedicated risk agent can block or downsize any trade that violates exposure limits |
| **Live Dashboard (web UI)** | Full visibility into every agent's reasoning, confidence scores, and the final decision per cycle |
| **Multi-LLM Support** | DeepSeek, OpenAI, Claude, Qwen, Gemini — switchable at runtime via the Dashboard |

---

## How It Does It — Architecture

The system follows a **pipeline architecture** where each stage is an independent agent:

```
Symbol Selector → DataSync (5m/15m/1h) → Quant Analyst → Semantic Agents (Trend/Setup/Trigger)
                                                              ↓
                                              Multi-Period Parser
                                                              ↓
                         Reflection Agent → Decision Core → Risk Audit → Execution Engine
```

### Agents Explained

| Agent | Role |
|---|---|
| **Symbol Selector** | Picks the most promising trading pair based on momentum, volume, and volatility |
| **DataSync** | Fetches and time-aligns multi-timeframe OHLCV data in a single concurrent snapshot |
| **Quant Analyst** | Computes technical indicators, detects market regime, flags bull/bear traps |
| **Trend Agent** | Analyzes directional bias using LLM reasoning or local models |
| **Setup Agent** | Evaluates entry conditions (structure, liquidity, confluence) |
| **Trigger Agent** | Confirms timing — decides when setup is actionable |
| **Reflection Agent** | Reviews past trade outcomes and biases to improve current decisions |
| **Decision Core** | Fuses all agent outputs into a single action (LONG / SHORT / HOLD) with confidence score |
| **Risk Audit** | Checks position size, portfolio heat, correlation, and can veto the trade |
| **Execution Engine** | Sends signed orders to Binance with stop-loss — audits every fill |

The key innovation is the **adversarial layer**: agents don't simply agree — they challenge each other. Conflicting signals are resolved through calibrated voting with confidence penalties, not naive majority rule.

---

## Workload It Solves: Manual vs. Automated

### The Manual Trader's Workflow (per cycle, every 5 minutes)

| Step | Manual Effort | Pitfall |
|---|---|---|
| Open 3+ charts across timeframes | 1–2 min | Mental misalignment between timeframes |
| Read order flow, volume profile | 2–3 min | Subjective interpretation varies |
| Check macro context / news | 1–2 min | Confirmation bias, anchoring |
| Decide direction and entry | 1–2 min | Emotional override |
| Calculate position size | 30 sec | Often skipped or gut-driven |
| Place orders with stop-loss | 30 sec | Slippage, misclicks |
| Monitor and manage open trade | Continuous | Fatigue, FOMO, revenge trading |
| Document and review | Rarely done | No systematic learning |
| **Per cycle** | **~8–10 minutes** | **Cognitive load compounds over hours** |

Over a 24-hour crypto market with 5-minute cycles = **288 decisions per day** requiring sustained focus. No human maintains that.

### LLM-TradeBot's Approach

| Step | Automated Time | Method |
|---|---|---|
| Multi-timeframe data fetch | ~500 ms | Async concurrent WebSocket + REST |
| Regime detection + signal computation | ~1–2 ms | Vectorized NumPy/Pandas |
| Multi-agent analysis (parallel) | ~3–8 sec | LLM or local model inference |
| Decision fusion + risk audit | ~1 ms | Deterministic voting engine |
| Order execution | ~200 ms | Binance REST API with retry logic |
| Audit logging | Async | Zero-latency pipeline stage |
| **Per cycle** | **~5–10 seconds** | **Consistent, tireless, auditable** |

**The bot does not sleep, does not chase losses, does not override risk limits.** Every decision is logged with full provenance — you can inspect exactly why it entered or avoided any trade.

### Summary Comparison

| Dimension | Human Trader | LLM-TradeBot |
|---|---|---|
| Decisions per day | 40–80 (fatigue-limited) | 288 (automated, 24/7) |
| Timeframe alignment | Prone to error | Atomic snapshot, guaranteed |
| Emotion / bias | Present and costly | Eliminated |
| Consistency | Degrades over time | Deterministic rules + adaptive LLM |
| Audit trail | Incomplete or missing | Full per-cycle trace |
| Risk enforcement | Manual, overridable | Hard-coded, non-bypassable |
| Speed of reaction | Seconds to minutes | Sub-second |

---

## Implementation

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Architecture | Async pipeline with agent abstraction (asyncio, multi-process safe) |
| Data Layer | Binance WebSocket (real-time) + REST API (historical) with multi-timeframe alignment |
| AI/LLM Layer | Multi-provider client (DeepSeek, OpenAI, Claude, Qwen, Gemini) with factory pattern |
| Decision Engine | Calibrated voting with confidence weighting, conflict detection, and veto capability |
| Risk Layer | Portfolio heat checks, correlation limits, Kelly-derived sizing, stop-loss enforcement |
| Backtesting | Walk-forward engine with regime-aware walk-forward optimization |
| Web Dashboard | HTML/CSS/JS single-page app served by FastAPI, real-time balance/PnL curves, agent chatroom |
| Deployment | One-click install script, Docker Compose, Railway-compatible |
| Testing | 40+ unit and integration tests covering protocols, data flow, and risk invariants |

---

## Use Cases

1. **Individual traders** who want systematic, emotion-free execution without building infrastructure from scratch
2. **Quant teams** who need a modular multi-agent framework to prototype and deploy strategies rapidly
3. **Prop trading desks** looking for a transparent, auditable decision pipeline (every trade is explainable)
4. **Researchers** studying LLM-based decision systems in adversarial, high-stakes environments
5. **Fund managers** who want to offer AI-managed crypto strategies with full client-facing transparency

---

## Current Status

- Binance Futures: live and tested
- Paper trading mode: fully functional
- Web Dashboard: deployed and operational
- Multi-LLM: 5 providers integrated
- Roadmap: Bybit, OKX, Hyperliquid, Aster DEX, Lighter, Grok, Kimi

---

*For technical documentation, architecture diagrams, and setup guides, see the project repository.*
