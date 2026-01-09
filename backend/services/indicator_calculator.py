"""
10D - Indicator Calculator
Calculates SMA, RSI, Pivot Point S. Trend, Volume, and Pullback indicators
"""

from typing import List, Dict, Tuple, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SMA_FAST_PERIOD, SMA_SLOW_PERIOD,
    PIVOT_PERIOD, ATR_FACTOR, ATR_PERIOD,
    VOLUME_THRESHOLD, VOLUME_LOOKBACK,
    RSI_PERIOD, RSI_OVERSOLD, RSI_OVERBOUGHT,
    PULLBACK_THRESHOLD
)


def calculate_sma(closes: List[float], period: int) -> List[Optional[float]]:
    """Calculate Simple Moving Average"""
    sma_values = []
    
    for i in range(len(closes)):
        if i < period - 1:
            sma_values.append(None)
        else:
            window = closes[i - period + 1:i + 1]
            sma_values.append(sum(window) / period)
    
    return sma_values


def calculate_rsi(closes: List[float], period: int = RSI_PERIOD) -> List[Optional[float]]:
    """
    Calculate Relative Strength Index (RSI)
    
    Returns:
        List of RSI values (0-100)
    """
    if len(closes) < period + 1:
        return [None] * len(closes)
    
    rsi_values = [None] * period
    
    # Calculate initial gains and losses
    gains = []
    losses = []
    
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(0, change))
        losses.append(max(0, -change))
    
    # Calculate RSI using Wilder's smoothing
    for i in range(period - 1, len(gains)):
        if i == period - 1:
            avg_gain = sum(gains[i - period + 1:i + 1]) / period
            avg_loss = sum(losses[i - period + 1:i + 1]) / period
        else:
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        rsi_values.append(round(rsi, 2))
    
    return rsi_values


def detect_sma_crossover(candles: List[Dict]) -> Tuple[Optional[str], Dict]:
    """
    Detect SMA crossover on the last closed candle
    
    Returns:
        Tuple of (signal_direction, details)
        signal_direction: "LONG", "SHORT", or None
    """
    if len(candles) < max(SMA_FAST_PERIOD, SMA_SLOW_PERIOD) + 2:
        return None, {"error": "Not enough data"}
    
    closes = [c["close"] for c in candles]
    
    sma_fast = calculate_sma(closes, SMA_FAST_PERIOD)
    sma_slow = calculate_sma(closes, SMA_SLOW_PERIOD)
    
    current_fast = sma_fast[-1]
    current_slow = sma_slow[-1]
    prev_fast = sma_fast[-2]
    prev_slow = sma_slow[-2]
    
    if any(v is None for v in [current_fast, current_slow, prev_fast, prev_slow]):
        return None, {"error": "SMA not yet calculated"}
    
    details = {
        "sma_fast": round(current_fast, 6),
        "sma_slow": round(current_slow, 6),
        "sma_fast_prev": round(prev_fast, 6),
        "sma_slow_prev": round(prev_slow, 6)
    }
    
    # LONG: Fast SMA crosses above Slow SMA
    if prev_fast <= prev_slow and current_fast > current_slow:
        return "LONG", details
    
    # SHORT: Fast SMA crosses below Slow SMA
    if prev_fast >= prev_slow and current_fast < current_slow:
        return "SHORT", details
    
    return None, details


def detect_trend_direction(candles: List[Dict]) -> Tuple[Optional[str], Dict]:
    """
    Detect current trend direction based on SMA position
    
    Returns:
        Tuple of (trend_direction, details)
        trend_direction: "UPTREND", "DOWNTREND", or None
    """
    if len(candles) < max(SMA_FAST_PERIOD, SMA_SLOW_PERIOD) + 1:
        return None, {"error": "Not enough data"}
    
    closes = [c["close"] for c in candles]
    
    sma_fast = calculate_sma(closes, SMA_FAST_PERIOD)
    sma_slow = calculate_sma(closes, SMA_SLOW_PERIOD)
    
    current_fast = sma_fast[-1]
    current_slow = sma_slow[-1]
    
    if current_fast is None or current_slow is None:
        return None, {"error": "SMA not calculated"}
    
    diff_percent = ((current_fast - current_slow) / current_slow) * 100
    
    details = {
        "sma_fast": round(current_fast, 6),
        "sma_slow": round(current_slow, 6),
        "diff_percent": round(diff_percent, 4)
    }
    
    # UPTREND: Fast SMA above Slow SMA
    if current_fast > current_slow:
        return "UPTREND", details
    
    # DOWNTREND: Fast SMA below Slow SMA
    if current_fast < current_slow:
        return "DOWNTREND", details
    
    return None, details


