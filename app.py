from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("API_KEY", "change-me")

latest_data = {
    "temperature": None,
    "humidity": None,
    "motion": None,
    "light_level": None,
    "light_status": None,
    "device": None,
    "timestamp": None
}

@app.route("/")
def home():
    return "Smart Room Backend is running on Railway"

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/api/sensor-data", methods=["POST"])
def receive_sensor_data():
    global latest_data

    client_key = request.headers.get("X-API-KEY")
    if client_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON received"}), 400

    latest_data["temperature"] = data.get("temperature")
    latest_data["humidity"] = data.get("humidity")
    latest_data["motion"] = data.get("motion")
    latest_data["light_level"] = data.get("light_level")
    latest_data["light_status"] = data.get("light_status")
    latest_data["device"] = data.get("device")
    latest_data["timestamp"] = datetime.now().isoformat()

    return jsonify({
        "message": "Sensor data received successfully",
        "received": latest_data
    }), 200

@app.route("/api/latest", methods=["GET"])
def get_latest_data():
    return jsonify(latest_data), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)