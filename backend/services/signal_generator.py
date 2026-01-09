"""
10D - Signal Generator
Main signal generation engine with multiple signal types:
- SMA Crossover
- Trend Pullback
- RSI Extreme Reversal
"""

import time
from typing import List, Dict, Optional
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT

from services.bybit_client import BybitClient
from services.indicator_calculator import analyze_candles
from services.sr_detector import get_all_sr_levels, check_sr_proximity, get_sr_alignment
from services.signal_scorer import calculate_signal_score, get_score_rating, get_score_emoji


class SignalGenerator:
    """Main signal generation engine with multiple signal types"""
    
    def __init__(self):
        self.client = BybitClient()
        self.active_signals: Dict[str, Dict] = {}
        self.signal_history: List[Dict] = []
        self.monitored_pairs: List[str] = []
    
    def initialize(self, pair_limit: int = 100):
        """Initialize the generator with top pairs"""
        print(f"[GENERATOR] Fetching top {pair_limit} pairs...", flush=True)
        self.monitored_pairs = self.client.get_top_pairs(pair_limit)
        print(f"[GENERATOR] Monitoring {len(self.monitored_pairs)} pairs", flush=True)
        
        # Log all pairs being monitored
        if self.monitored_pairs:
            print(f"[GENERATOR] Pairs: {', '.join(self.monitored_pairs[:10])}... and {len(self.monitored_pairs)-10} more", flush=True)
        return self.monitored_pairs
    
    def analyze_pair(self, symbol: str) -> Optional[Dict]:
        """
        Analyze a single pair for ALL signal types:
        1. SMA Crossover (original)
        2. Trend Pullback (new)
        3. RSI Extreme Reversal (new)
        
        Returns the BEST signal if multiple are found
        """
        # Fetch 30M candles
        candles_30m = self.client.get_klines(symbol, "30", 100)
        if not candles_30m:
            return None
        
        # Run indicator analysis
        analysis = analyze_candles(candles_30m)
        
        # Collect all potential signals
        potential_signals = []
        
        # === SIGNAL TYPE 1: SMA Crossover ===
        sma_signal = analysis["sma"]["signal"]
        volume_confirmed = analysis["volume"]["confirmed"]
        
        if sma_signal and volume_confirmed:
            potential_signals.append({
                "type": "SMA_CROSSOVER",
                "direction": sma_signal,
                "base_score": 30,
                "volume_confirmed": True
            })
        
        # === SIGNAL TYPE 2: Trend Pullback ===
        pullback_signal = analysis["pullback"]["signal"]
        trend_direction = analysis["trend"]["direction"]
        
        if pullback_signal:
            # Pullback is stronger when volume is moderate (not too high, not too low)
            vol_ratio = analysis["volume"]["details"].get("volume_ratio", 0)
            has_decent_volume = vol_ratio >= 0.8  # At least 80% of average
            
            if has_decent_volume:
                potential_signals.append({
                    "type": "TREND_PULLBACK",
                    "direction": pullback_signal,
                    "base_score": 25,
                    "volume_confirmed": volume_confirmed,
                    "pullback_details": analysis["pullback"]["details"]
                })
        
        # === SIGNAL TYPE 3: RSI Extreme Reversal ===
        rsi_signal = analysis["rsi"]["signal"]
        
        if rsi_signal:
            # RSI signal is stronger with volume confirmation
            potential_signals.append({
                "type": "RSI_EXTREME",
                "direction": rsi_signal,
                "base_score": 20,
                "volume_confirmed": volume_confirmed,
                "rsi_value": analysis["rsi"]["current_value"],
                "rsi_details": analysis["rsi"]["details"]
            })
        
        # If no signals found, return None
        if not potential_signals:
            return None
        
        # Get current price
        current_price = analysis["current_price"]
        
        # Fetch daily candles for S/R
        candles_daily = self.client.get_klines(symbol, "D", 30)
        
        # Calculate S/R levels
        sr_levels = get_all_sr_levels(candles_daily) if candles_daily else {"resistances": [], "supports": []}
        
        # Check S/R proximity
        sr_proximity = check_sr_proximity(current_price, sr_levels)
        
        # Build and score each potential signal
        scored_signals = []
        
        for sig in potential_signals:
            # Get S/R alignment for this signal direction
            sr_alignment, _ = get_sr_alignment(sig["direction"], sr_proximity)
            
            # Get pivot trend direction
            pivot_trend = analysis["pivot_trend"]["direction"]
            
            # Calculate score
            score_result = calculate_signal_score(
                sig["direction"],
                sig["volume_confirmed"],
                pivot_trend,
                sr_alignment,
                signal_type=sig["type"]
            )
            
            scored_signals.append({
                **sig,
                "score": score_result["score"],
                "score_result": score_result,
                "sr_alignment": sr_alignment,
                "pivot_trend": pivot_trend
            })
        
        # Select the BEST signal (highest score)
        best_signal = max(scored_signals, key=lambda x: x["score"])
        
        # Calculate SL and TP
        if best_signal["direction"] == "LONG":
            stop_loss = current_price * (1 - STOP_LOSS_PERCENT)
            take_profit = current_price * (1 + TAKE_PROFIT_PERCENT)
        else:  # SHORT
            stop_loss = current_price * (1 + STOP_LOSS_PERCENT)
            take_profit = current_price * (1 - TAKE_PROFIT_PERCENT)
        
        # Build signal object
        signal = {
            "id": f"{symbol}_{int(time.time() * 1000)}",
            "symbol": symbol,
            "direction": best_signal["direction"],
            "signal_type": best_signal["type"],
            "entry_price": round(current_price, 6),
            "stop_loss": round(stop_loss, 6),
            "take_profit": round(take_profit, 6),
            "score": best_signal["score"],
            "rating": get_score_rating(best_signal["score"]),
            "emoji": get_score_emoji(best_signal["score"]),
            "confirmations": best_signal["score_result"]["confirmations"],
            "breakdown": best_signal["score_result"]["breakdown"],
            "sr_zone": sr_proximity["zone"],
            "sr_alignment": best_signal["sr_alignment"],
            "pivot_trend": best_signal["pivot_trend"],
            "volume_ratio": analysis["volume"]["details"].get("volume_ratio", 0),
            "rsi": analysis["rsi"]["current_value"],
            "trend": analysis["trend"]["direction"],
            "timestamp": int(time.time() * 1000),
            "timestamp_readable": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "indicators": {
                "sma_fast": analysis["sma"]["details"].get("sma_fast"),
                "sma_slow": analysis["sma"]["details"].get("sma_slow"),
                "rsi": analysis["rsi"]["current_value"],
                "atr": analysis["pivot_trend"]["details"].get("atr"),
                "upper_band": analysis["pivot_trend"]["details"].get("upper_band"),
                "lower_band": analysis["pivot_trend"]["details"].get("lower_band")
            },
            "sr_levels": {
                "nearest_resistance": sr_proximity.get("nearest_resistance"),
                "nearest_support": sr_proximity.get("nearest_support"),
                "distance_to_resistance": sr_proximity.get("distance_to_resistance"),
                "distance_to_support": sr_proximity.get("distance_to_support")
            }
        }
        
        return signal
    
    def scan_all_pairs(self) -> List[Dict]:
        """Scan all monitored pairs for signals"""
        new_signals = []
        total_pairs = len(self.monitored_pairs)
        
        print(f"[SCAN] Starting scan of {total_pairs} pairs...", flush=True)
        
        for i, symbol in enumerate(self.monitored_pairs):
            try:
                # Log progress every 10 pairs
                if (i + 1) % 10 == 0 or i == 0:
                    print(f"  [SCAN] Progress: [{i+1}/{total_pairs}] - Current: {symbol}", flush=True)
                
                signal = self.analyze_pair(symbol)
                
                if signal:
                    # Check if we already have an active signal for this pair
                    if symbol not in self.active_signals:
                        self.active_signals[symbol] = signal
                        self.signal_history.append(signal)
                        new_signals.append(signal)
                        sig_type = signal['signal_type'].replace('_', ' ')
                        print(f"[NEW SIGNAL] {symbol} {signal['direction']} ({sig_type}) Score: {signal['score']}", flush=True)
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[SCAN ERROR] {symbol}: {e}", flush=True)
                continue
        
        # Summary after scan
        active_count = len(self.active_signals)
        print(f"[SCAN] Complete. Found {len(new_signals)} new signals. Total active: {active_count}", flush=True)
        return new_signals
    
    def get_active_signals(self) -> List[Dict]:
        """Get all active signals sorted by score"""
        signals = list(self.active_signals.values())
        signals.sort(key=lambda x: x["score"], reverse=True)
        return signals
    
    def get_signal_history(self, limit: int = 50) -> List[Dict]:
        """Get signal history (most recent first)"""
        return self.signal_history[-limit:][::-1]
    
    def clear_signal(self, symbol: str):
        """Remove a signal from active signals"""
        if symbol in self.active_signals:
            del self.active_signals[symbol]
    
    def clear_expired_signals(self, max_age_minutes: int = 60):
        """Remove signals older than max_age_minutes"""
        current_time = int(time.time() * 1000)
        max_age_ms = max_age_minutes * 60 * 1000
        
        expired = []
        for symbol, signal in self.active_signals.items():
            if current_time - signal["timestamp"] > max_age_ms:
                expired.append(symbol)
        
        for symbol in expired:
            del self.active_signals[symbol]
        
        return len(expired)
    
    def get_stats(self) -> Dict:
        """Get summary statistics"""
        active = self.get_active_signals()
        
        long_count = sum(1 for s in active if s["direction"] == "LONG")
        short_count = sum(1 for s in active if s["direction"] == "SHORT")
        avg_score = sum(s["score"] for s in active) / len(active) if active else 0
        
        # Count by signal type
        type_counts = {}
        for s in active:
            sig_type = s.get("signal_type", "UNKNOWN")
            type_counts[sig_type] = type_counts.get(sig_type, 0) + 1
        
        return {
            "monitored_pairs": len(self.monitored_pairs),
            "active_signals": len(active),
            "long_signals": long_count,
            "short_signals": short_count,
            "average_score": round(avg_score, 1),
            "total_historical": len(self.signal_history),
            "signal_types": type_counts
        }
