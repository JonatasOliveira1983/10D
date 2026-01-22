
import sys
import os
import unittest.mock
import traceback
import time

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# MOCK LLM to avoid import hang
print("[DEBUG] Mocking services.llm_trading_brain...", flush=True)
mock_llm = unittest.mock.MagicMock()
sys.modules["services.llm_trading_brain"] = mock_llm

# Also mock database manager if needed, but let's try to keep it real first to test DB
# from services.database_manager import DatabaseManager

try:
    print("[DEBUG] Importing SignalGenerator...", flush=True)
    from services.signal_generator import SignalGenerator
    print("[DEBUG] Success.", flush=True)
except Exception as e:
    print(f"[FAIL] Import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

def main():
    print("=== STARTING MINIMAL DIAGNOSTIC ===")
    
    try:
        print("[TEST] Instantiating SignalGenerator...")
        generator = SignalGenerator()
        print("[OK] Instantiated.")
        
        # Test get_active_signals
        print("\n[TEST] get_active_signals()")
        active = generator.get_active_signals()
        print(f"[OK] Result: {len(active)} signals")
        
        # Test get_signal_history
        print("\n[TEST] get_signal_history(limit=10)")
        history = generator.get_signal_history(limit=10)
        print(f"[OK] Result: {len(history)} signals")
        
        # Test get_stats (we need to find where it is defined, assuming it exists)
        print("\n[TEST] get_stats()")
        if hasattr(generator, "get_stats"):
            stats = generator.get_stats()
            print(f"[OK] Result: {stats}")
        else:
            print("[WARN] get_stats method not found")

    except Exception as e:
        print(f"\n[CRITICAL ERROR] Caught exception during execution:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