def detect_pullback(candles: List[Dict]) -> Tuple[Optional[str], Dict]:
    """
    Detect pullback to SMA during established trend
    
    Returns:
        Tuple of (signal_direction, details)
        signal_direction: "LONG" (pullback in uptrend), "SHORT" (pullback in downtrend), or None
    """
    if len(candles) < max(SMA_FAST_PERIOD, SMA_SLOW_PERIOD) + 3:
        return None, {"error": "Not enough data"}
    
    closes = [c["close"] for c in candles]
    current_close = closes[-1]
    prev_close = closes[-2]
    
    sma_fast = calculate_sma(closes, SMA_FAST_PERIOD)
    sma_slow = calculate_sma(closes, SMA_SLOW_PERIOD)
    
    current_fast = sma_fast[-1]
    current_slow = sma_slow[-1]
    
    if current_fast is None or current_slow is None:
        return None, {"error": "SMA not calculated"}
    
    # Calculate distance from SMA Fast as percentage
    distance_from_sma = abs(current_close - current_fast) / current_fast
    
    details = {
        "current_price": round(current_close, 6),
        "sma_fast": round(current_fast, 6),
        "sma_slow": round(current_slow, 6),
        "distance_percent": round(distance_from_sma * 100, 4),
        "threshold_percent": round(PULLBACK_THRESHOLD * 100, 4)
    }
    
    # Check if price is near SMA Fast (pullback zone)
    is_near_sma = distance_from_sma <= PULLBACK_THRESHOLD
    
    if not is_near_sma:
        return None, details
    
    # UPTREND pullback: SMA Fast > SMA Slow AND price touches SMA Fast from above AND bouncing up
    if current_fast > current_slow:
        # Price touched SMA from above and is now bouncing (current > prev)
        if current_close <= current_fast and current_close > prev_close:
            details["pullback_type"] = "UPTREND_PULLBACK"
            return "LONG", details
    
    # DOWNTREND pullback: SMA Fast < SMA Slow AND price touches SMA Fast from below AND bouncing down
    if current_fast < current_slow:
        # Price touched SMA from below and is now falling (current < prev)
        if current_close >= current_fast and current_close < prev_close:
            details["pullback_type"] = "DOWNTREND_PULLBACK"
            return "SHORT", details
    
    return None, details


def detect_rsi_extreme(candles: List[Dict]) -> Tuple[Optional[str], Dict]:
    """
    Detect RSI extreme levels (oversold/overbought) with reversal
    
    Returns:
        Tuple of (signal_direction, details)
        signal_direction: "LONG" (oversold reversal), "SHORT" (overbought reversal), or None
    """
    if len(candles) < RSI_PERIOD + 3:
        return None, {"error": "Not enough data for RSI"}
    
    closes = [c["close"] for c in candles]
    rsi_values = calculate_rsi(closes, RSI_PERIOD)
    
    current_rsi = rsi_values[-1]
    prev_rsi = rsi_values[-2]
    
    if current_rsi is None or prev_rsi is None:
        return None, {"error": "RSI not calculated"}
    
    details = {
        "current_rsi": current_rsi,
        "prev_rsi": prev_rsi,
        "oversold_level": RSI_OVERSOLD,
        "overbought_level": RSI_OVERBOUGHT
    }
    
    # Check last 3 RSI values for extreme levels
    rsi_last_3 = [r for r in rsi_values[-3:] if r is not None]
    
    if len(rsi_last_3) < 2:
        return None, details
    
    min_rsi = min(rsi_last_3)
    max_rsi = max(rsi_last_3)
    
    details["min_rsi_3"] = min_rsi
    details["max_rsi_3"] = max_rsi
    
    # LONG: RSI was oversold in last 3 candles and current is rising
    if min_rsi <= RSI_OVERSOLD and current_rsi > min_rsi:
        details["signal_type"] = "OVERSOLD_REVERSAL"
        return "LONG", details
    
    # SHORT: RSI was overbought in last 3 candles and current is falling
    if max_rsi >= RSI_OVERBOUGHT and current_rsi < max_rsi:
        details["signal_type"] = "OVERBOUGHT_REVERSAL"
        return "SHORT", details
    
    return None, details


