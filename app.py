#!/usr/bin/env python3
"""
RFP Scout - Web API
Lightweight Flask wrapper for the scanner and alert generator.
"""

import os
import json
import subprocess
from datetime import datetime
from flask import Flask, jsonify, Response

app = Flask(__name__)

RESULTS_FILE = os.getenv("RESULTS_FILE", "rfps.json")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")


@app.route("/")
def health():
    return jsonify({
        "service": "RFP Scout",
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


@app.route("/rfps")
def get_rfps():
    if not os.path.exists(RESULTS_FILE):
        return jsonify({"error": "No results yet. Run /scan first."}), 404
    with open(RESULTS_FILE) as f:
        data = json.load(f)
    return jsonify({"count": len(data), "rfps": data})


@app.route("/scan")
def scan():
    try:
        subprocess.run(["python", "sam_gov_scanner.py"], check=True, timeout=300)
        subprocess.run(["python", "alert_generator.py"], check=True, timeout=300)
        return jsonify({"status": "scan complete", "timestamp": datetime.utcnow().isoformat() + "Z"})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"error": "scan timed out"}), 504


@app.route("/digest")
def digest():
    if not os.path.exists(OUTPUT_DIR):
        return jsonify({"error": "No output yet. Run /scan first."}), 404
    files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".html")])
    if not files:
        return jsonify({"error": "No digest found. Run /scan first."}), 404
    latest = os.path.join(OUTPUT_DIR, files[-1])
    with open(latest) as f:
        html = f.read()
    return Response(html, mimetype="text/html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
