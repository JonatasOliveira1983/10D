import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")

print(f"URL: {url}")
print(f"KEY: {key[:10]}...")

try:
    client = create_client(url, key)
    print("Client created successfully")
    res = client.table("signals").select("id").limit(1).execute()
    print(f"Query successful: {res.data}")
except Exception as e:
    print(f"Error: {e}")
