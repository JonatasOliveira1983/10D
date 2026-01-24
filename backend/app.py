"""
10D - Flask API
REST API for frontend communication and serving static files
"""

# VERSION STAMP - to verify which code is running
BUILD_VERSION = "2026-01-22-v5.1-STABLE"



# EARLY DEBUG - before any complex imports
import sys
print(f"[DEBUG] ===== BUILD VERSION: {BUILD_VERSION} =====", flush=True)
# FORCE UTF-8 STDOUT/STDERR FOR WINDOWS
import os
import io

print(f"[BOOT] ===== 10D STARTING (BUILD: {BUILD_VERSION}) =====", flush=True)

# Ensure UTF-8 output even if TextIOWrapper is already set (safe check)
try:
    if os.name == 'nt' and (not hasattr(sys.stdout, 'encoding') or sys.stdout.encoding.lower() != 'utf-8'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except (AttributeError, io.UnsupportedOperation):
    pass

print("[DEBUG] app.py starting - before imports", flush=True)

from flask import Flask, jsonify, request, send_from_directory
from decimal import Decimal
from datetime import datetime, date
import uuid
print("[DEBUG] Flask imported OK", flush=True)

from flask_cors import CORS
import threading
import time
import os
import numpy as np

print("[DEBUG] Basic imports OK", flush=True)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("[DEBUG] About to import config...", flush=True)
from config import API_HOST, API_PORT, DEBUG, UPDATE_INTERVAL_SECONDS, PAIR_LIMIT, ML_ENABLED, ML_MIN_SAMPLES
print(f"[DEBUG] Config imported OK - PAIR_LIMIT={PAIR_LIMIT}", flush=True)

print("[DEBUG] About to import SignalGenerator...", flush=True)
from services.signal_generator import SignalGenerator
from services.ai_analytics_service import AIAnalyticsService
from services.news_service import news_service
from services.health_monitor import HealthMonitor
print("[DEBUG] SignalGenerator imported OK", flush=True)

# Initialize Flask app
# static_folder points to where Vite builds the frontend
app = Flask(__name__, static_folder='../frontend/dist', static_url_path='/')
CORS(app)

# === REAL-TIME LOG BUFFER ===
# Stores the last 50 logs in memory for immediate UI feedback without DB delay
from collections import deque
RECENT_LOGS = deque(maxlen=50)

def log_feed_callback(agent_id, type_id, message, details=None):
    """Callback injected into SignalGenerator to capture real-time logs"""
    try:
        log_entry = {
            "id": f"rt_{int(time.time()*1000)}",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "agent": agent_id,
            "message": f"🧠 {type_id.replace('COUNCIL_', '')}: {message}"
        }
        RECENT_LOGS.append(log_entry)
        print(f"[CALLBACK] Log captured: {message}", flush=True)
    except Exception as e:
        print(f"[CALLBACK] Error: {e}")

# Initialize signal generator with callback
print("[INIT] Creating SignalGenerator with Log Channel...", flush=True)
generator = SignalGenerator(limit=PAIR_LIMIT, log_callback=log_feed_callback)
print("[DEBUG] Creating SignalGenerator instance...", flush=True)
# The second initialization was shadowing the first one! Removing the duplicate.
# generator = SignalGenerator() 
# Initialize AI Analytics Service
analytics_service = AIAnalyticsService(generator.db)
# Initialize Health Monitor
health_monitor = HealthMonitor(generator)

# === NEW: Push Notification Service ===
try:
    from services.push_service import PushService
    push_service = PushService(generator.db)
    generator.set_push_service(push_service)
except Exception as e:
    print(f"[BOOT] [WARN] PushService initialization failed (Check VAPID keys): {e}", flush=True)
    push_service = None

# Background scanning flag
scanning = False
scan_thread = None

def sanitize_for_json(obj):
    """Recursively convert Decimal, numpy types, and others to JSON-serializable types"""
    # Base types that are safe
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)) and not isinstance(obj, (np.generic, np.ndarray)):
        return obj

    # NumPy types
    if isinstance(obj, (np.integer, np.int64, np.int32, np.uint64, np.uint32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return [sanitize_for_json(x) for x in obj.tolist()]
    
    # Complex types
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, uuid.UUID):
        return str(obj)
        
    # Recursive containers
    elif isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(v) for v in obj]
        
    # Fallback
    return str(obj)


