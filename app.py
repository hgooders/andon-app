from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from datetime import datetime
from collections import Counter
import os
import json
import pandas as pd
import io

from flask import session

app.secret_key = 'something'

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
    entries = []
    total_stopped = 0
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
            stopped_time = entry.get("stopped_time", 0)

            try:
                stopped_time = int(stopped_time)
            except ValueError:
                stopped_time = 0

            total_stopped += stopped_time

            entries.append({
                "timestamp": timestamp,
                "reason": reason,
                "name": name,
                "stopped_time": stopped_time
            })

            if reason not in reasons:
                reasons[reason] = 0
            reasons[reason] += stopped_time

    sorted_reasons = sorted(reasons.items(), key=lambda x: x[1], reverse=True)
    top_reasons = sorted_reasons[:3]

    total_shift_minutes = 480  # 8-hour shift
    percent_stopped = (total_stopped / total_shift_minutes) * 100 if total_shift_minutes > 0 else 0
    percent_running = 100 - percent_stopped

    pareto_labels = [r[0] for r in sorted_reasons]
    pareto_downtime = [r[1] for r in sorted_reasons]
    cumulative = []
    cum_sum = 0
    for dt in pareto_downtime:
        cum_sum += dt
        cumulative.append(round((cum_sum / total_stopped) * 100 if total_stopped else 0, 2))

    pareto_data = {
        "labels": pareto_labels,
        "downtime": pareto_downtime,
        "cumulative": cumulative
    }

    return render_template("summary.html",
                           entries=entries,
                           total_stopped=total_stopped,
                           percent_stopped=round(percent_stopped, 2),
                           percent_running=round(percent_running, 2),
                           top_reasons=top_reasons,
                           pareto_data=pareto_data)




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
    
@app.route('/stop-flash', methods=['POST'])
def stop_flash():
    session['flash_stopped'] = True
    return redirect('/summary')

