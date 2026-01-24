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
    PULLBACK_THRESHOLD, RS_LOOKBACK, RS_MIN_THRESHOLD,
    ABSORPTION_LOOKBACK, ABSORPTION_CVD_RATIO, SFP_WICK_PERCENT,
    JUDAS_RECLAIM_CANDLES, JUDAS_WICK_PERCENT,
    LSR_LONG_HEAVY, LSR_SHORT_HEAVY, OI_HIGH_MULTIPLIER
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


def detect_rsi_crossover_vs_btc(alt_candles: List[Dict], btc_candles: List[Dict]) -> Tuple[Optional[str], Dict]:
    """
    Detect RSI crossover between ALT and BTC
    When ALT RSI crosses ABOVE BTC RSI = altcoin gaining independent momentum (LONG)
    When ALT RSI crosses BELOW BTC RSI = altcoin losing strength vs BTC (SHORT context)
    """
    if len(alt_candles) < RSI_PERIOD + 2 or len(btc_candles) < RSI_PERIOD + 2:
        return None, {}
    
    alt_closes = [c["close"] for c in alt_candles]
    btc_closes = [c["close"] for c in btc_candles]
    
    rsi_alt = calculate_rsi(alt_closes)
    rsi_btc = calculate_rsi(btc_closes)
    
    # Need at least 2 valid RSI values to detect crossover
    if rsi_alt[-1] is None or rsi_alt[-2] is None:
        return None, {}
    if rsi_btc[-1] is None or rsi_btc[-2] is None:
        return None, {}
    
    details = {
        "rsi_alt": round(rsi_alt[-1], 2),
        "rsi_btc": round(rsi_btc[-1], 2),
        "rsi_alt_prev": round(rsi_alt[-2], 2),
        "rsi_btc_prev": round(rsi_btc[-2], 2)
    }
    
    # Bullish crossover: ALT RSI crosses above BTC RSI
    if rsi_alt[-1] > rsi_btc[-1] and rsi_alt[-2] <= rsi_btc[-2]:
        details["crossover_type"] = "BULLISH"
        return "LONG", details
    
    # Bearish crossover: ALT RSI crosses below BTC RSI
    if rsi_alt[-1] < rsi_btc[-1] and rsi_alt[-2] >= rsi_btc[-2]:
        details["crossover_type"] = "BEARISH"
        return "SHORT", details
    
    return None, details


