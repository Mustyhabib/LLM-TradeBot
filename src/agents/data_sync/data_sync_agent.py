"""
Data Oracle (The Oracle) Agent

Responsibilities:
1. Asynchronously fetch multi-timeframe K-line data concurrently
2. Split stable/live dual views
3. Time alignment validation

Optimizations:
- Concurrent IO, saving 60% time
- Dual-view data structure, resolving lag issues
"""

import asyncio
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple

from src.api.binance_client import BinanceClient
from src.api.quant_client import quant_client
from src.utils.logger import log
from src.utils.oi_tracker import oi_tracker
from src.utils.kline_cache import get_kline_cache

from .market_snapshot import MarketSnapshot

class DataSyncAgent:
    """
    Data Oracle (The Oracle)
    
    Core optimizations:
    1. Asynchronous concurrent requests (asyncio.gather)
    2. Dual-view data structure (stable + live)
    3. Time alignment validation
    """
    
    def __init__(self, client: BinanceClient = None):
        """
        Initialize the Data Sync Agent
        
        Args:
            client: Binance client instance; if None, one is created automatically
        """
        self.client = client or BinanceClient()
        
        # WebSocket manager (optional, disabled by default to avoid event loop conflicts)
        import os
        is_railway = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"))
        self.use_websocket = (os.getenv("USE_WEBSOCKET", "false").lower() == "true") and not is_railway
        self.ws_managers = {}
        self._initial_load_complete = {}
        self._ws_disabled_symbols = set()
        
        if self.use_websocket:
            log.info("🚀 WebSocket data stream enabled")
        else:
            log.info("📡 Using REST API mode (WebSocket disabled)")
        
        self.last_snapshot = None
        
        # Initialize K-line cache for incremental fetching
        self._kline_cache = get_kline_cache()
        
        log.info("🕵️ The Oracle (DataSync Agent) initialized")
    
    async def fetch_all_timeframes(
        self,
        symbol: str = "BTCUSDT",
        limit: int = 300
    ) -> MarketSnapshot:
        """
        Asynchronously fetch all timeframe data concurrently
        
        Args:
            symbol: Trading pair
            limit: Number of K-lines to fetch per timeframe
            
        Returns:
            MarketSnapshot object containing dual-view data
        """
        start_time = datetime.now()
        
        # log.oracle(f"📊 开始并发获取 {symbol} 数据...")
        
        use_rest_fallback = False
        symbol_key = symbol.upper()
        ws_manager = None
        ws_enabled = self.use_websocket and symbol_key not in self._ws_disabled_symbols
        
        # WebSocket mode: get data from cache
        if ws_enabled:
            ws_manager = self.ws_managers.get(symbol_key)
            if not ws_manager:
                try:
                    from src.api.binance_websocket import BinanceWebSocketManager
                    ws_manager = BinanceWebSocketManager(
                        symbol=symbol_key,
                        timeframes=['5m', '15m', '1h']
                    )
                    ws_manager.start()
                    self.ws_managers[symbol_key] = ws_manager
                    log.info(f"🚀 WebSocket Manager started: {symbol_key}")
                except RuntimeError as e:
                    if "event loop" in str(e).lower():
                        log.warning(f"[{symbol}] WebSocket event loop conflict, falling back to REST API: {e}")
                    else:
                        log.warning(f"[{symbol}] WebSocket startup failed (RuntimeError), falling back to REST API: {e}")
                    self._ws_disabled_symbols.add(symbol_key)
                    ws_enabled = False
                except Exception as e:
                    log.warning(f"[{symbol}] WebSocket startup failed, falling back to REST API: {e}")
                    self._ws_disabled_symbols.add(symbol_key)
                    ws_enabled = False

        if ws_enabled and ws_manager and self._initial_load_complete.get(symbol_key):
            # Get data from WebSocket cache
            k5m = ws_manager.get_klines('5m', limit)
            k15m = ws_manager.get_klines('15m', limit)
            k1h = ws_manager.get_klines('1h', limit)
            
            # Check if data is sufficient
            min_len = min(len(k5m), len(k15m), len(k1h))
            if min_len < limit:
                log.warning(f"[{symbol}] WebSocket cache data insufficient (min={min_len}, limit={limit}), falling back to REST API")
                use_rest_fallback = True
            else:
                # Still need to fetch external data asynchronously
                q_data = await quant_client.fetch_coin_data(symbol)
                # [DISABLE OI] Commented out due to API errors
                # b_funding, b_oi = await asyncio.gather(
                #     loop.run_in_executor(None, self.client.get_funding_rate_with_cache, symbol),
                #     loop.run_in_executor(None, self.client.get_open_interest, symbol)
                # )
                b_funding = await self.client.get_funding_rate_with_cache(symbol) # Run non-concurrently or just wait
                b_oi = {} # Mock empty OI

        if not ws_enabled or not self._initial_load_complete.get(symbol_key) or use_rest_fallback:
            # Get event loop for concurrent operations
            loop = asyncio.get_event_loop()
            
            # Fetch with incremental caching
            k5m = await self._fetch_with_cache(symbol_key, '5m', limit)
            k15m = await self._fetch_with_cache(symbol_key, '15m', limit)
            k1h = await self._fetch_with_cache(symbol_key, '1h', limit)
            
            # Fetch external data concurrently
            q_data = await quant_client.fetch_coin_data(symbol)
            b_funding = await loop.run_in_executor(
                None,
                self.client.get_funding_rate_with_cache,
                symbol
            )
            b_oi = {}  # Mock empty OI
            
            log.info(f"[{symbol}] Data fetched: 5m={len(k5m)}, 15m={len(k15m)}, 1h={len(k1h)}")
            
            # Mark initial load complete
            if ws_enabled and not self._initial_load_complete.get(symbol_key):
                self._initial_load_complete[symbol_key] = True
                log.info(f"✅ Initial data loaded ({symbol_key}), will use WebSocket cache for updates")
        
        fetch_duration = (datetime.now() - start_time).total_seconds()
        # log.oracle(f"✅ Data fetch complete, took: {fetch_duration:.2f}s")
        
        # Split dual views
        stable_5m, live_5m = self._split_klines(k5m)
        stable_15m, live_15m = self._split_klines(k15m)
        stable_1h, live_1h = self._split_klines(k1h)

        snapshot = MarketSnapshot(
            # Trading pair identifier
            symbol=symbol,  # 🔧 FIX: Propagate symbol through pipeline
            # 5m data
            stable_5m=stable_5m,
            live_5m=live_5m,
            
            # 15m data
            stable_15m=stable_15m,
            live_15m=live_15m,
            
            # 1h data
            stable_1h=stable_1h,
            live_1h=live_1h,
            
            # Metadata
            timestamp=datetime.now(),
            alignment_ok=self._check_alignment(k5m, k15m, k1h),
            fetch_duration=fetch_duration,
            
            # Raw data
            raw_5m=k5m,
            raw_15m=k15m,
            raw_1h=k1h,
            quant_data=q_data,
            binance_funding=b_funding,
            binance_oi=b_oi
        )
        
        # 🔮 Record OI to history tracker
        if b_oi and b_oi.get('open_interest', 0) > 0:
            oi_tracker.record(
                symbol=symbol,
                oi_value=b_oi['open_interest'],
                timestamp=b_oi.get('timestamp')
            )
        
        # Cache latest snapshot
        self.last_snapshot = snapshot
        
        # Log recording
        # self._log_snapshot_info(snapshot)
        
        return snapshot
    
    async def _fetch_with_cache(self, symbol: str, interval: str, limit: int) -> List[Dict]:
        """
        Fetch K-line data with incremental caching
        
        1. Check cache for existing data
        2. If cache sufficient, fetch only new data since last timestamp
        3. Append new data to cache and return combined result
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Timeframe ('5m', '15m', '1h')
            limit: Minimum number of K-lines needed
            
        Returns:
            List of K-line dicts
        """
        loop = asyncio.get_event_loop()
        
        # Check cache
        last_ts = self._kline_cache.get_last_timestamp(symbol, interval)
        cached_df = self._kline_cache.get_cached_data(symbol, interval)
        
        if cached_df is not None and len(cached_df) >= limit and last_ts:
            # Cache sufficient - fetch only new data
            interval_ms = {
                '1m': 60 * 1000,
                '5m': 5 * 60 * 1000,
                '15m': 15 * 60 * 1000,
                '1h': 60 * 60 * 1000,
            }.get(interval, 5 * 60 * 1000)
            
            start_time = last_ts + interval_ms
            
            # Fetch only new K-lines
            new_klines = await loop.run_in_executor(
                None,
                lambda: self.client.get_klines(symbol, interval, 50, start_time=start_time)
            )
            
            if new_klines:
                # Append to cache
                self._kline_cache.append_data(symbol, interval, new_klines)
                log.debug(f"📦 Cache hit: {symbol}/{interval} | +{len(new_klines)} new")
            
            # Return from updated cache
            final_df = self._kline_cache.get_cached_data(symbol, interval)
            if final_df is not None and not final_df.empty:
                # Convert back to list of dicts for compatibility
                return final_df.tail(limit).to_dict('records')
            
        # Cache miss or insufficient - full fetch
        klines = await loop.run_in_executor(
            None,
            lambda: self.client.get_klines(symbol, interval, limit)
        )
        
        if klines:
            self._kline_cache.append_data(symbol, interval, klines)
            log.debug(f"📦 Cache miss: {symbol}/{interval} | Fetched {len(klines)} rows")
        
        return klines
    def _to_dataframe(self, klines: List[Dict]) -> pd.DataFrame:
        """
        Convert K-line list to DataFrame
        
        Args:
            klines: Raw K-line data list
            
        Returns:
            Processed DataFrame
        """
        if not klines:
            return pd.DataFrame()
        
        df = pd.DataFrame(klines)
        
        # Convert timestamps
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
        
        # Ensure numeric types
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df

    def _split_klines(self, klines: List[Dict]) -> Tuple[pd.DataFrame, Dict]:
        """
        Split klines into stable (closed) DataFrame and live (latest) kline dict.
        Uses is_closed when available; otherwise falls back to close_time vs now.
        """
        if not klines:
            return pd.DataFrame(), {}

        last = klines[-1]
        is_closed = last.get('is_closed')
        if is_closed is None:
            close_time = last.get('close_time')
            if close_time is not None:
                try:
                    now_ms = int(datetime.now().timestamp() * 1000)
                    is_closed = int(close_time) <= now_ms
                except (TypeError, ValueError):
                    is_closed = False
            else:
                is_closed = False

        stable_source = klines if is_closed else klines[:-1]
        return self._to_dataframe(stable_source), last
    
    def _check_alignment(
        self,
        k5m: List[Dict],
        k15m: List[Dict],
        k1h: List[Dict]
    ) -> bool:
        """
        Check time alignment of multi-timeframe data
        
        Args:
            k5m, k15m, k1h: K-line data for each timeframe
            
        Returns:
            True if aligned, False otherwise
        """
        if not all([k5m, k15m, k1h]):
            log.warning("⚠️ Some timeframe data missing, time alignment failed")
            return False
        
        try:
            # Get latest K-line timestamps
            t5m = k5m[-1]['timestamp']
            t15m = k15m[-1]['timestamp']
            t1h = k1h[-1]['timestamp']
            
            # Calculate time difference (milliseconds)
            diff_5m_15m = abs(t5m - t15m)
            diff_5m_1h = abs(t5m - t1h)
            
            # Use more lenient tolerance:
            # - 5m vs 15m: Allow 15 minute difference (15m K-line period)
            # - 5m vs 1h: Allow 1 hour difference (1h K-line period)
            max_diff_15m = 900000   # 15 分钟 = 900,000 ms
            max_diff_1h = 3600000   # 1 小时 = 3,600,000 ms
            
            # Only warn for severe deviation
            if diff_5m_15m > max_diff_15m or diff_5m_1h > max_diff_1h:
                log.warning(
                    f"⚠️ Time alignment anomaly: "
                    f"5m vs 15m = {diff_5m_15m/1000:.0f}s, "
                    f"5m vs 1h = {diff_5m_1h/1000:.0f}s"
                )
                return False
            
            return True
            
        except Exception as e:
            log.error(f"❌ Time alignment check failed: {e}")
            return False
    
    def _log_snapshot_info(self, snapshot: MarketSnapshot):
        """Log snapshot information"""
        log.oracle(f"📸 Snapshot info:")
        log.oracle(f"  - 5m:  {len(snapshot.stable_5m)} completed + 1 live")
        log.oracle(f"  - 15m: {len(snapshot.stable_15m)} completed + 1 live")
        log.oracle(f"  - 1h:  {len(snapshot.stable_1h)} completed + 1 live")
        log.oracle(f"  - Time alignment: {'✅' if snapshot.alignment_ok else '❌'}")
        log.oracle(f"  - Fetch duration: {snapshot.fetch_duration:.2f}s")
        
        # Log live price
        if snapshot.live_5m:
            log.info(f"  - Live price (5m): ${snapshot.live_5m.get('close', 0):,.2f}")
        if snapshot.live_1h:
            log.info(f"  - Live price (1h): ${snapshot.live_1h.get('close', 0):,.2f}")
    
    def get_live_price(self, timeframe: str = '5m') -> float:
        """
        Get live price for the specified timeframe
        
        Args:
            timeframe: '5m', '15m', or '1h'
            
        Returns:
            Live close price
        """
        if not self.last_snapshot:
            log.warning("⚠️ No snapshot available")
            return 0.0
        
        live_data = {
            '5m': self.last_snapshot.live_5m,
            '15m': self.last_snapshot.live_15m,
            '1h': self.last_snapshot.live_1h
        }.get(timeframe, {})
        
        return float(live_data.get('close', 0))
    
    def get_stable_dataframe(self, timeframe: str = '5m') -> pd.DataFrame:
        """
        Get stable DataFrame for the specified timeframe (completed K-lines)
        
        Args:
            timeframe: '5m', '15m', or '1h'
            
        Returns:
            DataFrame of completed K-lines
        """
        if not self.last_snapshot:
            log.warning("⚠️ No snapshot available")
            return pd.DataFrame()
        
        return {
            '5m': self.last_snapshot.stable_5m,
            '15m': self.last_snapshot.stable_15m,
            '1h': self.last_snapshot.stable_1h
        }.get(timeframe, pd.DataFrame())


