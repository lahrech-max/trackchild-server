from flask import Flask, request, jsonify, render_template
import urllib.request
import json
import os
import time

app = Flask(__name__)

FIREBASE_BASE = "https://trackchildsystem-default-rtdb.europe-west1.firebasedatabase.app/trackchild/device1"


def firebase_request(path, method='GET', data=None):
    url = FIREBASE_BASE + path + ".json"
    headers = {'Content-Type': 'application/json'}
    payload = json.dumps(data).encode('utf-8') if data is not None else None
    req = urllib.request.Request(url, data=payload, method=method, headers=headers)
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8'), response.status


# ════════════════════════════════════════════════════════
# Position actuelle
# ════════════════════════════════════════════════════════
@app.route('/update', methods=['POST'])
def update():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data"}), 400

        body, status = firebase_request("/current", "PATCH", data)
        return jsonify({"status": "ok", "code": status}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════
# Historique des positions (POST = ajouter point)
# ════════════════════════════════════════════════════════
@app.route('/history', methods=['POST', 'GET'])
def history():
    try:
        if request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data"}), 400
            body, status = firebase_request("/history", "POST", data)
            return jsonify({"status": "ok", "code": status}), 200
        else:
            body, status = firebase_request("/history", "GET")
            return body, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════
# SOS - lecture
# ════════════════════════════════════════════════════════
@app.route('/sos', methods=['GET'])
def get_sos():
    try:
        body, status = firebase_request("/current/sos", "GET")
        return body, 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════
# Evenements SOS (historique des alertes)
# ════════════════════════════════════════════════════════
@app.route('/sos_event', methods=['POST', 'GET'])
def sos_event():
    try:
        if request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data"}), 400
            body, status = firebase_request("/sos_history", "POST", data)
            return jsonify({"status": "ok", "code": status}), 200
        else:
            body, status = firebase_request("/sos_history", "GET")
            return body, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════
# Données actuelles + calcul distance
# ════════════════════════════════════════════════════════
@app.route('/data', methods=['GET'])
def get_data():
    try:
        current_body, _ = firebase_request("/current", "GET")
        current = json.loads(current_body) if current_body != "null" else {}

        history_body, _ = firebase_request("/history", "GET")
        history_data = json.loads(history_body) if history_body != "null" else {}

        # Calcul de la distance totale et stats
        distance_km = 0.0
        max_speed = 0.0
        points = []

        if history_data:
            sorted_points = sorted(history_data.values(), key=lambda x: x.get('timestamp', 0))
            for p in sorted_points:
                points.append({
                    "lat": p.get("latitude"),
                    "lng": p.get("longitude"),
                    "speed": p.get("speed", 0)
                })
                if p.get("speed", 0) > max_speed:
                    max_speed = p.get("speed", 0)

            for i in range(1, len(sorted_points)):
                lat1, lng1 = sorted_points[i-1]["latitude"], sorted_points[i-1]["longitude"]
                lat2, lng2 = sorted_points[i]["latitude"], sorted_points[i]["longitude"]
                distance_km += haversine(lat1, lng1, lat2, lng2)

        result = current
        result["distance_km"] = round(distance_km, 2)
        result["max_speed"] = max_speed
        result["track_points"] = points

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def haversine(lat1, lng1, lat2, lng2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371  # km
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


# ════════════════════════════════════════════════════════
# Effacer l'historique (reset journalier)
# ════════════════════════════════════════════════════════
@app.route('/history/clear', methods=['POST'])
def clear_history():
    try:
        body, status = firebase_request("/history", "DELETE")
        return jsonify({"status": "cleared"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════
# Page web
# ════════════════════════════════════════════════════════
@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
