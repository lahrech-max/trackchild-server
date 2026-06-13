from flask import Flask, request, jsonify, render_template
import urllib.request
import json
import os

app = Flask(__name__)

FIREBASE_BASE = "https://trackchildsystem-default-rtdb.europe-west1.firebasedatabase.app/trackchild/device1"

@app.route('/update', methods=['POST'])
def update():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data"}), 400

        payload = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            FIREBASE_BASE + ".json",
            data=payload,
            method='PATCH',
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            return jsonify({"status": "ok", "code": response.status}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sos', methods=['GET'])
def get_sos():
    try:
        url = FIREBASE_BASE + "/sos.json"
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
            return data, 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/data', methods=['GET'])
def get_data():
    try:
        url = FIREBASE_BASE + ".json"
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
            return data, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
