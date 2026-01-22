
import requests
import json
import sys

def check_endpoint(url):
    print(f"Checking {url}...", flush=True)
    try:
        response = requests.get(url, timeout=5)
        print(f"Status: {response.status_code}", flush=True)
        if response.status_code == 500:
            print("ERROR BODY:", flush=True)
            print(response.text, flush=True)
        else:
            print("Response OK (preview):", response.text[:200], flush=True)
    except Exception as e:
        print(f"Failed to connect: {e}", flush=True)

if __name__ == "__main__":
    base_url = "http://localhost:5001"
    endpoints = [
        "/api/stats",
        "/api/history?limit=20",
        "/api/signals?min_score=0"
    ]
    
    for ep in endpoints:
        check_endpoint(f"{base_url}{ep}")
        print("-" * 40)
