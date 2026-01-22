
import sys
import os
import time
import traceback

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("[DEBUG] importing services...", flush=True)

try:
    from services.database_manager import DatabaseManager
    from services.signal_generator import SignalGenerator
except Exception as e:
    print(f"[CRITICAL] Import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

def test_db_connection():
    print("\n[TEST] Testing Database Connection...")
    try:
        db = DatabaseManager()
        # Wait a bit for async connection
        max_wait = 10
        start = time.time()
        while not db.is_connected() and time.time() - start < max_wait:
            time.sleep(1)
        
        if db.is_connected():
            print("[OK] Database connected.")
            return db
        else:
            print("[FAIL] Database failed to connect within timeout.")
            return db # Return anyway to see if calls fail gracefully
    except Exception as e:
        print(f"[FAIL] Database initialization error: {e}")
        traceback.print_exc()
        return None

def test_signal_generator_history(generator):
    print("\n[TEST] Testing get_signal_history...")
    try:
        history = generator.get_signal_history(limit=10, hours_limit=240)
        print(f"[OK] History fetched: {len(history)} items")
    except Exception as e:
        print(f"[FAIL] get_signal_history failed: {e}")
        traceback.print_exc()

def test_active_signals(generator):
    print("\n[TEST] Testing get_active_signals...")
    try:
        active = generator.get_active_signals()
        print(f"[OK] Active fetched: {len(active)} items")
    except Exception as e:
        print(f"[FAIL] get_active_signals failed: {e}")
        traceback.print_exc()

def main():
    print("=== STARTING DIAGNOSTIC ===")
    
    # 1. Test DB
    db = test_db_connection()
    
    # 2. Initialize SignalGenerator (this might fail if dependencies are missing)
    print("\n[TEST] Initializing SignalGenerator...")
    try:
        generator = SignalGenerator()
        # Inject the DB we just created to be sure, or let it use its own
        if db:
            generator.db = db 
        print("[OK] SignalGenerator initialized.")
    except Exception as e:
        print(f"[FAIL] SignalGenerator init failed: {e}")
        traceback.print_exc()
        return
        
    # 3. Test Flask-like calls
    test_active_signals(generator)
    test_signal_generator_history(generator)
    
    print("\n=== DIAGNOSTIC COMPLETE ===")

if __name__ == "__main__":
    main()
