from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from datetime import datetime
from collections import Counter
import os
import json
import pandas as pd
import io

app = Flask(__name__)
DATA_FILE = 'andon_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/andon', methods=['POST'])
def andon():
    reason = request.form.get('reason', 'Unknown')
    name = request.form.get('name', 'Unknown')
    stopped_time = request.form.get('stopped_time', '0')

    try:
        stopped_time = int(stopped_time)
    except ValueError:
        stopped_time = 0

    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "reason": reason,
        "name": name,
        "stopped_time": stopped_time
    }

    data = load_data()
    data.append(new_entry)
    save_data(data)

    return redirect(url_for('opr'))

@app.route("/opr")
def opr():
    entries = []
    reasons = {}

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

            for entry in data:
                timestamp = entry.get("timestamp", "Missing")
                reason = entry.get("reason", "Missing")
                name = entry.get("name", "Missing")
                stopped_time = entry.get("stopped_time", "Missing")

                entries.append({
                    "timestamp": timestamp,
                    "reason": reason,
                    "name": name,
                    "stopped_time": stopped_time
                })

                # Count reasons for display
                if reason not in reasons:
                    reasons[reason] = 0
                reasons[reason] += 1

    return render_template("opr.html", entries=entries, reasons=reasons)


@app.route('/summary')
def summary():
    data = load_data()
    total_stopped = sum(int(entry.get('stopped_time', 0)) for entry in data)
    percent_stopped = round((total_stopped / (total_stopped + 1)) * 100, 2)
    percent_running = round(100 - percent_stopped, 2)
    top_reasons = Counter(entry.get('reason') for entry in data).most_common(3)

    return render_template(
        'summary.html',
        entries=data,
        total_stopped=total_stopped,
        percent_stopped=percent_stopped,
        percent_running=percent_running,
        top_reasons=top_reasons
    )

@app.route('/summary-data')
def summary_data():
    data = load_data()
    reason_totals = {}

    for entry in data:
        reason = entry.get("reason")
        stopped_time = int(entry.get("stopped_time", 0))
        if reason:
            reason_totals[reason] = reason_totals.get(reason, 0) + stopped_time

    sorted_reasons = sorted(reason_totals.items(), key=lambda x: x[1], reverse=True)
    labels = [r[0] for r in sorted_reasons]
    downtime = [r[1] for r in sorted_reasons]

    cumulative = []
    running = 0
    total = sum(downtime)
    for time in downtime:
        running += time
        cumulative.append(round((running / total) * 100 if total else 0, 2))

    return jsonify({
        "labels": labels,
        "downtime": downtime,
        "cumulative": cumulative
    })

@app.route('/download')
def download():
    data = load_data()
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='AndonData')
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="andon_data.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/reset', methods=['POST'])
def reset():
    save_data([])
    return redirect(url_for('opr'))

if __name__ == '__main__':
    app.run(debug=True)