def background_scanner():
    """Background thread for continuous scanning and monitoring"""
    global scanning
    print("[SCANNER] Scanner thread started (Warm-up mode)", flush=True)
    
    while scanning:
        try:
            # Check if system is ready (ML trained)
            if not generator.system_ready:
                print("[SCANNER] Waiting for ML training to complete... (System Warm-up)", flush=True)
                time.sleep(5)
                continue

            # 1. Monitor active signals for TP/SL hits
            generator.monitor_active_signals()
            
            # 2. Scan for new signals
            if self.log_callback and int(time.time()) % 60 < 5: # Log once per minute approx
                self.log_callback("scout", "SCAN_PULSE", "🔭 Escaneando 109 pares na velocidade da luz...", None)
                
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
    
    # === NEW: Wait for DB connection (Max 60s with soft fail) ===
    print("[INIT] Waiting for Database connection...", flush=True)
    wait_start = time.time()
    db_connected = False
    
    # Loop for up to 60 seconds
    while time.time() - wait_start < 60:
        if generator.db.is_connected():
            db_connected = True
            break
            
        if not generator.db.is_connecting():
            # Trigger connection if not in progress
            generator.db.start_background_connection()
            
        time.sleep(1)
    
    if db_connected:
        print(f"[INIT] Database connected successfully in {int(time.time() - wait_start)}s!", flush=True)
    else:
        print("[INIT] [WARN] Database connection timeout (60s) - Starting in OFFLINE/MEMORY ONLY mode", flush=True)

    # === STEP 1: Initialize pairs (ROBUST RETRY) ===
    pairs_loaded = False
    retry_count = 0
    max_retries = 3
    
    while not pairs_loaded and retry_count < max_retries:
        try:
            print(f"[INIT] Calling generator.initialize({PAIR_LIMIT}) (Attempt {retry_count+1}/{max_retries})...", flush=True)
            pairs = generator.initialize(pair_limit=PAIR_LIMIT)
            if pairs and len(pairs) > 0:
                print(f"[INIT] SUCCESS - Loaded {len(pairs)} pairs", flush=True)
                pairs_loaded = True
            else:
                 print(f"[INIT] [WARN] Generator returned empty pairs list.", flush=True)
                 retry_count += 1
                 time.sleep(2)
        except Exception as e:
            print(f"[INIT] [WARN] Failed to initialize pairs (API Error?): {e}", flush=True)
            retry_count += 1
            time.sleep(3)

    if not pairs_loaded:
        print("[INIT] [CRITICAL] All API attempts failed. Using extended fallback pair list...", flush=True)
        # Fallback to Top 10 Major Pairs as requested
        generator.monitored_pairs = [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", 
            "ADAUSDT", "AVAXUSDT", "LINKUSDT", "MATICUSDT", "LTCUSDT"
        ]
        print(f"[INIT] Monitoring {len(generator.monitored_pairs)} fallback pairs.", flush=True)

    # === STEP 2: Start background scanner (CRITICAL) ===
    # We allow scanner to start even if DB or Init failed partially
    try:
        print("[SCANNER] Starting background thread...", flush=True)
        scanning = True
        scan_thread = threading.Thread(target=background_scanner, daemon=True)
        scan_thread.start()
        print(f"[SCANNER] Started (interval: {UPDATE_INTERVAL_SECONDS}s)", flush=True)
    except Exception as e:
         print(f"[INIT] [FATAL] Could not start scanner thread: {e}", flush=True)

    # === STEP 3: Start System Health Monitor ===
    try:
        health_monitor.start()
    except Exception as e:
        print(f"[INIT] Failed to start HealthMonitor: {e}", flush=True)

    # === STEP 4: Train ML model (SLOW/HEAVY) ===
    if ML_ENABLED and generator.ml_predictor and db_connected:
        print("=" * 60, flush=True)
        print("[ML STARTUP] Verificando modelo ML (Training in background)...", flush=True)
        print("=" * 60, flush=True)
        
        # Always try to train/retrain at startup
        try:
            # Get current labeled signals count for progress reporting
            stats = generator.db.count_labeled_signals()
            total_samples = stats.get("total", 0)
            print(f"[ML STARTUP] Amostras rotuladas encontradas: {total_samples}/{ML_MIN_SAMPLES}", flush=True)

            if not generator.ml_predictor.model:
                print("[ML STARTUP] Nenhum modelo carregado. Iniciando treinamento...", flush=True)
            else:
                print("[ML STARTUP] Modelo existente encontrado. Retreinando...", flush=True)
            
            # Train the model
            train_result = generator.ml_predictor.train_model(min_samples=ML_MIN_SAMPLES)
            
            if train_result.get("status") == "SUCCESS":
                accuracy = train_result.get("metrics", {}).get("accuracy", 0)
                print(f"============================================================", flush=True)
                print(f"[ML STARTUP] [OK] Modelo treinado com sucesso! Acc: {accuracy:.2%}", flush=True)
                print(f"============================================================", flush=True)
            elif train_result.get("status") == "INSUFFICIENT_DATA":
                print(f"[ML STARTUP] [WARN] Dados insuficientes ({total_samples}/{ML_MIN_SAMPLES}). Sistema em modo FALLBACK.", flush=True)
            else:
                print(f"[ML STARTUP] [ERROR] Erro no treinamento: {train_result}", flush=True)
        except Exception as e:
            print(f"[ML STARTUP] [CRITICAL] Falha no treinamento: {e}", flush=True)
            # Even if ML fails, we might want to let system pass if we allow fallback? 
            # Currently generator checks for ML before using it, so it's safe to proceed.
    else:
        if not db_connected:
             print("[ML STARTUP] Skipped - Database not connected", flush=True)

    # === STEP 5: System Ready ===
    try:
        generator.set_system_ready(True)
        
        # Link Elite Agent to Strategist Agent data for display
        if hasattr(generator, 'bankroll_manager') and generator.bankroll_manager:
            generator.strategist_report["elite_learning"] = generator.bankroll_manager.elite_agent.get_status()
        
        print("=" * 60, flush=True)
        print("[INIT] SYSTEM FULLY OPERATIONAL - Scanning Active", flush=True)
        print("=" * 60, flush=True)
    except Exception as e:
         print(f"[INIT] Error setting system ready: {e}", flush=True)

