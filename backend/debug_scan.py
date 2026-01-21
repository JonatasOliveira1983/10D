import sys
import os
import time

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.signal_generator import SignalGenerator

print("Initializing SignalGenerator...")
try:
    generator = SignalGenerator()
    print("SignalGenerator initialized.")
    
    # Manually set system ready for testing
    generator.system_ready = True
    print("System set to READY.")
    
    # Initialize pairs (required for scan)
    print("Initializing pairs...")
    generator.initialize(pair_limit=5) # Limit to 5 for speed
    
    print("Starting scan_all_pairs...")
    signals = generator.scan_all_pairs()
    
    print(f"Scan complete. Found {len(signals)} signals.")
    for sig in signals:
        print(f"Signal: {sig['symbol']} {sig['direction']} - Score: {sig['score']}")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
