
import os
from dotenv import load_dotenv
from supabase import create_client

# Force load backend/.env
load_dotenv(dotenv_path="backend/.env", override=True)
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")

print(f"Checking data for: {url}")
client = create_client(url, key)

try:
    res = client.table("bankroll_status").select("*").eq("id", "elite_bankroll").execute()
    if res.data:
        print(f"✅ Status Found: {res.data[0]}")
    else:
        print("❌ bankroll_status table is EMPTY (No 'elite_bankroll' row).")
        # Try to insert it?
        print("Attempting to insert default row...")
        data = {
            "id": "elite_bankroll",
            "current_balance": 20.0,
            "base_balance": 20.0,
            "entry_size_usd": 1.0,
            "cycle_number": 1
        }
        client.table("bankroll_status").insert(data).execute()
        print("✅ Inserted default status row.")
except Exception as e:
    print(f"❌ Error checking/inserting data: {e}")
