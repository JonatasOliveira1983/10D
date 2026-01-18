"""
10D - Flask API
REST API for frontend communication and serving static files
"""

# VERSION STAMP - to verify which code is running
BUILD_VERSION = "2026-01-14-2227-SUPABASE-FIX"



# EARLY DEBUG - before any complex imports
import sys
print(f"[DEBUG] ===== BUILD VERSION: {BUILD_VERSION} =====", flush=True)
print("[DEBUG] app.py starting - before imports", flush=True)

from flask import Flask, jsonify, request, send_from_directory
print("[DEBUG] Flask imported OK", flush=True)

from flask_cors import CORS
import threading
import time
import os

print("[DEBUG] Basic imports OK", flush=True)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("[DEBUG] About to import config...", flush=True)
from config import API_HOST, API_PORT, DEBUG, UPDATE_INTERVAL_SECONDS, PAIR_LIMIT, ML_ENABLED, ML_MIN_SAMPLES
print(f"[DEBUG] Config imported OK - PAIR_LIMIT={PAIR_LIMIT}", flush=True)

print("[DEBUG] About to import SignalGenerator...", flush=True)
from services.signal_generator import SignalGenerator
from services.signal_generator import SignalGenerator
from services.ai_analytics_service import AIAnalyticsService
from services.news_service import news_service
print("[DEBUG] SignalGenerator imported OK", flush=True)

# Initialize Flask app
# static_folder points to where Vite builds the frontend
app = Flask(__name__, static_folder='../frontend/dist', static_url_path='/')
CORS(app)

# Initialize signal generator
print("[DEBUG] Creating SignalGenerator instance...", flush=True)
generator = SignalGenerator()
# Initialize AI Analytics Service
analytics_service = AIAnalyticsService(generator.db)

# Background scanning flag
scanning = False
scan_thread = None


def background_scanner():
    """Background thread for continuous scanning and monitoring"""
    global scanning
    while scanning:
        try:
            # 1. Monitor active signals for TP/SL hits
            generator.monitor_active_signals()
            
            # 2. Scan for new signals
            generator.scan_all_pairs()
            
            time.sleep(UPDATE_INTERVAL_SECONDS)
        except Exception as e:
            print(f"[SCANNER ERROR] {e}", flush=True)
            time.sleep(5)

def delayed_init():
    """Delayed initialization to satisfy Cloud Run health check"""
    global scanning, scan_thread
    print("=" * 60, flush=True)
    print("[INIT] Starting delayed initialization in background...", flush=True)
    print("=" * 60, flush=True)
    
    # Wait a few seconds for server to bind
    time.sleep(2)
    
    try:
        # === STEP 1: Train ML model BEFORE monitoring ===
        if ML_ENABLED and generator.ml_predictor:
            print("=" * 60, flush=True)
            print("[ML STARTUP] Verificando modelo ML antes de iniciar...", flush=True)
            print("=" * 60, flush=True)
            
            # Always try to train/retrain at startup to ensure model is fresh
            if not generator.ml_predictor.model:
                print("[ML STARTUP] Nenhum modelo carregado. Iniciando treinamento...", flush=True)
            else:
                print("[ML STARTUP] Modelo existente encontrado. Retreinando para garantir atualização...", flush=True)
            
            # Train the model
            train_result = generator.ml_predictor.train_model(min_samples=ML_MIN_SAMPLES)
            
            if train_result.get("status") == "SUCCESS":
                accuracy = train_result.get("metrics", {}).get("accuracy", 0)
                samples = train_result.get("samples", {}).get("total", 0)
                print(f"[ML STARTUP] ✅ Modelo treinado com sucesso!", flush=True)
                print(f"[ML STARTUP]    Accuracy: {accuracy:.2%}", flush=True)
                print(f"[ML STARTUP]    Amostras: {samples}", flush=True)
            elif train_result.get("status") == "INSUFFICIENT_DATA":
                current = train_result.get("current_samples", 0)
                required = train_result.get("required_samples", ML_MIN_SAMPLES)
                print(f"[ML STARTUP] ⚠️ Dados insuficientes para treinar: {current}/{required} amostras", flush=True)
                print(f"[ML STARTUP] Sistema funcionará em modo FALLBACK (apenas regras)", flush=True)
            else:
                print(f"[ML STARTUP] ❌ Erro no treinamento: {train_result}", flush=True)
            
            print("=" * 60, flush=True)
        
        # === STEP 2: Initialize pairs ===
        print(f"[INIT] Calling generator.initialize({PAIR_LIMIT})...", flush=True)
        pairs = generator.initialize(pair_limit=PAIR_LIMIT)
        print(f"[INIT] SUCCESS - Loaded {len(pairs)} pairs", flush=True)
        
        # === STEP 3: Start background scanner ===
        print("[SCANNER] Starting background thread...", flush=True)
        scanning = True
        scan_thread = threading.Thread(target=background_scanner, daemon=True)
        scan_thread.start()
        print(f"[SCANNER] Started (interval: {UPDATE_INTERVAL_SECONDS}s)", flush=True)
        
    except Exception as e:
        print(f"[INIT] ERROR during initialization: {e}", flush=True)
        import traceback
        traceback.print_exc()

