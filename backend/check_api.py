import urllib.request
import urllib.error
import sys

url = "http://127.0.0.1:5001/api/stats"
print(f"Fetching {url}...")
try:
    with urllib.request.urlopen(url) as response:
        print(f"Status: {response.status}")
        print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code}")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
