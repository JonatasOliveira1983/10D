"""
10D - Indicator Calculator
3: Calculates SMA, RSI, Pivot Point S. Trend, Volume, Pullback, CVD, and Judas Swing indicators
"""

from typing import List, Dict, Tuple, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    EMA_FAST_PERIOD, EMA_SLOW_PERIOD,
    MACD_FAST, MACD_SLOW, MACD_SIGNAL,
    BB_PERIOD, BB_STD_DEV,
    PIVOT_PERIOD, ATR_FACTOR, ATR_PERIOD,
    VOLUME_THRESHOLD, VOLUME_LOOKBACK,
    RSI_PERIOD, RSI_OVERSOLD, RSI_OVERBOUGHT,
    PULLBACK_THRESHOLD, RS_LOOKBACK
)


def calculate_sma(closes: List[float], period: int) -> List[Optional[float]]:
    """Calculate Simple Moving Average"""
    if len(closes) < period:
        return [None] * len(closes)
        
    sma_values = []
    
    for i in range(len(closes)):
        if i < period - 1:
            sma_values.append(None)
        else:
            window = closes[i - period + 1:i + 1]
            sma_values.append(sum(window) / period)
    
    return sma_values


def calculate_ema(closes: List[float], period: int) -> List[Optional[float]]:
    """Calculate Exponential Moving Average"""
    if len(closes) < period:
        return [None] * len(closes)
    
    ema_values = [None] * len(closes)
    multiplier = 2 / (period + 1)
    
    # Simple SMA for the first EMA value
    initial_sma = sum(closes[:period]) / period
    ema_values[period - 1] = initial_sma
    
    for i in range(period, len(closes)):
        ema_values[i] = (closes[i] - ema_values[i - 1]) * multiplier + ema_values[i - 1]
    
    return ema_values


def calculate_macd(closes: List[float]) -> Dict[str, List[Optional[float]]]:
    """Calculate MACD Line, Signal Line, and Histogram"""
    ema_fast = calculate_ema(closes, MACD_FAST)
    ema_slow = calculate_ema(closes, MACD_SLOW)
    
    macd_line = []
    for f, s in zip(ema_fast, ema_slow):
        if f is not None and s is not None:
            macd_line.append(f - s)
        else:
            macd_line.append(None)
            
    # Remove None values for signal calculation
    valid_macd = [m for m in macd_line if m is not None]
    if len(valid_macd) < MACD_SIGNAL:
        return {
            "macd": macd_line,
            "signal": [None] * len(closes),
            "histogram": [None] * len(closes)
        }
        
    # Calculate signal line (EMA of MACD line)
    signal_line_short = calculate_ema(valid_macd, MACD_SIGNAL)
    
    # Pad signal line with Nones to match original length
    none_count = len(closes) - len(signal_line_short)
    signal_line = [None] * none_count + signal_line_short
    
    histogram = []
    for m, s in zip(macd_line, signal_line):
        if m is not None and s is not None:
            histogram.append(m - s)
        else:
            histogram.append(None)
            
    return {
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram
    }


def calculate_bollinger_bands(closes: List[float], period: int = BB_PERIOD, std_dev: int = BB_STD_DEV) -> Dict[str, List[Optional[float]]]:
    """Calculate Bollinger Bands"""
    sma = calculate_sma(closes, period)
    upper_band = []
    lower_band = []
    
    for i in range(len(closes)):
        if sma[i] is None:
            upper_band.append(None)
            lower_band.append(None)
        else:
            window = closes[i - period + 1:i + 1]
            variance = sum((x - sma[i]) ** 2 for x in window) / period
            stdev = variance ** 0.5
            upper_band.append(sma[i] + (std_dev * stdev))
            lower_band.append(sma[i] - (std_dev * stdev))
            
    return {
        "upper": upper_band,
        "middle": sma,
        "lower": lower_band
    }


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


