"""
CryptoFastSignals - Support/Resistance Detector
Detects S/R levels using Pivot Points and historical High/Low
"""

from typing import List, Dict, Tuple, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SR_PROXIMITY_THRESHOLD, SR_LOOKBACK_DAYS


def calculate_pivot_points(daily_candles: List[Dict]) -> Dict:
    """
    Calculate Pivot Points from daily candles
    Uses the previous day's OHLC to calculate today's pivots
    
    Args:
        daily_candles: List of daily candles (at least 1 needed)
    
    Returns:
        Dictionary with pivot levels: PP, R1, R2, R3, S1, S2, S3
    """
    if not daily_candles:
        return {}
    
    # Use the last completed daily candle
    prev_day = daily_candles[-1]
    
    high = prev_day["high"]
    low = prev_day["low"]
    close = prev_day["close"]
    
    # Standard Pivot Point formula
    pp = (high + low + close) / 3
    
    # Resistance levels
    r1 = (2 * pp) - low
    r2 = pp + (high - low)
    r3 = high + 2 * (pp - low)
    
    # Support levels
    s1 = (2 * pp) - high
    s2 = pp - (high - low)
    s3 = low - 2 * (high - pp)
    
    return {
        "PP": round(pp, 6),
        "R1": round(r1, 6),
        "R2": round(r2, 6),
        "R3": round(r3, 6),
        "S1": round(s1, 6),
        "S2": round(s2, 6),
        "S3": round(s3, 6),
        "source": "daily_pivot"
    }


def get_high_low_levels(daily_candles: List[Dict], period: int = SR_LOOKBACK_DAYS) -> Dict:
    """
    Get highest high and lowest low over a period
    
    Args:
        daily_candles: List of daily candles
        period: Number of days to look back
    
    Returns:
        Dictionary with HIGH and LOW levels
    """
    if len(daily_candles) < period:
        period = len(daily_candles)
    
    if period == 0:
        return {}
    
    recent_candles = daily_candles[-period:]
    
    highest_high = max(c["high"] for c in recent_candles)
    lowest_low = min(c["low"] for c in recent_candles)
    
    return {
        "HIGH": round(highest_high, 6),
        "LOW": round(lowest_low, 6),
        "period": period,
        "source": f"{period}d_highlow"
    }


def get_all_sr_levels(daily_candles: List[Dict]) -> Dict:
    """
    Get all S/R levels from both methods
    
    Args:
        daily_candles: List of daily candles
    
    Returns:
        Dictionary with all resistances and supports
    """
    pivot_levels = calculate_pivot_points(daily_candles)
    highlow_levels = get_high_low_levels(daily_candles, SR_LOOKBACK_DAYS)
    
    # Organize into resistances and supports
    resistances = []
    supports = []
    
    # Add pivot levels
    if pivot_levels:
        resistances.extend([
            {"level": pivot_levels["R1"], "name": "R1", "source": "pivot"},
            {"level": pivot_levels["R2"], "name": "R2", "source": "pivot"},
            {"level": pivot_levels["R3"], "name": "R3", "source": "pivot"}
        ])
        supports.extend([
            {"level": pivot_levels["S1"], "name": "S1", "source": "pivot"},
            {"level": pivot_levels["S2"], "name": "S2", "source": "pivot"},
            {"level": pivot_levels["S3"], "name": "S3", "source": "pivot"}
        ])
    
    # Add high/low levels
    if highlow_levels:
        resistances.append({
            "level": highlow_levels["HIGH"],
            "name": f"{SR_LOOKBACK_DAYS}D HIGH",
            "source": "highlow"
        })
        supports.append({
            "level": highlow_levels["LOW"],
            "name": f"{SR_LOOKBACK_DAYS}D LOW",
            "source": "highlow"
        })
    
    # Sort by level
    resistances.sort(key=lambda x: x["level"])
    supports.sort(key=lambda x: x["level"], reverse=True)
    
    return {
        "resistances": resistances,
        "supports": supports,
        "pivot_point": pivot_levels.get("PP"),
        "raw": {
            "pivot": pivot_levels,
            "highlow": highlow_levels
        }
    }


def check_sr_proximity(
    current_price: float,
    sr_levels: Dict,
    threshold: float = SR_PROXIMITY_THRESHOLD
) -> Dict:
    """
    Check if current price is near any S/R level
    
    Args:
        current_price: Current price
        sr_levels: Dictionary from get_all_sr_levels()
        threshold: Percentage threshold for "near" (default 0.5%)
    
    Returns:
        Dictionary with proximity analysis
    """
    result = {
        "zone": "NEUTRAL",
        "nearest_resistance": None,
        "nearest_support": None,
        "distance_to_resistance": None,
        "distance_to_support": None,
        "at_resistance": False,
        "at_support": False
    }
    
    resistances = sr_levels.get("resistances", [])
    supports = sr_levels.get("supports", [])
    
    # Find nearest resistance (above current price)
    for r in resistances:
        if r["level"] > current_price:
            distance = (r["level"] - current_price) / current_price
            result["nearest_resistance"] = r
            result["distance_to_resistance"] = round(distance, 6)
            
            if distance <= threshold:
                result["at_resistance"] = True
                result["zone"] = "RESISTANCE"
            break
    
    # Find nearest support (below current price)
    for s in supports:
        if s["level"] < current_price:
            distance = (current_price - s["level"]) / current_price
            result["nearest_support"] = s
            result["distance_to_support"] = round(distance, 6)
            
            if distance <= threshold:
                result["at_support"] = True
                result["zone"] = "SUPPORT"
            break
    
    return result


