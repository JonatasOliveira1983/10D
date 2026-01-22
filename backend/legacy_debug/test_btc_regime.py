"""
Test script for BTC Regime Tracker
Tests the regime detection and decoupling score calculation
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("BTC REGIME TRACKER - TEST SCRIPT")
print("=" * 60)

# Test 1: Import the module
print("\n[TEST 1] Importing BTCRegimeTracker...")
try:
    from services.btc_regime_tracker import BTCRegimeTracker
    print("[OK] Import successful")
except Exception as e:
    print(f"[FAIL] Import failed: {e}")
    sys.exit(1)

# Test 2: Initialize the tracker
print("\n[TEST 2] Initializing tracker...")
try:
    tracker = BTCRegimeTracker()
    print(f"[OK] Tracker initialized")
    print(f"   Default regime: {tracker.current_regime}")
    tp, sl = tracker.get_dynamic_targets()
    print(f"   Default TP/SL: {tp*100}% / {sl*100}%")
except Exception as e:
    print(f"[FAIL] Initialization failed: {e}")
    sys.exit(1)

# Test 3: Create mock BTC data for RANGING regime
print("\n[TEST 3] Testing RANGING regime detection...")
try:
    # Create 50 candles with tight range (low volatility)
    base_price = 50000
    ranging_candles = []
    for i in range(50):
        # Price oscillates in a tight 1% range
        price = base_price + (i % 10 - 5) * 50  # ±250 from base
        ranging_candles.append({
            "open": price - 10,
            "high": price + 20,
            "low": price - 20,
            "close": price,
            "volume": 1000 + (i % 5) * 100
        })
    
    regime, details = tracker.detect_regime(ranging_candles)
    print(f"[OK] Regime detected: {regime}")
    print(f"   Details: BB Width={details.get('bb_width')}%, ATR={details.get('atr_pct')}%")
    print(f"   Trigger: {details.get('trigger')}")
    
    regime_info = tracker.get_regime_info()
    print(f"   TP/SL: {regime_info['tp_pct']}% / {regime_info['sl_pct']}%")
    print(f"   Priority: {regime_info['priority']}")
    print(f"   Description: {regime_info['description']}")
except Exception as e:
    print(f"[FAIL] RANGING test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Create mock BTC data for TRENDING regime
print("\n[TEST 4] Testing TRENDING regime detection...")
try:
    # Create 50 candles with clear uptrend
    trending_candles = []
    for i in range(50):
        price = 50000 + i * 200  # Steady uptrend
        trending_candles.append({
            "open": price - 50,
            "high": price + 100,
            "low": price - 100,
            "close": price,
            "volume": 1000 + (i % 5) * 100
        })
    
    regime, details = tracker.detect_regime(trending_candles)
    print(f"[OK] Regime detected: {regime}")
    print(f"   Details: EMA Distance={details.get('ema_distance')}%")
    print(f"   Trigger: {details.get('trigger')}")
    if 'trend_direction' in details:
        print(f"   Direction: {details['trend_direction']}")
    
    regime_info = tracker.get_regime_info()
    print(f"   TP/SL: {regime_info['tp_pct']}% / {regime_info['sl_pct']}%")
except Exception as e:
    print(f"[FAIL] TRENDING test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Create mock BTC data for BREAKOUT regime
print("\n[TEST 5] Testing BREAKOUT regime detection...")
try:
    # Create 50 candles with breakout pattern
    breakout_candles = []
    for i in range(48):
        # First 48 candles in range
        price = 50000 + (i % 10 - 5) * 50
        breakout_candles.append({
            "open": price - 10,
            "high": price + 20,
            "low": price - 20,
            "close": price,
            "volume": 1000
        })
    
    # Last 2 candles: breakout with high volume
    for i in range(2):
        price = 51000 + i * 500  # Breaking above 24h high
        breakout_candles.append({
            "open": price - 100,
            "high": price + 200,
            "low": price - 150,
            "close": price,
            "volume": 5000  # 5x normal volume
        })
    
    regime, details = tracker.detect_regime(breakout_candles)
    print(f"[OK] Regime detected: {regime}")
    print(f"   Details: Volume Ratio={details.get('volume_ratio')}x, ATR Expansion={details.get('atr_expansion')}x")
    print(f"   Trigger: {details.get('trigger')}")
    if 'breakout_direction' in details:
        print(f"   Direction: {details['breakout_direction']}")
    print(f"   24h High: ${details.get('high_24h')}, Current: ${details.get('current_price')}")
    
    regime_info = tracker.get_regime_info()
    print(f"   TP/SL: {regime_info['tp_pct']}% / {regime_info['sl_pct']}%")
except Exception as e:
    print(f"[FAIL] BREAKOUT test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Test decoupling score
print("\n[TEST 6] Testing decoupling score calculation...")
try:
    # Create BTC candles (flat)
    btc_candles = []
    for i in range(30):
        price = 50000 + (i % 5 - 2) * 50  # BTC oscillating
        btc_candles.append({
            "close": price
        })
    
    # Create ALT candles (trending up while BTC flat)
    alt_candles = []
    for i in range(30):
        price = 1.0 + i * 0.02  # ALT going up
        alt_candles.append({
            "close": price
        })
    
    decoupling_score = tracker.calculate_decoupling_score(alt_candles, btc_candles, lookback=20)
    print(f"[OK] Decoupling score calculated: {decoupling_score}")
    print(f"   Interpretation: {'HIGH - Alt is independent' if decoupling_score > 0.5 else 'LOW - Alt follows BTC'}")
except Exception as e:
    print(f"[FAIL] Decoupling test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 7: Test Sniper Targets
print("\n[TEST 7] Testing SNIPER targets...")
try:
    tp, sl = tracker.get_dynamic_targets(force_sniper=True)
    print(f"[OK] Sniper targets: TP {tp*100}% / SL {sl*100}%")
    if tp == 0.06 and sl == 0.01:
        print("   ✅ Correct Sniper targets returned")
    else:
        print(f"   ❌ Incorrect Sniper targets: expected 6%/1%, got {tp*100}%/{sl*100}%")
except Exception as e:
    print(f"[FAIL] Sniper targets test failed: {e}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETED")
print("=" * 60)