def detect_ema_crossover(candles: List[Dict]) -> Tuple[Optional[str], Dict]:
    """
    Detect EMA crossover with MACD confirmation
    
    Returns:
        Tuple of (signal_direction, details)
    """
    if len(candles) < max(EMA_SLOW_PERIOD, MACD_SLOW + MACD_SIGNAL) + 2:
        return None, {"error": "Not enough data"}
    
    closes = [c["close"] for c in candles]
    
    ema_fast = calculate_ema(closes, EMA_FAST_PERIOD)
    ema_slow = calculate_ema(closes, EMA_SLOW_PERIOD)
    macd_data = calculate_macd(closes)
    
    current_fast = ema_fast[-1]
    current_slow = ema_slow[-1]
    prev_fast = ema_fast[-2]
    prev_slow = ema_slow[-2]
    
    current_hist = macd_data["histogram"][-1]
    
    if any(v is None for v in [current_fast, current_slow, prev_fast, prev_slow, current_hist]):
        return None, {"error": "EMA or MACD not yet calculated"}
    
    details = {
        "ema_fast": round(current_fast, 6),
        "ema_slow": round(current_slow, 6),
        "macd_hist": round(current_hist, 6)
    }
    
    # LONG: EMA 20 crosses above EMA 50 AND MACD Histogram is positive
    if prev_fast <= prev_slow and current_fast > current_slow:
        details["macd_confirmed"] = current_hist > 0
        return "LONG", details
    
    # SHORT: EMA 20 crosses below EMA 50 AND MACD Histogram is negative
    if prev_fast >= prev_slow and current_fast < current_slow:
        details["macd_confirmed"] = current_hist < 0
        return "SHORT", details
    
    return None, details


def detect_trend_4h(candles_4h: List[Dict]) -> Tuple[Optional[str], Dict]:
    """
    Detect trend on 4H timeframe using EMA 50
    """
    if len(candles_4h) < EMA_SLOW_PERIOD + 1:
        return None, {"error": "Not enough 4H data"}
        
    closes = [c["close"] for c in candles_4h]
    ema_50 = calculate_ema(closes, EMA_SLOW_PERIOD)
    
    current_price = closes[-1]
    current_ema = ema_50[-1]
    
    if current_ema is None:
        return None, {"error": "4H EMA not calculated"}
        
    direction = "UPTREND" if current_price > current_ema else "DOWNTREND"
    
    return direction, {
        "4h_price": round(current_price, 6),
        "4h_ema50": round(current_ema, 6)
    }


