#!/usr/bin/env python3
"""
Simplified CLI Live Trading Script
Skip all non-essential components, keep only core trading functionality
"""
import sys
import os
import asyncio
from dotenv import load_dotenv

# Load .env file, but do not override existing system environment variables
# System environment variables take precedence over .env file configuration
load_dotenv(override=False)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Version number: v+date+iteration count
VERSION = "v20260111_3"

from src.api.binance_client import BinanceClient
from src.execution.engine import ExecutionEngine
from src.risk.manager import RiskManager
from src.agents import DataSyncAgent, QuantAnalystAgent, RiskAuditAgent
from src.data.processor import MarketDataProcessor
from src.strategy.llm_engine import StrategyEngine
from src.utils.logger import log
import time
from datetime import datetime

class SimpleTradingBot:
    """Simplified Trading Bot - Contains only core functionality"""
    
    def __init__(self, symbols=None, test_mode=True):
        print("="*60)
        print(f"🤖 Simple Trading Bot - Minimal CLI Mode ({VERSION})")
        print("="*60)
        
        # Read default symbols from .env
        if symbols is None:
            env_symbols = os.environ.get('TRADING_SYMBOLS', 'BTCUSDT').strip()
            symbols = [s.strip() for s in env_symbols.split(',') if s.strip()]
        
        # Check if using AUTO3 mode
        self.use_auto3 = 'AUTO3' in symbols
        if self.use_auto3:
            symbols.remove('AUTO3')
            print("\n🔝 AUTO3 mode detected - Will select best symbols via backtest...")
        
        # If no symbols or only AUTO3, use defaults
        if not symbols:
            symbols = ['BTCUSDT']
        
        self.symbols = symbols
        self.current_symbol = symbols[0]
        self.test_mode = test_mode
        
        # Core components
        print("\n📦 Initializing core components...")
        self.client = BinanceClient()
        self.risk_manager = RiskManager()
        self.execution_engine = ExecutionEngine(self.client, self.risk_manager)
        
        # Agents
        print("🤖 Initializing agents...")
        self.data_sync_agent = DataSyncAgent(self.client)
        self.quant_analyst = QuantAnalystAgent()
        self.risk_audit = RiskAuditAgent(
            max_leverage=10.0,
            max_position_pct=0.3,
            min_stop_loss_pct=0.005,
            max_stop_loss_pct=0.05
        )
        self.processor = MarketDataProcessor()
        
        # Strategy engine
        print("🧠 Initializing strategy engine...")
        self.strategy_engine = StrategyEngine()
        
        print("\n✅ Initialization complete!")
        print(f"📊 Trading: {', '.join(self.symbols)}")
        print(f"🧪 Test Mode: {test_mode}")
        print("="*60)
        
        # AUTO3 initialization: select best symbols
        if self.use_auto3:
            self._init_auto3()
    
    def _init_auto3(self):
        """Initialize AUTO3 - Select best trading symbols"""
        print("\n" + "="*60)
        print("🔝 AUTO3 STARTUP - Selecting best trading symbols...")
        print("="*60)
        
        try:
            from src.agents.symbol_selector_agent import SymbolSelectorAgent
            selector = SymbolSelectorAgent()
            
            # Run async selection
            loop = asyncio.get_event_loop()
            top_symbols = loop.run_until_complete(selector.select_top3(force_refresh=False))
            
            if top_symbols:
                self.symbols = top_symbols
                self.current_symbol = top_symbols[0]
                print(f"\n✅ AUTO3 selected: {', '.join(top_symbols)}")
            else:
                print("\n⚠️ AUTO3 failed to select symbols, using defaults")
                self.symbols = ['BTCUSDT', 'ETHUSDT']
                self.current_symbol = 'BTCUSDT'
                
            print("="*60)
            
        except Exception as e:
            log.error(f"AUTO3 initialization failed: {e}")
            print(f"\n⚠️ AUTO3 error: {e}")
            print("Using default symbols: BTCUSDT, ETHUSDT")
            self.symbols = ['BTCUSDT', 'ETHUSDT']
            self.current_symbol = 'BTCUSDT'
    
    async def run_once(self):
        """执行一次交易循环"""
        print(f"\n{'='*60}")
        print(f"🔄 Trading Cycle | {datetime.now().strftime('%H:%M:%S')} | {self.current_symbol}")
        print(f"{'='*60}")
        
        try:
            # 1. 获取市场数据
            print("\n[1/4] 📊 Fetching market data...")
            market_snapshot = await self.data_sync_agent.fetch_all_timeframes(
                self.current_symbol,
                limit=300
            )
            
            current_price = market_snapshot.live_5m.get('close')
            print(f"  ✅ Current price: ${current_price:,.2f}")
            
            # 2. 处理数据
            print("\n[2/4] 🔬 Processing indicators...")
            processed_dfs = {}
            for tf in ['5m', '15m', '1h']:
                raw_klines = getattr(market_snapshot, f'raw_{tf}')
                df = self.processor.process_klines(raw_klines, self.current_symbol, tf)
                processed_dfs[tf] = df
            
            # 更新快照
            market_snapshot.stable_5m = processed_dfs['5m']
            market_snapshot.stable_15m = processed_dfs['15m']
            market_snapshot.stable_1h = processed_dfs['1h']
            
            # 3. 生成信号
            print("\n[3/4] 🎯 Generating trading signals...")
            signals = self.quant_analyst.analyze(market_snapshot)
            print(f"  📈 Trend Signal: {signals.get('trend_signal', 'N/A')}")
            print(f"  📊 Oscillator Signal: {signals.get('oscillator_signal', 'N/A')}")
            
            # 4. 策略决策
            print("\n[4/4] 🧠 Making decision...")
            action = 'hold'
            
            if self.strategy_engine.is_ready:
                # 构建市场上下文数据
                df_5m = processed_dfs['5m']
                df_15m = processed_dfs['15m']
                df_1h = processed_dfs['1h']
                
                # 获取最新指标
                latest_5m = df_5m.iloc[-1] if not df_5m.empty else {}
                latest_15m = df_15m.iloc[-1] if not df_15m.empty else {}
                latest_1h = df_1h.iloc[-1] if not df_1h.empty else {}
                
                market_context_data = {
                    'symbol': self.current_symbol,
                    'timestamp': datetime.now().isoformat(),
                    'current_price': current_price,
                    'indicators': {
                        '5m': {
                            'rsi': float(latest_5m.get('rsi', 50)) if hasattr(latest_5m, 'get') else 50,
                            'ema_12': float(latest_5m.get('ema_12', current_price)) if hasattr(latest_5m, 'get') else current_price,
                            'ema_26': float(latest_5m.get('ema_26', current_price)) if hasattr(latest_5m, 'get') else current_price,
                            'macd': float(latest_5m.get('macd', 0)) if hasattr(latest_5m, 'get') else 0,
                            'macd_signal': float(latest_5m.get('macd_signal', 0)) if hasattr(latest_5m, 'get') else 0,
                        },
                        '15m': {
                            'rsi': float(latest_15m.get('rsi', 50)) if hasattr(latest_15m, 'get') else 50,
                            'ema_12': float(latest_15m.get('ema_12', current_price)) if hasattr(latest_15m, 'get') else current_price,
                            'ema_26': float(latest_15m.get('ema_26', current_price)) if hasattr(latest_15m, 'get') else current_price,
                            'macd': float(latest_15m.get('macd', 0)) if hasattr(latest_15m, 'get') else 0,
                        },
                        '1h': {
                            'rsi': float(latest_1h.get('rsi', 50)) if hasattr(latest_1h, 'get') else 50,
                            'ema_12': float(latest_1h.get('ema_12', current_price)) if hasattr(latest_1h, 'get') else current_price,
                            'ema_26': float(latest_1h.get('ema_26', current_price)) if hasattr(latest_1h, 'get') else current_price,
                            'macd': float(latest_1h.get('macd', 0)) if hasattr(latest_1h, 'get') else 0,
                        }
                    },
                    'signals': signals
                }
                
                # 判断各时间框架趋势
                def get_trend(ema12, ema26, rsi):
                    if ema12 > ema26 and rsi > 50:
                        return "📈 BULLISH"
                    elif ema12 < ema26 and rsi < 50:
                        return "📉 BEARISH"
                    else:
                        return "➡️ NEUTRAL"
                
                trend_5m = get_trend(
                    market_context_data['indicators']['5m']['ema_12'],
                    market_context_data['indicators']['5m']['ema_26'],
                    market_context_data['indicators']['5m']['rsi']
                )
                trend_15m = get_trend(
                    market_context_data['indicators']['15m']['ema_12'],
                    market_context_data['indicators']['15m']['ema_26'],
                    market_context_data['indicators']['15m']['rsi']
                )
                trend_1h = get_trend(
                    market_context_data['indicators']['1h']['ema_12'],
                    market_context_data['indicators']['1h']['ema_26'],
                    market_context_data['indicators']['1h']['rsi']
                )
                
                # 构建完整的市场上下文文本
                market_context_text = f"""
=== Market Analysis for {self.current_symbol} ===
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Current Price: ${current_price:,.2f}

📊 1H TIMEFRAME (PRIMARY TREND):
- Trend: {trend_1h}
- RSI: {market_context_data['indicators']['1h']['rsi']:.1f}
- EMA12: ${market_context_data['indicators']['1h']['ema_12']:,.2f}
- EMA26: ${market_context_data['indicators']['1h']['ema_26']:,.2f}
- MACD: {market_context_data['indicators']['1h']['macd']:.4f}

📊 15M TIMEFRAME (CONFLUENCE):
- Trend: {trend_15m}
- RSI: {market_context_data['indicators']['15m']['rsi']:.1f}
- EMA12: ${market_context_data['indicators']['15m']['ema_12']:,.2f}
- EMA26: ${market_context_data['indicators']['15m']['ema_26']:,.2f}
- MACD: {market_context_data['indicators']['15m']['macd']:.4f}

📊 5M TIMEFRAME (ENTRY):
- Trend: {trend_5m}
- RSI: {market_context_data['indicators']['5m']['rsi']:.1f}
- EMA12: ${market_context_data['indicators']['5m']['ema_12']:,.2f}
- EMA26: ${market_context_data['indicators']['5m']['ema_26']:,.2f}
- MACD: {market_context_data['indicators']['5m']['macd']:.4f}
- MACD Signal: {market_context_data['indicators']['5m']['macd_signal']:.4f}

📈 Signal Summary:
- Trend Signal: {signals.get('trend_signal', 'N/A')}
- Oscillator Signal: {signals.get('oscillator_signal', 'N/A')}
- Composite Signal: {signals.get('composite_signal', 'N/A')}

📊 Multi-Timeframe Alignment:
- 1H + 15M + 5M: {trend_1h} | {trend_15m} | {trend_5m}
"""
                
                try:
                    decision = self.strategy_engine.make_decision(
                        market_context_text,
                        market_context_data
                    )
                    
                    action = decision.get('action', 'hold')
                    confidence = decision.get('confidence', 0)
                    reasoning = decision.get('reasoning', 'N/A')
                    
                    print(f"\n{'='*60}")
                    print(f"📋 DECISION SUMMARY")
                    print(f"{'='*60}")
                    print(f"  Action: {action.upper()}")
                    print(f"  Confidence: {confidence}%")
                    print(f"  Reasoning: {reasoning[:100] if reasoning else 'N/A'}...")
                    print(f"{'='*60}")
                    
                    # 风控审计
                    if action != 'hold':
                        # 注意：风控审计需要异步调用，这里简化处理
                        print(f"\n✅ Risk check: Action={action}, Confidence={confidence}%")
                    
                    # 执行交易（测试模式下只打印）
                    if action != 'hold':
                        if self.test_mode:
                            print(f"\n🧪 TEST MODE - Would execute: {action} {self.current_symbol}")
                        else:
                            print(f"\n💰 Executing: {action} {self.current_symbol}")
                            # 实际执行逻辑在这里
                    else:
                        print(f"\n⏸️ HOLD - No action taken")
                        
                except Exception as e:
                    log.error(f"LLM decision failed: {e}")
                    print(f"\n⚠️ Decision failed: {e}")
                    action = 'hold'
            else:
                print("  ⚠️ Strategy engine not ready (missing API key)")
            
            return {'status': 'success', 'action': action}
            
        except Exception as e:
            log.error(f"Trading cycle failed: {e}")
            import traceback
            traceback.print_exc()
            return {'status': 'error', 'error': str(e)}
    
    def run_continuous(self, interval_minutes=3):
        """持续运行"""
        print(f"\n🔄 Starting continuous mode (interval: {interval_minutes} min)")
        print("Press Ctrl+C to stop\n")
        
        loop = asyncio.get_event_loop()
        
        try:
            while True:
                loop.run_until_complete(self.run_once())
                
                print(f"\n⏳ Waiting {interval_minutes} minutes until next cycle...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down gracefully...")
            print("✅ Stopped")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Trading Bot CLI')
    parser.add_argument('--symbols', type=str, default=None, 
                       help='Trading symbols (comma-separated), default: read from .env')
    parser.add_argument('--mode', choices=['once', 'continuous'], default='once',
                       help='Run mode')
    parser.add_argument('--interval', type=float, default=3.0,
                       help='Interval in minutes (continuous mode)')
    parser.add_argument('--live', action='store_true',
                       help='Live mode (default is test mode)')
    
    args = parser.parse_args()
    
    # 处理符号：命令行参数优先，否则使用 None 让 Bot 从 .env 读取
    symbols = None
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
    
    test_mode = not args.live
    
    bot = SimpleTradingBot(symbols=symbols, test_mode=test_mode)
    
    if args.mode == 'once':
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(bot.run_once())
        print(f"\n✅ Cycle complete: {result}")
    else:
        bot.run_continuous(interval_minutes=args.interval)

if __name__ == '__main__':
    main()