def detect_liquidity_hunt_target(lsr_data: Optional[List[Dict]], oi_data: Optional[List[Dict]]) -> Tuple[Optional[str], Dict]:
    """
    Predict where whales will hunt liquidity based on LSR imbalance and OI levels.
    Also calculates an intensity score (1-6) representing the 'hunger' of the smart money.
    
    Logic:
    - LSR Imbalance: High LSR = Long stops hunt (Down), Low LSR = Short stops hunt (Up).
    - OI Growth: Rapid increase in OI indicates robots are loading positions.
    - Intensity Score (Hunger Index):
        1-2: Low/Neutral. No clear imbalance.
        3-4: Moderate. Robots active, looking for liquidity.
        5-6: High. Aggressive hunting, imminent squeeze/liquidation.
    """
    if not lsr_data or len(lsr_data) < 2:
        return None, {"error": "Not enough LSR data", "intensity_score": 1}
    
    current_lsr = lsr_data[0].get("ratio", 1.0)
    prev_lsr = lsr_data[1].get("ratio", 1.0)
    
    # Base Intensity Calculation
    intensity = 1
    
    # 1. LSR Imbalance Intensity
    if current_lsr >= 2.0 or current_lsr <= 0.5:
        intensity += 2  # Extreme imbalance
    elif current_lsr >= 1.5 or current_lsr <= 0.7:
        intensity += 1  # Moderate imbalance
        
    # 2. Open Interest Intensity
    oi_ratio = 1.0
    if oi_data and len(oi_data) >= 5:
        current_oi = oi_data[0].get("openInterest", 0)
        recent_ois = [d.get("openInterest", 0) for d in oi_data[:5]]
        avg_oi = sum(recent_ois) / 5
        
        if avg_oi > 0:
            oi_ratio = current_oi / avg_oi
            if oi_ratio >= 1.3: # 30% jump
                intensity += 2
            elif oi_ratio >= 1.15: # 15% jump
                intensity += 1
                
    # 3. LSR Movement (Fome em aceleração)
    lsr_change = abs(current_lsr - prev_lsr) / prev_lsr if prev_lsr > 0 else 0
    if lsr_change > 0.1: # 10% change in one interval
        intensity += 1

    # Clamp intensity 1 to 6
    intensity_score = max(1, min(6, intensity))
    
    details = {
        "current_lsr": round(current_lsr, 3),
        "prev_lsr": round(prev_lsr, 3),
        "lsr_threshold_long": 1.5,
        "lsr_threshold_short": 0.7,
        "oi_ratio": round(oi_ratio, 2),
        "intensity_score": intensity_score,
        "hunger_label": "EXTREME" if intensity_score >= 5 else "HIGH" if intensity_score >= 3 else "LOW"
    }
    
    # Detect hunt direction
    if current_lsr >= 1.5:
        # Too many longs = whales will hunt LONG stops (push price DOWN first)
        details["hunt_direction"] = "DOWN_THEN_UP"
        details["sardinha_side"] = "LONG"
        return "LONG_HUNT", details
    
    elif current_lsr <= 0.7:
        # Too many shorts = whales will hunt SHORT stops (push price UP first)
        details["hunt_direction"] = "UP_THEN_DOWN"
        details["sardinha_side"] = "SHORT"
        return "SHORT_HUNT", details
    
    return None, details


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


def detect_absorption(candles: List[Dict], recent_trades: List[Dict]) -> Tuple[bool, Dict]:
    """
    Detect Institutional Absorption
    Logic: Price is tightening (small bodies) but CVD is increasing/decreasing significantly
    indicates big players are eating all orders.
    """
    if len(candles) < ABSORPTION_LOOKBACK or not recent_trades:
        return False, {}
        
    recent_candles = candles[-ABSORPTION_LOOKBACK:]
    
    # Calculate average body size
    bodies = [abs(c["close"] - c["open"]) for c in recent_candles]
    avg_body = sum(bodies) / len(bodies)
    
    # Calculate price volatility
    highs = [c["high"] for c in recent_candles]
    lows = [c["low"] for c in recent_candles]
    price_range = max(highs) - min(lows)
    
    # Calculate CVD for the same period
    # Note: calculate_cvd already takes a list of trades
    cvd_total = calculate_cvd(recent_trades)
    
    # Total volume in the lookback period
    total_volume = sum(c["volume"] for c in recent_candles)
    
    if total_volume == 0:
        return False, {}
        
    cvd_volume_ratio = abs(cvd_total) / total_volume
    
    # Absorption: Small price range but high CVD relative to volume
    # This means someone is buying/selling a lot but price isn't moving much
    is_absorbed = cvd_volume_ratio >= ABSORPTION_CVD_RATIO and avg_body < (price_range / 2)
    
    return is_absorbed, {
        "cvd_volume_ratio": round(cvd_volume_ratio, 4),
        "avg_body": round(avg_body, 6),
        "price_range": round(price_range, 6),
        "side": "BUY" if cvd_total > 0 else "SELL"
    }


