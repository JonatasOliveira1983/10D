import os
import time
from dotenv import load_dotenv
from services.database_manager import DatabaseManager
from collections import Counter
from datetime import datetime

# Load env vars
load_dotenv()

db = DatabaseManager()

print("--- Inspecting Production DB ---")
try:
    # 1. Fetch raw latest history without time limit
    history = db.get_signal_history(limit=100, hours_limit=0)
    print(f"Total rows fetched (limit=100): {len(history)}")
    
    if not history:
        print("WARN: No history found at all.")
        exit()

    # 2. Analyze Timestamps
    timestamps = [s.get("timestamp", 0) for s in history]
    if timestamps:
        latest_ts = max(timestamps)
        oldest_ts = min(timestamps)
        now_ms = int(time.time() * 1000)
        
        print(f"Latest Signal: {datetime.fromtimestamp(latest_ts/1000)}")
        print(f"Oldest Signal (in batch): {datetime.fromtimestamp(oldest_ts/1000)}")
        print(f"Hours since latest signal: {(now_ms - latest_ts) / (1000*3600):.2f} hours")
    
    # 3. Analyze Status
    statuses = [s.get("status", "UNKNOWN") for s in history]
    print(f"Status Distribution: {Counter(statuses)}")
    
    # 4. Test 24h Filter
    recent = db.get_signal_history(limit=50, hours_limit=24)
    print(f"Signals in last 24h: {len(recent)}")
    
    # 5. Check AI Eligibility
    valid_labeled = [s for s in history if s.get("status") in ["TP_HIT", "SL_HIT"]]
    print(f"Valid Labeled Signals (TP/SL) for AI: {len(valid_labeled)}")

except Exception as e:
    print(f"CRASH: {e}")