# Start delayed initialization thread
print("[BOOT] Launching delayed init thread...", flush=True)
threading.Thread(target=delayed_init, daemon=True).start()


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


@app.route("/api/system/health")
def get_system_health():
    """Get system health vitals and AI assessment"""
    try:
        return jsonify(health_monitor.get_full_report())
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500


@app.route("/api/system/agents")
def get_agents_status():
    """Get status and metrics for all specialized agents"""
    try:
        # Aggregate data from core agents
        agents = [
            {
                "id": "technical_agent",
                "name": "Scout Técnico",
                "status": "ATIVO",
                "role": "Análise de Preço & MTF",
                "last_action": "Monitorando Pivot/EMA",
                "details": "Conectado à Bybit API. Analisando 109 pares em 3 timeframes (30m, 1h, 4h).",
                "comm_status": "ONLINE"
            },
            {
                "id": "fundamental_agent",
                "name": "Sentinela de Fluxo",
                "status": "ATIVO",
                "role": "Liquidez & Order Flow",
                "last_action": "Analisando CVD/OI",
                "details": "Processando dados institutional de Open Interest e Long/Short Ratio.",
                "comm_status": "ONLINE"
            },
            {
                "id": "risk_agent",
                "name": "Governador de Risco",
                "status": "ATIVO",
                "role": "Relação R:R & Proteção",
                "last_action": "Validando Stop Loss",
                "details": "Supervisionando limites de perda máxima e proteção de capital.",
                "comm_status": "ONLINE"
            },
            {
                "id": "market_info_agent",
                "name": "Âncora de Mercado",
                "status": "ATIVO",
                "role": "Notícias & Listagens",
                "last_action": "Checando Bybit/RSS",
                "details": "Monitorando Bybit Announcements e feeds RSS (CoinTelegraph, Coindesk).",
                "comm_status": "ONLINE"
            },
            {
                "id": "ml_supervisor_agent",
                "name": "Supervisor ML",
                "status": "ATIVO" if generator.ml_predictor and generator.ml_predictor.model else "WARMUP",
                "role": "Integridade do Modelo",
                "last_action": "Gerindo Model Care",
                "details": f"Status: {getattr(generator.ml_supervisor_agent, 'model_status', 'N/A')}. Analisando amostras para otimização contínua.",
                "comm_status": "ONLINE"
            },
            {
                "id": "bankroll_captain_agent",
                "name": "Capitão da Banca",
                "status": "ATIVO",
                "role": "Sniper & Gestão 20%",
                "last_action": "Monitorando Slots",
                "details": f"Slots: {getattr(generator.llm_brain.council.bankroll_captain, 'active_trades', {}) if hasattr(generator, 'llm_brain') and hasattr(generator.llm_brain, 'council') else 'N/A'}. Limite de Risco: 20%.",
                "comm_status": "ONLINE"
            }
        ]
        
        # Add Council Debate if available
        council_data = getattr(generator, "last_council_debate", None)
        
        return jsonify({
            "status": "OK",
            "agents": agents,
            "council_debate": council_data,
            "system_readiness": generator.system_ready
        })
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500


