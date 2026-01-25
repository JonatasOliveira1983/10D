
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Force load backend/.env
load_dotenv(dotenv_path="backend/.env", override=True)
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.services.database_manager import DatabaseManager
from backend.services.bankroll_manager import BankrollManager

print("Initializing DB Manager...")
db = DatabaseManager()
print("Initializing Bankroll Manager...")
bm = BankrollManager(db_manager=db)

print("Fetching Status...")
status = bm.get_status()
print(f"Status: {status}")

if not status:
    print("❌ Status is None. Cannot trade.")
    sys.exit(1)

signal = {
    "id": f"debug_{int(time.time())}",
    "symbol": "SOLUSDT",
    "direction": "LONG",
    "entry_price": 120.0,
    "score": 99,
    "signal_type": "DEBUG",
    "score_breakdown": {"rules_score": 99},
    "timestamp": int(time.time() * 1000),
    "status": "ACTIVE"
}

print("Attempting _open_trade...")
try:
    success = bm._open_trade(signal, status)
    if success:
        print("✅ _open_trade RETURNED TRUE")
    else:
        print("❌ _open_trade RETURNED FALSE")
except Exception as e:
    print(f"❌ Exception in _open_trade: {e}")
    import traceback
    traceback.print_exc()
