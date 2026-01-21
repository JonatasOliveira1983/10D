import sys
import os
import time
sys.path.append(os.path.join(os.getcwd(), 'backend'))

os.environ["SYNC_DB_INIT"] = "true" 

from services.database_manager import DatabaseManager
import json

db = DatabaseManager()
print("Connecting...")
time.sleep(5)

if db.client:
    try:
        # Query total count
        res_all = db.client.table("signals").select("id", count="exact").execute()
        total = res_all.count if hasattr(res_all, 'count') else len(res_all.data)
        print(f"Total signals in DB: {total}")

        # Query labeled signals (TP_HIT or SL_HIT)
        res_labeled = db.client.table("signals").select("id, payload, status").in_("status", ["TP_HIT", "SL_HIT"]).execute()
        labeled_data = res_labeled.data
        print(f"Total labeled signals: {len(labeled_data)}")

        ai_count = 0
        for row in labeled_data:
            payload = row.get("payload") or {}
            if "ai_features" in payload:
                ai_count += 1
        
        print(f"Total labeled signals with ai_features: {ai_count}")

        # Test the specific query used by MLPredictor
        print("\nTesting MLPredictor's specific query...")
        try:
            response = db.client.table("signals") \
                .select("payload") \
                .neq("status", "ACTIVE") \
                .not_.is_("payload->ai_features", "null") \
                .order("timestamp", desc=True) \
                .limit(500) \
                .execute()
            print(f"ML query results: {len(response.data)}")
        except Exception as e:
            print(f"ML query failed: {e}")

    except Exception as e:
        print(f"Error: {e}")
else:
    print("Database client not initialized.")