def detect_trend_direction(candles: List[Dict]) -> Tuple[Optional[str], Dict]:
    """
    Detect current trend direction based on EMA position
    
    Returns:
        Tuple of (trend_direction, details)
        trend_direction: "UPTREND", "DOWNTREND", or None
    """
    if len(candles) < max(EMA_FAST_PERIOD, EMA_SLOW_PERIOD) + 1:
        return None, {"error": "Not enough data"}
    
    closes = [c["close"] for c in candles]
    
    ema_fast = calculate_ema(closes, EMA_FAST_PERIOD)
    ema_slow = calculate_ema(closes, EMA_SLOW_PERIOD)
    
    current_fast = ema_fast[-1]
    current_slow = ema_slow[-1]
    
    if current_fast is None or current_slow is None:
        return None, {"error": "SMA not calculated"}
    
    diff_percent = ((current_fast - current_slow) / current_slow) * 100
    
    details = {
        "ema_fast": round(current_fast, 6),
        "ema_slow": round(current_slow, 6),
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
    Detect pullback to EMA during established trend
    """
    if len(candles) < max(EMA_FAST_PERIOD, EMA_SLOW_PERIOD) + 3:
        return None, {"error": "Not enough data"}
    
    closes = [c["close"] for c in candles]
    current_close = closes[-1]
    prev_close = closes[-2]
    
    ema_fast = calculate_ema(closes, EMA_FAST_PERIOD)
    ema_slow = calculate_ema(closes, EMA_SLOW_PERIOD)
    
    current_fast = ema_fast[-1]
    current_slow = ema_slow[-1]
    
    if current_fast is None or current_slow is None:
        return None, {"error": "EMA not calculated"}
    
    # Calculate distance from EMA Fast as percentage
    distance_from_ema = abs(current_close - current_fast) / current_fast
    
    details = {
        "current_price": round(current_close, 6),
        "ema_fast": round(current_fast, 6),
        "ema_slow": round(current_slow, 6),
        "distance_percent": round(distance_from_ema * 100, 4)
    }
    
    # UPTREND pullback: EMA Fast > EMA Slow AND price touches EMA Fast from above AND bouncing up
    if current_fast > current_slow:
        if current_close <= current_fast * (1 + PULLBACK_THRESHOLD) and current_close > prev_close:
            details["pullback_type"] = "UPTREND_PULLBACK"
            return "LONG", details
    
    # DOWNTREND pullback: EMA Fast < EMA Slow AND price touches EMA Fast from below AND bouncing down
    if current_fast < current_slow:
        if current_close >= current_fast * (1 - PULLBACK_THRESHOLD) and current_close < prev_close:
            details["pullback_type"] = "DOWNTREND_PULLBACK"
            return "SHORT", details
    
    return None, details


def detect_rsi_bb_reversal(candles: List[Dict]) -> Tuple[Optional[str], Dict]:
    """
    Detect RSI + Bollinger Bands extreme reversal
    """
    if len(candles) < max(RSI_PERIOD, BB_PERIOD) + 3:
        return None, {"error": "Not enough data"}
    
    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    
    rsi_values = calculate_rsi(closes, RSI_PERIOD)
    bb_data = calculate_bollinger_bands(closes, BB_PERIOD, BB_STD_DEV)
    
    current_rsi = rsi_values[-1]
    current_close = closes[-1]
    current_upper = bb_data["upper"][-1]
    current_lower = bb_data["lower"][-1]
    
    if any(v is None for v in [current_rsi, current_upper, current_lower]):
        return None, {"error": "RSI or BB not calculated"}
    
    details = {
        "rsi": round(current_rsi, 2),
        "bb_upper": round(current_upper, 6),
        "bb_lower": round(current_lower, 6),
        "close": round(current_close, 6)
    }
    
    # Reversal candle logic (simplified version of Hammer/Shooting Star)
    # Hammer-like (for LONG): Close above Open and bounced from BB Lower
    is_hammer = current_close > candles[-1]["open"] and candles[-1]["low"] <= current_lower
    # Shooting star-like (for SHORT): Close below Open and bounced from BB Upper
    is_star = current_close < candles[-1]["open"] and candles[-1]["high"] >= current_upper
    
    # LONG: RSI Oversold (<30) + Touch/Fura BB Lower + Bullish Reversal
    if current_rsi <= RSI_OVERSOLD and (candles[-1]["low"] <= current_lower) and current_close > candles[-1]["open"]:
        return "LONG", details
    
    # SHORT: RSI Overbought (>70) + Touch/Fura BB Upper + Bearish Reversal
    if current_rsi >= RSI_OVERBOUGHT and (candles[-1]["high"] >= current_upper) and current_close < candles[-1]["open"]:
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


def calculate_cvd(recent_trades: List[Dict]) -> float:
    """
    Calculate Cumulative Volume Delta from recent trades
    Delta = Buy Volume - Sell Volume
    """
    if not recent_trades:
        return 0.0
        
    delta = 0.0
    for trade in recent_trades:
        if trade["side"] == "Buy":
            delta += trade["size"]
        else:
            delta -= trade["size"]
            
    return delta


def calculate_relative_strength(alt_candles: List[Dict], btc_candles: List[Dict], lookback: int = 14) -> float:
    """
    Calculate Relative Strength (RS) of Alt vs BTC
    Returns average ratio of % change during drop candles
    """
    if len(alt_candles) < lookback or len(btc_candles) < lookback:
        return 0.0
        
    alt_changes = []
    btc_changes = []
    
    # Analyze the last N candles
    for i in range(-lookback, 0):
        alt_change = (alt_candles[i]["close"] - alt_candles[i-1]["close"]) / alt_candles[i-1]["close"]
        btc_change = (btc_candles[i]["close"] - btc_candles[i-1]["close"]) / btc_candles[i-1]["close"]
        
        alt_changes.append(alt_change)
        btc_changes.append(btc_change)
        
    # During BTC drop, how did Alt perform?
    rs_score = 0
    count = 0
    for a, b in zip(alt_changes, btc_changes):
        if b < 0: # BTC dropped
            # If alt dropped less than btc (a > b since both are negative), it's strong
            rs_score += (a - b)
            count += 1
            
    return rs_score / count if count > 0 else 0.0


def find_ranges_30m(candles: List[Dict], lookback: int = 50) -> Dict[str, List[float]]:
    """
    Identify horizontal support and resistance levels in the 30M timeframe
    A level is defined where price touched at least 2 times (within a tolerance)
    """
    if len(candles) < lookback:
        return {"supports": [], "resistances": []}
        
    recent_candles = candles[-lookback:]
    
    # Extract highs and lows
    highs = [c["high"] for c in recent_candles]
    lows = [c["low"] for c in recent_candles]
    
    # Parameters for grouping
    tolerance = 0.001 # 0.1% tolerance
    
    def get_clusters(values):
        clusters = []
        for val in values:
            found = False
            for group in clusters:
                avg = sum(group) / len(group)
                if abs(val - avg) / avg <= tolerance:
                    group.append(val)
                    found = True
                    break
            if not found:
                clusters.append([val])
        
        # Filter for clusters with at least 2 touches
        return [sum(c) / len(c) for c in clusters if len(c) >= 2]

    return {
        "supports": sorted(get_clusters(lows)),
        "resistances": sorted(get_clusters(highs), reverse=True)
    }


def detect_judas_swing(
    candles: List[Dict], 
    ranges: Dict[str, List[float]], 
    atr_values: List[Optional[float]]
) -> Tuple[Optional[str], Dict]:
    """
    Detect Judas Swing (Institutional Stop Hunt)
    Criteria:
    1. Rompimento de S/R.
    2. Desvio entre 0.5x e 1.5x ATR.
    3. Reclaiming em no máximo 3 candles.
    4. Vela de reversão com pavio >= 50%.
    """
    if len(candles) < 5 or not atr_values[-1]:
        return None, {"error": "Not enough data"}
        
    current = candles[-1]
    atr = atr_values[-1]
    
    # Check for Long: False Break of Support
    # Look back at last 4 candles to see if we breached a support and then reclaimed it
    for support in ranges["supports"]:
        # Requirement: Breach must have happened recently
        # Check last 3 candles for the "Incursion"
        for i in range(-4, -1):
            low_candle = candles[i]
            if low_candle["low"] < support:
                desvio = (support - low_candle["low"]) / atr
                
                # Desvio entre 0.5x e 1.5x ATR
                if 0.5 <= desvio <= 1.5:
                    # Closing back inside the range (Reclaiming)
                    # Current candle or any of the last 2 must close back above support
                    reclaimed = False
                    for j in range(i + 1, 0 if i < -1 else 1): # Indexing trick for candles list
                        if candles[j]["close"] > support:
                            reclaimed = True
                            reclaim_index = j
                            break
                    
                    if reclaimed:
                        # Reclaim must happen within 3 candles from breach
                        if (reclaim_index - i) <= 3:
                            # Candle signature: Reversal candle has >50% wick
                            # Using the candle that reclaimed
                            target_candle = candles[reclaim_index]
                            body = abs(target_candle["close"] - target_candle["open"])
                            total = target_candle["high"] - target_candle["low"]
                            wick = total - body
                            
                            if total > 0 and (wick / total) >= 0.5:
                                return "LONG", {
                                    "type": "JUDAS_SWING",
                                    "level": round(support, 6),
                                    "deviation_atr": round(desvio, 2),
                                    "reclaim_candles": reclaim_index - i,
                                    "wick_percent": round((wick/total)*100, 2)
                                }

    # Check for Short: False Break of Resistance
    for resistance in ranges["resistances"]:
        for i in range(-4, -1):
            high_candle = candles[i]
            if high_candle["high"] > resistance:
                desvio = (high_candle["high"] - resistance) / atr
                
                if 0.5 <= desvio <= 1.5:
                    reclaimed = False
                    for j in range(i + 1, 0 if i < -1 else 1):
                        if candles[j]["close"] < resistance:
                            reclaimed = True
                            reclaim_index = j
                            break
                    
                    if reclaimed:
                        if (reclaim_index - i) <= 3:
                            target_candle = candles[reclaim_index]
                            body = abs(target_candle["close"] - target_candle["open"])
                            total = target_candle["high"] - target_candle["low"]
                            wick = total - body
                            
                            if total > 0 and (wick / total) >= 0.5:
                                return "SHORT", {
                                    "type": "JUDAS_SWING",
                                    "level": round(resistance, 6),
                                    "deviation_atr": round(desvio, 2),
                                    "reclaim_candles": reclaim_index - i,
                                    "wick_percent": round((wick/total)*100, 2)
                                }
                                
    return None, {}


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


def analyze_candles(
    candles: List[Dict], 
    candles_4h: Optional[List[Dict]] = None,
    recent_trades: Optional[List[Dict]] = None,
    oi_data: Optional[List[Dict]] = None,
    lsr_data: Optional[List[Dict]] = None,
    btc_candles: Optional[List[Dict]] = None
) -> Dict:
    """
    Run all indicator analysis on candles including Institutional metrics
    """
    # ATR calculation (needed for Judas Swing)
    atr_values = calculate_atr(candles, ATR_PERIOD)
    
    # 30M Range detection
    ranges_30m = find_ranges_30m(candles)
    
    # Judas Swing detection
    judas_signal, judas_details = detect_judas_swing(candles, ranges_30m, atr_values)
    
    # CVD calculation
    cvd_value = calculate_cvd(recent_trades) if recent_trades else 0.0
    
    # Relative Strength
    rs_score = calculate_relative_strength(candles, btc_candles, RS_LOOKBACK) if btc_candles else 0.0

    # 4H Trend Filter
    trend_4h, trend_4h_details = None, {}
    if candles_4h:
        trend_4h, trend_4h_details = detect_trend_4h(candles_4h)

    # EMA Crossover
    ema_signal, ema_details = detect_ema_crossover(candles)
    
    # Pullback Detection
    pullback_signal, pullback_details = detect_pullback(candles)
    
    # RSI + BB Reversal
    rsi_signal, rsi_details = detect_rsi_bb_reversal(candles)
    
    # Volume confirmation
    volume_confirmed, volume_details = check_volume_confirmation(candles)
    
    # Pivot Trend
    pivot_trend, pivot_details = calculate_pivot_trend(candles)
    
    # MACD Current Data
    closes = [c["close"] for c in candles]
    macd_data = calculate_macd(closes)
    current_hist = macd_data["histogram"][-1] if macd_data["histogram"] else None
    
    # RSI current value
    rsi_values = calculate_rsi(closes, RSI_PERIOD)
    current_rsi = rsi_values[-1] if rsi_values else None
    
    # Current price info
    current_candle = candles[-1] if candles else {}
    
    return {
        "current_price": current_candle.get("close", 0),
        "timestamp": current_candle.get("timestamp", 0),
        "trend_4h": {
            "direction": trend_4h,
            "details": trend_4h_details
        },
        "ema": {
            "signal": ema_signal,
            "details": ema_details
        },
        "pullback": {
            "signal": pullback_signal,
            "details": pullback_details
        },
        "rsi_bb": {
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
        },
        "macd": {
            "histogram": current_hist
        },
        "institutional": {
            "judas_signal": judas_signal,
            "judas_details": judas_details,
            "cvd": cvd_value,
            "rs_score": rs_score,
            "ranges_30m": ranges_30m,
            "oi_latest": oi_data[0]["openInterest"] if oi_data else None,
            "lsr_latest": lsr_data[0]["ratio"] if lsr_data else None
        }
    }
