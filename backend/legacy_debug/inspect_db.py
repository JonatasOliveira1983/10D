
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(override=True)
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")

if not url or not key:
    print("Error: Missing Supabase credentials")
    exit(1)

client = create_client(url, key)

try:
    # Get one row to see columns
    print("Fetching one row from bankroll_trades...")
    res = client.table("bankroll_trades").select("*").limit(1).execute()
    if res.data:
        print(f"Columns found: {list(res.data[0].keys())}")
    else:
        print("No data in bankroll_trades. Trying to insert and then rollback/delete to see schema...")
        # Since we can't easily see schema via API without data, let's try a test query
        # that intentionally fails to see if we can get column info? 
        # Actually, let's just try to select 'current_price' specifically.
        try:
            client.table("bankroll_trades").select("current_price").limit(1).execute()
            print("Column 'current_price' EXISTS.")
        except Exception as e:
            print(f"Column 'current_price' NOT FOUND or Error: {e}")
except Exception as e:
    print(f"General Error: {e}")
