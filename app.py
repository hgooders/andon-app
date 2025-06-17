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

from flask import send_file
from openpyxl import Workbook
from io import BytesIO
from datetime import datetime

@app.route("/download")
def download_data():
    if not os.path.exists(DATA_FILE):
        return "No data available to download."

    with open(DATA_FILE, "r") as f:
        lines = f.readlines()

    if not lines:
        return "No data available to download."

    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Andon Data"

    # Headers
    headers = ["Reason", "Name", "Time Stopped (min)", "Timestamp"]
    ws.append(headers)

    # Add rows
    for line in lines:
        parts = line.strip().split(",")
        if len(parts) == 4:
            ws.append(parts)

    # Auto-size columns
    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        ws.column_dimensions[col_letter].width = max_length + 2

    # Save to memory
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"andon_data_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
    return send_file(
        output,
        download_name=filename,
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Run the app locally (optional)
# if __name__ == "__main__":
#     app.run(debug=True)
@app.route("/summary-data")
def summary_data():
    from flask import jsonify

    entries = []
    total_stopped = 0

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

            for entry in data:
                try:
                    stopped_time = int(entry.get("stopped_time", 0))
                except ValueError:
                    stopped_time = 0
                total_stopped += stopped_time
                entries.append(entry)

    shift_minutes = 480
    percent_stopped = round((total_stopped / shift_minutes) * 100, 1)
    percent_running = round(100 - percent_stopped, 1)

    return jsonify({
        "total_stopped": total_stopped,
        "percent_stopped": percent_stopped,
        "percent_running": percent_running,
        "entries": entries
    })



   