def detect_sfp(candles: List[Dict], lookback: int = 20) -> Tuple[Optional[str], Dict]:
    """
    Detect Swing Failure Pattern (SFP)
    Logic: Price breaches a previous significant high/low but closes back inside it.
    Must have a significant wick (> SFP_WICK_PERCENT).
    """
    if len(candles) < lookback + 1:
        return None, {}
        
    current = candles[-1]
    prev_candles = candles[-(lookback+1):-1]
    
    highest_prev = max(c["high"] for c in prev_candles)
    lowest_prev = min(c["low"] for c in prev_candles)
    
    body = abs(current["close"] - current["open"])
    total = current["high"] - current["low"]
    if total == 0: return None, {}
    
    wick_percent = ((total - body) / total) * 100
    
    # Bullish SFP: Current Low < Lowest Prev AND Current Close > Lowest Prev
    if current["low"] < lowest_prev and current["close"] > lowest_prev:
        if wick_percent >= SFP_WICK_PERCENT:
            return "LONG", {"level": lowest_prev, "wick_percent": round(wick_percent, 2), "type": "SFP"}
            
    # Bearish SFP: Current High > Highest Prev AND Current Close < Highest Prev
    if current["high"] > highest_prev and current["close"] < highest_prev:
        if wick_percent >= SFP_WICK_PERCENT:
            return "SHORT", {"level": highest_prev, "wick_percent": round(wick_percent, 2), "type": "SFP"}
            
    return None, {}


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
    Includes SFP (Swing Failure Pattern) as an alternative trigger.
    """
    if len(candles) < 5 or not atr_values[-1]:
        return None, {"error": "Not enough data"}
        
    current = candles[-1]
    atr = atr_values[-1]
    
    # Check for SFP first as it's a stronger pre-pump signal
    sfp_direction, sfp_details = detect_sfp(candles)
    if sfp_direction:
        return sfp_direction, {
            "type": "SFP",
            "level": sfp_details.get("level"),
            "wick_percent": sfp_details.get("wick_percent"),
            "deviation_atr": 0.0 # SFP doesn't care about ATR deviation the same way
        }

    # Check for Long: False Break of Support
    for support in ranges["supports"]:
        for i in range(-4, -1):
            low_candle = candles[i]
            if low_candle["low"] < support:
                desvio = (support - low_candle["low"]) / (atr if atr > 0 else 1)
                
                if 0.5 <= desvio <= 1.5:
                    reclaimed = False
                    reclaim_index = -1
                    for j in range(i + 1, 0):
                        if candles[j]["close"] > support:
                            reclaimed = True
                            reclaim_index = j
                            break
                    
                    if reclaimed and (reclaim_index - i) <= JUDAS_RECLAIM_CANDLES:
                        target_candle = candles[reclaim_index]
                        body = abs(target_candle["close"] - target_candle["open"])
                        total = target_candle["high"] - target_candle["low"]
                        wick = total - body
                        
                        if total > 0 and (wick / total) >= (JUDAS_WICK_PERCENT / 100):
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
                desvio = (high_candle["high"] - resistance) / (atr if atr > 0 else 1)
                
                if 0.5 <= desvio <= 1.5:
                    reclaimed = False
                    reclaim_index = -1
                    for j in range(i + 1, 0):
                        if candles[j]["close"] < resistance:
                            reclaimed = True
                            reclaim_index = j
                            break
                    
                    if reclaimed and (reclaim_index - i) <= JUDAS_RECLAIM_CANDLES:
                        target_candle = candles[reclaim_index]
                        body = abs(target_candle["close"] - target_candle["open"])
                        total = target_candle["high"] - target_candle["low"]
                        wick = total - body
                        
                        if total > 0 and (wick / total) >= (JUDAS_WICK_PERCENT / 100):
                            return "SHORT", {
                                "type": "JUDAS_SWING",
                                "level": round(resistance, 6),
                                "deviation_atr": round(desvio, 2),
                                "reclaim_candles": reclaim_index - i,
                                "wick_percent": round((wick/total)*100, 2)
                            }
    return None, {}


def calculate_fibonacci_levels(candles: List[Dict], period: int = 144) -> Dict[str, float]:
    """
    Calculate Fibonacci retracement levels for the given period.
    Identifies the local Swing High and Swing Low and returns the standard levels.
    """
    if len(candles) < 2:
        return {}
        
    recent_candles = candles[-period:] if len(candles) > period else candles
    
    highs = [c["high"] for c in recent_candles]
    lows = [c["low"] for c in recent_candles]
    
    swing_high = max(highs)
    swing_low = min(lows)
    diff = swing_high - swing_low
    
    if diff == 0:
        return {}
        
    return {
        "swing_high": swing_high,
        "swing_low": swing_low,
        "diff": diff,
        # Standard Retracement Levels (from High to Low - Bullish Retracement)
        "bull_0.382": swing_high - (0.382 * diff),
        "bull_0.5": swing_high - (0.5 * diff),
        "bull_0.618": swing_high - (0.618 * diff),
        # Standard Retracement Levels (from Low to High - Bearish Retracement)
        "bear_0.382": swing_low + (0.382 * diff),
        "bear_0.5": swing_low + (0.5 * diff),
        "bear_0.618": swing_low + (0.618 * diff),
    }


def detect_candlestick_patterns(candles: List[Dict]) -> Dict[str, bool]:
    """
    Detect common candlestick patterns:
    - Hammer / Inverted Hammer (Bullish)
    - Shooting Star / Hanging Man (Bearish)
    - Engulfing (Bullish/Bearish)
    - Doji (Indecision)
    """
    if len(candles) < 2:
        return {}
        
    curr = candles[-1]
    prev = candles[-2]
    
    # Pre-calculate body and wicks
    c_open, c_close, c_high, c_low = curr["open"], curr["close"], curr["high"], curr["low"]
    p_open, p_close = prev["open"], prev["close"]
    
    body = abs(c_close - c_open)
    upper_wick = c_high - max(c_open, c_close)
    lower_wick = min(c_open, c_close) - c_low
    total_range = c_high - c_low
    
    if total_range == 0:
        return {"doji": True}
        
    patterns = {
        "hammer": False,
        "shooting_star": False,
        "bullish_engulfing": False,
        "bearish_engulfing": False,
        "doji": body <= (total_range * 0.1),
        "heavy_wick_top": upper_wick > (total_range * 0.5),
        "heavy_wick_bottom": lower_wick > (total_range * 0.5)
    }
    
    # Hammer
    if body <= (total_range * 0.3) and lower_wick >= (body * 2) and upper_wick <= (body * 0.5):
        patterns["hammer"] = (c_close > c_open) # Confirm bullish hammer
        
    # Shooting Star
    if body <= (total_range * 0.3) and upper_wick >= (body * 2) and lower_wick <= (body * 0.5):
        patterns["shooting_star"] = (c_close < c_open) # Confirm bearish star
        
    # Engulfing
    p_body = abs(p_close - p_open)
    if body > p_body and p_body > 0:
        if c_close > c_open and p_close < p_open: # Bullish
            patterns["bullish_engulfing"] = True
        elif c_close < c_open and p_close > p_open: # Bearish
            patterns["bearish_engulfing"] = True
            
    return patterns


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

    # Absorption Detection
    absorption_confirmed, absorption_details = detect_absorption(candles, recent_trades)
    
    # SFP Detection
    sfp_signal, sfp_details = detect_sfp(candles)
    
    # RSI Crossover vs BTC Detection
    rsi_crossover_btc, rsi_crossover_details = detect_rsi_crossover_vs_btc(candles, btc_candles) if btc_candles else (None, {})
    
    # Liquidity Hunt Target Detection
    liquidity_hunt, liquidity_details = detect_liquidity_hunt_target(lsr_data, oi_data)

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
            "lsr_latest": lsr_data[0]["ratio"] if lsr_data else None,
            "absorption": {
                "confirmed": absorption_confirmed,
                "details": absorption_details
            },
            "sfp": {
                "signal": sfp_signal,
                "details": sfp_details
            },
            "rsi_crossover_btc": {
                "signal": rsi_crossover_btc,
                "details": rsi_crossover_details
            },
            "liquidity_hunt": {
                "target": liquidity_hunt,
                "details": liquidity_details
            }
        }
    }
