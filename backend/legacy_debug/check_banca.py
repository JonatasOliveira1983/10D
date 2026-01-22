
import requests
try:
    r = requests.get('http://localhost:5001/api/bankroll/trades')
    trades = r.json()
    open_trades = [t for t in trades if t["status"] == "OPEN"]
    print(f"DEBUG: Found {len(open_trades)} open trades")
    for t in open_trades:
        print(f"SYMBOL: {t['symbol']} | ENTRY: {t['entry_price']} | ROI: {t.get('current_roi', 'N/A')}%")
except Exception as e:
    print(f"ERROR: {e}")