# Start delayed initialization thread
print("[BOOT] Launching delayed init thread...", flush=True)
threading.Thread(target=delayed_init, daemon=True).start()


# =============================================================================
# Frontend Routes
# =============================================================================

@app.route("/")
def serve_index():
    """Serve the React frontend index.html"""
    if os.path.exists(os.path.join(app.static_folder, 'index.html')):
        return send_from_directory(app.static_folder, 'index.html')
    else:
        return jsonify({
            "name": "10D Trading System",
            "version": "1.0.0",
            "status": "online",
            "message": "Frontend not found. Please build it first."
        })

@app.errorhandler(404)
def not_found(e):
    """Catch-all for React Router paths"""
    if os.path.exists(os.path.join(app.static_folder, 'index.html')):
        return send_from_directory(app.static_folder, 'index.html')
    return jsonify({"error": "Not found"}), 404


# =============================================================================
# API Routes
# =============================================================================

@app.route("/api/version")
def get_version():
    """Get current build version - useful for debugging deployments"""
    return jsonify({
        "version": BUILD_VERSION,
        "monitored_pairs_count": len(generator.monitored_pairs),
        "api_key_loaded": bool(os.environ.get("BYBIT_API_KEY")),
        "api_secret_loaded": bool(os.environ.get("BYBIT_API_SECRET")),
        "status": "running"
    })


@app.route("/api/pairs")
def get_pairs():
    """Get list of monitored pairs"""
    return jsonify({
        "pairs": generator.monitored_pairs,
        "count": len(generator.monitored_pairs)
    })


@app.route("/api/signals")
def get_signals():
    """Get active signals"""
    min_score = request.args.get("min_score", 0, type=int)
    
    signals = generator.get_active_signals()
    
    # Filter by minimum score if specified
    if min_score > 0:
        signals = [s for s in signals if s["score"] >= min_score]
    
    return jsonify({
        "signals": signals,
        "count": len(signals),
        "filter": {"min_score": min_score}
    })


@app.route("/api/history")
def get_history():
    """Get signal history (limited to last 24h for clean UI)"""
    limit = request.args.get("limit", 50, type=int)
    # Hardcoded 24h retention as requested
    history = generator.get_signal_history(limit, hours_limit=24)
    
    return jsonify({
        "history": history,
        "count": len(history),
        "retention_policy": "24h"
    })


@app.route("/api/stats")
def get_stats():
    """Get summary statistics"""
    stats = generator.get_stats()
    return jsonify(stats)


@app.route("/api/scan", methods=["POST"])
def trigger_scan():
    """Manually trigger a scan"""
    new_signals = generator.scan_all_pairs()
    return jsonify({
        "message": "Scan complete",
        "new_signals": len(new_signals),
        "signals": new_signals
    })


@app.route("/api/scanner/start", methods=["POST"])
def start_scanner():
    """Start background scanner"""
    global scanning, scan_thread
    
    if not scanning:
        scanning = True
        scan_thread = threading.Thread(target=background_scanner, daemon=True)
        scan_thread.start()
        return jsonify({"message": "Scanner started", "status": "running"})
    
    return jsonify({"message": "Scanner already running", "status": "running"})


@app.route("/api/scanner/stop", methods=["POST"])
def stop_scanner():
    """Stop background scanner"""
    global scanning
    scanning = False
    return jsonify({"message": "Scanner stopped", "status": "stopped"})


@app.route("/api/signal/<symbol>/clear", methods=["POST"])
def clear_signal(symbol):
    """Clear a specific signal"""
    generator.clear_signal(symbol)
    return jsonify({"message": f"Signal for {symbol} cleared"})


@app.route("/api/analyze/<symbol>")
def analyze_symbol(symbol):
    """Analyze a specific symbol"""
    signal = generator.analyze_pair(symbol.upper())
    
    if signal:
        return jsonify({
            "found": True,
            "signal": signal
        })
    
    return jsonify({
        "found": False,
        "message": f"No signal for {symbol} at this time"
    })


