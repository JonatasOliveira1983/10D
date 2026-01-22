
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

# Since we can't run raw SQL directly through the client easily (it's usually for PostgREST)
# we can use the 'rpc' if a 'exec_sql' function exists, or just warn the user.
# However, usually we can try to "upsert" with new columns and sometimes it works if DB is auto-migrating (unlikely for Supabase).

print("Check completed. Recommending manual SQL execution for schema stability.")
print("""
PLEASE EXECUTE THIS IN SUPABASE SQL EDITOR:

ALTER TABLE bankroll_trades ADD COLUMN IF NOT EXISTS current_price FLOAT;
ALTER TABLE bankroll_trades ADD COLUMN IF NOT EXISTS current_roi FLOAT;
ALTER TABLE bankroll_trades ADD COLUMN IF NOT EXISTS direction TEXT;

ALTER TABLE bankroll_status ADD COLUMN IF NOT EXISTS current_balance FLOAT;
ALTER TABLE bankroll_status ADD COLUMN IF NOT EXISTS active_slots_used INTEGER;

NOTIFY pgrst, 'reload schema';
""")
