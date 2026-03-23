from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import os

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("API_KEY", "change-me")

# latest snapshot
latest_data = {
    "temperature": None,
    "humidity": None,
    "motion": None,
    "light_level": None,
    "light_status": None,
    "device": None,
    "timestamp": None,
    "last_motion": None
}

# history storage
history = []

@app.route("/")
def home():
    return "Smart Room Backend is running on Railway"

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/api/sensor-data", methods=["POST"])
def receive_sensor_data():
    global latest_data, history

    client_key = request.headers.get("X-API-KEY")
    if client_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON received"}), 400

    now = datetime.now().isoformat()

    # update latest values
    latest_data["temperature"] = data.get("temperature")
    latest_data["humidity"] = data.get("humidity")
    latest_data["motion"] = data.get("motion")
    latest_data["light_level"] = data.get("light_level")
    latest_data["light_status"] = data.get("light_status")
    latest_data["device"] = data.get("device")
    latest_data["timestamp"] = now

    # 🔥 FIXED MOTION LOGIC (robust)
    motion_value = str(data.get("motion", "")).lower()

    if "detect" in motion_value:
        latest_data["last_motion"] = now

    # store history
    entry = {
        "temperature": data.get("temperature"),
        "humidity": data.get("humidity"),
        "motion": data.get("motion"),
        "timestamp": now
    }

    history.append(entry)

    # prevent memory overflow
    if len(history) > 1000:
        history.pop(0)

    return jsonify({
        "message": "Sensor data received successfully",
        "received": latest_data
    }), 200

@app.route("/api/latest", methods=["GET"])
def get_latest_data():
    return jsonify(latest_data), 200

@app.route("/api/history", methods=["GET"])
def get_history():
    range_param = request.args.get("range", "1h")

    now = datetime.now()

    if range_param == "1h":
        cutoff = now - timedelta(hours=1)
    elif range_param == "24h":
        cutoff = now - timedelta(hours=24)
    elif range_param == "7d":
        cutoff = now - timedelta(days=7)
    else:
        cutoff = now - timedelta(hours=1)

    filtered = [
        item for item in history
        if datetime.fromisoformat(item["timestamp"]) >= cutoff
    ]

    return jsonify(filtered), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)