def calculate_atr(candles: List[Dict], period: int = ATR_PERIOD) -> List[Optional[float]]:
    """Calculate Average True Range (ATR)"""
    if len(candles) < 2:
        return [None] * len(candles)
    
    true_ranges = [None]
    
    for i in range(1, len(candles)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        prev_close = candles[i - 1]["close"]
        
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        true_ranges.append(tr)
    
    atr_values = []
    for i in range(len(true_ranges)):
        if i < period:
            atr_values.append(None)
        else:
            window = [tr for tr in true_ranges[i - period + 1:i + 1] if tr is not None]
            if window:
                atr_values.append(sum(window) / len(window))
            else:
                atr_values.append(None)
    
    return atr_values


def calculate_pivot_trend(candles: List[Dict]) -> Tuple[Optional[str], Dict]:
    """Calculate Pivot Point Standard Trend"""
    if len(candles) < ATR_PERIOD + 2:
        return None, {"error": "Not enough data for Pivot Trend"}
    
    atr_values = calculate_atr(candles, ATR_PERIOD)
    
    current_atr = atr_values[-1]
    if current_atr is None:
        return None, {"error": "ATR not calculated"}
    
    current = candles[-1]
    prev = candles[-2]
    
    pivot = (current["high"] + current["low"]) / 2
    
    upper_band = pivot + (ATR_FACTOR * current_atr)
    lower_band = pivot - (ATR_FACTOR * current_atr)
    
    close = current["close"]
    prev_close = prev["close"]
    
    details = {
        "pivot": round(pivot, 6),
        "upper_band": round(upper_band, 6),
        "lower_band": round(lower_band, 6),
        "atr": round(current_atr, 6),
        "close": round(close, 6)
    }
    
    if close > upper_band:
        return "UP", details
    elif close < lower_band:
        return "DOWN", details
    else:
        if close > prev_close:
            return "UP", details
        elif close < prev_close:
            return "DOWN", details
        else:
            return None, details


def check_volume_confirmation(candles: List[Dict]) -> Tuple[bool, Dict]:
    """Check if current volume is above threshold"""
    if len(candles) < VOLUME_LOOKBACK + 1:
        return False, {"error": "Not enough data for volume analysis"}
    
    volumes = [c["volume"] for c in candles[-(VOLUME_LOOKBACK + 1):-1]]
    current_volume = candles[-1]["volume"]
    
    avg_volume = sum(volumes) / len(volumes)
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
    
    details = {
        "current_volume": round(current_volume, 2),
        "avg_volume": round(avg_volume, 2),
        "volume_ratio": round(volume_ratio, 2),
        "threshold": VOLUME_THRESHOLD
    }
    
    is_confirmed = volume_ratio >= VOLUME_THRESHOLD
    
    return is_confirmed, details


def analyze_candles(candles: List[Dict]) -> Dict:
    """
    Run all indicator analysis on candles
    
    Returns:
        Dictionary with all analysis results including:
        - SMA crossover signal
        - Trend direction
        - Pullback signal
        - RSI extreme signal
        - Volume confirmation
        - Pivot Trend
    """
    # SMA Crossover
    sma_signal, sma_details = detect_sma_crossover(candles)
    
    # Trend Direction
    trend_direction, trend_details = detect_trend_direction(candles)
    
    # Pullback Detection
    pullback_signal, pullback_details = detect_pullback(candles)
    
    # RSI Extreme
    rsi_signal, rsi_details = detect_rsi_extreme(candles)
    
    # Volume confirmation
    volume_confirmed, volume_details = check_volume_confirmation(candles)
    
    # Pivot Trend
    pivot_trend, pivot_details = calculate_pivot_trend(candles)
    
    # RSI current value
    closes = [c["close"] for c in candles]
    rsi_values = calculate_rsi(closes, RSI_PERIOD)
    current_rsi = rsi_values[-1] if rsi_values else None
    
    # Current price info
    current_candle = candles[-1] if candles else {}
    
    return {
        "current_price": current_candle.get("close", 0),
        "timestamp": current_candle.get("timestamp", 0),
        "sma": {
            "signal": sma_signal,
            "details": sma_details
        },
        "trend": {
            "direction": trend_direction,
            "details": trend_details
        },
        "pullback": {
            "signal": pullback_signal,
            "details": pullback_details
        },
        "rsi": {
            "signal": rsi_signal,
            "current_value": current_rsi,
            "details": rsi_details
        },
        "volume": {
            "confirmed": volume_confirmed,
            "details": volume_details
        },
        "pivot_trend": {
            "direction": pivot_trend,
            "details": pivot_details
        }
    }
