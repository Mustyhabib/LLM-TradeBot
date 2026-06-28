#!/usr/bin/env python3
"""
Backtest Parameter Optimization Script
Automatically run multiple backtests to find optimal parameter combinations
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.backtest.engine import BacktestEngine, BacktestConfig


class BacktestOptimizer:
    """Backtest Parameter Optimizer"""
    
    def __init__(self):
        self.results = []
    
    async def run_single_backtest(self, config: BacktestConfig) -> Dict:
        """Run single backtest"""
        try:
            engine = BacktestEngine(config)
            result = await engine.run()
            
            return {
                'config': {
                    'symbol': config.symbol,
                    'start_date': config.start_date,
                    'end_date': config.end_date,
                    'initial_capital': config.initial_capital,
                    'stop_loss_pct': config.stop_loss_pct,
                    'take_profit_pct': config.take_profit_pct,
                    'strategy_mode': config.strategy_mode,
                },
                'metrics': {
                    'total_return': result.metrics.total_return,
                    'total_return_pct': result.metrics.total_return_pct,
                    'win_rate': result.metrics.win_rate,
                    'total_trades': result.metrics.total_trades,
                    'sharpe_ratio': result.metrics.sharpe_ratio,
                    'max_drawdown_pct': result.metrics.max_drawdown_pct,
                },
                'success': True
            }
        except Exception as e:
            print(f"❌ Backtest failed: {e}")
            return {
                'config': {
                    'symbol': config.symbol,
                    'start_date': config.start_date,
                    'end_date': config.end_date,
                },
                'error': str(e),
                'success': False
            }
    
    async def optimize_time_periods(self, symbol: str = "BTCUSDT", capital: float = 10000):
        """Optimize returns across different time periods"""
        
        print("\n" + "="*60)
        print("🔍 Starting time period optimization")
        print("="*60)
        
        # 定义测试的时间周期（从今天往前推）
        today = datetime.now()
        test_periods = [
            ("1天", today - timedelta(days=1), today),
            ("3天", today - timedelta(days=3), today),
            ("7天", today - timedelta(days=7), today),
            ("14天", today - timedelta(days=14), today),
        ]
        
        results = []
        
        for period_name, start_date, end_date in test_periods:
            print(f"\n📊 测试 {period_name} ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
            
            config = BacktestConfig(
                symbol=symbol,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                initial_capital=capital,
                step=3,  # 15分钟
                strategy_mode="technical",
            )
            
            result = await self.run_single_backtest(config)
            result['period_name'] = period_name
            results.append(result)
            
            if result['success']:
                m = result['metrics']
                print(f"  ✅ 收益率: {m['total_return_pct']:+.2f}% | 胜率: {m['win_rate']:.1f}% | 交易次数: {m['total_trades']}")
            else:
                print(f"  ❌ 失败: {result.get('error', 'Unknown error')}")
        
        return results
    
    async def optimize_parameters(self, symbol: str = "BTCUSDT", days: int = 7):
        """优化策略参数（止损、止盈）"""
        
        print("\n" + "="*60)
        print("🔍 开始参数优化")
        print("="*60)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 定义参数网格
        stop_loss_values = [0.5, 1.0, 1.5, 2.0]
        take_profit_values = [1.0, 2.0, 3.0, 4.0]
        
        results = []
        total_tests = len(stop_loss_values) * len(take_profit_values)
        current_test = 0
        
        for sl in stop_loss_values:
            for tp in take_profit_values:
                current_test += 1
                print(f"\n[{current_test}/{total_tests}] 测试 SL={sl}% TP={tp}%")
                
                config = BacktestConfig(
                    symbol=symbol,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                    initial_capital=10000,
                    stop_loss_pct=sl,
                    take_profit_pct=tp,
                    step=3,
                    strategy_mode="technical",
                )
                
                result = await self.run_single_backtest(config)
                results.append(result)
                
                if result['success']:
                    m = result['metrics']
                    print(f"  收益率: {m['total_return_pct']:+.2f}% | 胜率: {m['win_rate']:.1f}%")
        
        return results
    
    async def optimize_symbols(self, days: int = 3):
        """优化不同币种的收益率"""
        
        print("\n" + "="*60)
        print("🔍 开始币种优化")
        print("="*60)
        
        # 热门交易对
        symbols = [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
            "LINKUSDT", "NEARUSDT", "FETUSDT", "RENDERUSDT"
        ]
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        results = []
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}] 测试 {symbol}")
            
            config = BacktestConfig(
                symbol=symbol,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                initial_capital=10000,
                step=3,
                strategy_mode="technical",
            )
            
            result = await self.run_single_backtest(config)
            results.append(result)
            
            if result['success']:
                m = result['metrics']
                print(f"  ✅ 收益率: {m['total_return_pct']:+.2f}% | 胜率: {m['win_rate']:.1f}% | 交易: {m['total_trades']}")
        
        return results
    
    def save_results(self, results: List[Dict], filename: str):
        """保存优化结果"""
        os.makedirs('reports', exist_ok=True)
        filepath = f"reports/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 结果已保存到: {filepath}")
    
    def print_summary(self, results: List[Dict]):
        """打印优化总结"""
        
        successful_results = [r for r in results if r.get('success', False)]
        
        if not successful_results:
            print("\n❌ 没有成功的回测结果")
            return
        
        # 按收益率排序
        sorted_results = sorted(
            successful_results,
            key=lambda x: x['metrics']['total_return_pct'],
            reverse=True
        )
        
        print("\n" + "="*60)
        print("🏆 优化结果总结（按收益率排序）")
        print("="*60)
        
        for i, result in enumerate(sorted_results[:10], 1):
            config = result['config']
            metrics = result['metrics']
            
            print(f"\n#{i}")
            print(f"  币种: {config.get('symbol', 'N/A')}")
            print(f"  周期: {config.get('start_date', 'N/A')} to {config.get('end_date', 'N/A')}")
            if 'stop_loss_pct' in config:
                print(f"  参数: SL={config['stop_loss_pct']}% TP={config['take_profit_pct']}%")
            print(f"  📈 收益率: {metrics['total_return_pct']:+.2f}%")
            print(f"  📊 胜率: {metrics['win_rate']:.1f}%")
            print(f"  🔢 交易次数: {metrics['total_trades']}")
            print(f"  📉 最大回撤: {metrics['max_drawdown_pct']:.2f}%")


async def main():
    """主函数"""
    
    optimizer = BacktestOptimizer()
    
    print("\n" + "="*60)
    print("🚀 LLM-TradeBot 回测优化器")
    print("="*60)
    print("\n选择优化模式:")
    print("1. 时间周期优化 (1天, 3天, 7天, 14天)")
    print("2. 参数优化 (止损/止盈)")
    print("3. 币种优化 (多个交易对)")
    print("4. 全面优化 (所有模式)")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    all_results = []
    
    if choice == "1":
        results = await optimizer.optimize_time_periods()
        all_results.extend(results)
        optimizer.save_results(results, "optimization_time_periods.json")
    
    elif choice == "2":
        results = await optimizer.optimize_parameters()
        all_results.extend(results)
        optimizer.save_results(results, "optimization_parameters.json")
    
    elif choice == "3":
        results = await optimizer.optimize_symbols()
        all_results.extend(results)
        optimizer.save_results(results, "optimization_symbols.json")
    
    elif choice == "4":
        print("\n🔥 开始全面优化...")
        
        # 时间周期
        time_results = await optimizer.optimize_time_periods()
        all_results.extend(time_results)
        
        # 参数优化
        param_results = await optimizer.optimize_parameters(days=3)
        all_results.extend(param_results)
        
        # 币种优化
        symbol_results = await optimizer.optimize_symbols(days=3)
        all_results.extend(symbol_results)
        
        optimizer.save_results(all_results, "optimization_full.json")
    
    else:
        print("❌ 无效选择")
        return
    
    # 打印总结
    optimizer.print_summary(all_results)
    
    print("\n" + "="*60)
    print("✅ 优化完成!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
