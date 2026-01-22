"""
Quick test to check if backend is running and test BTC Regime endpoint
"""

import requests
import json

print("=" * 60)
print("BACKEND API TEST")
print("=" * 60)

# Test 1: Check if backend is running
print("\n[TEST 1] Checking if backend is running...")
try:
    response = requests.get("http://localhost:5001/api/version", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Backend is running!")
        print(f"   Version: {data.get('version')}")
        print(f"   Monitored pairs: {data.get('monitored_pairs_count')}")
        print(f"   Status: {data.get('status')}")
    else:
        print(f"❌ Backend returned status code: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ Backend is NOT running (connection refused)")
    print("   Please start the backend with: python app.py")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 2: Test BTC Regime endpoint
print("\n[TEST 2] Testing BTC Regime Tracker endpoint...")
try:
    response = requests.get("http://localhost:5001/api/btc/regime", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ BTC Regime endpoint working!")
        print(f"\n   Current Regime: {data.get('regime')}")
        print(f"   TP Target: {data.get('tp_pct')}%")
        print(f"   SL Target: {data.get('sl_pct')}%")
        print(f"   Priority: {data.get('priority')}")
        print(f"   Description: {data.get('description')}")
        
        if data.get('high_24h'):
            print(f"\n   24h High: ${data.get('high_24h')}")
            print(f"   24h Low: ${data.get('low_24h')}")
        
        if data.get('regime_details'):
            print(f"\n   Regime Details:")
            details = data.get('regime_details', {})
            for key, value in details.items():
                print(f"      {key}: {value}")
    else:
        print(f"❌ Endpoint returned status code: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Test signals endpoint
print("\n[TEST 3] Testing signals endpoint...")
try:
    response = requests.get("http://localhost:5001/api/signals", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Signals endpoint working!")
        print(f"   Active signals: {data.get('count')}")
        
        if data.get('count', 0) > 0:
            print(f"\n   First signal:")
            signal = data.get('signals', [])[0]
            print(f"      Symbol: {signal.get('symbol')}")
            print(f"      Score: {signal.get('score')}")
            print(f"      Type: {signal.get('signal_type')}")
            print(f"      Entry: ${signal.get('entry_price')}")
            print(f"      TP: ${signal.get('tp_price')}")
            print(f"      SL: ${signal.get('sl_price')}")
    else:
        print(f"❌ Endpoint returned status code: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("TESTS COMPLETED")
print("=" * 60)
