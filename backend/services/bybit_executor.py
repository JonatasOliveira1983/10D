import os
from pybit.unified_trading import HTTP
from typing import List, Dict

# Load credentials – can be overridden by environment variables for security
API_KEY = os.getenv("BYBIT_TEST_API_KEY", "hFIuE6sTcw4czIQnhR")
API_SECRET = os.getenv("BYBIT_TEST_API_SECRET", "cGpQblrDjqHAVX0kjGxOgm0xHzmnPwZJq3hJ")

client = HTTP(testnet=True, api_key=API_KEY, api_secret=API_SECRET)

def place_test_order(signal: Dict) -> Dict:
    """Place a single test order based on a signal.
    Expected signal keys: symbol, side ("Buy"/"Sell"), qty, price (optional).
    Returns the raw response from Bybit.
    """
    # Determine order type: use explicit 'order_type' if present, otherwise fallback to price presence
    order_type = signal.get("order_type")
    if not order_type:
        order_type = "Limit" if "price" in signal else "Market"
    params = {
        "category": "linear",  # USDC perpetual – adjust if needed
        "symbol": signal["symbol"],
        "side": signal["side"].lower(),
        "orderType": order_type,
        "qty": str(signal["qty"]),
        "timeInForce": "GTC",
        "orderLinkId": f"captain_test_{int(signal.get('timestamp', 0))}",
    }
    if "price" in signal:
        params["price"] = str(signal["price"])
    return client.place_order(**params)

def execute_signals(signals: List[Dict]) -> List[Dict]:
    """Iterate over elite signals and place test orders.
    Returns a list of Bybit responses.
    """
    results = []
    for sig in signals:
        try:
            res = place_test_order(sig)
            results.append({"signal": sig, "response": res})
        except Exception as e:
            results.append({"signal": sig, "error": str(e)})
    return results
