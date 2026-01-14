"""
10D - Signal Scorer
Calculates signal score based on multiple confirmations and signal types
Integrates with ML Brain for dynamic score adjustments
"""

from typing import Dict, Optional
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SCORE_EMA_CROSSOVER,
    SCORE_TREND_PULLBACK,
    SCORE_RSI_BB_REVERSAL,
    SCORE_VOLUME_CONFIRMED,
    SCORE_MACD_CONFIRMED,
    SCORE_4H_TREND_ALIGNED,
    SCORE_PIVOT_CONFIRMED,
    SCORE_SR_ALIGNED,
    SCORE_SR_MISALIGNED,
    SCORE_INSTITUTIONAL_JUDAS,
    SCORE_CVD_DIVERGENCE,
    SCORE_OI_ACCUMULATION,
    SCORE_LSR_CLEANUP,
    SCORE_ABSORPTION_CONFIRMED,
    SCORE_RSI_CROSSOVER_BTC,
    SCORE_LIQUIDITY_ALIGNED
)

# ML Brain path
ML_BRAIN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml_brain.json")

# Cache for ML Brain to avoid reading file on every call
_ml_brain_cache = None
_ml_brain_loaded = False


def load_ml_brain() -> Optional[Dict]:
    """Load ML Brain insights from JSON file (cached)"""
    global _ml_brain_cache, _ml_brain_loaded
    
    if _ml_brain_loaded:
        return _ml_brain_cache
    
    try:
        if os.path.exists(ML_BRAIN_PATH):
            with open(ML_BRAIN_PATH, "r") as f:
                _ml_brain_cache = json.load(f)
                print(f"[ML BRAIN] Loaded insights from {ML_BRAIN_PATH}", flush=True)
        else:
            _ml_brain_cache = None
            print("[ML BRAIN] No brain file found, using default scoring", flush=True)
    except Exception as e:
        print(f"[ML BRAIN ERROR] Failed to load brain: {e}", flush=True)
        _ml_brain_cache = None
    
    _ml_brain_loaded = True
    return _ml_brain_cache


def get_ml_bonus(rsi_value: float = 50, feature_scores: Dict = None) -> int:
    """
    Calculate ML-based bonus/penalty based on learned insights.
    
    Args:
        rsi_value: Current RSI value of the signal
        feature_scores: Dict with feature values (oi_change_pct, lsr_change_pct, etc)
    
    Returns:
        Bonus points to add to the score (-10 to +10)
    """
    brain = load_ml_brain()
    if not brain:
        return 0
    
    bonus = 0
    
    # 1. RSI Range Check
    optimal_rsi = brain.get("optimal_thresholds", {}).get("optimal_rsi_range")
    if optimal_rsi and len(optimal_rsi) == 2:
        rsi_min, rsi_max = optimal_rsi
        if rsi_min <= rsi_value <= rsi_max:
            bonus += 5  # RSI is in optimal range
        elif rsi_value < rsi_min - 10 or rsi_value > rsi_max + 10:
            bonus -= 3  # RSI is far from optimal range
    
    # 2. Feature Importance Weighted Bonus
    if feature_scores:
        importance = brain.get("feature_importance", {})
        
        # Boost score if high-importance features are positive
        for feature, weight in importance.items():
            if feature in feature_scores and weight > 0.15:  # Only consider important features
                value = feature_scores.get(feature, 0)
                if isinstance(value, (int, float)):
                    # Positive value on positive correlation = good
                    if value > 0:
                        bonus += int(weight * 5)  # Up to +1 per important feature
    
    # Clamp bonus to reasonable range
    return max(-10, min(10, bonus))


def reload_ml_brain():
    """Force reload of ML Brain (call after training cycle)"""
    global _ml_brain_loaded
    _ml_brain_loaded = False
    return load_ml_brain()