def get_sr_alignment(signal_direction: str, sr_proximity: Dict, signal_type: str = "EMA_CROSSOVER") -> Tuple[str, int]:
    """
    Determine if signal is aligned with S/R zones
    
    For TRADITIONAL signals (EMA_CROSSOVER, TREND_PULLBACK, RSI_BB_REVERSAL):
        - LONG at support = ALIGNED (good)
        - LONG at resistance = MISALIGNED (risky)
    
    For INSTITUTIONAL signals (JUDAS_SWING, SFP):
        - The logic is INVERTED because institutional players hunt liquidity at S/R levels
        - Being AWAY from traditional S/R after a stop hunt = GOOD (liquidation already happened)
        - Being AT traditional S/R during Judas = you might be the liquidity
    
    Args:
        signal_direction: "LONG" or "SHORT"
        sr_proximity: Result from check_sr_proximity()
        signal_type: Type of signal for context-aware logic
    
    Returns:
        Tuple of (alignment_status, score_modifier)
        alignment_status: "ALIGNED", "MISALIGNED", or "NEUTRAL"
    """
    zone = sr_proximity.get("zone", "NEUTRAL")
    
    # Institutional signals have inverted logic
    is_institutional = signal_type in ["JUDAS_SWING", "SFP"]
    
    if zone == "NEUTRAL":
        if is_institutional:
            # For institutional: being in neutral zone = GOOD (away from sardinha pools)
            return "ALIGNED", 15
        return "NEUTRAL", 0
    
    # === TRADITIONAL SIGNALS (EMA, Pullback, RSI) ===
    if not is_institutional:
        # LONG signal
        if signal_direction == "LONG":
            if zone == "SUPPORT":
                # Buying near support = GOOD
                return "ALIGNED", 25
            elif zone == "RESISTANCE":
                # Buying near resistance = RISKY
                return "MISALIGNED", -15
        
        # SHORT signal
        elif signal_direction == "SHORT":
            if zone == "RESISTANCE":
                # Selling near resistance = GOOD
                return "ALIGNED", 25
            elif zone == "SUPPORT":
                # Selling near support = RISKY
                return "MISALIGNED", -15
    
    # === INSTITUTIONAL SIGNALS (Judas Swing, SFP) ===
    else:
        # For Judas Swing: the stop hunt already happened
        # Being at traditional "good" zones means you might be the liquidity target!
        
        if signal_direction == "LONG":
            if zone == "SUPPORT":
                # At support after Judas = you might be late or be liquidated next
                return "MISALIGNED", -10
            elif zone == "RESISTANCE":
                # Away from support pool after Judas = whales already cleaned liquidity there
                return "ALIGNED", 20
        
        elif signal_direction == "SHORT":
            if zone == "RESISTANCE":
                # At resistance after Judas = you might be late or be liquidated next
                return "MISALIGNED", -10
            elif zone == "SUPPORT":
                # Away from resistance pool after Judas = whales already cleaned liquidity there
                return "ALIGNED", 20
    
    return "NEUTRAL", 0


# Test the S/R detector
if __name__ == "__main__":
    from bybit_client import BybitClient
    
    client = BybitClient()
    
    print("=" * 60)
    print("Testing S/R Detector")
    print("=" * 60)
    
    symbol = "BTCUSDT"
    
    # Get daily candles
    print(f"\n📊 Fetching daily candles for {symbol}...")
    daily_candles = client.get_klines(symbol, "D", 30)
    
    if daily_candles:
        # Get current price
        ticker = client.get_ticker(symbol)
        current_price = ticker["lastPrice"] if ticker else daily_candles[-1]["close"]
        
        print(f"\n💰 Current Price: ${current_price:,.2f}")
        
        # Calculate S/R levels
        sr_levels = get_all_sr_levels(daily_candles)
        
        print(f"\n📈 Resistance Levels:")
        for r in sr_levels["resistances"]:
            print(f"   {r['name']}: ${r['level']:,.2f} ({r['source']})")
        
        print(f"\n📉 Support Levels:")
        for s in sr_levels["supports"]:
            print(f"   {s['name']}: ${s['level']:,.2f} ({s['source']})")
        
        # Check proximity
        proximity = check_sr_proximity(current_price, sr_levels)
        
        print(f"\n🎯 Proximity Analysis:")
        print(f"   Zone: {proximity['zone']}")
        
        if proximity['nearest_resistance']:
            dist = proximity['distance_to_resistance'] * 100
            print(f"   Nearest Resistance: {proximity['nearest_resistance']['name']} ({dist:.2f}% away)")
        
        if proximity['nearest_support']:
            dist = proximity['distance_to_support'] * 100
            print(f"   Nearest Support: {proximity['nearest_support']['name']} ({dist:.2f}% away)")
        
        # Test alignment
        print(f"\n📊 Signal Alignment Test:")
        for direction in ["LONG", "SHORT"]:
            alignment, score = get_sr_alignment(direction, proximity)
            print(f"   {direction}: {alignment} (score: {'+' if score >= 0 else ''}{score})")
    else:
        print("Failed to fetch daily candles")
