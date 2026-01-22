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
import io

# FORCE UTF-8 STDOUT/STDERR FOR WINDOWS
try:
    if os.name == 'nt' and (not hasattr(sys.stdout, 'encoding') or sys.stdout.encoding.lower() != 'utf-8'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except (AttributeError, io.UnsupportedOperation):
    pass

from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT,
    RS_MIN_THRESHOLD, VOLUME_CLIMAX_THRESHOLD,
    HISTORY_RETENTION_HOURS, SIGNAL_TTL_MINUTES,
    ENTRY_ZONE_IDEAL, ENTRY_ZONE_LATE, ENTRY_MISSED_PERCENT,
    ML_ENABLED, ML_PROBABILITY_THRESHOLD, ML_MIN_SAMPLES,
    ML_AUTO_RETRAIN_INTERVAL, ML_MODEL_PATH, ML_METRICS_PATH,
    ML_HYBRID_SCORE_WEIGHT, DECOUPLING_SCORE_BONUS,
    PARTIAL_TP_PERCENT, TRAILING_STOP_TRIGGER, TRAILING_STOP_DISTANCE, TARGET_SNIPER_6,
    SNIPER_FORCE_TARGET, SNIPER_DECOUPLING_THRESHOLD, SNIPER_BEST_SCORE_THRESHOLD,
    LLM_ENABLED, LLM_MODEL, LLM_VALIDATE_SIGNALS, LLM_OPTIMIZE_TP,
    LLM_MONITOR_EXITS, LLM_CACHE_TTL_SECONDS, LLM_MIN_CONFIDENCE,
    MIN_SCORE_TO_SAVE
)

import json

print("[SG] Importing bybit_client...", flush=True)
from services.bybit_client import BybitClient
print("[SG] bybit_client imported OK", flush=True)

print("[SG] Importing indicator_calculator...", flush=True)
from services.indicator_calculator import analyze_candles
print("[SG] indicator_calculator imported OK", flush=True)

print("[SG] Importing sr_detector...", flush=True)
from services.sr_detector import get_all_sr_levels, check_sr_proximity, get_sr_alignment
print("[SG] sr_detector imported OK", flush=True)

print("[SG] Importing signal_scorer...", flush=True)
from services.signal_scorer import calculate_signal_score, get_score_rating, get_score_emoji
print("[SG] signal_scorer imported OK", flush=True)

print("[SG] Importing database_manager...", flush=True)
from services.database_manager import DatabaseManager
print("[SG] database_manager imported OK", flush=True)

print("[SG] Importing ml_predictor...", flush=True)
from services.ml_predictor import MLPredictor
print("[SG] ml_predictor imported OK", flush=True)

print("[SG] Importing btc_regime_tracker...", flush=True)
from services.btc_regime_tracker import BTCRegimeTracker
print("[SG] btc_regime_tracker imported OK", flush=True)

print("[SG] Importing llm_trading_brain...", flush=True)
from services.llm_trading_brain import LLMTradingBrain
print("[SG] llm_trading_brain imported OK", flush=True)

print("[SG] Importing news_service...", flush=True)
from services.news_service import news_service
print("[SG] news_service imported OK", flush=True)

print("[SG] Importing rag_memory...", flush=True)
from services.rag_memory import RAGMemory
print("[SG] rag_memory imported OK", flush=True)

from services.llm_agents.adaptive_bias_agent import AdaptiveBiasAgent
from services.llm_agents.liquidity_sentinel_agent import LiquiditySentinelAgent
from services.llm_agents.strategist_agent import StrategistAgent
from services.llm_agents.portfolio_governor_agent import PortfolioGovernorAgent
from services.llm_agents.portfolio_governor_agent import PortfolioGovernorAgent
from services.llm_agents.global_anchor_agent import GlobalAnchorAgent
from services.bankroll_manager import BankrollManager


# ============================================================================
# UTILITY FUNCTIONS (Module Level)
# ============================================================================

