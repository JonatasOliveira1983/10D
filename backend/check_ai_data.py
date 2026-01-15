import os
import time
from dotenv import load_dotenv
from services.database_manager import DatabaseManager

load_dotenv()
db = DatabaseManager()

print("--- AI Features Audit ---")
try:
    history = db.get_signal_history(limit=500, hours_limit=0)
    total = len(history)
    print(f"Total Signals: {total}")
    
    with_features = 0
    with_status = 0
    valid_labeled_with_features = 0
    
    for s in history:
        features = s.get("ai_features")
        status = s.get("status")
        
        if features and isinstance(features, dict) and len(features) > 0:
            with_features += 1
            if status in ["TP_HIT", "SL_HIT"]:
                valid_labeled_with_features += 1
                
        if status in ["TP_HIT", "SL_HIT"]:
            with_status += 1
            
    print(f"Signals with AI Features: {with_features} ({with_features/total*100:.1f}%)")
    print(f"Signals Finalized (TP/SL): {with_status}")
    print(f"READY FOR AI (features + finalized): {valid_labeled_with_features}")
    
    if valid_labeled_with_features == 0:
        print("\nCONCLUSION: AI Audit is empty because no signal combines 'finalized status' AND 'ai_features'.")
        print("Old signals lack features. New signals might not be finalized yet.")

except Exception as e:
    print(f"Error: {e}")