@app.route("/api/system/logs")
def get_system_logs():
    """Get real logs from agents and trades for the UI"""
    try:
        logs = []
        
        if not generator.db.is_connected() or not generator.db.client:
             return jsonify({
                "status": "BOOTING", 
                "message": "System is initializing...", 
                "logs": []
             })

        # 1. Fetch recent trade telemetry (The "War Room" feed)
        recent_trades = generator.db.client.table("bankroll_trades")\
            .select("symbol, telemetry, opened_at, status")\
            .order("opened_at", desc=True)\
            .limit(10)\
            .execute()
            
        if recent_trades.data:
            for t in recent_trades.data:
                msg = t.get("telemetry") or f"Trade {t['status']} on {t['symbol']}"
                logs.append({
                    "id": f"trade_{t['symbol']}_{t['opened_at']}",
                    "timestamp": datetime.fromisoformat(t['opened_at']).strftime("%H:%M:%S"),
                    "agent": "elite_manager",
                    "message": f"🦅 {msg}"
                })

        # 2. Merge Real-Time Logs (Memory Buffer)
        # Using memory buffer guarantees visibility even if DB write fails
        logs.extend(list(RECENT_LOGS))

        # 2. Fetch recent learning/insights
        try:
            learning = generator.db.client.table("llm_insights")\
                .select("*")\
                .order("created_at", desc=True)\
                .limit(5)\
                .execute()
                
            if learning.data:
                 for l in learning.data:
                    # Parse combined type "agent_id|insight_type"
                    raw_type = l.get('insight_type', 'strategist|INFO')
                    parts = raw_type.split('|')
                    
                    if len(parts) > 1:
                        agent_id = parts[0]
                        insight = parts[1]
                    else:
                        agent_id = "strategist"
                        insight = raw_type
                    
                    # Map to UI icon
                    agent_name = agent_id
                    
                    # Message from content JSONB
                    content = l.get('content') or {}
                    msg = content.get('message') or insight
                    
                    logs.append({
                        "id": f"learn_{l['id']}",
                        "timestamp": datetime.fromisoformat(l['created_at']).strftime("%H:%M:%S"),
                        "agent": agent_name,
                        "message": f"🧠 {insight}: {msg}"
                    })
        except Exception as e:
            print(f"[LOGS] Error fetching agent learning from llm_insights: {e}")
        
        # 3. Add current Risk Status log
        if hasattr(generator, 'bankroll_manager') and generator.bankroll_manager:
            status = generator.bankroll_manager.get_status()
            if status:
                slots = status.get('active_slots_used', 0)
                logs.append({
                    "id": "status_monitor",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "agent": "governor",
                    "message": f"⚖️ Monitoramento de Risco: Utilizando {slots}/10 slots. Banca: ${status.get('current_balance', 0):.2f}"
                })

        # Sort by timestamp (string sort works for HH:MM:SS effectively for today's logs)
        logs.sort(key=lambda x: x['timestamp'])
        
        return jsonify({
            "status": "OK",
            "logs": logs
        })
    except Exception as e:
        print(f"[LOGS ERROR] {e}")
        return jsonify({"status": "ERROR", "message": str(e)}), 500

