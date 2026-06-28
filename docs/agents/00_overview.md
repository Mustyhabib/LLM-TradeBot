# 🤖 Multi-Agent Runtime Architecture

> LLM-TradeBot current runtime Multi-Agent architecture (aligned with `main.py` implementation)

## Architecture Overview

The system is currently not a single-path 5-Agent linear pipeline, but rather "multi-branch analysis + decision routing + risk control gate + single-opportunity execution".

```text
Symbol Selector (AUTO1/AUTO3)
        │
        ▼
DataSyncAgent ──► QuantAnalystAgent ──┬──► PredictAgent (optional)
                                       ├──► ReflectionAgent (optional)
                                       ├──► Trend/Setup/Trigger Agent (LLM/Local optional)
                                       └──► MultiPeriodParserAgent
                                                │
                                                ▼
                                      Decision Router
                      (Forced Exit / Fast Trend / LLM / Rule-Based DecisionCore)
                                                │
                                                ▼
                                         RiskAuditAgent
                                                │
                                                ▼
                                      Executor (single best open per cycle)
```

## Agent Layering

| Layer | Agent | Function | Required? |
|---|---|---|---|
| Data | DataSyncAgent | Fetch 5m/15m/1h snapshots and real-time prices | Yes |
| Analysis | QuantAnalystAgent | Trend/Oscillator/Sentiment/Trap signals | Yes |
| Analysis | PredictAgent | 30m probability prediction | No |
| Analysis | ReflectionAgent / ReflectionAgentLLM | Trade review, provide prompt context | No |
| Analysis | Trend/Setup/Trigger Agent (LLM/Local) | Semantic interpretation and structured stance | No |
| Summary | MultiPeriodParserAgent | Multi-period consistency summary | Yes |
| Decision | Decision Router | Select forced-exit / fast-trend / LLM / rule-based path | Yes |
| Risk | RiskAuditAgent | Veto power, stop-loss correction, margin/risk checks | Yes |
| Execution | Executor | Execute orders, maintain trade/position state | Yes |

## Cycle Execution Flow

1. Read symbols (can be dynamically refreshed by Selector).
2. Execute analysis flow for each symbol (`analyze_only=True`):
   - Data preparation and validity check
   - Parallel analysis tasks (Quant / Predict / Reflection)
   - Four-Layer Filter + semantic analysis + Multi-Period summary
   - Decision routing through RiskAudit
3. Collect all `suggested` open recommendations.
4. Only execute the 1 open recommendation with highest confidence (single cycle single open limit).
5. Update account, logs, decision history, and visualization status.

## Decision Routing Priority

1. `forced_exit`: Position timeout/loss threshold triggers forced liquidation.  
2. `fast_trend`: 30m momentum fast signal triggers.  
3. `llm`: Bull/Bear parallel perspective + LLM decision.  
4. `decision_core`: Rule-based decision fallback when LLM unavailable.  

## Action Protocol (Unified)

System unified action enumeration (see `src/utils/action_protocol.py`):

- `open_long`
- `open_short`
- `close_long`
- `close_short`
- `wait`
- `hold`

Notes:

- All external/internal actions are normalized before entering the risk control and execution layer.
- `close/close_position` is compatibility input only; at runtime it is mapped to a directional close action.

## Key Implementation Files

- Orchestration main flow: `/Users/yunxuanhan/Documents/workspace/ai/LLM-TradeBot/main.py`
- Agent config: `/Users/yunxuanhan/Documents/workspace/ai/LLM-TradeBot/src/agents/agent_config.py`
- Action protocol: `/Users/yunxuanhan/Documents/workspace/ai/LLM-TradeBot/src/utils/action_protocol.py`
- Analysis→Execution contract: `/Users/yunxuanhan/Documents/workspace/ai/LLM-TradeBot/src/agents/contracts.py`
- Risk control: `/Users/yunxuanhan/Documents/workspace/ai/LLM-TradeBot/src/agents/risk_audit_agent.py`
- State & API: `/Users/yunxuanhan/Documents/workspace/ai/LLM-TradeBot/src/server/state.py`, `/Users/yunxuanhan/Documents/workspace/ai/LLM-TradeBot/src/server/app.py`

## Extension Recommendations

1. When adding a new Agent, prefer integrating via `agent_outputs` with a clear input/output schema.  
2. New actions must first extend the action protocol, then integrate with risk control and execution.  
3. Dashboard display fields should come from `global_state`'s lock-protected snapshot to avoid race condition reads.  
