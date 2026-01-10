"""
10D - Signal Generator
Main signal generation engine with multiple signal types:
- SMA Crossover
- Trend Pullback
- RSI Extreme Reversal
"""

import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
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
        1. EMA 20/50 Crossover + MACD
        2. Trend Pullback
        3. RSI + Bollinger Reversal
        
        Returns the BEST signal if multiple are found
        """
        # Fetch 30M candles
        candles_30m = self.client.get_klines(symbol, "30", 100)
        if not candles_30m:
            return None
            
        # Fetch 4H candles for trend filter
        candles_4h = self.client.get_klines(symbol, "240", 60)
        
        # Run indicator analysis
        # Fetch institutional data
        trades = self.client.get_recent_trades(symbol, 100)
        oi_data = self.client.get_open_interest(symbol, "30min", 10)
        lsr_data = self.client.get_long_short_ratio(symbol, "30min", 10)
        
        # Use existing btc_candles if available (should be passed or stored)
        btc_candles = getattr(self, "current_btc_candles", None)
        
        analysis = analyze_candles(
            candles_30m, 
            candles_4h, 
            recent_trades=trades,
            oi_data=oi_data,
            lsr_data=lsr_data,
            btc_candles=btc_candles
        )
        
        # 4H Trend Filter Logic
        trend_4h = analysis["trend_4h"]["direction"] # "UPTREND" or "DOWNTREND"
        
        # Collect all potential signals
        potential_signals = []
        
        # === SIGNAL TYPE 1: EMA Crossover ===
        ema_signal = analysis["ema"]["signal"]
        volume_confirmed = analysis["volume"]["confirmed"]
        macd_confirmed = analysis["ema"]["details"].get("macd_confirmed", False)
        
        if ema_signal:
            # FILTER: Only allow signal if it matches 4H trend
            if (ema_signal == "LONG" and trend_4h == "UPTREND") or (ema_signal == "SHORT" and trend_4h == "DOWNTREND"):
                potential_signals.append({
                    "type": "EMA_CROSSOVER",
                    "direction": ema_signal,
                    "volume_confirmed": volume_confirmed,
                    "macd_confirmed": macd_confirmed,
                    "trend_4h_aligned": True
                })
        
        # === SIGNAL TYPE 2: Trend Pullback ===
        pullback_signal = analysis["pullback"]["signal"]
        
        if pullback_signal:
            # FILTER: Only allow signal if it matches 4H trend
            if (pullback_signal == "LONG" and trend_4h == "UPTREND") or (pullback_signal == "SHORT" and trend_4h == "DOWNTREND"):
                potential_signals.append({
                    "type": "TREND_PULLBACK",
                    "direction": pullback_signal,
                    "volume_confirmed": volume_confirmed,
                    "macd_confirmed": False, # Typically not used for pullback but could be
                    "trend_4h_aligned": True
                })
        
        # === SIGNAL TYPE 3: RSI + BB Reversal ===
        rsi_signal = analysis["rsi_bb"]["signal"]
        
        if rsi_signal:
            # Reversal can be counter-trend but we PREFER trend-aligned
            is_aligned = (rsi_signal == "LONG" and trend_4h == "UPTREND") or (rsi_signal == "SHORT" and trend_4h == "DOWNTREND")
            
            potential_signals.append({
                "type": "RSI_BB_REVERSAL",
                "direction": rsi_signal,
                "volume_confirmed": volume_confirmed,
                "macd_confirmed": False,
                "trend_4h_aligned": is_aligned
            })
            
        # === SIGNAL TYPE 4: Institutional Judas Swing ===
        judas_signal = analysis["institutional"]["judas_signal"]
        
        if judas_signal:
            # Judas Swing MUST match 4H trend
            if (judas_signal == "LONG" and trend_4h == "UPTREND") or (judas_signal == "SHORT" and trend_4h == "DOWNTREND"):
                # Order Flow Confluences
                cvd = analysis["institutional"]["cvd"]
                rs_score = analysis["institutional"]["rs_score"]
                
                # CVD Divergence Check
                cvd_div = False
                if judas_signal == "LONG" and cvd >= 0: # Price dipped but CVD is positive
                    cvd_div = True
                elif judas_signal == "SHORT" and cvd <= 0: # Price ripped but CVD is negative
                    cvd_div = True
                    
                # OI Accumulation (Simple check: latest OI > prev OI)
                oi_acc = False
                inst_data = analysis["institutional"]
                if inst_data["oi_latest"] and len(oi_data) > 1:
                    if inst_data["oi_latest"] > oi_data[1]["openInterest"]:
                        oi_acc = True
                        
                # LSR Cleanup (LSR should fall for Long, rise for Short - clearing retail)
                lsr_clean = False
                if inst_data["lsr_latest"] and len(lsr_data) > 1:
                    if judas_signal == "LONG" and inst_data["lsr_latest"] < lsr_data[1]["ratio"]:
                        lsr_clean = True
                    elif judas_signal == "SHORT" and inst_data["lsr_latest"] > lsr_data[1]["ratio"]:
                        lsr_clean = True

                potential_signals.append({
                    "type": "JUDAS_SWING",
                    "direction": judas_signal,
                    "volume_confirmed": volume_confirmed,
                    "macd_confirmed": False,
                    "trend_4h_aligned": True,
                    "cvd_divergence": cvd_div,
                    "oi_accumulation": oi_acc,
                    "lsr_cleanup": lsr_clean,
                    "rs_score": rs_score,
                    "details": analysis["institutional"]["judas_details"]
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
                signal_type=sig["type"],
                macd_confirmed=sig.get("macd_confirmed", False),
                trend_4h_aligned=sig.get("trend_4h_aligned", False),
                cvd_divergence=sig.get("cvd_divergence", False),
                oi_accumulation=sig.get("oi_accumulation", False),
                lsr_cleanup=sig.get("lsr_cleanup", False)
            )
            
            scored_signals.append({
                **sig,
                "score": score_result["score"],
                "score_result": score_result,
                "sr_alignment": sr_alignment,
                "pivot_trend": pivot_trend,
                "lsr_cleanup": sig.get("lsr_cleanup", False),
                "oi_accumulation": sig.get("oi_accumulation", False),
                "cvd_divergence": sig.get("cvd_divergence", False),
                "rs_score": sig.get("rs_score", 0.0),
                "institutional_details": sig.get("details", {})
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
            "rsi": analysis["rsi_bb"].get("current_value"),
            "trend": analysis["trend_4h"].get("direction"),
            "timestamp": int(time.time() * 1000),
            "timestamp_readable": (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
            "indicators": {
                "ema_fast": analysis["ema"]["details"].get("ema_fast"),
                "ema_slow": analysis["ema"]["details"].get("ema_slow"),
                "rsi": analysis["rsi_bb"].get("current_value"),
                "atr": analysis["pivot_trend"]["details"].get("atr"),
                "upper_band": analysis["pivot_trend"]["details"].get("upper_band"),
                "lower_band": analysis["pivot_trend"]["details"].get("lower_band"),
                "macd_hist": analysis["ema"]["details"].get("macd_hist")
            },
            "sr_levels": {
                "nearest_resistance": sr_proximity.get("nearest_resistance"),
                "nearest_support": sr_proximity.get("nearest_support"),
                "distance_to_resistance": sr_proximity.get("distance_to_resistance"),
                "distance_to_support": sr_proximity.get("distance_to_support")
            },
            "institutional": {
                "rs_score": best_signal.get("rs_score"),
                "cvd": analysis["institutional"]["cvd"],
                "oi_latest": analysis["institutional"]["oi_latest"],
                "lsr_latest": analysis["institutional"]["lsr_latest"],
                "judas_details": best_signal.get("institutional_details"),
                "cvd_divergence": best_signal.get("cvd_divergence"),
                "oi_accumulation": best_signal.get("oi_accumulation"),
                "lsr_cleanup": best_signal.get("lsr_cleanup")
            }
        }
        
        return signal
    
    def scan_all_pairs(self) -> List[Dict]:
        """Scan all monitored pairs for signals"""
        new_signals = []
        total_pairs = len(self.monitored_pairs)
        
        print(f"[SCAN] Starting scan of {total_pairs} pairs...", flush=True)
        
        # Fetch BTC candles once for RS calculation
        try:
            self.current_btc_candles = self.client.get_klines("BTCUSDT", "30", 100)
        except:
            self.current_btc_candles = None
            
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

    def monitor_active_signals(self):
        """Monitor active signals for TP or SL hits"""
        if not self.active_signals:
            return []
            
        print(f"[MONITOR] Checking {len(self.active_signals)} active signals...", flush=True)
        
        # Get all tickers in one call for efficiency
        tickers = self.client.get_all_tickers()
        if not tickers:
            return []
            
        ticker_map = {t["symbol"]: float(t["lastPrice"]) for t in tickers}
        
        finalized = []
        current_time = int(time.time() * 1000)
        
        for symbol, signal in list(self.active_signals.items()):
            current_price = ticker_map.get(symbol)
            if not current_price:
                continue
                
            entry_price = signal["entry_price"]
            tp = signal["take_profit"]
            sl = signal["stop_loss"]
            direction = signal["direction"]
            
            hit = False
            status = "ACTIVE"
            
            if direction == "LONG":
                if current_price >= tp:
                    hit = True
                    status = "TP_HIT"
                elif current_price <= sl:
                    hit = True
                    status = "SL_HIT"
            else: # SHORT
                if current_price <= tp:
                    hit = True
                    status = "TP_HIT"
                elif current_price >= sl:
                    hit = True
                    status = "SL_HIT"
                    
            if hit:
                # Update signal object
                signal["status"] = status
                signal["exit_price"] = current_price
                signal["exit_timestamp"] = current_time
                signal["exit_timestamp_readable"] = (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
                
                # Calculate final ROI
                if direction == "LONG":
                    roi = ((current_price - entry_price) / entry_price) * 100
                else:
                    roi = ((entry_price - current_price) / entry_price) * 100
                signal["final_roi"] = round(roi, 2)
                
                # Remove from active
                print(f"[FINALIZED] {symbol} {status} at ${current_price} (ROI: {roi:.2f}%)", flush=True)
                del self.active_signals[symbol]
                finalized.append(signal)
                
        return finalized
    
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