@app.route("/api/test/log", methods=["POST"])
def test_log_injection():
    """Manually inject a log for testing UI visibility"""
    try:
        data = request.json or {}
        message = data.get("message", "Test Log")
        agent = data.get("agent", "gemini")
        
        # Inject into buffer
        log_entry = {
            "id": f"test_{int(time.time()*1000)}",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "agent": agent,
            "message": f"🧪 TEST: {message}"
        }
        RECENT_LOGS.append(log_entry)
        print(f"[TEST] Injected log: {message}", flush=True)
        
        return jsonify({"status": "OK", "log": log_entry})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500


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
    try:
        min_score = request.args.get("min_score", 0, type=int)
        
        signals = generator.get_active_signals()
        
        # Filter by minimum score if specified
        if min_score > 0:
            signals = [s for s in signals if s["score"] >= min_score]
        
        return jsonify(sanitize_for_json({
            "signals": signals,
            "count": len(signals),
            "filter": {"min_score": min_score}
        }))
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[API ERROR] /api/signals failed: {e}", flush=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/history")
def get_history():
    """Get signal history"""
    try:
        limit = request.args.get("limit", 50, type=int)
        hours = request.args.get("hours", 0, type=int)
        
        history = generator.get_signal_history(limit=limit, hours_limit=hours)
        print(f"[API] /api/history: limit={limit}, hours={hours} -> returning {len(history)} items", flush=True)
        return jsonify(sanitize_for_json({
            "history": history,
            "count": len(history)
        }))
    except Exception as e:
        print(f"[API ERROR] /api/history failed: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/debug/state")
