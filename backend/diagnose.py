"""
Diagnostic script to find where Python is hanging
"""

print("Step 1: Starting script...")

print("Step 2: Importing sys...")
import sys

print("Step 3: Importing os...")
import os

print("Step 4: Importing time...")
import time

print("Step 5: Trying to import Flask...")
try:
    from flask import Flask
    print("✅ Flask imported successfully")
except Exception as e:
    print(f"❌ Flask import failed: {e}")
    sys.exit(1)

print("Step 6: Trying to import flask_cors...")
try:
    from flask_cors import CORS
    print("✅ CORS imported successfully")
except Exception as e:
    print(f"❌ CORS import failed: {e}")
    sys.exit(1)

print("Step 7: Adding path...")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Step 8: Importing config...")
try:
    from config import API_HOST, API_PORT
    print(f"✅ Config imported - API_HOST={API_HOST}, API_PORT={API_PORT}")
except Exception as e:
    print(f"❌ Config import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Step 9: Importing SignalGenerator...")
try:
    from services.signal_generator import SignalGenerator
    print("✅ SignalGenerator imported successfully")
except Exception as e:
    print(f"❌ SignalGenerator import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ ALL IMPORTS SUCCESSFUL!")
print("The problem is NOT with imports.")
