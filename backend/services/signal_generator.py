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
import pytz
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT,
    RS_MIN_THRESHOLD, VOLUME_CLIMAX_THRESHOLD,
    HISTORY_RETENTION_HOURS, SIGNAL_TTL_MINUTES,
    ENTRY_ZONE_IDEAL, ENTRY_ZONE_LATE, ENTRY_MISSED_PERCENT,
    ML_ENABLED, ML_PROBABILITY_THRESHOLD, ML_MIN_SAMPLES,
    ML_AUTO_RETRAIN_INTERVAL, ML_MODEL_PATH, ML_METRICS_PATH,
    ML_HYBRID_SCORE_WEIGHT
)

import json

from services.bybit_client import BybitClient
from services.indicator_calculator import analyze_candles
from services.sr_detector import get_all_sr_levels, check_sr_proximity, get_sr_alignment
from services.signal_scorer import calculate_signal_score, get_score_rating, get_score_emoji
from services.database_manager import DatabaseManager
from services.ml_predictor import MLPredictor


class SignalGenerator:
    """Main signal generation engine with multiple signal types"""
    
    def __init__(self):
        self.client = BybitClient()
        self.db = DatabaseManager()
        self.active_signals: Dict[str, Dict] = {}
        self.signal_history: List[Dict] = []
        self.monitored_pairs: List[str] = []
        self.instruments_info: Dict[str, Dict] = {}
        self.tz = pytz.timezone('America/Sao_Paulo')
        
        # Initialize ML Predictor
        ml_config = {
            "ML_MODEL_PATH": ML_MODEL_PATH,
            "ML_METRICS_PATH": ML_METRICS_PATH,
            "ML_MIN_SAMPLES": ML_MIN_SAMPLES,
            "ML_AUTO_RETRAIN_INTERVAL": ML_AUTO_RETRAIN_INTERVAL
        }
        self.ml_predictor = MLPredictor(self.db, ml_config) if ML_ENABLED else None
        
        self.load_state()
    
    def initialize(self, pair_limit: int = 100):
        """Initialize the generator with top pairs"""
        print(f"[GENERATOR] Fetching top {pair_limit} pairs...", flush=True)
        instruments = self.client.get_instruments()
        self.instruments_info = {inst["symbol"]: inst for inst in instruments}
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
                # Check for RSI crossover vs BTC
                rsi_crossover = analysis["institutional"]["rsi_crossover_btc"]
                rsi_crossover_confirmed = rsi_crossover["signal"] == ema_signal
                
                potential_signals.append({
                    "type": "EMA_CROSSOVER",
                    "direction": ema_signal,
                    "volume_confirmed": volume_confirmed,
                    "macd_confirmed": macd_confirmed,
                    "trend_4h_aligned": True,
                    "rsi_crossover_btc": rsi_crossover_confirmed
                })
        
        # === SIGNAL TYPE 2: Trend Pullback ===
        pullback_signal = analysis["pullback"]["signal"]
        
        if pullback_signal:
            # FILTER: Only allow signal if it matches 4H trend
            if (pullback_signal == "LONG" and trend_4h == "UPTREND") or (pullback_signal == "SHORT" and trend_4h == "DOWNTREND"):
                # Check for RSI crossover vs BTC
                rsi_crossover = analysis["institutional"]["rsi_crossover_btc"]
                rsi_crossover_confirmed = rsi_crossover["signal"] == pullback_signal
                
                potential_signals.append({
                    "type": "TREND_PULLBACK",
                    "direction": pullback_signal,
                    "volume_confirmed": volume_confirmed,
                    "macd_confirmed": False, # Typically not used for pullback but could be
                    "trend_4h_aligned": True,
                    "rsi_crossover_btc": rsi_crossover_confirmed
                })
        
        # === SIGNAL TYPE 3: RSI + BB Reversal ===
        rsi_signal = analysis["rsi_bb"]["signal"]
        
        if rsi_signal:
            # Reversal can be counter-trend but we PREFER trend-aligned
            is_aligned = (rsi_signal == "LONG" and trend_4h == "UPTREND") or (rsi_signal == "SHORT" and trend_4h == "DOWNTREND")
            
            # Check for RSI crossover vs BTC
            rsi_crossover = analysis["institutional"]["rsi_crossover_btc"]
            rsi_crossover_confirmed = rsi_crossover["signal"] == rsi_signal
            
            potential_signals.append({
                "type": "RSI_BB_REVERSAL",
                "direction": rsi_signal,
                "volume_confirmed": volume_confirmed,
                "macd_confirmed": False,
                "trend_4h_aligned": is_aligned,
                "rsi_crossover_btc": rsi_crossover_confirmed
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

                # New Filters: RS and Absorption
                absorption = analysis["institutional"]["absorption"]
                
                # HARD FILTER: RS must be positive for LONGS
                rs_ok = True
                if judas_signal == "LONG" and rs_score < RS_MIN_THRESHOLD:
                    rs_ok = False
                
                if rs_ok:
                    # Check for RSI crossover vs BTC
                    rsi_crossover = analysis["institutional"]["rsi_crossover_btc"]
                    rsi_crossover_confirmed = rsi_crossover["signal"] == judas_signal
                    
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
                        "absorption_confirmed": absorption["confirmed"],
                        "rsi_crossover_btc": rsi_crossover_confirmed,
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
            # Get S/R alignment for this signal direction (inverted for institutional signals)
            sr_alignment, _ = get_sr_alignment(sig["direction"], sr_proximity, sig["type"])
            
            # Get pivot trend direction
            pivot_trend = analysis["pivot_trend"]["direction"]
            
            # Check liquidity alignment (signal aligns with predicted hunt target)
            liquidity_hunt = analysis["institutional"]["liquidity_hunt"]["target"]
            liquidity_aligned = False
            if liquidity_hunt:
                # LONG signal after SHORT_HUNT (whales pushed up, hunting shorts) = ALIGNED
                # SHORT signal after LONG_HUNT (whales pushed down, hunting longs) = ALIGNED
                if sig["direction"] == "LONG" and liquidity_hunt == "SHORT_HUNT":
                    liquidity_aligned = True
                elif sig["direction"] == "SHORT" and liquidity_hunt == "LONG_HUNT":
                    liquidity_aligned = True
            
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
                lsr_cleanup=sig.get("lsr_cleanup", False),
                absorption_confirmed=sig.get("absorption_confirmed", False),
                rsi_crossover_btc=sig.get("rsi_crossover_btc", False),
                liquidity_aligned=liquidity_aligned,
                rsi_value=analysis["rsi_bb"].get("current_value", 50),
                ai_features=None  # Features serão capturadas após o score ser calculado
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
        
        # Get tickSize for this symbol
        inst_info = self.instruments_info.get(symbol, {})
        tick_size = float(inst_info.get("tickSize", "0.000001"))
        def round_step(price, step):
            return round(round(price / step) * step, 8)

        # Build signal object
        signal = {
            "id": f"{symbol}_{int(time.time() * 1000)}",
            "symbol": symbol,
            "direction": best_signal["direction"],
            "signal_type": best_signal["type"],
            "entry_price": round_step(current_price, tick_size),
            "stop_loss": round_step(stop_loss, tick_size),
            "take_profit": round_step(take_profit, tick_size),
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
            "timestamp_readable": datetime.now(self.tz).strftime("%Y-%m-%d %H:%M:%S"),
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
                "lsr_cleanup": best_signal.get("lsr_cleanup"),
                "rsi_crossover_btc": best_signal.get("rsi_crossover_btc"),
                "rsi_crossover_details": analysis["institutional"]["rsi_crossover_btc"].get("details", {}),
                "liquidity_hunt": analysis["institutional"]["liquidity_hunt"]["target"],
                "liquidity_aligned": score_result.get("confirmations", {}).get("liquidity_aligned", False),
                "liquidity_details": analysis["institutional"]["liquidity_hunt"]["details"]
            },
            "ai_features": self._capture_ai_features(symbol, analysis, best_signal)
        }
        
        # === ML PREDICTION INTEGRATION ===
        if self.ml_predictor and ML_ENABLED:
            try:
                # Get ML probability prediction
                ml_probability = self.ml_predictor.predict_probability(signal["ai_features"])
                signal["ml_probability"] = round(ml_probability, 4)
                
                # Create hybrid score: 40% rules + 60% ML
                rules_score = signal["score"]
                ml_score = ml_probability * 100
                hybrid_score = (rules_score * (1 - ML_HYBRID_SCORE_WEIGHT)) + (ml_score * ML_HYBRID_SCORE_WEIGHT)
                
                signal["score_breakdown"] = {
                    "rules_score": rules_score,
                    "ml_score": round(ml_score, 2),
                    "hybrid_score": round(hybrid_score, 2),
                    "ml_probability": round(ml_probability, 4)
                }
                
                # Update final score with hybrid
                signal["score"] = round(hybrid_score, 2)
                signal["rating"] = get_score_rating(signal["score"])
                signal["emoji"] = get_score_emoji(signal["score"])
                
                print(f"[ML] {symbol} - Rules: {rules_score}% | ML: {ml_score:.1f}% | Hybrid: {hybrid_score:.1f}%", flush=True)
                
            except Exception as e:
                print(f"[ML ERROR] Failed to predict for {symbol}: {e}", flush=True)
                signal["ml_probability"] = None
        else:
            signal["ml_probability"] = None
        
        return signal
    
    def _capture_ai_features(self, symbol: str, analysis: Dict, best_signal: Dict) -> Dict:
        """
        Captura um instantâneo (snapshot) de métricas de mercado para treinamento de IA.
        Calcula as variações percentuais em vez de valores absolutos.
        """
        try:
            oi_latest = analysis["institutional"].get("oi_latest", 0)
            lsr_latest = analysis["institutional"].get("lsr_latest", 0)
            
            # Buscamos dados históricos para calcular Δ%
            oi_data = self.client.get_open_interest(symbol, "30min", 2)
            lsr_data = self.client.get_long_short_ratio(symbol, "30min", 2)
            
            oi_change = 0
            if len(oi_data) > 1:
                prev_oi = oi_data[1]["openInterest"]
                if prev_oi > 0:
                    oi_change = (oi_latest - prev_oi) / prev_oi
            
            lsr_change = 0
            if len(lsr_data) > 1:
                prev_lsr = lsr_data[1]["ratio"]
                if prev_lsr > 0:
                    lsr_change = (lsr_latest - prev_lsr) / prev_lsr
            
            # Volatilidade Relativa
            current_price = analysis.get("current_price", 0)
            atr = analysis["pivot_trend"]["details"].get("atr", 0)
            volatility = (atr / current_price) if current_price > 0 else 0
            
            return {
                "oi_change_pct": round(oi_change * 100, 4),
                "lsr_change_pct": round(lsr_change * 100, 4),
                "cvd_delta": analysis["institutional"].get("cvd", 0),
                "rs_score": best_signal.get("rs_score", 0),
                "volatility_idx": round(volatility * 100, 4),
                "master_score": best_signal.get("score", 0),
                "trend_aligned": 1 if best_signal.get("trend_4h_aligned") else 0,
                "rsi_value": analysis["rsi_bb"].get("current_value", 50)
            }
        except Exception as e:
            print(f"[AI LOGGER ERROR] {symbol}: {e}", flush=True)
            return {}

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
                        # ML-Based Filtering (if ML enabled)
                        if ML_ENABLED and self.ml_predictor and signal.get("ml_probability") is not None:
                            # If ML probability is below threshold, block the signal
                            if signal["ml_probability"] < ML_PROBABILITY_THRESHOLD:
                                print(f"[ML FILTER] {symbol} probability {signal['ml_probability']:.2%} < {ML_PROBABILITY_THRESHOLD:.0%}, bloqueado", flush=True)
                                continue
                            # If ML approves (>= threshold), allow signal even if score < 100%
                            print(f"[ML APPROVED] {symbol} - ML: {signal['ml_probability']:.2%} >= {ML_PROBABILITY_THRESHOLD:.0%}", flush=True)
                        else:
                            # No ML: Apply original rule (score must be 100%)
                            if signal["score"] < 100:
                                print(f"[SKIP] {symbol} score {signal['score']:.1f}% < 100%, não será monitorado", flush=True)
                                continue
                        
                        self.active_signals[symbol] = signal
                        new_signals.append(signal)
                        sig_type = signal['signal_type'].replace('_', ' ')
                        ml_info = f" | ML: {signal['ml_probability']:.2%}" if signal.get('ml_probability') else ""
                        print(f"[NEW SIGNAL] {symbol} {signal['direction']} ({sig_type}) Score: {signal['score']:.1f}%{ml_info}", flush=True)
                        self.save_signal_to_db(signal) # Save on new signal
                
                # Periodic cleanup of history (every scan)
                self.cleanup_history()

                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[SCAN ERROR] {symbol}: {e}", flush=True)
                continue
        
        # Summary after scan
        active_count = len(self.active_signals)
        print(f"[SCAN] Complete. Found {len(new_signals)} new signals. Total active: {active_count}", flush=True)
        
        # Check if ML model should be retrained
        if ML_ENABLED and self.ml_predictor and self.ml_predictor.should_retrain():
            print("[ML] Auto-retrain triggered...", flush=True)
            try:
                metrics = self.ml_predictor.train_model(min_samples=ML_MIN_SAMPLES)
                if metrics.get("status") == "SUCCESS":
                    print(f"[ML] ✅ Auto-retrain complete - Accuracy: {metrics['metrics']['accuracy']:.2%}", flush=True)
            except Exception as e:
                print(f"[ML ERROR] Auto-retrain failed: {e}", flush=True)
        
        return new_signals
    
    def get_active_signals(self) -> List[Dict]:
        """Get all currently active signals with freshness check"""
        current_time = int(time.time() * 1000)
        initial_count = len(self.active_signals)
        active_list = []
        to_remove = []  # Collect symbols to remove to avoid dict modification during iteration
        
        # We also need to update the entry zone for display
        for symbol, signal in list(self.active_signals.items()):
            # 1. Freshness Check (Expire older than 2 hours)
            minutes_active = (current_time - signal["timestamp"]) / (1000 * 60)
            if minutes_active > SIGNAL_TTL_MINUTES:
                print(f"[AUTO-CLEANUP] Expiring {symbol} {int(minutes_active)}m old (descartado)", flush=True)
                signal["status"] = "EXPIRED"
                signal["exit_timestamp"] = current_time
                self.save_signal_to_db(signal) # REGRA: Agora salvamos EXPIRED para análise de IA
                to_remove.append(symbol)
                continue
            
            # 2. Update Entry Zone (Best effort)
            try:
                # Get current price
                ticker = self.client.get_ticker(symbol)
                if ticker:
                    current_price = ticker["lastPrice"]
                    entry_price = signal["entry_price"]
                    direction = signal["direction"]
                    
                    dist_pct = (current_price - entry_price) / entry_price
                    if direction == "SHORT": dist_pct = -dist_pct
                    
                    # Missed Entry Check
                    if dist_pct < -ENTRY_MISSED_PERCENT:
                        print(f"[AUTO-CLEANUP] Expiring {symbol} (Missed Entry - descartado)", flush=True)
                        signal["status"] = "EXPIRED"
                        signal["exit_timestamp"] = current_time
                        self.save_signal_to_db(signal) # REGRA: Salvar no DB para histórico completo
                        to_remove.append(symbol)
                        continue

                    # Zone update
                    if abs(dist_pct) <= ENTRY_ZONE_IDEAL:
                        signal["entry_zone"] = "IDEAL"
                    elif dist_pct < -ENTRY_ZONE_IDEAL:
                        signal["entry_zone"] = "WAIT"
                    elif dist_pct > ENTRY_ZONE_LATE:
                        signal["entry_zone"] = "LATE"
                    else:
                        signal["entry_zone"] = "NEAR"
            except Exception as e:
                print(f"[ERROR] Updating zone for {symbol}: {e}", flush=True)
                
            active_list.append(signal)
        
        # Remove expired signals after iteration completes
        for symbol in to_remove:
            if symbol in self.active_signals:
                del self.active_signals[symbol]
        
        # Custom sort: Entry Zone Priority (IDEAL > WAIT > NEAR > LATE) then by Score
        def sort_priority(sig):
            zone_weights = {"IDEAL": 4, "WAIT": 3, "NEAR": 2, "LATE": 1}
            zone_weight = zone_weights.get(sig.get("entry_zone"), 0)
            return (zone_weight, sig["score"])

        return sorted(active_list, key=sort_priority, reverse=True)
    
    def get_signal_history(self, limit: int = 50, hours_limit: int = 0) -> List[Dict]:
        """Get signal history (most recent first) with optional time filtering"""
        filtered_history = self.signal_history
        
        if hours_limit > 0:
            current_time = int(time.time() * 1000)
            cutoff = current_time - (hours_limit * 60 * 60 * 1000)
            filtered_history = [s for s in self.signal_history if s.get("timestamp", 0) > cutoff]
            
        return filtered_history[-limit:][::-1]
    
    def clear_signal(self, symbol: str):
        """Remove a signal from active signals"""
        if symbol in self.active_signals:
            del self.active_signals[symbol]
    
    def cleanup_history(self):
        """Remove signals from history older than HISTORY_RETENTION_HOURS"""
        current_time = int(time.time() * 1000)
        max_age_ms = HISTORY_RETENTION_HOURS * 60 * 60 * 1000
        
        # We only remove FINALIZED signals from history. 
        # Active signals are handled by clear_expired_signals if needed, 
        # but history should keep only recent results.
        original_count = len(self.signal_history)
        self.signal_history = [
            s for s in self.signal_history 
            if s.get("status", "ACTIVE") != "ACTIVE" and (current_time - s.get("timestamp", 0)) < max_age_ms
        ]
        
        removed = original_count - len(self.signal_history)
        if removed > 0:
            print(f"[CLEANUP] Removed {removed} old signals from history", flush=True)

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
        
        if expired:
            self.save_state()
            
        return len(expired)

    def save_signal_to_db(self, signal: Dict):
        """Salva um sinal individual no banco de dados"""
        try:
            self.db.save_signal(signal)
        except Exception as e:
            print(f"[DB ERROR] Erro ao persistir sinal: {e}", flush=True)

    def save_state(self):
        """Save active signals and history to disk (Legacy - now uses DB for individual signals)"""
        # Mantemos o método para não quebrar chamadas existentes, mas agora é redundante 
        # para sinais novos que são salvos individualmente.
        pass

    def load_state(self):
        """Load active signals and history from Supabase"""
        try:
            print("[LOAD] Recarregando estado do Supabase...", flush=True)
            self.active_signals = self.db.get_active_signals()
            self.signal_history = self.db.get_signal_history(limit=HISTORY_RETENTION_HOURS * 2) # Estimativa
            print(f"[LOAD] Estado carregado: {len(self.active_signals)} ativos, {len(self.signal_history)} histórico", flush=True)
        except Exception as e:
            print(f"[LOAD ERROR] Falha ao carregar estado: {e}", flush=True)

    def monitor_active_signals(self):
        """Monitor active signals for TP, SL, or Volume Climax hits"""
        if not self.active_signals:
            return []
            
        print(f"[MONITOR] Checking {len(self.active_signals)} active signals...", flush=True)
        
        # Get all tickers in one call for efficiency
        tickers = self.client.get_all_tickers()
        if not tickers:
            return []
            
        ticker_map = {t["symbol"]: t for t in tickers}
        
        finalized = []
        current_time = int(time.time() * 1000)
        
        for symbol, signal in list(self.active_signals.items()):
            ticker = ticker_map.get(symbol)
            if not ticker:
                continue
                
            current_price = float(ticker["lastPrice"])
            entry_price = signal["entry_price"]
            tp = signal["take_profit"]
            sl = signal["stop_loss"]
            direction = signal["direction"]
            
            hit = False
            status = "ACTIVE"
            
            # 1. Standard TP/SL Check (Real-time trigger)
            if direction == "LONG":
                if current_price >= tp:
                    hit, status = self._verify_with_klines(symbol, direction, entry_price, tp, sl)
                elif current_price <= sl:
                    hit, status = self._verify_with_klines(symbol, direction, entry_price, tp, sl)
            else: # SHORT
                if current_price <= tp:
                    hit, status = self._verify_with_klines(symbol, direction, entry_price, tp, sl)
                elif current_price >= sl:
                    hit, status = self._verify_with_klines(symbol, direction, entry_price, tp, sl)
            
            # 2. Expiration Checks (TTL and Price Distance)
            if not hit:
                # TTL Expiration (Default 2 hours)
                minutes_active = (current_time - signal["timestamp"]) / (1000 * 60)
                if minutes_active > SIGNAL_TTL_MINUTES:
                    hit = True
                    status = "EXPIRED"
                    # Calculate ROI at expiration for records
                    roi = self._calculate_roi(direction, entry_price, current_price)
                    signal["final_roi"] = round(roi, 2)
                    print(f"[EXPIRED] {symbol} expired after {int(minutes_active)} minutes (ROI: {roi:.2f}%)", flush=True)

                # Price Distance "Missed Entry" Check
                # If price moves too far AGAINST or too far TOWARDS TP without entering
                dist_pct = (current_price - entry_price) / entry_price
                if direction == "SHORT":
                    dist_pct = -dist_pct
                
                # If price drops > ENTRY_MISSED_PERCENT (1%) against us, expire it
                if dist_pct < -ENTRY_MISSED_PERCENT:
                    hit = True
                    status = "EXPIRED"
                    roi = self._calculate_roi(direction, entry_price, current_price)
                    signal["final_roi"] = round(roi, 2)
                    signal["exit_timestamp"] = current_time
                    self.save_signal_to_db(signal) # Salvar no DB
                    print(f"[EXPIRED] {symbol} missed entry (price moved against trade)", flush=True)
                
            # 3. Volume Climax Check - DISABLED
            # Reason: We want to always hit the 2% TP target, not exit early
            # if not hit:
            #     in_profit = (direction == "LONG" and current_price > entry_price) or \
            #                (direction == "SHORT" and current_price < entry_price)
            #     
            #     if in_profit:
            #         klines = self.client.get_klines(symbol, "30", 2)
            #         if len(klines) >= 2:
            #             current_vol = klines[-1]["volume"]
            #             if current_vol > klines[-2]["volume"] * VOLUME_CLIMAX_THRESHOLD:
            #                 hit = True
            #                 status = "VOL_CLIMAX"
            #                 print(f"[EXIT] Volume Climax detected for {symbol}!", flush=True)

            # 4. Update Entry Zone (for UI guidance)
            if not hit:
                dist_pct = (current_price - entry_price) / entry_price
                if direction == "SHORT": dist_pct = -dist_pct

                if abs(dist_pct) <= ENTRY_ZONE_IDEAL:
                    signal["entry_zone"] = "IDEAL"
                elif dist_pct < -ENTRY_ZONE_IDEAL:
                    signal["entry_zone"] = "WAIT" # Price is better than entry, wait for confirmation/pullback
                elif dist_pct > ENTRY_ZONE_LATE:
                    signal["entry_zone"] = "LATE"
                else:
                    signal["entry_zone"] = "NEAR"
                    
            if hit:
                # Update signal object
                signal["status"] = status
                signal["exit_price"] = current_price
                signal["exit_timestamp"] = current_time
                signal["exit_timestamp_readable"] = datetime.now(self.tz).strftime("%Y-%m-%d %H:%M:%S")
                
                # Remove from active signals
                del self.active_signals[symbol]
                
                roi = self._calculate_roi(direction, entry_price, current_price)
                signal["final_roi"] = round(roi, 2)
                
                # REGRA: Todos os sinais finalizados vão para o histórico local (se recente) e DB
                if status in ["TP_HIT", "SL_HIT"]:
                    self.signal_history.append(signal)
                    finalized.append(signal)
                
                self.save_signal_to_db(signal) # Salva SEMPRE no Supabase
                print(f"[FINALIZED] {symbol} {status} at ${current_price} (ROI: {roi:.2f}%) - Persistido no DB", flush=True)
                
        return finalized
    
    def _verify_with_klines(self, symbol: str, direction: str, entry: float, tp: float, sl: float) -> tuple:
        """
        Realiza uma auditoria fina usando candles de 1 minuto para confirmar 
        qual alvo (TP ou SL) foi atingido primeiro.
        """
        try:
            # Pegamos as últimas candles de 1min (cobertura de 60 min)
            klines = self.client.get_klines(symbol, "1", 60)
            if not klines:
                return True, "TP_HIT" if direction == "LONG" else "SL_HIT" # Fallback para o trigger original

            for candle in klines:
                high = candle["high"]
                low = candle["low"]

                if direction == "LONG":
                    # Se em 1min a mínima atingiu o SL antes/junto com a máxima atingindo o TP
                    # Marcamos como SL para sermos conservadores no treinamento da IA
                    if low <= sl:
                        return True, "SL_HIT"
                    if high >= tp:
                        return True, "TP_HIT"
                else: # SHORT
                    if high >= sl:
                        return True, "SL_HIT"
                    if low <= tp:
                        return True, "TP_HIT"
            
            # Se não encontrou nas candles (delay de API?), mantém o trigger original
            return True, "TP_HIT" # Assume TP por padrão
        except Exception as e:
            print(f"[VERIFY ERROR] {symbol}: {e}", flush=True)
            return True, "TP_HIT"

    def _calculate_roi(self, direction: str, entry: float, exit: float) -> float:
        """Helper to calculate percentage ROI"""
        if entry == 0: return 0
        if direction == "LONG":
            return ((exit - entry) / entry) * 100
        else:
            return ((entry - exit) / entry) * 100

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
