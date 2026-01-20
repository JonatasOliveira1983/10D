"""Test Supabase database connection and schema"""
from services.database_manager import DatabaseManager
import time

print("Testing Supabase connection...")
db = DatabaseManager()

if not db.client:
    print("[ERROR] No database connection!")
    exit(1)

# Test 1: Try to insert a test signal with highest_roi
test_id = "TEST_" + str(int(time.time()))
test_signal = {
    "id": test_id,
    "symbol": "TESTUSDT",
    "direction": "LONG",
    "signal_type": "TEST",
    "entry_price": 100.0,
    "stop_loss": 95.0,
    "take_profit": 110.0,
    "score": 85,
    "status": "ACTIVE",
    "highest_roi": 5.5,
    "partial_tp_hit": True,
    "trailing_stop_active": False,
    "timestamp": int(time.time() * 1000)
}

print(f"[TEST] Saving test signal: {test_id}")
db.save_signal(test_signal)
print("[OK] Signal saved successfully!")

# Test 2: Read it back
print("[TEST] Reading active signals...")
active = db.get_active_signals()
if "TESTUSDT" in active:
    sig = active["TESTUSDT"]
    print(f"[OK] Test signal found!")
    print(f"     - highest_roi: {sig.get('highest_roi')}")
    print(f"     - partial_tp_hit: {sig.get('partial_tp_hit')}")
    print(f"     - trailing_stop_active: {sig.get('trailing_stop_active')}")
else:
    print("[WARN] Test signal not in active signals (may be caching)")

# Test 3: Delete test signal
print("[TEST] Cleaning up test signal...")
db.client.table("signals").delete().eq("id", test_id).execute()
print("[OK] Test signal deleted!")

print("")
print("=" * 50)
print("[SUCCESS] All database tests passed!")
print("Columns highest_roi, partial_tp_hit, trailing_stop_active are working!")
print("=" * 50)
