"""
🤖 LLM-TradeBot - Multi-Agent Architecture Main Loop
===========================================

Integrations:
1. 🕵️ DataSyncAgent - Asynchronous concurrent data collection
2. 👨‍🔬 QuantAnalystAgent - Quantitative signal analysis
3. ⚖️ DecisionCoreAgent - Weighted voting decision
4. 👮 RiskAuditAgent - Risk audit interception

Optimizations:
- Asynchronous concurrent execution (reduces wait time by 60%)
- Dual-view data structure (stable + live)
- Layered signal analysis (trend + oscillation)
- Multi-period aligned decisions
- Automatic stop-loss direction correction
- Single-veto risk control

Author: AI Trader Team
Date: 2025-12-19
"""

# Version: v+date+iteration count
VERSION = "v20260111_3"

import sys
import os
from dotenv import load_dotenv

# Load .env file, but do not override existing system environment variables
# System environment variables take precedence over .env file configuration
load_dotenv(override=False)

# Deployment mode detection: 'local' or 'railway'
# Railway deployment sets RAILWAY_ENVIRONMENT, use that as detection
DEPLOYMENT_MODE = os.environ.get('DEPLOYMENT_MODE', 'railway' if os.environ.get('RAILWAY_ENVIRONMENT') else 'local')

# Configure based on deployment mode
if DEPLOYMENT_MODE == 'local':
    # Local deployment: Prefer REST API for data fetching (more stable for local dev)
    if 'USE_WEBSOCKET' not in os.environ:
        os.environ['USE_WEBSOCKET'] = 'false'
    # Enable detailed LLM logging
    os.environ['ENABLE_DETAILED_LLM_LOGS'] = 'true'
else:
    # Railway deployment: Also use REST API for stability
    if 'USE_WEBSOCKET' not in os.environ:
        os.environ['USE_WEBSOCKET'] = 'false'
    # Disable detailed LLM logging to save disk space
    os.environ['ENABLE_DETAILED_LLM_LOGS'] = 'false'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

import json
import threading

from src.utils.logger import log
from src.server.state import global_state

print("[DEBUG] Importing uvicorn...")
import uvicorn

# Import Multi-Agent
print("[DEBUG] Importing PredictAgent...")
from src.agents import PredictAgent
print("[DEBUG] Importing server.app...")
from src.server.app import app
print("[DEBUG] Importing global_state...")
from src.server.state import global_state
print("[DEBUG] Importing MultiAgentTradingBot")
from src.trading import MultiAgentTradingBot, TradingParameters

# ✅ [NEW] Import TradingLogger to initialize the database
# FIXME: TradingLogger's SQLAlchemy import blocks startup, switched to lazy import
# from src.monitoring.logger import TradingLogger
print("[DEBUG] All imports complete!")

