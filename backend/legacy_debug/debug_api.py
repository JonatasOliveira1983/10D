import requests
import json
import traceback

BASE_URL = "http://127.0.0.1:5001"

def test_endpoint(endpoint):
    url = f"{BASE_URL}{endpoint}"
    print(f"Testing {url}...")
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"Response Text: {response.text}")
        else:
            try:
                data = response.json()
                print(f"Response JSON keys: {list(data.keys())}")
            except:
                print("Response is not JSON")
    except Exception as e:
        print(f"Failed to connect: {e}")
        traceback.print_exc()
    print("-" * 40)

def main():
    print("Starting API Test...")
    test_endpoint("/api/version")
    test_endpoint("/api/signals?min_score=0")
    test_endpoint("/api/stats")
    test_endpoint("/api/llm/summary")
    test_endpoint("/api/llm/status")

if __name__ == "__main__":
    main()