def _sanitize_obj(obj):
    """Recursively convert Decimal to float and handle other non-serializable types"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: _sanitize_obj(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_obj(v) for v in obj]
    return obj

def round_step(price: float, step: float) -> float:
    """Round price to the nearest step size (tick size)"""
    if step <= 0:
        step = 0.000001
    return round(round(price / step) * step, 8)



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
        
        # INFO: Se ML está habilitado mas modelo não treinado, sistema funciona em modo fallback
        if ML_ENABLED:
            if not self.ml_predictor or not self.ml_predictor.model:
                print("\n" + "="*80, flush=True)
                print("[!] AVISO: ML esta habilitado mas o modelo ainda nao foi treinado.", flush=True)
                print("="*80, flush=True)
                print("\nO sistema vai funcionar em MODO FALLBACK (apenas regras, sem ML).", flush=True)
                print("Quando houver 100+ amostras finalizadas, o modelo sera treinado automaticamente.", flush=True)
                print("="*80 + "\n", flush=True)
            else:
                print("[ML] [OK] Modelo ML carregado com sucesso!", flush=True)
        
        # Initialize BTC Regime Tracker
        self.btc_tracker = BTCRegimeTracker()
        self.current_btc_regime = "TRENDING"
        self.current_regime_details = {}
        print("[BTC REGIME] [OK] Tracker inicializado", flush=True)
        
        # Sentiment Cache (News)
        self.market_sentiment = {"score": 50, "sentiment": "NEUTRAL", "summary": "Initializing..."}
        self.last_sentiment_update = 0
        self.sentiment_update_interval = 900  # 15 minutes
        
        
        # Initialize RAG Memory (Visual Memory Engine)
        self.rag_memory = RAGMemory(storage_path="data/memory_index.json")
        print("[RAG] [OK] RAG Memory Engine inicializado", flush=True)

        # Initialize Specialized Agents (Scout & Sentinel)
        self.scout_agent = AdaptiveBiasAgent()
        self.sentinel_agent = LiquiditySentinelAgent()
        
        # Initialize Intelligence Agents (Strategist, Governor, Anchor)
        self.strategist_agent = StrategistAgent()
        self.governor_agent = PortfolioGovernorAgent()
        self.strategist_agent = StrategistAgent()
        self.governor_agent = PortfolioGovernorAgent()
        self.anchor_agent = GlobalAnchorAgent()
        
        # Initialize Bankroll Manager (The Elite Simulator)
        self.bankroll_manager = BankrollManager(self.db, self.client)
        
    def set_push_service(self, push_service):
        """Inject push service into relevant managers"""
        self.bankroll_manager.push_service = push_service
        print("[SG] PushService injected into BankrollManager", flush=True)
        
        # State for Intelligence
        self.global_macro_context = {"confidence_multiplier": 1.0, "global_sentiment": "NEUTRAL"}
        self.strategist_report = {}
        
        print("[AGENTS] [OK] Intelligence Neural Layer inicializada", flush=True)

        # Initialize LLM Trading Brain (Gemini)
        if LLM_ENABLED:
            llm_config = {
                "LLM_MODEL": LLM_MODEL,
                "LLM_CACHE_TTL_SECONDS": LLM_CACHE_TTL_SECONDS,
                "LLM_MIN_CONFIDENCE": LLM_MIN_CONFIDENCE
            }
            # Inject RAG Memory into LLM Brain (Shared Instance)
            self.llm_brain = LLMTradingBrain(llm_config, rag_memory=self.rag_memory)
            if self.llm_brain.is_enabled():
                self.llm_brain.set_database_manager(self.db) 
                print("[LLM] [OK] LLM Trading Brain inicializado com Gemini", flush=True)
            else:
                print("[LLM] [WARN] LLM habilitado mas Gemini nao disponivel - usando fallback", flush=True)
        else:
            self.llm_brain = None
            print("[LLM] [INFO] LLM Trading Brain desabilitado", flush=True)
        
        self.system_ready = False # Flag for Async Initialization
        
        self.load_state()

    def _update_market_sentiment(self):
        """Update market sentiment from news if interval passed"""
        if not self.llm_brain or not self.llm_brain.is_enabled():
            return

        try:
            if time.time() - self.last_sentiment_update > self.sentiment_update_interval:
                print(f"[SENTIMENT] Updating market sentiment...", flush=True)
                headlines = news_service.get_latest_headlines(limit=15)
                analysis = self.llm_brain.analyze_market_sentiment(headlines)
                
                self.market_sentiment = analysis
                self.last_sentiment_update = time.time()
                print(f"[SENTIMENT] [OK] Updated: {analysis.get('sentiment')} ({analysis.get('score')})", flush=True)
        except Exception as e:
            print(f"[SENTIMENT] [WARN] Failed to update: {e}", flush=True)

    def set_system_ready(self, status: bool):
        """Set system readiness status (called after ML training)"""
        self.system_ready = status
        print(f"[SYSTEM] System Ready Status set to: {status}", flush=True)
    
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
        best_signal = None
        
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
        
        # === NEW: MULTI-TIMEFRAME (MTF) CONFLUENCE ===
        # For Elite Banca signals, we monitor higher timeframes to capture real rompimentos
        mtf_confluence = self._check_mtf_confluence(symbol, trend_4h)
        best_signal["mtf_confluence"] = mtf_confluence
        
        # Calculate SL and TP DYNAMICALLY based on BTC regime
        tp_pct, sl_pct = self.btc_tracker.get_dynamic_targets(self.current_btc_regime)
        
        # Calculate decoupling score (Always, for ML and Turbo logic)
        decoupling_score = 0.0
        if self.current_btc_candles:
            decoupling_score = self.btc_tracker.calculate_decoupling_score(
                candles_30m, self.current_btc_candles
            )

        # [TURBO STRATEGY] If Alt is Decoupled (>0.6), force BREAKOUT targets regardless of regime
        if decoupling_score > 0.6:
            tp_pct, sl_pct = self.btc_tracker.get_dynamic_targets("BREAKOUT")
            print(f"[TURBO DECOUPLED] {symbol} (Score: {decoupling_score:.2f}) -> Forcing BREAKOUT targets (TP {tp_pct*100:.1f}%)", flush=True)

        # Add bonus to score for highly decoupled alts (especially valuable in RANGING)
        if decoupling_score > 0.5 and self.current_btc_regime == "RANGING":
            best_signal["score"] += DECOUPLING_SCORE_BONUS
            print(f"[DECOUPLING BONUS] {symbol} score +{DECOUPLING_SCORE_BONUS} (decoupling: {decoupling_score:.2f})", flush=True)
        
        # [SNIPER LOGIC] Determine if this signal qualifies for Sniper Mode (6% target)
        is_sniper_signal = False
        if self.current_btc_regime == "RANGING" and decoupling_score >= SNIPER_DECOUPLING_THRESHOLD:
            is_sniper_signal = True
            print(f"[SNIPER MODE] {symbol} (RANGING + Decoupled) -> Targeting 6%!", flush=True)
        elif self.current_btc_regime in ["TRENDING", "BREAKOUT"] and best_signal["score"] >= SNIPER_BEST_SCORE_THRESHOLD:
            is_sniper_signal = True
            print(f"[SNIPER MODE] {symbol} (TRENDING + High Score) -> Targeting 6%!", flush=True)

        # Get TP/SL targets (dynamic or sniper)
        # FORCE SNIPER TARGET (6%+) for all approved signals to allow "Surf"
        tp_pct, sl_pct = self.btc_tracker.get_dynamic_targets(self.current_btc_regime, force_sniper=is_sniper_signal)
        
        # Override to 6% if it's a sniper signal, ensuring consistency
        if is_sniper_signal:
            tp_pct = TARGET_SNIPER_6
        
        if best_signal["direction"] == "LONG":
            stop_loss = current_price * (1 - sl_pct)
            take_profit = current_price * (1 + tp_pct)
        else:  # SHORT
            stop_loss = current_price * (1 + sl_pct)
            take_profit = current_price * (1 - tp_pct)
        
        # Get tickSize for this symbol
        inst_info = self.instruments_info.get(symbol, {})
        tick_size = float(inst_info.get("tickSize", "0.000001"))
        # Note: Using module-level round_step() function

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
                "hunger_score": analysis["institutional"]["liquidity_hunt"]["details"].get("intensity_score", 1),
                "liquidity_aligned": score_result.get("confirmations", {}).get("liquidity_aligned", False),
                "liquidity_details": analysis["institutional"]["liquidity_hunt"]["details"]
            },
            "ai_features": self._capture_ai_features(symbol, analysis, best_signal, decoupling_score),
            # BTC Regime Tracking
            "btc_regime": self.current_btc_regime,
            "is_sniper": is_sniper_signal,
            "dynamic_targets": {
                "tp_pct": round(tp_pct * 100, 2),
                "sl_pct": round(sl_pct * 100, 2)
            },
            "decoupling_score": round(decoupling_score, 3) if decoupling_score > 0 else None,
            "trailing_stop_active": False,
            "mtf_confluence": best_signal.get("mtf_confluence")
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
        
        # === LLM INTELLIGENCE LAYER ===
        if self.llm_brain and LLM_ENABLED:
            market_context = {
                "btc_regime": self.current_btc_regime,
                "decoupling_score": decoupling_score,
                "regime_details": self.current_regime_details,
                "sentiment_score": self.market_sentiment.get("score", 50),
                "sentiment_summary": self.market_sentiment.get("summary", "Neutral")
            }
            
            # 1. Validate signal context with LLM
            if LLM_VALIDATE_SIGNALS:
                try:
                    llm_validation = self.llm_brain.validate_signal_context(signal, market_context)
                    signal["llm_validation"] = llm_validation
                    
                    # Store for UI (AI Page Audit)
                    self.last_council_debate = llm_validation
                    
                    if llm_validation.get("approved"):
                        print(f"[LLM] [OK] {symbol} aprovado (conf: {llm_validation.get('confidence', 0):.0%})", flush=True)
                    else:
                        print(f"[LLM] [WARN] {symbol} {llm_validation.get('suggested_action', 'SKIP')}: {llm_validation.get('reasoning', '')[:50]}", flush=True)
                except Exception as e:
                    print(f"[LLM ERROR] Validation failed for {symbol}: {e}", flush=True)
                    signal["llm_validation"] = None
            
            # 2. Suggest optimal TP with LLM
            if LLM_OPTIMIZE_TP:
                try:
                    tp_suggestion = self.llm_brain.suggest_optimal_tp(signal, market_context)
                    signal["llm_tp_suggestion"] = tp_suggestion
                    
                    if tp_suggestion.get("should_adjust") and tp_suggestion.get("suggested_tp_pct"):
                        original_tp = signal.get("dynamic_targets", {}).get("tp_pct", 2.0)
                        suggested_tp = tp_suggestion["suggested_tp_pct"]
                        
                        # Only adjust if suggestion is significantly different (>0.5%)
                        if abs(suggested_tp - original_tp) >= 0.5:
                            # Recalculate TP based on suggestion
                            new_tp_pct = suggested_tp / 100  # Convert to decimal
                            if signal["direction"] == "LONG":
                                signal["take_profit"] = round_step(current_price * (1 + new_tp_pct), tick_size)
                            else:
                                signal["take_profit"] = round_step(current_price * (1 - new_tp_pct), tick_size)
                            
                            signal["dynamic_targets"]["tp_pct"] = suggested_tp
                            signal["dynamic_targets"]["tp_adjusted_by_llm"] = True
                            print(f"[LLM] [TP] {symbol} TP ajustado: {original_tp:.1f}% -> {suggested_tp:.1f}%", flush=True)
                except Exception as e:
                    print(f"[LLM ERROR] TP optimization failed for {symbol}: {e}", flush=True)
                    signal["llm_tp_suggestion"] = None
        
        # === EAGLE ELITE TAGGING ===
        # If signal has high score and MTF confluence, tag it as Eagle Elite
        mtf_data = signal.get("mtf_confluence", {})
        mtf_score = mtf_data.get("total_score", 0)
        
        if signal["score"] >= 70:
            print(f"[MTF] {symbol} Confluence Score: {mtf_score}/3", flush=True)

        if signal["score"] >= 65 and mtf_score >= 1:
            signal["is_eagle_elite"] = True
            print(f"[EAGLE ELITE] 🦅 {symbol} identified with high MTF confluence!", flush=True)
        else:
            signal["is_eagle_elite"] = False

        return signal

    def _check_mtf_confluence(self, symbol: str, trend_4h: str) -> Dict:
        """
        Análise Cirúrgica de Múltiplos Timeframes (4H, 2H, 1H, 30M)
        Busca alinhamento total para 'surfar' grandes movimentos de 6%+.
        """
        try:
            # Fetch additional klines
            klines_2h = self.client.get_klines(symbol, "120", 50)
            klines_1h = self.client.get_klines(symbol, "60", 50)
            
            if not klines_2h or not klines_1h:
                return {"total_score": 0, "details": "Insufficient data"}

            # Analyze 2H Structure
            # Simplified structure check: SMA 20 vs SMA 50 equivalent
            close_2h = [c["close"] for c in klines_2h]
            sma20_2h = sum(close_2h[-20:]) / 20
            sma50_2h = sum(close_2h[-50:]) / 50
            trend_2h = "UPTREND" if sma20_2h > sma50_2h else "DOWNTREND"

            # Analyze 1H Structure (Looking for actual breakout)
            close_1h = [c["close"] for c in klines_1h]
            sma20_1h = sum(close_1h[-20:]) / 20
            # Check for "Engulfing" or strength in the last 2 candles
            recent_strength = close_1h[-1] > close_1h[-2] if trend_4h == "UPTREND" else close_1h[-1] < close_1h[-2]

            score = 0
            if trend_2h == trend_4h: score += 1
            if (trend_4h == "UPTREND" and close_1h[-1] > sma20_1h) or (trend_4h == "DOWNTREND" and close_1h[-1] < sma20_1h):
                score += 1
            if recent_strength: score += 1

            return {
                "total_score": score, # Max 3
                "trend_2h": trend_2h,
                "trend_1h_aligned": (trend_4h == "UPTREND" and close_1h[-1] > sma20_1h) or (trend_4h == "DOWNTREND" and close_1h[-1] < sma20_1h),
                "recent_strength": recent_strength
            }
        except Exception as e:
            print(f"[MTF ERROR] {symbol}: {e}", flush=True)
            return {"total_score": 0, "error": str(e)}
    def _update_active_signals_prices(self):

        """
        Batch update current prices for all active signals.
        This avoids N network calls in get_active_signals (read path).
        """
        if not self.active_signals:
            return

        try:
            # Batch fetch all tickers (Bybit v5 supports category=linear)
            # Fetching all is often faster than N individual calls
            tickers = self.client.get_all_tickers()
            
            # Create a lookup map
            price_map = {t["symbol"]: float(t["lastPrice"]) for t in tickers if "symbol" in t and "lastPrice" in t}
            
            # Update our active signals in memory
            for symbol, signal in self.active_signals.items():
                if symbol in price_map:
                    current_price = price_map[symbol]
                    signal["current_price"] = current_price # Store for frontend if needed
                    
                    # Recalculate entry zone
                    entry_price = signal["entry_price"]
                    direction = signal["direction"]
                    
                    dist_pct = (current_price - entry_price) / entry_price
                    if direction == "SHORT": dist_pct = -dist_pct
                    
                    # Zone update logic
                    if abs(dist_pct) <= ENTRY_ZONE_IDEAL:
                        signal["entry_zone"] = "IDEAL"
                    elif dist_pct < -ENTRY_ZONE_IDEAL:
                        signal["entry_zone"] = "WAIT"
                    elif dist_pct > ENTRY_ZONE_LATE:
                        signal["entry_zone"] = "LATE"
                    else:
                        signal["entry_zone"] = "NEAR"
                        
                    # Also update ROI for display if needed
                    if signal.get("status") not in ["TP_HIT", "SL_HIT"]:
                         if direction == "LONG":
                             roi = (current_price - entry_price) / entry_price
                         else:
                             roi = (entry_price - current_price) / entry_price
                         signal["current_roi"] = roi * 100
                         
        except Exception as e:
            print(f"[PRICE UPDATE ERROR] Failed to batch update prices: {e}", flush=True)

    def _capture_ai_features(self, symbol: str, analysis: Dict, best_signal: Dict, decoupling_score: float = 0.0) -> Dict:
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
            pivot_data = analysis.get("pivot_trend", {})
            atr = pivot_data.get("details", {}).get("atr", 0)
            volatility = (atr / current_price) if current_price > 0 else 0
            
            # Encode BTC Regime for ML
            # 1 = RANGING, 2 = TRENDING, 3 = BREAKOUT
            regime_map = {"RANGING": 1, "TRENDING": 2, "BREAKOUT": 3}
            regime_val = regime_map.get(self.current_btc_regime, 2)  # Default to TRENDING

            # 1. Base indicators
            rsi_bb = analysis.get("rsi_bb", {})
            rsi_val = rsi_bb.get("current_value", 50)
            
            # 2. Institutional
            inst = analysis.get("institutional", {})
            cvd = inst.get("cvd", 0)
            
            # Encode BTC Regime for ML
            # 1 = RANGING, 2 = TRENDING, 3 = BREAKOUT
            regime_map = {"RANGING": 1, "TRENDING": 2, "BREAKOUT": 3}
            regime_val = regime_map.get(self.current_btc_regime, 2)  # Default to TRENDING

            return {
                "oi_change_pct": round(oi_change * 100, 4),
                "lsr_change_pct": round(lsr_change * 100, 4),
                "cvd_delta": cvd,
                "rs_score": best_signal.get("rs_score", 0),
                "volatility_idx": round(volatility * 100, 4),
                "master_score": best_signal.get("score", 0),
                "trend_aligned": 1 if best_signal.get("trend_4h_aligned") else 0,
                "rsi_value": rsi_val,
                "btc_regime_val": regime_val,
                "decoupling_score": decoupling_score
            }
        except Exception as e:
            print(f"[AI LOGGER ERROR] {symbol}: {e}", flush=True)
            return {}

    def scan_all_pairs(self) -> List[Dict]:
        """Core engine: Scans all monitored pairs and generates signals"""
        if not self.system_ready:
            print("[SCAN] System not ready. Skipping.", flush=True)
            return []

        new_signals = []
        total_pairs = len(self.monitored_pairs)
        
        print(f"[SCAN] Starting scan of {total_pairs} pairs...", flush=True)
        
        # Fetch BTC candles once for RS calculation
        # Sentiment update moved to after regime detection
        
        try:
            self.current_btc_candles = self.client.get_klines("BTCUSDT", "30", 100)
        except:
            self.current_btc_candles = None
        
        # Detect BTC market regime
        try:
            btc_4h = self.client.get_klines("BTCUSDT", "240", 50)
            self.current_btc_regime, self.current_regime_details = self.btc_tracker.detect_regime(
                self.current_btc_candles, btc_4h
            )
            regime_info = self.btc_tracker.get_regime_info()
            print(f"[BTC REGIME] {self.current_btc_regime} | TP: {regime_info['tp_pct']:.1f}% | SL: {regime_info['sl_pct']:.1f}%", flush=True)
        except Exception as e:
            print(f"[BTC REGIME] Error detecting regime: {e}", flush=True)
            self.current_btc_regime = "TRENDING"
            
        # Update market sentiment if needed
        self._update_market_sentiment()

        # === 1. MACRO ANCHOR ANALYSIS ===
        # Run after regime detection to have BTC price and latest sentiment
        if LLM_ENABLED:
            try:
                macro_data = {
                    "btc_price": self.current_regime_details.get("current_price", 0),
                    "market_sentiment": getattr(self, "market_sentiment", {}).get("sentiment", "NEUTRAL"),
                    "dxy_trend": "STABLE",
                    "sp500_status": "NORMAL"
                }
                anchor_res = self.anchor_agent.analyze_macro_context(macro_data, lambda p: self.llm_brain.call_gemini(p))
                self.global_macro_context = anchor_res
                print(f"[ANCHOR] Global Sentiment: {anchor_res.get('global_sentiment')} (Conf Multiplier: {anchor_res.get('confidence_multiplier')})", flush=True)
            except Exception as e:
                print(f"[ANCHOR ERROR] Macro analysis failed: {e}", flush=True)
            
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
                        ml_approved = False
                        
                        if ML_ENABLED and self.ml_predictor and signal.get("ml_probability") is not None:
                            # If ML probability is below threshold, log it but check Technical Score as fallback
                            if signal["ml_probability"] < ML_PROBABILITY_THRESHOLD:
                                print(f"[ML FILTER] {symbol} probability {signal['ml_probability']:.2%} < {ML_PROBABILITY_THRESHOLD:.0%}, bloqueado temporariamente", flush=True)
                                # IMPORTANT: For training purposes, we might want to let high technical score signals pass even if ML is unsure?
                                # For now, we respect the ML lock.
                                continue
                            else:
                                # ML Approves
                                ml_approved = True
                                print(f"[ML APPROVED] {symbol} - ML: {signal['ml_probability']:.2%} >= {ML_PROBABILITY_THRESHOLD:.0%}", flush=True)
                        
                        # Technical Score Check
                        # [DATA COLLECTION] Use RAW Rules Score if available (don't let ML dilute it)
                        raw_score = signal.get("score_breakdown", {}).get("rules_score", signal["score"])
                        
                        if raw_score < MIN_SCORE_TO_SAVE:
                            print(f"[SKIP] {symbol} Raw Score {raw_score:.1f}% < {MIN_SCORE_TO_SAVE}%, nao sera monitorado", flush=True)
                            continue
                        
                        if signal:
                        # 4. PORTFOLIO GOVERNANCE CHECK
                        # Before adding to active, check if Governor allows it
                            if LLM_ENABLED:
                                gov_res = self.governor_agent.authorize_trade(
                                    signal, 
                                    list(self.active_signals.values()), 
                                    lambda p: self.llm_brain.call_gemini(p)
                                )
                                signal["governor_report"] = gov_res
                                if not gov_res.get("authorized", True):
                                    # [DATA COLLECTION MODE] Log warning but DO NOT BLOCK
                                    print(f"[GOVERNOR] ⚠️ Signal {symbol} NOT AUTHORIZED (Soft Veto): {gov_res.get('reasoning')} - Proceeding for Data Collection", flush=True)
                                    signal["governor_veto"] = True  # Tag it so we know it was vetoed
                                    # continue  <-- DISABLED FOR TRAINING
                                if gov_res.get("suggested_size_reduction", 0) > 0:
                                    print(f"[GOVERNOR] ⚠️ {symbol} size reduced by {gov_res.get('suggested_size_reduction')*100:.0f}%", flush=True)

                        # [SNIPER FILTER] Enforce strict selection rules
                        # [DATA COLLECTION] Use RAW Score for Sniper check too (allow signals with high Technical but low ML)
                        sniper_check_score = raw_score # Use the calculated raw_score from above
                        
                        if self.current_btc_regime == "RANGING":
                            # Only decoupled alts in Ranging
                            if signal.get("decoupling_score", 0) < SNIPER_DECOUPLING_THRESHOLD:
                                print(f"[SNIPER FILTER] {symbol} REJECTED: Decoupling Score ({signal.get('decoupling_score', 0)}) < {SNIPER_DECOUPLING_THRESHOLD} in RANGING market. (Strict Enforcement)", flush=True)
                                continue
                        elif self.current_btc_regime in ["TRENDING", "BREAKOUT"]:
                            # Only best scores in Trending
                            if sniper_check_score < SNIPER_BEST_SCORE_THRESHOLD:
                                print(f"[SNIPER FILTER] {symbol} REJECTED: Score ({sniper_check_score:.1f}) < {SNIPER_BEST_SCORE_THRESHOLD} in TRENDING market.", flush=True)
                                continue
                        
                        # LLM Intelligence Layer - additional validation (soft filter - logs warning but doesn't block)
                        llm_info = ""
                        if LLM_ENABLED and signal.get("llm_validation"):
                            llm_val = signal["llm_validation"]
                            llm_conf = llm_val.get("confidence", 0)
                            llm_info = f" | LLM: {llm_conf:.0%}"
                            if not llm_val.get("approved") and llm_conf >= LLM_MIN_CONFIDENCE:
                                # LLM disapproved but with good confidence - this is a warning
                                print(f"[LLM WARNING] {symbol} - LLM nao aprovou mas seguindo com sinal (conf: {llm_conf:.0%})", flush=True)
                        
                        self.active_signals[symbol] = signal
                        new_signals.append(signal)
                        sig_type = signal['signal_type'].replace('_', ' ')
                        ml_info = f" | ML: {signal['ml_probability']:.2%}" if signal.get('ml_probability') else ""
                        print(f"[NEW SIGNAL] {symbol} {signal['direction']} ({sig_type}) Score: {signal['score']:.1f}%{ml_info}{llm_info}", flush=True)
                        
                        # === BANKROLL MANAGER (SIMULATION) ===
                        # Assess if this signal qualifies for the Elite Bankroll
                        if self.bankroll_manager:
                            self.bankroll_manager.assess_signal(signal)
                            
                        self.save_signal_to_db(signal) # Save on new signal
                
                # Periodic cleanup of history (every scan)
                self.cleanup_history()
                

                # === 5. STRATEGIST REFLECTION ===
                # Every 20 scans or if history is fresh, run strategist
                if LLM_ENABLED and len(self.signal_history) >= 5:
                    # Run roughly once an hour (assuming 3 min scans)
                    if int(time.time()) % 20 == 0: 
                        print("[STRATEGIST] 🧠 Running post-mortem analysis...", flush=True)
                        report = self.strategist_agent.analyze_performance(
                            self.signal_history, 
                            lambda p: self.llm_brain.call_gemini(p)
                        )
                        self.strategist_report = report

                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                import traceback
                print(f"[SCAN ERROR] {symbol}: {e}", flush=True)
                traceback.print_exc()
                continue
        
        # === BATCH PRICE UPDATE ===
        # Update prices for all active signals (both new and old)
        # This ensures get_active_signals is fast (no network calls)
        self._update_active_signals_prices()

        # === UPDATE BANKROLL POSITIONS (Optimized) ===
        if self.bankroll_manager:
            # Re-use price_map from _update_active_signals_prices if possible or build from ticker_map
            # Actually, _update_active_signals_prices doesn't return the map, so we use ticker_map if it was built
            # But ticker_map is local to monitor_active_signals. Let's build a quick one here if needed.
            # Actually, let's just use what's available.
            tickers = self.client.get_all_tickers()
            price_map = {t["symbol"]: float(t["lastPrice"]) for t in tickers if "symbol" in t and "lastPrice" in t}
            self.bankroll_manager.update_positions(price_map)
        
        # Summary after scan
        active_count = len(self.active_signals)
        print(f"[SCAN] Complete. Found {len(new_signals)} new signals. Total active: {active_count}", flush=True)
        
        # Log why signals were skipped (to help user debugging)
        if not new_signals and total_pairs > 0:
             print(f"[SCAN INFO] Nenhum sinal novo atendeu aos critérios de Sniper ({self.current_btc_regime}). Filtros ativos: Score >= {SNIPER_BEST_SCORE_THRESHOLD if self.current_btc_regime != 'RANGING' else 'N/A'}, Decoupling >= {SNIPER_DECOUPLING_THRESHOLD if self.current_btc_regime == 'RANGING' else 'N/A'}", flush=True)
        
        # Check if ML model should be retrained
        if ML_ENABLED and self.ml_predictor and self.ml_predictor.should_retrain():
            print("[ML] Auto-retrain triggered...", flush=True)
            try:
                metrics = self.ml_predictor.train_model(min_samples=ML_MIN_SAMPLES)
                if metrics.get("status") == "SUCCESS":
                    print(f"[ML] [OK] Auto-retrain complete - Accuracy: {metrics['metrics']['accuracy']:.2%}", flush=True)
            except Exception as e:
                print(f"[ML ERROR] Auto-retrain failed: {e}", flush=True)
        
        return new_signals
    
    def get_active_signals(self) -> List[Dict]:
        """Get all currently active signals (Instant - No Network Calls)"""
        current_time = int(time.time() * 1000)
        active_list = []
        to_remove = []  # Collect symbols to remove
        
        # Iterate over a COPY to avoid issues if other thread modifies
        for symbol, signal in list(self.active_signals.items()):
            # 1. Freshness Check (Expire older than TTL)
            minutes_active = (current_time - signal["timestamp"]) / (1000 * 60)
            if minutes_active > SIGNAL_TTL_MINUTES:
                print(f"[AUTO-CLEANUP] Expiring {symbol} {int(minutes_active)}m old (descartado)", flush=True)
                signal["status"] = "EXPIRED"
                signal["exit_timestamp"] = current_time
                self.save_signal_to_db(signal)
                to_remove.append(symbol)
                continue
            
            # Check for Missed Entry (based on updated prices from background scan)
            # If current_roi is significantly negative (price moved away) before entry?
            # Or just rely on zone. If zone is WAIT for too long?
            # For now, simplistic approach: if price moved > 1% away against us before triggering?
            # Implementing "Missed Entry" logic requires tracking if it EVER entered entry zone.
            # Keeping it simple: if it's LATE and very far, maybe expire?
            # For now, just trust the _update_active_signals_prices logic for zone.
            
            if "entry_zone" not in signal:
                signal["entry_zone"] = "NEAR" # Default
            
            # [SNIPER EXCLUSIVE] Double check filter for UI delivery
            if signal.get("is_sniper", False):
                active_list.append(signal)
            else:
                to_remove.append(symbol)
        
        # Remove expired or non-sniper
        for sym in to_remove:
            sig = self.active_signals.get(sym)
            if sig:
                sig["status"] = "DISCARDED"
                sig["exit_timestamp"] = current_time
                self.save_signal_to_db(sig)
            self.active_signals.pop(sym, None)
            
        # Custom sort: Entry Zone Priority (IDEAL > WAIT > NEAR > LATE) then by Score
        def sort_priority(sig):
            zone_weights = {"IDEAL": 4, "WAIT": 3, "NEAR": 2, "LATE": 1}
            zone_weight = zone_weights.get(sig.get("entry_zone"), 0)
            return (zone_weight, sig["score"])

        return sorted(active_list, key=sort_priority, reverse=True)
    
    def get_signal_history(self, limit: int = 50, hours_limit: int = 0) -> List[Dict]:
        """Get signal history (most recent first) with optional time filtering"""
        print(f"[SG] get_signal_history: limit={limit}, hours={hours_limit}. History Size: {len(self.signal_history)}", flush=True)
        filtered_history = self.signal_history
        
        if hours_limit > 0:
            current_time = int(time.time() * 1000)
            cutoff = current_time - (hours_limit * 60 * 60 * 1000)
            filtered_history = [s for s in self.signal_history if s.get("timestamp", 0) > cutoff]
            print(f"[SG] Filtered history: {len(filtered_history)} signals", flush=True)
            
        # Fallback if empty
        if not filtered_history and self.db.is_connected():
            print("[SG] Memory empty, fetching from DB fallback...", flush=True)
            db_history = self.db.get_signal_history(limit=limit, hours_limit=hours_limit)
            return db_history
            
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
        """Load active signals and history from Supabase (non-blocking)"""
        import threading
        
        def load_async():
            try:
                # Wait for DB to be ready (non-blocking check in loop)
                max_wait = 60  # Wait up to 60 seconds
                waited = 0
                while not self.db.is_connected() and waited < max_wait:
                    if not self.db.is_connecting():
                        self.db.start_background_connection()
                    time.sleep(1)
                    waited += 1
                
                if not self.db.is_connected():
                    print("[LOAD] DB not connected after 60s, continuing with empty state", flush=True)
                    return
                
                print("[LOAD] Recarregando estado do Supabase...", flush=True)
                loaded_active = self.db.get_active_signals()
                loaded_history = self.db.get_signal_history(limit=1000)
                
                # Merge loaded data with any in-memory data
                for sym, sig in loaded_active.items():
                    if sym not in self.active_signals:
                        self.active_signals[sym] = _sanitize_obj(sig)
                
                # Merge history (avoid duplicates by ID)
                existing_ids = {s.get("id") for s in self.signal_history}
                for sig in loaded_history:
                    if sig.get("id") not in existing_ids:
                        self.signal_history.append(_sanitize_obj(sig))
                
                print(f"[LOAD] Estado carregado: {len(self.active_signals)} ativos, {len(self.signal_history)} historico", flush=True)
            except Exception as e:
                print(f"[LOAD ERROR] Falha ao carregar estado: {e}", flush=True)
        
        # Start background loading
        print("[LOAD] Starting background state loading...", flush=True)
        load_thread = threading.Thread(target=load_async, daemon=True)
        load_thread.start()


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
            is_sniper = signal.get("is_sniper", False)

            # [SNIPER EXCLUSIVE] Immediately discard signals that are NOT sniper
            if not is_sniper:
                print(f"[MONITOR PURGE] {symbol} is NOT a Sniper signal. Removing from monitoring.", flush=True)
                signal["status"] = "DISCARDED" # Permanent status for DB
                signal["exit_timestamp"] = current_time
                self.save_signal_to_db(signal)
                del self.active_signals[symbol]
                continue
            
            # Initialize hit flag for this iteration
            hit = False
            status = None
            
            # 1. Smart Exit Checks (Partial TP & Trailing Stop)
            roi = self._calculate_roi(direction, entry_price, current_price)
            
            # Track current ROI for real-time display
            signal["current_roi"] = round(roi, 2)
            
            # Track highest ROI reached
            if roi > signal.get("highest_roi", 0):
                signal["highest_roi"] = round(roi, 2)
            
            # --- PARTIAL TAKE PROFIT ---
            # If hits 2% (default), move SL to entry and mark as partially hit
            if not signal.get("partial_tp_hit", False):
                if roi >= PARTIAL_TP_PERCENT * 100:
                    signal["partial_tp_hit"] = True
                    signal["stop_loss"] = entry_price # Move SL to Breakeven
                    print(f"[SMART EXIT] {symbol} Partial TP hit ({roi:.2f}%)! SL moved to entry ${entry_price}", flush=True)
                    self.save_signal_to_db(signal) # Update DB state
            
            # --- TRAILING STOP ---
            # If hits 3%, start trailing
            if roi >= TRAILING_STOP_TRIGGER * 100:
                was_trailing = signal.get("trailing_stop_active", False)
                signal["trailing_stop_active"] = True
                new_sl = 0
                sl_updated = False
                tick_size = float(ticker.get("tickSize", 0.000001))
                
                if direction == "LONG":
                    new_sl = current_price * (1 - TRAILING_STOP_DISTANCE)
                    # Only move SL up, never down
                    if new_sl > signal["stop_loss"]:
                        signal["stop_loss"] = round_step(new_sl, tick_size)
                        sl_updated = True
                else: # SHORT
                    new_sl = current_price * (1 + TRAILING_STOP_DISTANCE)
                    # Only move SL down, never up
                    if new_sl < signal["stop_loss"]:
                        signal["stop_loss"] = round_step(new_sl, tick_size)
                        sl_updated = True
                
                # Persist trailing stop updates to DB for real-time sync
                if sl_updated or not was_trailing:
                    self.save_signal_to_db(signal)
                    if not was_trailing:
                        print(f"[TRAILING] {symbol} activated at {roi:.2f}% - SL: ${signal['stop_loss']}", flush=True)
            
            # --- LLM MONITOR EXITS & TRAP DETECTION ---
            # Only check every few iterations to save rate limit (when ROI is significant or trade is aging)
            minutes_active = (current_time - signal["timestamp"]) / 60000
            if LLM_MONITOR_EXITS and self.llm_brain and (roi >= 1.5 or minutes_active >= 5):
                # Only analyze if we haven't checked recently (every ~5 minutes per signal)
                last_llm_check = signal.get("last_llm_exit_check", 0)
                if current_time - last_llm_check > 300000:  # 5 minutes
                    try:
                        llm_func = lambda p: self.llm_brain.call_gemini(p)
                        
                        # A. Scout Analysis (Price Reaction)
                        candles_1m = self.client.get_klines(symbol, "1", 10)
                        scout_report = self.scout_agent.analyze_reaction(signal, candles_1m, llm_func)
                        signal["scout_report"] = scout_report
                        
                        # B. Sentinel Analysis (Order Flow)
                        # We capture current features as flow data
                        flow_data = self._capture_ai_features(symbol, {"institutional": {}, "current_price": current_price}, signal)
                        sentinel_report = self.sentinel_agent.analyze_order_flow(signal, flow_data, llm_func)
                        signal["sentinel_report"] = sentinel_report
                        
                        signal["last_llm_exit_check"] = current_time
                        
                        # TRAP DETECTION LOGIC
                        # If both agents are worried, or Sentinel sees ABORT_AND_FLIP
                        if sentinel_report.get("action") == "ABORT_AND_FLIP" or \
                           (scout_report.get("status") == "TRAP_DETECTED" and sentinel_report.get("trap_probability", 0) > 0.6):
                            
                            print(f"[TRAP DETECTED] ⚠️ Scout: {scout_report.get('status')} | Sentinel: {sentinel_report.get('flow_status')}", flush=True)
                            print(f"[TRAP REASON] {sentinel_report.get('reasoning')}", flush=True)
                            
                            # TRIGGER FLIP
                            self._trigger_signal_flip(signal, current_price)
                            continue # Move to next signal, this one is flipped
                        
                        # Standard exit analysis (legacy)
                        market_momentum = {
                            "trend": "BULLISH" if roi > 0 else "BEARISH",
                            "volume_status": "NORMAL"
                        }
                        exit_analysis = self.llm_brain.analyze_exit_opportunity(signal, roi, market_momentum)
                        signal["llm_exit_analysis"] = exit_analysis
                        
                        action = exit_analysis.get("action", "HOLD")
                        if action == "EXIT" and exit_analysis.get("confidence", 0) >= LLM_MIN_CONFIDENCE:
                            print(f"[LLM EXIT] [EXIT] {symbol} recomenda saida em {roi:.2f}%: {exit_analysis.get('reasoning', '')[:40]}", flush=True)
                        elif action == "PARTIAL":
                            print(f"[LLM PARTIAL] {symbol} recomenda fechamento parcial em {roi:.2f}%", flush=True)
                            
                    except Exception as e:
                        print(f"[LLM ERROR] Advanced monitoring failed for {symbol}: {e}", flush=True)
            
            # 2. Standard TP/SL Check (Real-time trigger)
            # [SURF LOGIC] If Trailing Stop is active, IGNORE the hard TP. 
            # We let the Trailing Stop handle the exit to capture 10%+ moves.
            trailing_active = signal.get("trailing_stop_active", False)
            
            if direction == "LONG":
                # Only check TP hit if NOT trailing
                if not trailing_active and current_price >= tp:
                    hit, status = self._verify_with_klines(symbol, direction, entry_price, tp, sl)
                # Always check SL/Trailing Stop hit
                elif current_price <= signal["stop_loss"]:
                    hit, status = True, "SL_HIT"
            else: # SHORT
                # Only check TP hit if NOT trailing
                if not trailing_active and current_price <= tp:
                    hit, status = self._verify_with_klines(symbol, direction, entry_price, tp, sl)
                # Always check SL/Trailing Stop hit
                elif current_price >= signal["stop_loss"]:
                    hit, status = True, "SL_HIT"
            
            # 3. Expiration Checks (TTL and Price Distance)
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
                
                # VALIDAÇÃO: Garantir consistência entre status e ROI
                # Se ROI > 0 mas status é SL_HIT, corrigir para TP_HIT
                # Se ROI < 0 mas status é TP_HIT, corrigir para SL_HIT
                if status in ["TP_HIT", "SL_HIT"]:  # Não validar EXPIRED
                    if roi > 0 and status == "SL_HIT":
                        print(f"[VALIDATION] {symbol} ROI +{roi:.2f}% but status was SL_HIT, correcting to TP_HIT", flush=True)
                        signal["status"] = "TP_HIT"
                        status = "TP_HIT"
                    elif roi < 0 and status == "TP_HIT":
                        print(f"[VALIDATION] {symbol} ROI {roi:.2f}% but status was TP_HIT, correcting to SL_HIT", flush=True)
                        signal["status"] = "SL_HIT"
                        status = "SL_HIT"
                
                # REGRA: Todos os sinais finalizados vão para o histórico local e DB (incluindo EXPIRED)
                self.signal_history.append(signal)
                finalized.append(signal)
                
                # === DECISION REPORT GENERATION ===
                try:
                    outcome_data = {"status": status, "roi": roi}
                    decision_report = self._generate_decision_report(signal, outcome_data)
                    signal["decision_report"] = decision_report
                    print(f"[REPORT] Decision report generated for {symbol}", flush=True)
                except Exception as e:
                    print(f"[REPORT] Error generating report: {e}", flush=True)

                # RAG Memory Auto-Feed: Aprende com trades finalizados (TP/SL)
                if status in ["TP_HIT", "SL_HIT"]:
                    try:
                        outcome = {"status": status, "roi": signal.get("final_roi", 0)}
                        self.rag_memory.add_memory(signal, outcome)
                        print(f"[RAG] [MEMORY] Trade adicionado a memoria: {symbol} {status} ({roi:.2f}%)", flush=True)
                    except Exception as e:
                        print(f"[RAG] [WARN] Erro ao salvar na memória: {e}", flush=True)
                
                self.save_signal_to_db(signal) # Salva SEMPRE no Supabase
                print(f"[FINALIZED] {symbol} {status} at ${current_price} (ROI: {roi:.2f}%) - Persistido no DB", flush=True)
                
        return finalized
    
    def _trigger_signal_flip(self, original_signal: Dict, current_price: float):
        """
        Triggers a 'Flip' (Stop and Reverse).
        Closes the current bias and opens the opposite direction.
        """
        symbol = original_signal["symbol"]
        old_direction = original_signal["direction"]
        new_direction = "SHORT" if old_direction == "LONG" else "LONG"
        
        print(f"[FLIP] 🔄 Triggering FLIP on {symbol}: {old_direction} -> {new_direction}", flush=True)
        
        # 1. Close original signal in memory/DB
        original_signal["status"] = "FLIPPED"
        original_signal["exit_price"] = current_price
        original_signal["exit_timestamp"] = int(time.time() * 1000)
        self.save_signal_to_db(original_signal)
        self.signal_history.append(original_signal)
        
        # 2. Analyze pair for new direction
        # We manually construct a "Turbo Flip" signal based on the original's indicators
        # but with the opposite bias.
        new_signal = self.analyze_pair(symbol)
        
        if new_signal and new_signal["direction"] == new_direction:
            # Add a tag to know it's a flip
            new_signal["is_flip"] = True
            new_signal["flip_from_id"] = original_signal["id"]
            new_signal["score"] = max(new_signal["score"], 100) # Force high score for flips
            
            # Start monitoring new signal
            self.active_signals[symbol] = new_signal
            self.save_signal_to_db(new_signal)
            print(f"[FLIP] [OK] New {new_direction} signal activated for {symbol} (Score: {new_signal['score']})", flush=True)
        else:
            # Fallback: remove from active if no valid flip found
            if symbol in self.active_signals:
                del self.active_signals[symbol]
            print(f"[FLIP] [WARN] Could not find valid technical confirmation for {new_direction} flip on {symbol}.", flush=True)

    def _verify_with_klines(self, symbol: str, direction: str, entry: float, tp: float, sl: float) -> tuple:
        """
        Verifica se TP ou SL foi atingido e retorna o status apropriado.
        IMPORTANTE: A classificação final será baseada no ROI real, não apenas em qual nível foi tocado.
        Esta função serve para confirmar que houve um hit válido.
        """
        try:
            # Pegamos as últimas candles de 1min (cobertura de 60 min)
            klines = self.client.get_klines(symbol, "1", 60)
            if not klines:
                # Fallback: usar preço atual para determinar
                ticker = self.client.get_ticker(symbol)
                if ticker:
                    current_price = float(ticker["lastPrice"])
                    roi = self._calculate_roi(direction, entry, current_price)
                    return True, "TP_HIT" if roi > 0 else "SL_HIT"
                return True, "TP_HIT"

            # Verificar se TP ou SL foram atingidos nas candles
            touched_tp = False
            touched_sl = False
            
            for candle in klines:
                high = candle["high"]
                low = candle["low"]

                if direction == "LONG":
                    if low <= sl:
                        touched_sl = True
                    if high >= tp:
                        touched_tp = True
                else: # SHORT
                    if high >= sl:
                        touched_sl = True
                    if low <= tp:
                        touched_tp = True
            
            # Determinar status baseado no que foi tocado
            # Se ambos foram tocados, usar o preço atual para decidir (ROI final)
            if touched_tp and touched_sl:
                ticker = self.client.get_ticker(symbol)
                if ticker:
                    current_price = float(ticker["lastPrice"])
                    roi = self._calculate_roi(direction, entry, current_price)
                    status = "TP_HIT" if roi > 0 else "SL_HIT"
                    print(f"[VERIFY] {symbol} touched both TP and SL, using ROI ({roi:.2f}%) -> {status}", flush=True)
                    return True, status
                return True, "TP_HIT"  # Default to TP if can't determine
            elif touched_tp:
                return True, "TP_HIT"
            elif touched_sl:
                return True, "SL_HIT"
            else:
                # Nenhum foi tocado nas candles, usar preço atual
                ticker = self.client.get_ticker(symbol)
                if ticker:
                    current_price = float(ticker["lastPrice"])
                    roi = self._calculate_roi(direction, entry, current_price)
                    return True, "TP_HIT" if roi > 0 else "SL_HIT"
                return True, "TP_HIT"
                
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
            "signal_types": type_counts,
            "db_connected": self.db.is_connected(),
            "db_connecting": self.db.is_connecting(),
            "system_ready": self.system_ready
        }

    def _generate_decision_report(self, signal: Dict, outcome: Dict) -> Dict:
        """
        Generate a comprehensive decision report for the signal lifecycle.
        Aggregates Technicals, Institutional data, AI reasoning, and Context.
        """
        # 1. Technical Context
        indicators = signal.get("indicators", {})
        institutional = signal.get("institutional", {})
        
        technical_summary = {
            "rsi": indicators.get("rsi"),
            "trend": indicators.get("trend_4h"),
            "cvd_delta": institutional.get("cvd_delta"),
            "open_interest": institutional.get("oi_latest"),
            "ls_ratio": institutional.get("lsr_latest"),
            "score": signal.get("score"),
            "score_breakdown": signal.get("score_breakdown")
        }
        
        # 2. AI & Council Context
        llm_validation = signal.get("llm_validation", {})
        council_decision = {
            "approved": llm_validation.get("approved", False),
            "confidence": llm_validation.get("confidence"),
            "reasoning": llm_validation.get("reasoning"),
            "action": llm_validation.get("suggested_action")
        }
        
        # 3. Market Context (News & Sentiment)
        market_narrative = {
            "sentiment_score": self.market_sentiment.get("score"),
            "sentiment_label": self.market_sentiment.get("sentiment"),
            "news_summary": self.market_sentiment.get("summary"),
            "btc_regime": signal.get("btc_regime")
        }
        
        # 4. Outcome Analysis
        outcome_analysis = {
            "final_status": outcome.get("status"),
            "final_roi": outcome.get("roi"),
        }
        
        return {
            "timestamp": int(time.time() * 1000),
            "technicals": technical_summary,
            "council": council_decision,
            "market": market_narrative,
            "outcome": outcome_analysis
        }

