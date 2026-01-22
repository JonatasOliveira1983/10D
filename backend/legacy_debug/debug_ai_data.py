import os
import time
from dotenv import load_dotenv
from services.database_manager import DatabaseManager
from collections import Counter
import sys

# Load env vars
load_dotenv()

try:
    db = DatabaseManager()
    print("CONNECTION: OK")
except Exception as e:
    print(f"CONNECTION: FAILED - {e}")
    sys.exit(1)

print("--- Inspecting AI Data in Production DB ---")
try:
    # Fetch raw latest history
    history = db.get_signal_history(limit=200, hours_limit=0)
    print(f"Total rows fetched: {len(history)}")
    
    if not history:
        print("RESULT: Database is empty (or get_signal_history returned nothing).")
        sys.exit(0)

    # Counters
    status_counts = Counter()
    has_features_count = 0
    valid_labeled_count = 0
    valid_labeled_with_features = 0

    for s in history:
        status = s.get("status", "UNKNOWN")
        features = s.get("ai_features", {})
        
        status_counts[status] += 1
        
        has_feat = bool(features)  # True if not empty/None
        if has_feat:
            has_features_count += 1
            
        is_labeled = status in ["TP_HIT", "SL_HIT"]
        if is_labeled:
            valid_labeled_count += 1
            if has_feat:
                valid_labeled_with_features += 1

    print("\n--- Statistics ---")
    print(f"Status Distribution: {dict(status_counts)}")
    print(f"Signals with 'ai_features': {has_features_count}")
    print(f"Signals with Final Status (TP_HIT/SL_HIT): {valid_labeled_count}")
    print(f"ELIGIBLE FOR AI (Labeled + Features): {valid_labeled_with_features}")
    
    if valid_labeled_with_features == 0:
        print("\nDIAGNOSIS: No eligible data for AI Audit.")
        if valid_labeled_count > 0 and has_features_count == 0:
            print("REASON: Signals exist and are labeled, but 'ai_features' are missing.")
        elif valid_labeled_count == 0:
            print("REASON: No signals have reached TP_HIT or SL_HIT yet (all Active/Expired).")
    else:
        print("\nDIAGNOSIS: Data exists. AI Audit should allow calculation.")
        
    # Sample check
    print("\n--- Sample Signal Debug ---")
    if history:
        sample = history[0]
        print(f"Latest Signal ID: {sample.get('id')}")
        print(f"Status: {sample.get('status')}")
        print(f"Features Payload: {str(sample.get('ai_features'))[:100]}...")

except Exception as e:
    print(f"CRASH: {e}")
    import traceback
    traceback.print_exc()
