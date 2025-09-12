from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from pathlib import Path

from model.safety_model import SafetyModel
from utils import log_event

BASE_DIR = Path(__file__).resolve().parents[0]
MODEL_GEOJSON = BASE_DIR / "model" / "danger_zones.geojson"

app = Flask(__name__, static_folder="../frontend", static_url_path="/")
CORS(app)

# instantiate safety model
safety_model = SafetyModel(str(MODEL_GEOJSON), danger_radius_m=100.0)

# simple fake users
users = {"user1": "password1", "user2": "password2"}

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    username = data.get("username")
    password = data.get("password")
    if username in users and users[username] == password:
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route("/api/check_safety", methods=["POST"])
def check_safety():
    payload = request.get_json(force=True)
    if not payload:
        return jsonify({"error": "invalid_json"}), 400

    lat = payload.get("latitude") or payload.get("lat")
    lon = payload.get("longitude") or payload.get("lon")
    tourist_id = payload.get("tourist_id")

    if lat is None or lon is None:
        return jsonify({"error": "latitude_and_longitude_required"}), 400

    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        return jsonify({"error": "lat_lon_must_be_numbers"}), 400

    result = safety_model.predict(lat, lon)  # returns dict with status & safety_score

    log_event({
        "event": "check_safety",
        "tourist_id": tourist_id,
        "latitude": lat,
        "longitude": lon,
        "result": result
    })

    return jsonify(result), 200

# serve frontend
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    front_path = Path(__file__).resolve().parents[1] / "frontend"
    requested = front_path / path
    if path != "" and requested.exists():
        return send_from_directory(str(front_path), path)
    return send_from_directory(str(front_path), "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
