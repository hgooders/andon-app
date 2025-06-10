from flask import Flask, render_template, request, redirect, url_for, send_file
from datetime import datetime
import os
import json

app = Flask(__name__)
DATA_FILE = "andon_log.json"

# Home page
@app.route("/")
def home():
    return render_template("home.html")

# Handle Andon press
@app.route("/andon", methods=["POST"])
def andon():
    reason = request.form['reason']
    name = request.form['name']
    stopped_time = request.form['stopped_time']
    timestamp = datetime.now().isoformat()
    log_andon(reason, name, stopped_time, timestamp)
    return redirect(url_for("opr"))

# Log to JSON file
def log_andon(reason, name, stopped_time, timestamp):
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
    with open(DATA_FILE, "r+") as f:
        data = json.load(f)
        data.append({
            "reason": reason,
            "name": name,
            "stopped_time": stopped_time,
            "timestamp": timestamp
        })
        f.seek(0)
        json.dump(data, f, indent=2)

# OPR page
@app.route("/opr")
def opr():
    entries = []
    reason_counts = {}

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

            for entry in data:
                reason = entry.get("reason", "Missing")
                name = entry.get("name", "Missing")
                stopped_time = entry.get("stopped_time", "0")
                timestamp = entry.get("timestamp", "Missing")
                entries.append({
                    "reason": reason,
                    "name": name,
                    "stopped_time": stopped_time,
                    "timestamp": timestamp
                })
                reason_counts[reason] = reason_counts.get(reason, 0) + 1

    return render_template("opr.html", entries=entries, reasons=reason_counts)

# Summary page
@app.route("/summary")
def summary():
    entries = []
    total_stopped = 0

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

            for entry in data:
                reason = entry.get("reason", "Missing")
                name = entry.get("name", "Missing")
                try:
                    stopped_time = int(entry.get("stopped_time", 0))
                except ValueError:
                    stopped_time = 0
                timestamp = entry.get("timestamp", "Missing")
                entries.append({
                    "reason": reason,
                    "name": name,
                    "stopped_time": stopped_time,
                    "timestamp": timestamp
                })
                total_stopped += stopped_time

    shift_minutes = 425  # adjust this if needed
    percent_stopped = round((total_stopped / shift_minutes) * 100, 1)
    percent_running = round(100 - percent_stopped, 1)

    return render_template("summary.html",
                           entries=entries,
                           total_stopped=total_stopped,
                           percent_stopped=percent_stopped,
                           percent_running=percent_running)

# Reset data
@app.route("/reset", methods=["POST"])
def reset():
    with open(DATA_FILE, "w") as f:
        f.write("[]")
    return redirect(url_for("opr"))

# Download data
@app.route("/download")
def download():
    return send_file(DATA_FILE, as_attachment=True)

# Run the app locally (optional)
# if __name__ == "__main__":
#     app.run(debug=True)


   