def debug_state():
    """Debug route to check internal state"""
    try:
        return jsonify({
            "active_count": len(generator.active_signals),
            "history_count": len(generator.signal_history),
            "monitored_pairs": len(generator.monitored_pairs),
            "system_ready": generator.system_ready,
            "db_connected": generator.db.is_connected(),
            "sample_signal": generator.signal_history[0] if generator.signal_history else None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =============================================================================
# Frontend Routes (Moved down to avoid shadowing API)
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
    # If the path starts with /api/, don't serve index.html, it's a real 404 for an API
    if request.path.startswith('/api/'):
        return jsonify({"error": "API route not found"}), 404

    if os.path.exists(os.path.join(app.static_folder, 'index.html')):
        return send_from_directory(app.static_folder, 'index.html')
    return jsonify({"error": "Not found"}), 404




@app.route("/api/stats")
def get_stats():
    """Get summary statistics"""
    try:
        print("[DEBUG] Entered get_stats request handler", flush=True)
        stats = generator.get_stats()
        return jsonify(sanitize_for_json(stats))
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[API ERROR] /api/stats failed: {e}", flush=True)
        return jsonify({"error": str(e)}), 500


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
        return jsonify(sanitize_for_json({
            "found": True,
            "signal": signal
        }))
    
    return jsonify({
        "found": False,
        "message": f"No signal for {symbol} at this time"
    })


@app.route("/api/chart/klines/<symbol>")
def get_klines_data(symbol):
    """Get candlestick data for a symbol (v2 robust route)"""
    try:
        interval = request.args.get("interval", "30")
        limit = request.args.get("limit", 150, type=int)
        
        candles = generator.client.get_klines(symbol.upper(), interval, limit)
        return jsonify(sanitize_for_json({
            "symbol": symbol.upper(),
            "interval": interval,
            "candles": candles,
            "count": len(candles)
        }))
    except Exception as e:
        print(f"[CHART API ERROR] {e}", flush=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/btc/regime")
def get_btc_regime():
    """Get current BTC market regime and dynamic TP/SL targets"""
    try:
        regime_info = generator.btc_tracker.get_regime_info()
        return jsonify(sanitize_for_json({
            "status": "OK",
            **regime_info,
            "regime_details": generator.current_regime_details
        }))
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
# Bankroll Management Routes
# =============================================================================

@app.route("/api/bankroll/status")
def get_bankroll_status():
    """Get active bankroll status"""
    try:
        if not generator.bankroll_manager:
              return jsonify({"status": "DISABLED", "message": "Bankroll Manager disabled"}), 503
        
        status = generator.bankroll_manager.get_status()
        if status:
            # Compatibility fix for UI (initial_balance/total_pnl)
            status['initial_balance'] = status.get('base_balance', 1000.0)
            status['total_pnl'] = status.get('current_balance', 1000.0) - status.get('initial_balance', 1000.0)
            status['roi_percentage'] = status.get('win_rate', 0.0)
            
        return jsonify(sanitize_for_json(status if status else {}))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === NEW: Push Notification Routes ===

@app.route("/api/push/vapid-public-key")
def get_vapid_public_key():
    """Get the VAPID public key for subscription"""
    key = os.environ.get("VAPID_PUBLIC_KEY")
    if not key:
        return jsonify({"error": "VAPID key not configured"}), 503
    return jsonify({"publicKey": key})

@app.route("/api/push/subscribe", methods=["POST"])
def subscribe_push():
    """Register a new PWA push subscription"""
    try:
        data = request.json
        subscription = data.get("subscription")
        user_id = data.get("userId", "default_user")
        
        if not subscription:
            return jsonify({"error": "No subscription provided"}), 400
            
        success = push_service.save_subscription(user_id, subscription)
        if success:
            # Send an immediate confirmation push
            push_service.send_notification(
                user_id, 
                "🦅 10D Conectado!", 
                "Pronto. Agora o Capitão te avisará de cada GAIN no seu celular."
            )
            return jsonify({"success": True}), 201
        else:
            return jsonify({"error": "Failed to save subscription"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/bankroll/trades")
def get_bankroll_trades():
    """Get bankroll trades history"""
    try:
        print("[DEBUG] /api/bankroll/trades: Entered", flush=True)
        limit = request.args.get("limit", 50, type=int)
        # Fetch directly from DB via manager's connection for simplicity
        res = generator.db.client.table("bankroll_trades").select("*").order("opened_at", desc=True).limit(limit).execute()
        trades = [dict(t) for t in res.data]
        print(f"[DEBUG] /api/bankroll/trades: Fetched {len(trades)} trades (converted to dicts)", flush=True)
        
        # Inject live prices for OPEN trades
        open_trades = [t for t in trades if t["status"] == "OPEN"]
        if open_trades:
            print(f"[DEBUG] /api/bankroll/trades: Fetching tickers for {len(open_trades)} open trades", flush=True)
            tickers = generator.client.get_all_tickers()
            ticker_map = {t["symbol"]: float(t["lastPrice"]) for t in tickers if "symbol" in t and "lastPrice" in t}
            
            for trade in open_trades:
                symbol = trade["symbol"]
                if symbol in ticker_map:
                    current_price = ticker_map[symbol]
                    entry_price = trade["entry_price"]
                    direction = trade.get("direction", "SHORT")
                    
                    # Calculate ROI
                    pnl_pct = (current_price - entry_price) / entry_price if direction == "LONG" else (entry_price - current_price) / entry_price
                    roi = pnl_pct * 50 # Default leverage 50x
                    
                # Inject for frontend
                    trade["live_price"] = current_price
                    trade["live_roi"] = round(roi * 100, 2)
                    
                    # If DB is missing these, we provide them as fallbacks
                    if not trade.get("current_price"): trade["current_price"] = current_price
                    if not trade.get("current_roi"): trade["current_roi"] = trade["live_roi"]

        # --- UNIVERSAL PASS: Inject SL/TP for ALL trades ---
        for trade in trades:
            entry_price = trade["entry_price"]
            direction = trade.get("direction", "SHORT")
            
            # Fetch Signal Data for SL/TP if missing (always missing in v1 schema)
            if not trade.get("stop_loss") or not trade.get("take_profit"):
                 try:
                     sig = generator.db.client.table("signals").select("id, stop_loss, take_profit").eq("id", trade["signal_id"]).single().execute()
                     if sig and sig.data:
                         trade["stop_loss"] = float(sig.data.get("stop_loss", 0))
                         trade["take_profit"] = float(sig.data.get("take_profit", 0))
                 except:
                     pass
            
            # Fallback defaults if still missing (1% SL / 2% TP)
            if not trade.get("stop_loss"):
                trade["stop_loss"] = entry_price * 1.01 if direction == "SHORT" else entry_price * 0.99
                print(f"[DEBUG] Calculated Fallback SL for {trade['symbol']}: {trade['stop_loss']}", flush=True)
            if not trade.get("take_profit"):
                trade["take_profit"] = entry_price * 0.98 if direction == "SHORT" else entry_price * 1.02
                print(f"[DEBUG] Calculated Fallback TP for {trade['symbol']}: {trade['take_profit']}", flush=True)
        
        print("[DEBUG] /api/bankroll/trades: Sanitizing and returning", flush=True)
        return jsonify(sanitize_for_json(trades))
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[ERROR] /api/bankroll/trades: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/bankroll/reset", methods=["POST"])
def reset_bankroll():
    """Reset simulation (Dev tool) - New Schema V2"""
    try:
        # Reset bankroll_status to $20
        generator.db.client.table("bankroll_status").update({
            "current_balance": 20.0,
            "base_balance": 20.0,
            "entry_size_usd": 1.0,
            "trades_in_cycle": 0,
            "total_trades": 0,
            "cycle_number": 1,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0
        }).eq("id", "elite_bankroll").execute()
        
        # Clear trades
        try:
             generator.db.client.table("bankroll_trades").delete().neq("symbol", "WIPE").execute()
        except:
             pass 
        
        return jsonify({"message": "Bankroll reset to $20.0 (Cycle 1)"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# Main Entry Point (for local development)
# =============================================================================

if __name__ == "__main__":
    # Get port from environment variable (required for Google Cloud Run)
    port = int(os.environ.get("PORT", API_PORT))
    
    # Start the server
    print(f"\n[SERVER] ATTEMPTING TO START on http://{API_HOST}:{port}", flush=True)
    print(f"[SERVER] Threads active: {threading.active_count()}", flush=True)
    print("=" * 60, flush=True)
    
    try:
        app.run(host=API_HOST, port=port, debug=False, threaded=True, use_reloader=False)
    except Exception as e:
        print(f"[SERVER CRASH] Failed to start Flask: {e}", flush=True)
