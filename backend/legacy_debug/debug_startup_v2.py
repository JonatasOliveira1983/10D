
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Starting debug...", flush=True)
try:
    from flask import Flask
    print("Flask imported", flush=True)
    
    print("Importing SignalGenerator...", flush=True)
    from services.signal_generator import SignalGenerator
    print("SignalGenerator imported", flush=True)
    
    print("Instantiating SignalGenerator...", flush=True)
    sg = SignalGenerator()
    print("SignalGenerator instantiated", flush=True)
    
except Exception as e:
    print(f"Error: {e}", flush=True)
    import traceback
    traceback.print_exc()
