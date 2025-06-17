from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import json
import os
from datetime import datetime
from collections import Counter
import openpyxl

app = Flask(__name__)
DATA_FILE = 'andon_log.json'

# Ensure data file exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

# Logging function
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

# Get all data
def get_andon_data():
    with open(DATA_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/andon', methods=['POST'])
def andon():
    reason = request.form.get('reason')
    name = request.form.get('name')
    stopped_time = request.form.get('stopped_time', '0')
    log_andon(reason, name, stopped_time)
    return redirect(url_for('opr'))

@app.route('/opr')
def opr():
    entries = get_andon_data()
    return render_template('opr.html', entries=entries)

@app.route('/reset', methods=['POST'])
def reset():
    with open(DATA_FILE, 'w') as f:
        f.write("[]")
    return redirect(url_for('opr'))

@app.route('/download')
def download():
    entries = get_andon_data()
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Andon Data"
    sheet.append(["Timestamp", "Reason", "Name", "Stopped Time (min)"])
    for entry in entries:
        sheet.append([
            entry.get("timestamp", ""),
            entry.get("reason", ""),
            entry.get("name", ""),
            entry.get("stopped_time", "")
        ])
    path = 'andon_data.xlsx'
    workbook.save(path)
    return send_file(path, as_attachment=True)
@app.route('/summary')
def summary():
    entries = []
    reason_counts = {}
    total_stopped = 0

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
            for entry in data:
                reason = entry.get("reason", "Unknown")
                name = entry.get("name", "Unknown")
                stopped_time = int(entry.get("stopped_time", 0))
                timestamp = entry.get("timestamp", "")

                entries.append({
                    "reason": reason,
                    "name": name,
                    "stopped_time": stopped_time,
                    "timestamp": timestamp
                })

                reason_counts[reason] = reason_counts.get(reason, 0) + stopped_time
                total_stopped += stopped_time

    sorted_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)
    top_reasons = sorted_reasons[:3]

    percent_stopped = round((total_stopped / (total_stopped + 1)) * 100, 2)
    percent_running = 100 - percent_stopped

    # Pareto chart data
    labels = [r[0] for r in sorted_reasons]
    downtime = [r[1] for r in sorted_reasons]
    cumulative = []
    cumulative_total = 0
    for d in downtime:
        cumulative_total += d
        cumulative.append(round((cumulative_total / total_stopped) * 100, 2) if total_stopped else 0)

    pareto_data = {
        "labels": labels,
        "downtime": downtime,
        "cumulative": cumulative
    }

    return render_template(
        "summary.html",
        entries=entries,
        total_stopped=total_stopped,
        percent_stopped=percent_stopped,
        percent_running=percent_running,
        top_reasons=top_reasons,
        pareto_data=pareto_data  # Make sure this is included
    )


@app.route('/summary')
def summary():
    data = get_andon_data()
    total_stopped = 0
    reasons_counter = Counter()
    flashing = False

    for entry in data:
        try:
            stopped_time = int(entry.get("stopped_time", 0))
            total_stopped += stopped_time
            reason = entry.get("reason", "Unknown")
            reasons_counter[reason] += stopped_time
        except ValueError:
            continue

    top_reasons = reasons_counter.most_common(3)
    percent_stopped = 0
    percent_running = 100
    if total_stopped > 0:
        percent_stopped = total_stopped / (total_stopped + 60) * 100  # Example calc
        percent_running = 100 - percent_stopped

    if top_reasons and top_reasons[0][0].lower() == "health and safety":
        flashing = True

    return render_template(
        "summary.html",
        entries=data,
        total_stopped=total_stopped,
        percent_stopped=round(percent_stopped, 2),
        percent_running=round(percent_running, 2),
        top_reasons=top_reasons,
        flashing=flashing
    )

if __name__ == '__main__':
    app.run(debug=True)

