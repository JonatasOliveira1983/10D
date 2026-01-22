from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os

app = Flask(__name__)
CORS(app)

@app.route("/api/stats")
def stats():
    return jsonify({"status": "OK", "message": "Minimal server working"})

@app.route("/api/signals")
def signals():
    return jsonify({"signals": [], "count": 0})

if __name__ == "__main__":
    print("Starting SIMPLE debug server on 5001...", flush=True)
    app.run(host="0.0.0.0", port=5001)