@app.route("/api/btc/regime")
def get_btc_regime():
    """Get current BTC market regime and dynamic TP/SL targets"""
    try:
        regime_info = generator.btc_tracker.get_regime_info()
        return jsonify({
            "status": "OK",
            **regime_info,
            "regime_details": generator.current_regime_details
        })
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "regime": "TRENDING",
            "tp_pct": 2.0,
            "sl_pct": 1.0,
            "message": str(e)
        })


# =============================================================================
# AI Analytics Routes
# =============================================================================

@app.route("/api/ai/analytics")
def get_ai_analytics():
    """Get correlation and performance statistics for AI training"""
    try:
        result = analytics_service.get_market_correlations()
        print(f"[AI ANALYTICS] Status: {result.get('status')}, Data: {len(str(result))}", flush=True)
        return jsonify(result)
    except Exception as e:
        print(f"[AI ANALYTICS ERROR] {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({"status": "ERROR", "message": str(e)}), 500

@app.route("/api/ai/progress")
def get_ai_progress():
    """Get status of data collection for ML training"""
    try:
        result = analytics_service.get_training_progress()
        print(f"[AI PROGRESS] Samples: {result.get('current_samples')}/{result.get('target_samples')}", flush=True)
        return jsonify(result)
    except Exception as e:
        print(f"[AI PROGRESS ERROR] {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({"status": "ERROR", "message": str(e)}), 500


@app.route("/api/ai/brain")
def get_ai_brain():
    """Get ML Brain insights (optimal thresholds and feature importance)"""
    import json
    brain_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "services", "ml_brain.json")
    try:
        if os.path.exists(brain_path):
            with open(brain_path, "r") as f:
                brain_data = json.load(f)
            return jsonify({"status": "READY", "data": brain_data})
        return jsonify({"status": "NOT_TRAINED", "message": "ML Brain não foi treinado ainda"})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500


# =============================================================================
# LLM Intelligence Routes
# =============================================================================

@app.route("/api/llm/status")
def get_llm_status():
    """Get LLM Trading Brain status and statistics"""
    try:
        if not hasattr(generator, 'llm_brain') or not generator.llm_brain:
            return jsonify({
                "status": "DISABLED",
                "llm_enabled": False,
                "message": "LLM Trading Brain is not enabled"
            })
        
        status = generator.llm_brain.get_status()
        return jsonify({
            "status": "OK",
            "llm_enabled": True,
            **status
        })
    except Exception as e:
        print(f"[LLM STATUS ERROR] {e}", flush=True)
        return jsonify({"status": "ERROR", "message": str(e)}), 500


@app.route("/api/llm/test")
def test_llm_connection():
    """Test LLM connection to Gemini"""
    try:
        if not hasattr(generator, 'llm_brain') or not generator.llm_brain:
            return jsonify({
                "status": "DISABLED",
                "message": "LLM Trading Brain is not enabled"
            })
        
        result = generator.llm_brain.test_connection()
        return jsonify(result)
    except Exception as e:
        print(f"[LLM TEST ERROR] {e}", flush=True)
        return jsonify({"status": "ERROR", "message": str(e)}), 500


@app.route('/api/sentiment', methods=['GET'])
def get_sentiment():
    """Get market sentiment analysis based on new headlines"""
    try:
        # Get headlines
        headlines = news_service.get_latest_headlines(limit=15)
        
        # Analyze with LLM
        if hasattr(generator, 'llm_brain') and generator.llm_brain and generator.llm_brain.is_enabled():
            analysis = generator.llm_brain.analyze_market_sentiment(headlines)
        else:
            analysis = {"score": 50, "sentiment": "NEUTRAL", "summary": "LLM disabled"}
            
        return jsonify({
            "status": "success",
            "headlines": headlines,
            "analysis": analysis
        })
    except Exception as e:
        print(f"[API ERROR] Sentiment analysis failed: {e}", flush=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/llm/summary")
def get_llm_summary():
    """Get aggregated LLM metrics for Signal Journey header"""
    try:
        # Get history for calculations
        history = generator.db.get_signal_history(limit=200, hours_limit=240)  # Last 10 days
        
        # Calculate win rate
        completed = [s for s in history if s.get("status") in ["TP_HIT", "SL_HIT"]]
        wins = len([s for s in completed if s.get("status") == "TP_HIT"])
        total = len(completed)
        win_rate = (wins / total * 100) if total > 0 else 0
        
        # Calculate win rate history (last 7 days, daily)
        win_rate_history = []
        for days_ago in range(7, 0, -1):
            day_start = time.time() * 1000 - (days_ago * 24 * 60 * 60 * 1000)
            day_end = day_start + (24 * 60 * 60 * 1000)
            day_completed = [s for s in completed if day_start <= s.get("timestamp", 0) < day_end]
            day_wins = len([s for s in day_completed if s.get("status") == "TP_HIT"])
            day_total = len(day_completed)
            win_rate_history.append((day_wins / day_total * 100) if day_total > 0 else 50)
        
        # Calculate ROI accumulated
        roi_values = [s.get("final_roi") or s.get("current_roi") or 0 for s in completed]
        roi_accumulated = sum(roi_values)
        
        # ROI history (last 7 days, cumulative)
        roi_history = []
        cumulative_roi = 0
        for days_ago in range(7, 0, -1):
            day_start = time.time() * 1000 - (days_ago * 24 * 60 * 60 * 1000)
            day_end = day_start + (24 * 60 * 60 * 1000)
            day_completed = [s for s in completed if day_start <= s.get("timestamp", 0) < day_end]
            day_roi = sum(s.get("final_roi") or s.get("current_roi") or 0 for s in day_completed)
            cumulative_roi += day_roi
            roi_history.append(round(cumulative_roi, 2))
        
        # LLM confidence average
        llm_confs = []
        for s in history:
            if s.get("llm_validation") and s["llm_validation"].get("confidence"):
                llm_confs.append(s["llm_validation"]["confidence"] * 100)
        llm_confidence_avg = sum(llm_confs) / len(llm_confs) if llm_confs else 70
        
        # Best catch
        best = max(completed, key=lambda s: s.get("final_roi") or s.get("current_roi") or 0, default=None)
        best_catch = None
        if best:
            best_roi = best.get("final_roi") or best.get("current_roi") or 0
            if best_roi > 0:
                best_catch = {"symbol": best.get("symbol"), "roi": best_roi}
        
        # Average capture rate
        capture_rates = []
        for s in completed:
            final_roi = s.get("final_roi") or s.get("current_roi") or 0
            highest_roi = s.get("highest_roi") or 0
            if highest_roi > 0 and final_roi > 0:
                capture_rates.append(min(100, (final_roi / highest_roi) * 100))
        capture_rate_avg = sum(capture_rates) / len(capture_rates) if capture_rates else 0
        
        return jsonify({
            "status": "OK",
            "win_rate": round(win_rate, 1),
            "win_rate_history": win_rate_history,
            "roi_accumulated": round(roi_accumulated, 2),
            "roi_history": roi_history,
            "llm_confidence_avg": round(llm_confidence_avg, 0),
            "active_signals": len(generator.active_signals),
            "best_catch": best_catch,
            "capture_rate_avg": round(capture_rate_avg, 0),
            "total_trades": total
        })
    except Exception as e:
        print(f"[LLM SUMMARY ERROR] {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({"status": "ERROR", "message": str(e)}), 500


# =============================================================================
# ML Predictor Routes
# =============================================================================

@app.route("/api/ml/train", methods=["POST"])
def train_ml_model():
    """Train ML model with historical data"""
    try:
        if not generator.ml_predictor:
            return jsonify({"status": "DISABLED", "message": "ML is not enabled"}), 400
        
        print("[API] Manual ML training triggered...", flush=True)
        from config import ML_MIN_SAMPLES
        metrics = generator.ml_predictor.train_model(min_samples=ML_MIN_SAMPLES)
        
        return jsonify(metrics)
    except Exception as e:
        print(f"[ML TRAIN ERROR] {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({"status": "ERROR", "message": str(e)}), 500


@app.route("/api/ml/status")
def get_ml_status():
    """Get ML system status"""
    try:
        if not generator.ml_predictor:
            return jsonify({
                "status": "DISABLED",
                "ml_enabled": False,
                "message": "ML Predictor is not enabled"
            })
        
        status = generator.ml_predictor.get_status()
        return jsonify({
            "status": "OK",
            "ml_enabled": True,
            **status
        })
    except Exception as e:
        print(f"[ML STATUS ERROR] {e}", flush=True)
        return jsonify({"status": "ERROR", "message": str(e)}), 500


@app.route("/api/ml/metrics")
def get_ml_metrics():
    """Get detailed ML model metrics"""
    try:
        if not generator.ml_predictor:
            return jsonify({"status": "DISABLED", "message": "ML is not enabled"}), 400
        
        metrics = generator.ml_predictor.get_metrics()
        
        if not metrics:
            return jsonify({
                "status": "NOT_TRAINED",
                "message": "Model has not been trained yet"
            }), 404
        
        return jsonify(metrics)
    except Exception as e:
        print(f"[ML METRICS ERROR] {e}", flush=True)
        return jsonify({"status": "ERROR", "message": str(e)}), 500


@app.route("/api/ml/predict", methods=["POST"])
def test_ml_prediction():
    """Test ML prediction with custom features"""
    try:
        if not generator.ml_predictor:
            return jsonify({"status": "DISABLED", "message": "ML is not enabled"}), 400
        
        features = request.json.get("features", {})
        
        if not features:
            return jsonify({"status": "ERROR", "message": "No features provided"}), 400
        
        probability = generator.ml_predictor.predict_probability(features)
        
        return jsonify({
            "status": "SUCCESS",
            "probability": round(probability, 4),
            "probability_pct": round(probability * 100, 2),
            "features": features
        })
    except Exception as e:
        print(f"[ML PREDICT ERROR] {e}", flush=True)
        return jsonify({"status": "ERROR", "message": str(e)}), 500


@app.route("/api/debug/supabase")
def debug_supabase():
    """Debug endpoint to check Supabase connection and data availability"""
    debug_info = {
        "timestamp": time.time(),
        "env_vars": {
            "SUPABASE_URL": bool(os.environ.get("SUPABASE_URL")),
            "SUPABASE_ANON_KEY": bool(os.environ.get("SUPABASE_ANON_KEY")),
            "SUPABASE_URL_value": os.environ.get("SUPABASE_URL", "NOT_SET")[:50] + "..." if os.environ.get("SUPABASE_URL") else "NOT_SET"
        },
        "database": {
            "client_initialized": generator.db.client is not None,
            "connection_status": "UNKNOWN"
        },
        "data": {
            "total_signals": 0,
            "active_signals": 0,
            "history_signals": 0,
            "signals_with_features": 0,
            "labeled_signals": {"tp_hit": 0, "sl_hit": 0, "expired": 0, "total": 0}
        },
        "errors": []
    }
    
    # Test database connection
    try:
        if generator.db.client:
            debug_info["database"]["connection_status"] = "CONNECTED"
            
            # Try to count signals
            try:
                labeled = generator.db.count_labeled_signals()
                debug_info["data"]["labeled_signals"] = labeled
                debug_info["data"]["total_signals"] = labeled.get("total", 0)
            except Exception as e:
                debug_info["errors"].append(f"count_labeled_signals failed: {str(e)}")
            
            # Try to get active signals
            try:
                active = generator.db.get_active_signals()
                debug_info["data"]["active_signals"] = len(active)
            except Exception as e:
                debug_info["errors"].append(f"get_active_signals failed: {str(e)}")
            
            # Try to get history
            try:
                history = generator.db.get_signal_history(limit=100, hours_limit=0)
                debug_info["data"]["history_signals"] = len(history)
                
                # Count signals with ai_features
                with_features = sum(1 for s in history if s.get("ai_features"))
                debug_info["data"]["signals_with_features"] = with_features
            except Exception as e:
                debug_info["errors"].append(f"get_signal_history failed: {str(e)}")
        else:
            debug_info["database"]["connection_status"] = "NOT_INITIALIZED"
            debug_info["errors"].append("Database client is None - check SUPABASE_URL and SUPABASE_ANON_KEY")
    except Exception as e:
        debug_info["database"]["connection_status"] = "ERROR"
        debug_info["errors"].append(f"Database check failed: {str(e)}")
    
    return jsonify(debug_info)


# =============================================================================
# TradesOrganizer Persistence
# =============================================================================

PLAN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trading_plan.json")

@app.route("/api/users/artifacts/trading-plan", methods=["GET", "PUT"])
@app.route("/api/users/artifacts/trading-plan-public", methods=["GET", "PUT"])
def manage_trading_plan():
    """Handle loading and saving of the trading plan data using Supabase"""
    if request.method == "PUT":
        try:
            data = request.json
            generator.db.save_trading_plan(data)
            return jsonify({"success": True, "message": "Plan saved to Supabase successfully"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
            
    # GET method
    try:
        data = generator.db.get_trading_plan()
        if data:
            return jsonify({"success": True, "data": data})
        return jsonify({"success": False, "message": "No data found in Supabase"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# =============================================================================
# Main Entry Point (for local development)
# =============================================================================

if __name__ == "__main__":
    # Get port from environment variable (required for Google Cloud Run)
    port = int(os.environ.get("PORT", API_PORT))
    
    # Start the server
    print(f"\n🌐 Starting server on http://{API_HOST}:{port}", flush=True)
    print("=" * 60, flush=True)
    
    app.run(host=API_HOST, port=port, debug=False, threaded=True, use_reloader=False)
