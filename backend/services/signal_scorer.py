"""
10D - Signal Scorer
Calculates signal score based on multiple confirmations and signal types
"""

from typing import Dict, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SCORE_SMA_CROSSOVER,
    SCORE_TREND_PULLBACK,
    SCORE_RSI_EXTREME,
    SCORE_VOLUME_CONFIRMED,
    SCORE_PIVOT_CONFIRMED,
    SCORE_SR_ALIGNED,
    SCORE_SR_MISALIGNED
)


def calculate_signal_score(
    signal_direction: str,
    volume_confirmed: bool,
    pivot_trend_direction: Optional[str],
    sr_alignment: str,
    signal_type: str = "SMA_CROSSOVER"
) -> Dict:
    """
    Calculate the total score for a signal
    
    Args:
        signal_direction: "LONG" or "SHORT"
        volume_confirmed: True if volume >= 1.5x average
        pivot_trend_direction: "UP" or "DOWN"
        sr_alignment: "ALIGNED", "MISALIGNED", or "NEUTRAL"
        signal_type: "SMA_CROSSOVER", "TREND_PULLBACK", or "RSI_EXTREME"
    
    Returns:
        Dictionary with score breakdown
    """
    # Determine base score based on signal type
    if signal_type == "SMA_CROSSOVER":
        base_score = SCORE_SMA_CROSSOVER
        base_label = "sma_crossover"
    elif signal_type == "TREND_PULLBACK":
        base_score = SCORE_TREND_PULLBACK
        base_label = "trend_pullback"
    elif signal_type == "RSI_EXTREME":
        base_score = SCORE_RSI_EXTREME
        base_label = "rsi_extreme"
    else:
        base_score = 20
        base_label = "base"
    
    breakdown = {
        base_label: base_score,
        "volume": 0,
        "pivot_trend": 0,
        "sr_alignment": 0
    }
    
    total = base_score
    
    # Volume confirmation
    if volume_confirmed:
        breakdown["volume"] = SCORE_VOLUME_CONFIRMED
        total += SCORE_VOLUME_CONFIRMED
    
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
    
    # Ensure score is within 0-100
    total = max(0, min(100, total))
    
    # Build confirmations dict
    confirmations = {
        "volume": volume_confirmed,
        "pivot_trend": pivot_confirms,
        "sr_aligned": sr_alignment == "ALIGNED"
    }
    
    # Add signal type specific confirmation
    if signal_type == "SMA_CROSSOVER":
        confirmations["sma_crossover"] = True
    elif signal_type == "TREND_PULLBACK":
        confirmations["pullback"] = True
    elif signal_type == "RSI_EXTREME":
        confirmations["rsi_extreme"] = True
    
    return {
        "score": total,
        "breakdown": breakdown,
        "confirmations": confirmations,
        "signal_type": signal_type
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
        "SMA_CROSSOVER": "Cruzamento SMA",
        "TREND_PULLBACK": "Pullback na Tendência",
        "RSI_EXTREME": "RSI Extremo"
    }
    return labels.get(signal_type, signal_type)