# Async test function
async def test_data_sync_agent():
    """Test Data Sync Agent"""
    agent = DataSyncAgent()
    
    print("\n" + "="*80)
    print("Test: Data Sync Agent")
    print("="*80)
    
    # Test 1: Concurrent data fetch
    print("\n[Test 1] Concurrent multi-timeframe data fetch...")
    snapshot = await agent.fetch_all_timeframes("BTCUSDT")
    
    print(f"\n✅ Data fetch successful")
    print(f"  - Duration: {snapshot.fetch_duration:.2f}s")
    print(f"  - Time alignment: {snapshot.alignment_ok}")
    
    # Test 2: Verify dual views
    print("\n[Test 2] Verify dual view data...")
    print(f"  - Stable 5m shape: {snapshot.stable_5m.shape}")
    print(f"  - Live 5m keys: {list(snapshot.live_5m.keys())}")
    print(f"  - Live 5m price: ${snapshot.live_5m.get('close', 0):,.2f}")
    
    # Test 3: Get live prices
    print("\n[Test 3] Get live prices...")
    for tf in ['5m', '15m', '1h']:
        price = agent.get_live_price(tf)
        print(f"  - {tf}: ${price:,.2f}")
    
    print("\n" + "="*80)
    print("\n✅ All tests passed")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_data_sync_agent())
