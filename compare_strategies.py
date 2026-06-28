#!/usr/bin/env python3
"""
Strategy Comparison Backtest Script
Compare default strategy vs optimized V2 strategy
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.backtest.engine import BacktestEngine, BacktestConfig
from src.strategies.optimized_v2 import strategy_v2_wrapper, StrategyConfig


async def run_strategy_comparison(
    symbol: str = "SOLUSDT",  # Use the best performing symbol from previous runs
    days: int = 1
):
    """Run strategy comparison"""
    
    end_date = datetime.now() - timedelta(days=1)  # Use yesterday as end to avoid incomplete data
    start_date = end_date - timedelta(days=days)
    
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    print("\n" + "="*70)
    print("🔬 Strategy Comparison Backtest")
    print("="*70)
    print(f"📊 Symbol: {symbol}")
    print(f"📅 Period: {start_str} to {end_str}")
    print(f"💰 Initial Capital: $10,000")
    print("="*70)
    
    results = []
    
    # 1️⃣ Test default strategy (technical)
    print("\n📈 1. Testing default strategy (Technical)...")
    
    config1 = BacktestConfig(
        symbol=symbol,
        start_date=start_str,
        end_date=end_str,
        initial_capital=10000,
        step=3,
        strategy_mode="technical",
    )
    
    try:
        engine1 = BacktestEngine(config1)
        result1 = await engine1.run()
        results.append({
            'name': 'Default (Technical)',
            'return': result1.metrics.total_return,
            'win_rate': result1.metrics.win_rate,
            'trades': result1.metrics.total_trades,
            'sharpe': result1.metrics.sharpe_ratio,
            'max_dd': result1.metrics.max_drawdown_pct,
        })
        print(f"   ✅ Return: {result1.metrics.total_return:+.2f}%")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append({
            'name': 'Default (Technical)',
            'return': None,
            'error': str(e)
        })

    # 2️⃣ Test optimized V2 strategy
    print("\n📈 2. Testing optimized V2 strategy...")
    
    config2 = BacktestConfig(
        symbol=symbol,
        start_date=start_str,
        end_date=end_str,
        initial_capital=10000,
        step=3,
        strategy_mode="technical",  # Use technical mode but inject custom strategy
    )
    
    try:
        engine2 = BacktestEngine(config2)
        # Inject optimized strategy
        engine2.strategy_fn = strategy_v2_wrapper
        
        result2 = await engine2.run()
        results.append({
            'name': 'Optimized V2',
            'return': result2.metrics.total_return,
            'win_rate': result2.metrics.win_rate,
            'trades': result2.metrics.total_trades,
            'sharpe': result2.metrics.sharpe_ratio,
            'max_dd': result2.metrics.max_drawdown_pct,
        })
        print(f"   ✅ Return: {result2.metrics.total_return:+.2f}%")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append({
            'name': 'Optimized V2',
            'return': None,
            'error': str(e)
        })

    # 3️⃣ Test aggressive V2 strategy (lower entry threshold)
    print("\n📈 3. Testing aggressive V2 strategy (low threshold)...")
    
    config3 = BacktestConfig(
        symbol=symbol,
        start_date=start_str,
        end_date=end_str,
        initial_capital=10000,
        step=3,
        strategy_mode="technical",
    )
    
    # Create aggressive config
    aggressive_config = StrategyConfig(
        rsi_oversold=40,  # More relaxed
        rsi_overbought=60,
        ema_fast=5,  # Faster
        ema_slow=13,
        rvol_threshold=1.0,  # No high volume requirement
    )
    
    async def aggressive_strategy(snapshot, portfolio, current_price, config):
        from src.strategies.optimized_v2 import optimized_strategy_v2
        return optimized_strategy_v2(snapshot, portfolio, current_price, config, aggressive_config)
    
    try:
        engine3 = BacktestEngine(config3)
        engine3.strategy_fn = aggressive_strategy
        
        result3 = await engine3.run()
        results.append({
            'name': 'Aggressive V2',
            'return': result3.metrics.total_return,
            'win_rate': result3.metrics.win_rate,
            'trades': result3.metrics.total_trades,
            'sharpe': result3.metrics.sharpe_ratio,
            'max_dd': result3.metrics.max_drawdown_pct,
        })
        print(f"   ✅ Return: {result3.metrics.total_return:+.2f}%")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append({
            'name': 'Aggressive V2',
            'return': None,
            'error': str(e)
        })

    # Print comparison results
    print("\n" + "="*70)
    print("📊 Strategy Comparison Results")
    print("="*70)
    
    print(f"\n{'Strategy Name':<20} {'Return':>10} {'Win Rate':>10} {'Trades':>10} {'Sharpe':>10} {'Max Drawdown':>10}")
    print("-"*70)
    
    for r in results:
        if r.get('return') is not None:
            print(f"{r['name']:<20} {r['return']:>+9.2f}% {r['win_rate']:>9.1f}% {r['trades']:>10} {r['sharpe']:>10.2f} {r['max_dd']:>9.2f}%")
        else:
            print(f"{r['name']:<20} {'ERROR':>10}")
    
    # Find the best strategy
    valid_results = [r for r in results if r.get('return') is not None]
    if valid_results:
        best = max(valid_results, key=lambda x: x['return'])
        print("\n" + "="*70)
        print(f"🏆 Best Strategy: {best['name']}")
        print(f"   Return: {best['return']:+.2f}%")
        print(f"   Win Rate: {best['win_rate']:.1f}%")
        print(f"   Trades: {best['trades']}")
        print("="*70)
    
    return results


async def run_multi_symbol_comparison():
    """Multi-symbol comparison test"""
    
    symbols = ["SOLUSDT", "BTCUSDT", "ETHUSDT"]
    all_results = {}
    
    for symbol in symbols:
        print(f"\n\n{'#'*70}")
        print(f"# Testing symbol: {symbol}")
        print(f"{'#'*70}")
        
        results = await run_strategy_comparison(symbol=symbol, days=1)
        all_results[symbol] = results
    
    # Summary
    print("\n\n" + "="*70)
    print("📊 Multi-Symbol Strategy Summary")
    print("="*70)
    
    for symbol, results in all_results.items():
        print(f"\n{symbol}:")
        for r in results:
            if r.get('return') is not None:
                print(f"  {r['name']}: {r['return']:+.2f}%")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Strategy Comparison Backtest")
    parser.add_argument("--symbol", type=str, default="SOLUSDT", help="Trading pair")
    parser.add_argument("--days", type=int, default=1, help="Backtest days")
    parser.add_argument("--multi", action="store_true", help="Multi-symbol test")
    
    args = parser.parse_args()
    
    if args.multi:
        asyncio.run(run_multi_symbol_comparison())
    else:
        asyncio.run(run_strategy_comparison(symbol=args.symbol, days=args.days))
