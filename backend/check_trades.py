
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path="backend/.env", override=True)
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")

client = create_client(url, key)

print(f"Checking trades in: {url}")
try:
    res = client.table("bankroll_trades").select("*").order("opened_at", desc=True).limit(5).execute()
    print(f"Funds returned: {len(res.data)}")
    for t in res.data:
        print(f" - {t['symbol']} ({t['direction']}) Status: {t['status']} ID: {t['id']}")
except Exception as e:
    print(f"Error: {e}")
