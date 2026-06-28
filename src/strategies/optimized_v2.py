#!/usr/bin/env python3
"""
Optimized Trading Strategy V2
=============================

Improvements:
1. Lowered RSI entry threshold (35→40)
2. Added Bollinger Band breakout signals
3. Enhanced short-selling logic
4. Dynamic stop-loss and take-profit
5. Smarter exit conditions

Author: AI Trader Team
Date: 2026-01-10
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class StrategyConfig:
    """Strategy configuration"""
    # RSI parameters
    rsi_period: int = 14
    rsi_oversold: float = 32  # Relaxed entry condition (was 25)
    rsi_overbought: float = 68  # Relaxed exit condition (was 70)
    rsi_extreme_oversold: float = 25
    rsi_extreme_overbought: float = 80
    
    # EMA parameters
    ema_fast: int = 9  # Faster response (was 12)
    ema_slow: int = 21  # Faster response (was 26)
    
    # Bollinger Band parameters
    bb_period: int = 20
    bb_std: float = 2.0
    
    # ATR parameters
    atr_period: int = 14
    atr_sl_multiplier: float = 1.5  # Stop-loss = ATR * 1.5
    atr_tp_multiplier: float = 2.5  # Take-profit = ATR * 2.5
    
    # Volume
    rvol_threshold: float = 1.2  # Relaxed volume requirement (was 1.5)
    
    # Short-selling switch
    enable_short: bool = True


def calculate_indicators(df: pd.DataFrame, config: StrategyConfig) -> Dict:
    """Calculate technical indicators"""
    close = df['close'].astype(float)
    high = df['high'].astype(float)
    low = df['low'].astype(float)
    volume = df['volume'].astype(float)
    
    indicators = {}
    
    # EMA
    ema_fast = close.ewm(span=config.ema_fast, adjust=False).mean()
    ema_slow = close.ewm(span=config.ema_slow, adjust=False).mean()
    indicators['ema_fast'] = ema_fast.iloc[-1]
    indicators['ema_slow'] = ema_slow.iloc[-1]
    indicators['ema_fast_prev'] = ema_fast.iloc[-2]
    indicators['ema_slow_prev'] = ema_slow.iloc[-2]
    
    # EMA trend
    indicators['is_uptrend'] = indicators['ema_fast'] > indicators['ema_slow']
    indicators['golden_cross'] = (indicators['ema_fast'] > indicators['ema_slow'] and 
                                   indicators['ema_fast_prev'] <= indicators['ema_slow_prev'])
    indicators['death_cross'] = (indicators['ema_fast'] < indicators['ema_slow'] and 
                                  indicators['ema_fast_prev'] >= indicators['ema_slow_prev'])
    
    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=config.rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=config.rsi_period).mean()
    rs = gain / loss.replace(0, 1e-10)
    rsi = 100 - (100 / (1 + rs))
    indicators['rsi'] = rsi.iloc[-1]
    indicators['rsi_prev'] = rsi.iloc[-2]
    
    # MACD
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist = macd_line - signal_line
    indicators['macd_hist'] = macd_hist.iloc[-1]
    indicators['macd_hist_prev'] = macd_hist.iloc[-2]
    indicators['macd_momentum'] = indicators['macd_hist'] > indicators['macd_hist_prev']
    indicators['macd_positive'] = indicators['macd_hist'] > 0
    
    # Bollinger Bands
    bb_mid = close.rolling(window=config.bb_period).mean()
    bb_std = close.rolling(window=config.bb_period).std()
    bb_upper = bb_mid + config.bb_std * bb_std
    bb_lower = bb_mid - config.bb_std * bb_std
    indicators['bb_upper'] = bb_upper.iloc[-1]
    indicators['bb_lower'] = bb_lower.iloc[-1]
    indicators['bb_mid'] = bb_mid.iloc[-1]
    indicators['bb_position'] = (close.iloc[-1] - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
    
    # ATR
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=config.atr_period).mean()
    indicators['atr'] = atr.iloc[-1]
    indicators['atr_pct'] = (atr.iloc[-1] / close.iloc[-1]) * 100
    
    # Volume
    avg_volume = volume.rolling(window=20).mean().iloc[-1]
    current_volume = volume.iloc[-1]
    indicators['rvol'] = current_volume / avg_volume if avg_volume > 0 else 1.0
    
    # Price
    indicators['price'] = close.iloc[-1]
    indicators['price_prev'] = close.iloc[-2]
    
    return indicators


def optimized_strategy_v2(
    snapshot,
    portfolio,
    current_price: float,
    config,  # BacktestConfig
    strategy_config: Optional[StrategyConfig] = None
) -> Dict:
    """
    Optimized Strategy V2
    
    Core improvements:
    1. Multi-signal fusion (RSI + EMA + MACD + Bollinger Bands)
    2. Dynamic stop-loss and take-profit (ATR-based)
    3. Enhanced short-selling logic
    4. More flexible entry conditions
    """
    if strategy_config is None:
        strategy_config = StrategyConfig()
    
    # Get data
    df = snapshot.stable_5m.copy()
    
    if len(df) < 50:
        return {'action': 'hold', 'confidence': 0.0, 'reason': 'insufficient_data'}
    
    # Calculate indicators
    ind = calculate_indicators(df, strategy_config)
    
    # Position status
    symbol = config.symbol
    has_position = symbol in portfolio.positions
    
    # Dynamic stop-loss and take-profit parameters
    atr_sl = ind['atr'] * strategy_config.atr_sl_multiplier
    atr_tp = ind['atr'] * strategy_config.atr_tp_multiplier
    
    trade_params = {
        'stop_loss_pct': (atr_sl / current_price) * 100,
        'take_profit_pct': (atr_tp / current_price) * 100,
    }
    
    # ========== Entry Signals ==========
    
    if not has_position:
        # 🟢 Long signals
        long_signals = []
        
        # Signal 1: RSI oversold + uptrend
        if ind['rsi'] < strategy_config.rsi_oversold and ind['is_uptrend']:
            long_signals.append(('rsi_oversold_uptrend', 75))
        
        # Signal 2: RSI extremely oversold (any trend)
        if ind['rsi'] < strategy_config.rsi_extreme_oversold:
            long_signals.append(('rsi_extreme_oversold', 85))
        
        # Signal 3: Golden cross + MACD confirmation
        if ind['golden_cross'] and ind['macd_positive']:
            long_signals.append(('golden_cross_macd+', 80))
        
        # Signal 4: Bollinger Band lower breakout + RSI not overbought
        if ind['bb_position'] < 0.1 and ind['rsi'] < 50:
            long_signals.append(('bb_lower_breakout', 70))
        
        # Signal 5: RSI divergence reversal
        if ind['rsi'] < 40 and ind['rsi'] > ind['rsi_prev'] and ind['macd_momentum']:
            long_signals.append(('rsi_reversal', 65))
        
        # Select the strongest signal
        if long_signals:
            best_signal = max(long_signals, key=lambda x: x[1])
            confidence = best_signal[1]
            
            # Volume weighting
            if ind['rvol'] > strategy_config.rvol_threshold:
                confidence = min(confidence + 5, 95)
            
            return {
                'action': 'long',
                'confidence': confidence,
                'reason': f'long_{best_signal[0]}_rsi{ind["rsi"]:.0f}',
                'trade_params': trade_params
            }
        
        # 🔴 Short signals (if enabled)
        if strategy_config.enable_short:
            short_signals = []
            
            # Signal 1: RSI overbought + downtrend
            if ind['rsi'] > strategy_config.rsi_overbought and not ind['is_uptrend']:
                short_signals.append(('rsi_overbought_downtrend', 75))
            
            # Signal 2: RSI extremely overbought
            if ind['rsi'] > strategy_config.rsi_extreme_overbought:
                short_signals.append(('rsi_extreme_overbought', 80))
            
            # Signal 3: Death cross + MACD confirmation
            if ind['death_cross'] and not ind['macd_positive']:
                short_signals.append(('death_cross_macd-', 80))
            
            # Signal 4: Bollinger Band upper breakout + RSI overbought
            if ind['bb_position'] > 0.95 and ind['rsi'] > 60:
                short_signals.append(('bb_upper_breakout', 70))
            
            # Select the strongest signal
            if short_signals:
                best_signal = max(short_signals, key=lambda x: x[1])
                confidence = best_signal[1]
                
                if ind['rvol'] > strategy_config.rvol_threshold:
                    confidence = min(confidence + 5, 95)
                
                return {
                    'action': 'short',
                    'confidence': confidence,
                    'reason': f'short_{best_signal[0]}_rsi{ind["rsi"]:.0f}',
                    'trade_params': trade_params
                }
    
    # ========== Position Management ==========
    
    if has_position:
        from src.backtest.portfolio import Side
        
        position = portfolio.positions[symbol]
        current_side = position.side
        entry_price = position.entry_price
        
        if current_side == Side.LONG:
            pnl_pct = (current_price / entry_price - 1) * 100
        else:
            pnl_pct = (entry_price / current_price - 1) * 100
        
        # 🎯 Long exit
        if current_side == Side.LONG:
            # Condition 1: RSI overbought + weakening momentum
            if ind['rsi'] > strategy_config.rsi_overbought and not ind['macd_momentum']:
                return {'action': 'close', 'confidence': 75, 'reason': f'tp_rsi{ind["rsi"]:.0f}_macd_weak'}
            
            # Condition 2: RSI extremely overbought
            if ind['rsi'] > strategy_config.rsi_extreme_overbought:
                return {'action': 'close', 'confidence': 85, 'reason': f'tp_rsi_extreme_{ind["rsi"]:.0f}'}
            
            # Condition 3: Death cross + loss
            if ind['death_cross'] and pnl_pct < 0:
                return {'action': 'close', 'confidence': 70, 'reason': f'sl_death_cross_pnl{pnl_pct:.1f}%'}
            
            # Condition 4: Bollinger Band upper take-profit
            if ind['bb_position'] > 0.95 and pnl_pct > 0.5:
                return {'action': 'close', 'confidence': 65, 'reason': f'tp_bb_upper_pnl{pnl_pct:.1f}%'}
        
        # 🎯 Short exit
        elif current_side == Side.SHORT:
            # Condition 1: RSI oversold
            if ind['rsi'] < strategy_config.rsi_oversold:
                return {'action': 'close', 'confidence': 75, 'reason': f'tp_short_rsi{ind["rsi"]:.0f}'}
            
            # Condition 2: Golden cross
            if ind['golden_cross']:
                return {'action': 'close', 'confidence': 70, 'reason': 'sl_golden_cross'}
            
            # Condition 3: Bollinger Band lower take-profit
            if ind['bb_position'] < 0.05 and pnl_pct > 0.5:
                return {'action': 'close', 'confidence': 65, 'reason': f'tp_bb_lower_pnl{pnl_pct:.1f}%'}
        
        # Continue holding
        return {'action': 'hold', 'confidence': 50, 'reason': f'holding_pnl{pnl_pct:+.1f}%'}
    
    # No signal
    return {'action': 'hold', 'confidence': 30, 'reason': 'no_signal'}


# Export strategy function
async def strategy_v2_wrapper(snapshot, portfolio, current_price: float, config) -> Dict:
    """Async wrapper"""
    return optimized_strategy_v2(snapshot, portfolio, current_price, config)