def start_server():
    """Start FastAPI server in a separate thread"""
    import os
    port = int(os.getenv("PORT", 8000))
    is_railway = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"))
    is_production = is_railway or os.getenv("DEPLOYMENT_MODE", "local") != "local"
    host = "0.0.0.0" if is_production else os.getenv("HOST", "127.0.0.1")
    print(f"\n🌍 Starting Web Dashboard at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="error")

# ============================================
# Main entry point
# ============================================
def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Multi-Agent Trading Bot')
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--test', action='store_true', help='Test mode')
    mode_group.add_argument('--live', action='store_true', help='Live mode')
    parser.add_argument('--max-position', type=float, default=100.0, help='Maximum single position amount')
    parser.add_argument('--leverage', type=int, default=1, help='Leverage multiplier')
    parser.add_argument('--stop-loss', type=float, default=1.0, help='Stop-loss percentage')
    parser.add_argument('--take-profit', type=float, default=2.0, help='Take-profit percentage')
    parser.add_argument('--kline-limit', type=int, default=300, help='K-line pull quantity (for warmup test)')
    parser.add_argument('--symbols', type=str, default='', help='Override trading pairs (CSV, e.g., BTCUSDT,ETHUSDT)')
    parser.add_argument('--skip-auto3', action='store_true', help='Skip AUTO3 parsing in once mode')
    parser.add_argument('--mode', choices=['once', 'continuous'], default='continuous', help='Running mode')
    parser.add_argument('--interval', type=float, default=3.0, help='Continuous running interval (minutes)')
    # CLI Headless Mode
    parser.add_argument('--headless', action='store_true', help='Headless mode: Do not start Web Dashboard, display real-time data in terminal')
    args = parser.parse_args()
    
    # [NEW] Check RUN_MODE from .env (Config Manager integration)
    import os
    env_run_mode = os.getenv('RUN_MODE', 'test').lower()

    # Priority: explicit CLI (--test/--live) > Env Var
    if args.test:
        effective_test_mode = True
    elif args.live:
        effective_test_mode = False
    else:
        effective_test_mode = (env_run_mode != 'live')

    args.test = effective_test_mode

    if args.symbols:
        os.environ['TRADING_SYMBOLS'] = args.symbols.strip()
        
    print(f"🔧 Startup Mode: {'TEST' if args.test else 'LIVE'} (Env: {env_run_mode})")
    
    # ==============================================================================
    # 🛠️ [CORE FIX]: Force initialize database table structure
    # Instantiating TradingLogger will auto-execute _init_database() to create PostgreSQL tables
    # ==============================================================================
    try:
        log.info("🛠️ Checking/initializing database tables...")
        # This step is critical: it connects to the database and runs CREATE TABLE statements
        # Lazy import to avoid blocking startup (FIXME at line 112)
        from src.monitoring.logger import TradingLogger
        _db_init = TradingLogger()
        log.info("✅ Database tables ready")
    except Exception as e:
        log.error(f"❌ Database init failed (non-fatal, continuing): {e}")
        # Note: We catch the exception here but do not exit, to avoid affecting main program startup. However, please monitor the logs closely.
    # ==============================================================================
    
    # Set default cycle interval based on deployment mode
    # Local: 1 minute (for development/testing)
    # Railway: 5 minutes (production environment)
    if args.interval == 3.0:  # If user did not specify interval via CLI
        if DEPLOYMENT_MODE == 'local':
            args.interval = 1.0
            print(f"🏠 Local mode: Cycle interval set to 1 minute")
        else:
            args.interval = 5.0
            print(f"☁️ Railway mode: Cycle interval set to 5 minutes")
      
    # Trading parameters
    used_kline_limit = int(args.kline_limit) if args.kline_limit and args.kline_limit > 0 else 300

    trading_parameters = TradingParameters(
        max_position_size=args.max_position,
        leverage=args.leverage,
        stop_loss_pct=args.stop_loss,
        take_profit_pct=args.take_profit,
        kline_limit=used_kline_limit,
        test_mode=args.test
    )
    
    # Create bot
    bot = MultiAgentTradingBot(trading_parameters)

    # Set initial execution mode before dashboard starts
    # Require explicit user action (Start button) to begin trading
    global_state.execution_mode = "Stopped"
    
    # Start Dashboard Server (skip headless mode) - Start first so users can access immediately
    if not args.headless:
        try:
            server_thread = threading.Thread(target=start_server, daemon=True)
            server_thread.start()
            print("🌐 Dashboard server started at http://localhost:8000")
        except Exception as e:
            print(f"⚠️ Failed to start Dashboard: {e}")
    else:
        print("🖥️  Headless mode: Web Dashboard disabled")
    
    # 🔝 AUTO3 STARTUP EXECUTION (only for once mode; continuous uses selector loop)
    skip_auto3 = args.skip_auto3 and args.mode == 'once'
    if skip_auto3 and getattr(bot, 'use_auto3', False):
        log.info("⏭️ AUTO3 skipped for once mode")
        bot.use_auto3 = False

    if args.mode == 'once' and hasattr(bot, 'use_auto3') and bot.use_auto3:
        log.info("=" * 60)
        log.info("🔝 AUTO3 STARTUP - Getting AI500 Top5 and selecting Top2...")
        log.info("⏳ Dashboard available at http://localhost:8000 while backtest runs...")
        log.info("=" * 60)
        
        import asyncio
        loop = asyncio.get_event_loop()
        top2 = loop.run_until_complete(bot.resolve_auto3_symbols())
        
        # Update bot symbols
        bot.symbols = top2
        bot.current_symbol = top2[0] if top2 else 'FETUSDT'
        global_state.symbols = top2

        # Ensure PredictAgent exists for AUTO3 symbols
        for symbol in bot.symbols:
            if symbol not in bot.agent_provider.predict_agents_provider.predict_agents:
                bot.predict_agent_provider.predict_agents[symbol] = PredictAgent(horizon='30m', symbol=symbol)
                log.info(f"🆕 Initialized PredictAgent for {symbol} (AUTO3)")
        
        # Start auto-refresh thread (12h interval)
        bot.agent_provider.symbol_selector_agent.start_auto_refresh()
        
        log.info(f"✅ AUTO3 startup complete: {', '.join(top2)}")
        log.info("🔄 Auto-refresh started (12h interval)")
        log.info("=" * 60)
    
    # Run
    if args.mode == 'once':
        result = bot.run_once()
        print(f"\nFinal result: {json.dumps(result, indent=2)}")
        
        # Display statistics
        stats = bot.get_statistics()
        print(f"\nStatistics:")
        print(json.dumps(stats, indent=2))
        
        # Keep alive briefly for server to be reachable if desired, 
        # or exit immediately. Usually 'once' implies run and exit.
        
    else:
        # Default to Stopped - Wait for user to click Start button
        if global_state.execution_mode != "Running":
            global_state.execution_mode = "Stopped"
            log.info("🚀 System ready (Stopped). Waiting for user to click Start button...")
        
        global_state.is_running = True  # Keep event loop running
        bot.run_continuous(interval_minutes=args.interval, headless=args.headless)

if __name__ == '__main__':
    main()
