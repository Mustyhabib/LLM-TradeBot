#!/usr/bin/env python3
"""
LLM-TradeBot Backtest System CLI
==========================

Usage:
    python backtest.py --start 2024-01-01 --end 2024-12-01 \
        --symbol BTCUSDT --capital 10000 --output reports/

Parameters:
    --start       Backtest start date (YYYY-MM-DD)
    --end         Backtest end date (YYYY-MM-DD)
    --symbol      Trading pair (default: BTCUSDT)
    --capital     Initial capital (USDT, default: 10000)
    --step        Time step (1=5min, 3=15min, 12=1hour, default: 3)
    --output      Report output directory (default: reports/)
    --no-report   Do not generate HTML report

Author: AI Trader Team
Date: 2025-12-31
"""

import argparse
import asyncio
import sys
import os

# Add project root directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="LLM-TradeBot Backtester",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backtest BTC for the whole year 2024
  python backtest.py --start 2024-01-01 --end 2024-12-31 --symbol BTCUSDT

  # Quick backtest (hourly decisions)
  python backtest.py --start 2024-12-01 --end 2024-12-31 --step 12

  # Specify initial capital
  python backtest.py --start 2024-06-01 --end 2024-12-01 --capital 50000
        """
    )
    
    parser.add_argument(
        "--start", "-s",
        type=str,
        required=True,
        help="Backtest start date (YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "--end", "-e",
        type=str,
        required=True,
        help="Backtest end date (YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "--symbol",
        type=str,
        default="AUTO1",  # Default to AUTO1, consistent with live trading
        help="Trading pair (AUTO1=Momentum selection[default], AUTO3=Backtest selection, or specify like BTCUSDT)"
    )
    
    parser.add_argument(
        "--no-auto3",
        action="store_true",
        help="Disable AUTO3 automatic selection, use --symbol specified symbol"
    )
    
    parser.add_argument(
        "--capital",
        type=float,
        default=10000.0,
        help="Initial capital USDT (default: 10000)"
    )
    
    parser.add_argument(
        "--step",
        type=int,
        default=3,
        choices=[1, 3, 12],
        help="Time step: 1=5min, 3=15min, 12=1hour (default: 3)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="reports",
        help="Report output directory (default: reports/)"
    )
    
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Do not generate HTML report"
    )
    
    parser.add_argument(
        "--max-position",
        type=float,
        default=100.0,
        help="Maximum single position USDT (default: 100)"
    )
    
    parser.add_argument(
        "--stop-loss",
        type=float,
        default=1.0,
        help="Stop-loss percentage (default: 1.0%%)"
    )
    
    parser.add_argument(
        "--take-profit",
        type=float,
        default=2.0,
        help="Take-profit percentage (default: 2.0%%)"
    )
    
    parser.add_argument(
        "--strategy-mode",
        type=str,
        default="agent",
        choices=["technical", "agent"],
        help="Strategy mode: technical (Simple EMA) or agent (Multi-Agent framework, default: agent)"
    )
    
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Enable LLM enhancement (only effective in agent mode, will incur API costs)"
    )
    
    parser.add_argument(
        "--llm-cache",
        action="store_true",
        default=True,
        help="Cache LLM responses to save costs (default: True)"
    )
    
    return parser.parse_args()


def validate_dates(start: str, end: str):
    """Validate date format"""
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")
        
        if start_date >= end_date:
            print("❌ Error: Start date must be before end date")
            sys.exit(1)
        
        if end_date > datetime.now():
            print("⚠️ Warning: End date is in the future, using today's date")
            end_date = datetime.now()
        
        return start_date, end_date
        
    except ValueError as e:
        print(f"❌ Error: Invalid date format. Use YYYY-MM-DD")
        sys.exit(1)


async def main():
    """Main function"""
    args = parse_args()
    
    # Validate dates
    start_date, end_date = validate_dates(args.start, args.end)
    
    # Display configuration
    print("\n" + "=" * 60)
    print("🔬 LLM-TradeBot Backtester")
    print("=" * 60)
    print(f"📅 Period: {args.start} to {args.end}")
    print(f"💰 Symbol: {args.symbol}")
    print(f"💵 Initial Capital: ${args.capital:,.2f}")
    print(f"⏱️ Step: {args.step} ({['', '5min', '', '15min', '', '', '', '', '', '', '', '', '1hour'][args.step]})")
    print(f"🎯 Strategy Mode: {args.strategy_mode.upper()}")
    if args.strategy_mode == "agent":
        print(f"🤖 LLM Enhanced: {'Yes' if args.use_llm else 'No (Quant Only)'}")
        if args.use_llm:
            print(f"💾 LLM Cache: {'Enabled' if args.llm_cache else 'Disabled'}")
    print(f"🛡️ Stop Loss: {args.stop_loss}%")
    print(f"🎯 Take Profit: {args.take_profit}%")
    print("=" * 60)
    
    # Import backtest modules
    from src.backtest.engine import BacktestEngine, BacktestConfig
    from src.backtest.report import BacktestReport
    from src.agents.symbol_selector_agent import SymbolSelectorAgent
    
    # AUTO3/AUTO1 dynamic symbol selection
    symbols_to_test = []
    use_auto3 = args.symbol == "AUTO3" and not args.no_auto3
    use_auto1 = args.symbol == "AUTO1"
    
    if use_auto3:
        print("\n🔝 AUTO3 starting - Selecting best trading symbols...")
        try:
            selector = SymbolSelectorAgent()
            selected = selector.get_symbols(force_refresh=False)
            if selected:
                symbols_to_test = selected
                print(f"✅ AUTO3 selected: {', '.join(symbols_to_test)}")
            else:
                print("⚠️ AUTO3 selection failed, using default BTCUSDT")
                symbols_to_test = ['BTCUSDT']
        except Exception as e:
            print(f"⚠️ AUTO3 selection error: {e}, using default BTCUSDT")
            symbols_to_test = ['BTCUSDT']
    elif use_auto1:
        print("\n🎯 AUTO1 starting - Using recent momentum selection...")
        try:
            selector = SymbolSelectorAgent()
            selected = await selector.select_auto1_recent_momentum()
            if selected:
                symbols_to_test = selected
                print(f"✅ AUTO1 selected: {', '.join(symbols_to_test)}")
            else:
                print("⚠️ AUTO1 selection failed, using default BTCUSDT")
                symbols_to_test = ['BTCUSDT']
        except Exception as e:
            print(f"⚠️ AUTO1 selection error: {e}, using default BTCUSDT")
            symbols_to_test = ['BTCUSDT']
    else:
        symbols_to_test = [args.symbol]
    
    # Run multi-symbol backtest (AUTO3 supported)
    all_results = []
    
    for symbol in symbols_to_test:
        print(f"\n{'='*60}")
        print(f"🔬 Backtest symbol: {symbol}")
        print(f"{'='*60}")
        
        # Create configuration
        config = BacktestConfig(
            symbol=symbol,
            start_date=args.start,
            end_date=args.end,
            initial_capital=args.capital,
            max_position_size=args.max_position,
            stop_loss_pct=args.stop_loss,
            take_profit_pct=args.take_profit,
            step=args.step,
            strategy_mode=args.strategy_mode,
            use_llm=args.use_llm,
            llm_cache=args.llm_cache
        )
        
        # Create engine
        engine = BacktestEngine(config)
        
        # Progress display
        last_pct = 0
        def progress_callback(data):
            nonlocal last_pct
            pct = data.get('progress', data.get('pct', 0))
            if int(pct) > last_pct:
                last_pct = int(pct)
                bar_len = 30
                filled = int(bar_len * pct / 100)
                bar = "█" * filled + "░" * (bar_len - filled)
                print(f"\r📊 Progress: [{bar}] {pct:.1f}%", end="", flush=True)
        
        # Run backtest
        try:
            result = await engine.run(progress_callback=progress_callback)
            print()  # New line
            all_results.append((symbol, result, engine))
        except KeyboardInterrupt:
            print("\n\n⚠️ Backtest interrupted by user")
            sys.exit(0)
        except Exception as e:
            print(f"\n\n❌ Error during backtest for {symbol}: {e}")
            continue
    
    # Display all results summary
    if not all_results:
        print("\n❌ No successful backtests completed")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    mode_label = ""
    if use_auto3:
        mode_label = " (AUTO3)"
    elif use_auto1:
        mode_label = " (AUTO1)"
    print(f"📊 Backtest results summary{mode_label}")
    print("=" * 60)
    
    total_return_sum = 0
    for symbol, result, engine in all_results:
        m = result.metrics
        total_return_sum += m.total_return
        
        print(f"\n🪙 {symbol}:")
        print(f"   Return: {m.total_return:+.2f}% | Drawdown: {m.max_drawdown_pct:.2f}% | Win Rate: {m.win_rate:.1f}% | Trades: {m.total_trades}")
        
        # Generate report
        if not args.no_report:
            os.makedirs(args.output, exist_ok=True)
            report = BacktestReport(output_dir=args.output)
            filename = f"backtest_{symbol}_{args.start}_{args.end}"
            filepath = report.generate(
                metrics=m,
                equity_curve=result.equity_curve,
                trades_df=engine.portfolio.get_trades_dataframe(),
                config={
                    'symbol': symbol,
                    'initial_capital': args.capital,
                },
                filename=filename
            )
            print(f"   📄 Report: {filepath}")
    
    if len(all_results) > 1:
        print(f"\n📈 Total Return (All Symbols): {total_return_sum:+.2f}%")
    
    print("\n" + "=" * 60)
    print("✅ Backtest completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