def calculate_signal_score(
    signal_direction: str,
    volume_confirmed: bool,
    pivot_trend_direction: Optional[str],
    sr_alignment: str,
    signal_type: str = "EMA_CROSSOVER",
    macd_confirmed: bool = False,
    trend_4h_aligned: bool = False,
    cvd_divergence: bool = False,
    oi_accumulation: bool = False,
    lsr_cleanup: bool = False,
    absorption_confirmed: bool = False,
    rsi_crossover_btc: bool = False,
    liquidity_aligned: bool = False,
    rsi_value: float = 50,
    ai_features: Dict = None
) -> Dict:
    """
    Calculate the total score for a signal
    
    Args:
        signal_direction: "LONG" or "SHORT"
        volume_confirmed: True if volume >= 1.2x average
        pivot_trend_direction: "UP" or "DOWN"
        sr_alignment: "ALIGNED", "MISALIGNED", or "NEUTRAL"
        signal_type: "EMA_CROSSOVER", "TREND_PULLBACK", or "RSI_BB_REVERSAL"
        macd_confirmed: True if MACD histogram matches direction
        trend_4h_aligned: True if 30M signal matches 4H trend
        rsi_value: Current RSI value for ML bonus calculation
        ai_features: Dict with market features for ML bonus calculation
    
    Returns:
        Dictionary with score breakdown
    """
    # Determine base score based on signal type
    if signal_type == "EMA_CROSSOVER":
        base_score = SCORE_EMA_CROSSOVER
        base_label = "ema_crossover"
    elif signal_type == "TREND_PULLBACK":
        base_score = SCORE_TREND_PULLBACK
        base_label = "trend_pullback"
    elif signal_type == "RSI_BB_REVERSAL":
        base_score = SCORE_RSI_BB_REVERSAL
        base_label = "rsi_bb_reversal"
    elif signal_type == "JUDAS_SWING":
        base_score = SCORE_INSTITUTIONAL_JUDAS
        base_label = "institutional_judas"
    else:
        base_score = 20
        base_label = "base"
    
    breakdown = {
        base_label: base_score,
        "volume": 0,
        "macd": 0,
        "trend_4h": 0,
        "pivot_trend": 0,
        "sr_alignment": 0,
        "cvd": 0,
        "oi": 0,
        "lsr": 0,
        "absorption": 0,
        "rsi_btc": 0,
        "liquidity": 0,
        "ml_bonus": 0
    }
    
    total = base_score
    
    # Volume confirmation
    if volume_confirmed:
        breakdown["volume"] = SCORE_VOLUME_CONFIRMED
        total += SCORE_VOLUME_CONFIRMED
    
    # MACD confirmation
    if macd_confirmed:
        breakdown["macd"] = SCORE_MACD_CONFIRMED
        total += SCORE_MACD_CONFIRMED
        
    # 4H Trend alignment (Massive bonus/filter)
    if trend_4h_aligned:
        breakdown["trend_4h"] = SCORE_4H_TREND_ALIGNED
        total += SCORE_4H_TREND_ALIGNED
    
    # Pivot Trend confirmation
    pivot_confirms = False
    if signal_direction == "LONG" and pivot_trend_direction == "UP":
        pivot_confirms = True
    elif signal_direction == "SHORT" and pivot_trend_direction == "DOWN":
        pivot_confirms = True
    
    if pivot_confirms:
        breakdown["pivot_trend"] = SCORE_PIVOT_CONFIRMED
        total += SCORE_PIVOT_CONFIRMED
    
    # S/R alignment
    if sr_alignment == "ALIGNED":
        breakdown["sr_alignment"] = SCORE_SR_ALIGNED
        total += SCORE_SR_ALIGNED
    elif sr_alignment == "MISALIGNED":
        breakdown["sr_alignment"] = SCORE_SR_MISALIGNED
        total += SCORE_SR_MISALIGNED
    
    # CVD Divergence
    if cvd_divergence:
        breakdown["cvd"] = SCORE_CVD_DIVERGENCE
        total += SCORE_CVD_DIVERGENCE
        
    # OI Accumulation
    if oi_accumulation:
        breakdown["oi"] = SCORE_OI_ACCUMULATION
        total += SCORE_OI_ACCUMULATION
        
    # LSR Cleanup
    if lsr_cleanup:
        breakdown["lsr"] = SCORE_LSR_CLEANUP
        total += SCORE_LSR_CLEANUP
        
    # Absorption Confirmation
    if absorption_confirmed:
        breakdown["absorption"] = SCORE_ABSORPTION_CONFIRMED
        total += SCORE_ABSORPTION_CONFIRMED
    
    # RSI Crossover vs BTC (Decoupling)
    if rsi_crossover_btc:
        breakdown["rsi_btc"] = SCORE_RSI_CROSSOVER_BTC
        total += SCORE_RSI_CROSSOVER_BTC
    
    # Liquidity Hunt Alignment (signal direction matches predicted hunt)
    if liquidity_aligned:
        breakdown["liquidity"] = SCORE_LIQUIDITY_ALIGNED
        total += SCORE_LIQUIDITY_ALIGNED
    
    # ML Brain Bonus (Dynamic adjustment based on learned insights)
    ml_bonus = get_ml_bonus(rsi_value=rsi_value, feature_scores=ai_features)
    breakdown["ml_bonus"] = ml_bonus
    total += ml_bonus
    
    # Ensure score is within 0-100
    total = max(0, min(100, total))
    
    # Build confirmations dict
    confirmations = {
        "volume": volume_confirmed,
        "macd": macd_confirmed,
        "trend_4h": trend_4h_aligned,
        "pivot_trend": pivot_confirms,
        "sr_aligned": sr_alignment == "ALIGNED",
        "cvd_divergence": cvd_divergence,
        "oi_accumulation": oi_accumulation,
        "lsr_cleanup": lsr_cleanup,
        "absorption": absorption_confirmed,
        "rsi_crossover_btc": rsi_crossover_btc,
        "liquidity_aligned": liquidity_aligned,
        "ml_bonus_applied": ml_bonus != 0
    }
    
    # Add signal type specific confirmation
    if signal_type == "EMA_CROSSOVER":
        confirmations["ema_crossover"] = True
    elif signal_type == "TREND_PULLBACK":
        confirmations["pullback"] = True
    elif signal_type == "RSI_BB_REVERSAL":
        confirmations["rsi_bb_reversal"] = True
    elif signal_type == "JUDAS_SWING":
        confirmations["judas_swing"] = True
    
    return {
        "score": total,
        "breakdown": breakdown,
        "confirmations": confirmations,
        "signal_type": signal_type,
        "ml_bonus": ml_bonus
    }


def get_score_rating(score: int) -> str:
    """Get a human-readable rating for the score"""
    if score >= 90:
        return "EXCELLENT"
    elif score >= 75:
        return "STRONG"
    elif score >= 55:
        return "GOOD"
    elif score >= 40:
        return "MODERATE"
    else:
        return "WEAK"


def get_score_emoji(score: int) -> str:
    """Get emoji representation for score"""
    if score >= 90:
        return "🔥"
    elif score >= 75:
        return "⭐"
    elif score >= 55:
        return "✅"
    elif score >= 40:
        return "⚠️"
    else:
        return "❌"


def get_signal_type_label(signal_type: str) -> str:
    """Get human-readable label for signal type"""
    labels = {
        "EMA_CROSSOVER": "EMA 20/50 + MACD",
        "TREND_PULLBACK": "Pullback na Tendência",
        "RSI_BB_REVERSAL": "RSI + Bollinger Reversão",
        "JUDAS_SWING": "Institutional Judas Swing"
    }
    return labels.get(signal_type, signal_type)
