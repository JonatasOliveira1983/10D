
import os
import sys
from dotenv import load_dotenv
from supabase import create_client
import time

load_dotenv(dotenv_path="backend/.env", override=True)
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")

print(f"Checking tables for: {url}")

if not url or not key:
    print("Missing credentials")
    sys.exit(1)

client = create_client(url, key)

REQUIRED_TABLES = ["bankroll_status", "bankroll_trades", "signals"]

for table in REQUIRED_TABLES:
    print(f"Checking {table}...")
    try:
        # Just select 1 to see if table exists
        res = client.table(table).select("id").limit(1).execute()
        print(f"✅ {table} exists.")
    except Exception as e:
        print(f"❌ {table} MISSING or inaccessible. Error: {str(e)[:100]}...")
