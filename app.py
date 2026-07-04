from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timezone

app = Flask(__name__)
CORS(app)

latest_sensor_data = {}
led_state = {"state": "off"}
servo_state = {"state": "closed", "angle": 0}

last_motion = {
    "detected": False,
    "timestamp": None
}


def current_utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "timestamp": current_utc_timestamp()
    })


@app.route("/api/sensor-data", methods=["POST"])
def receive_sensor_data():
    global latest_sensor_data, last_motion

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "No JSON body"}), 400

    timestamp = current_utc_timestamp()
    data["timestamp"] = timestamp
    data["led_state"] = led_state["state"]
    data["servo_state"] = servo_state["state"]
    data["servo_angle"] = servo_state["angle"]

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


@app.route("/api/latest", methods=["GET"])
def get_latest():
    if not latest_sensor_data:
        return jsonify({"error": "No data yet"}), 404

    payload = dict(latest_sensor_data)
    payload["led_state"] = led_state["state"]
    payload["servo_state"] = servo_state["state"]
    payload["servo_angle"] = servo_state["angle"]
    payload["last_motion"] = last_motion

    return jsonify(payload)


@app.route("/api/led", methods=["GET"])
def get_led():
    return jsonify({
        "led_state": led_state["state"],
        "timestamp": current_utc_timestamp(),
    })


@app.route("/api/led", methods=["POST"])
def set_led():
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


# ── Servo control ──────────────────────────────────────────────────────
@app.route("/api/servo", methods=["GET"])
def get_servo():
    return jsonify({
        "servo_state": servo_state["state"],
        "servo_angle": servo_state["angle"],
        "timestamp": current_utc_timestamp(),
    })


@app.route("/api/servo", methods=["POST"])
def set_servo():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "No JSON body"}), 400

    requested = str(data.get("state", "")).lower()

    if requested not in ("open", "closed"):
        return jsonify({"error": "state must be 'open' or 'closed'"}), 400

    servo_state["state"] = requested
    servo_state["angle"] = 90 if requested == "open" else 0

    return jsonify({
        "servo_state": servo_state["state"],
        "servo_angle": servo_state["angle"],
        "timestamp": current_utc_timestamp(),
    }), 200


if __name__ == "__main__":
    app.run(debug=True)