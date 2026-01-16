"""
Minimal Flask server to test BTC Regime Tracker endpoint
This bypasses the full app.py initialization
"""

from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("[MINIMAL SERVER] Starting minimal Flask server...")

app = Flask(__name__)
CORS(app)

# Import only what we need
from services.btc_regime_tracker import BTCRegimeTracker
from services.bybit_api import BybitAPI

print("[MINIMAL SERVER] Imports successful")

# Initialize tracker and API
tracker = BTCRegimeTracker()
api = BybitAPI()

print("[MINIMAL SERVER] Services initialized")

@app.route("/api/version")
def get_version():
    return jsonify({
        "version": "MINIMAL-TEST-SERVER",
        "status": "running",
        "message": "Testing BTC Regime Tracker"
    })

@app.route("/api/btc/regime")
def get_btc_regime():
    """Get current BTC market regime"""
    try:
        # Fetch BTC candles
        print("[REGIME] Fetching BTC candles...")
        btc_candles_30m = api.get_kline("BTCUSDT", "30", limit=100)
        
        if not btc_candles_30m:
            return jsonify({
                "status": "ERROR",
                "message": "Failed to fetch BTC data"
            }), 500
        
        print(f"[REGIME] Got {len(btc_candles_30m)} candles")
        
        # Detect regime
        regime, details = tracker.detect_regime(btc_candles_30m)
        print(f"[REGIME] Detected: {regime}")
        
        # Get regime info
        regime_info = tracker.get_regime_info()
        
        return jsonify({
            "status": "OK",
            "regime": regime,
            "tp_pct": regime_info['tp_pct'],
            "sl_pct": regime_info['sl_pct'],
            "priority": regime_info['priority'],
            "description": regime_info['description'],
            "high_24h": regime_info.get('high_24h'),
            "low_24h": regime_info.get('low_24h'),
            "regime_details": details
        })
    except Exception as e:
        print(f"[REGIME ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "ERROR",
            "message": str(e)
        }), 500

@app.route("/api/test/decoupling/<symbol>")
def test_decoupling(symbol):
    """Test decoupling score for a symbol"""
    try:
        # Fetch candles
        print(f"[DECOUPLING] Testing {symbol}...")
        alt_candles = api.get_kline(symbol, "30", limit=30)
        btc_candles = api.get_kline("BTCUSDT", "30", limit=30)
        
        if not alt_candles or not btc_candles:
            return jsonify({
                "status": "ERROR",
                "message": "Failed to fetch candle data"
            }), 500
        
        # Calculate decoupling score
        score = tracker.calculate_decoupling_score(alt_candles, btc_candles, lookback=20)
        
        return jsonify({
            "status": "OK",
            "symbol": symbol,
            "decoupling_score": score,
            "interpretation": "HIGH - Independent" if score > 0.5 else "LOW - Follows BTC",
            "recommendation": "Good for RANGING regime" if score > 0.5 else "Better for TRENDING regime"
        })
    except Exception as e:
        print(f"[DECOUPLING ERROR] {e}")
        return jsonify({
            "status": "ERROR",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 MINIMAL SERVER READY")
    print("=" * 60)
    print("\nEndpoints:")
    print("  - http://localhost:5001/api/version")
    print("  - http://localhost:5001/api/btc/regime")
    print("  - http://localhost:5001/api/test/decoupling/<SYMBOL>")
    print("\n" + "=" * 60 + "\n")
    
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
