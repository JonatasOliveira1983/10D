import requests
import json

BASE_URL = "http://127.0.0.1:5001"

def test_api():
    print(f"Testing API at {BASE_URL}...")
    
    endpoints = [
        "/api/version",
        "/api/pairs",
        "/api/llm/status",
        "/api/ml/status",
        "/api/btc/regime"
    ]
    
    for ep in endpoints:
        try:
            print(f"\n- Testing {ep}...")
            r = requests.get(BASE_URL + ep, timeout=5)
            print(f"Status: {r.status_code}")
            print(f"Response: {json.dumps(r.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
