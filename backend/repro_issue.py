from flask import Flask, jsonify
import json
import sys

app = Flask(__name__)

try:
    with app.app_context():
        # strict behavior test
        data = {None: 1}
        print(f"Attempting to jsonify: {data}")
        print(jsonify(data).get_data(as_text=True))
except TypeError as e:
    print(f"Caught expected TypeError: {e}")
except Exception as e:
    print(f"Caught unexpected exception: {e}")
