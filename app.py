from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timezone

app = Flask(__name__)
CORS(app)

# In-memory store — survives only while the Railway process is alive.
# For persistence across Railway redeploys/restarts, use a database or Redis later.
latest_sensor_data = {}
led_state = {"state": "off"}  # "on" | "off"

# Stores the most recent time motion was detected.
last_motion = {
    "detected": False,
    "timestamp": None
}


def current_utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


# ── Health ─────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "timestamp": current_utc_timestamp()
    })


# ── Sensor data POST (from ESP32) ──────────────────────────────────────
@app.route("/api/sensor-data", methods=["POST"])
def receive_sensor_data():
    global latest_sensor_data, last_motion

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "No JSON body"}), 400

    timestamp = current_utc_timestamp()
    data["timestamp"] = timestamp

    # Inject current LED state so frontend can read it from /api/latest
    data["led_state"] = led_state["state"]

    # Track last motion detected time
    motion_value = data.get("motion", False)

    if motion_value is True or motion_value == "true" or motion_value == 1:
        last_motion = {
            "detected": True,
            "timestamp": timestamp
        }

    data["last_motion"] = last_motion

    latest_sensor_data = data

    return jsonify({
        "status": "ok",
        "timestamp": timestamp,
        "last_motion": last_motion
    }), 200


# ── Latest sensor data GET (for dashboard) ────────────────────────────
@app.route("/api/latest", methods=["GET"])
def get_latest():
    if not latest_sensor_data:
        return jsonify({"error": "No data yet"}), 404

    payload = dict(latest_sensor_data)

    # Always inject current LED state on every read
    payload["led_state"] = led_state["state"]

    # Always include last motion state
    payload["last_motion"] = last_motion

    return jsonify(payload)


# ── LED control ────────────────────────────────────────────────────────
@app.route("/api/led", methods=["GET"])
def get_led():
    """ESP32 polls this every few seconds to sync the physical LED."""
    return jsonify({
        "led_state": led_state["state"],
        "timestamp": current_utc_timestamp(),
    })


@app.route("/api/led", methods=["POST"])
def set_led():
    """Dashboard sends { 'state': 'on' | 'off' } to control the LED."""
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "No JSON body"}), 400

    requested = str(data.get("state", "")).lower()

    if requested not in ("on", "off"):
        return jsonify({"error": "state must be 'on' or 'off'"}), 400

    led_state["state"] = requested

    return jsonify({
        "led_state": led_state["state"],
        "timestamp": current_utc_timestamp(),
    }), 200


if __name__ == "__main__":
    app.run(debug=True)