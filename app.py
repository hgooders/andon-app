from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import json
import os
from datetime import datetime
from collections import Counter

app = Flask(__name__)
DATA_FILE = 'andon_log.json'

# Initialize file if not exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

def log_andon(reason, name, stopped_time):
    with open(DATA_FILE, 'r+') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
        data.append({
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "name": name,
            "stopped_time": stopped_time
        })
        f.seek(0)
        json.dump(data, f, indent=2)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/andon", methods=["POST"])
def andon():
    reason = request.form["reason"]
    name = request.form["name"]
    stopped_time = request.form["stopped_time"]
    log_andon(reason, name, stopped_time)
    return redirect(url_for("opr"))

@app.route("/opr")
def opr():
    entries = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
            for entry in data:
                entries.append({
                    "timestamp": entry.get("timestamp", "Unknown"),
                    "reason": entry.get("reason", "Unknown"),
                    "name": entry.get("name", "Unknown"),
                    "stopped_time": entry.get("stopped_time", "0")
                })
    return render_template("opr.html", entries=entries)

@app.route("/summary")
def summary():
    entries = []
    total_stopped = 0
    reason_counter = Counter()

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
            for entry in data:
                timestamp = entry.get("timestamp", "Unknown")
                reason = entry.get("reason", "Unknown")
                name = entry.get("name", "Unknown")
                stopped_time = int(entry.get("stopped_time", 0))
                total_stopped += stopped_time
                reason_counter[reason] += stopped_time
                entries.append({
                    "timestamp": timestamp,
                    "reason": reason,
                    "name": name,
                    "stopped_time": stopped_time
                })

    sorted_reasons = reason_counter.most_common()
    reasons = [item[0] for item in sorted_reasons]
    times = [item[1] for item in sorted_reasons]

    return render_template(
        "summary.html",
        entries=entries,
        total_stopped=total_stopped,
        reasons=reasons,
        times=times
    )

@app.route("/reset", methods=["POST"])
def reset():
    with open(DATA_FILE, "w") as f:
        f.write("[]")
    return redirect(url_for("opr"))

@app.route("/download")
def download():
    return send_file(DATA_FILE, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
