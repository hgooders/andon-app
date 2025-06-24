from flask import Flask, render_template, request, redirect, url_for, send_file, session
from datetime import datetime
from collections import Counter
import os
import json
import pandas as pd
import io

app = Flask(__name__)
app.secret_key = 'something'
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

@app.route('/andon', methods=['GET', 'POST'])
def andon():
    if request.method == 'POST':
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        reason = request.form.get("reason")
        name = request.form.get("name")
        stopped_time = request.form.get("stopped_time", 0)

        try:
            stopped_time = int(stopped_time)
        except ValueError:
            stopped_time = 0

        entry = {
            "timestamp": timestamp,
            "reason": reason,
            "name": name,
            "stopped_time": stopped_time
        }

        data = load_data()
        data.append(entry)
        save_data(data)

        if reason == "Health and Safety":
            session["red_alert_active"] = True

        return redirect(url_for('opr'))

    return render_template('andon.html')

@app.route('/opr')
def opr():
    data = load_data()
    return render_template('opr.html', data=data)

@app.route('/summary')
def summary():
    data = load_data()
    entries = []
    reasons = {}
    total_stopped = 0

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

    top_reasons = Counter(reasons).most_common(3)

    labels = [reason for reason, _ in top_reasons]
    downtime = [reasons[reason] for reason in labels]
    cumulative = []
    total = sum(downtime)
    running_total = 0

    for d in downtime:
        running_total += d
        cumulative.append(round((running_total / total) * 100, 2) if total else 0)

    # Fixed assumed 480-minute shift
    total_possible_time = 480
    percent_stopped = round((total_stopped / total_possible_time) * 100, 2)
    percent_running = 100 - percent_stopped

    pareto_data = {
        "labels": labels,
        "downtime": downtime,
        "cumulative": cumulative
    }

    return render_template("summary.html",
        entries=entries,
        top_reasons=top_reasons,
        total_stopped=total_stopped,
        percent_stopped=percent_stopped,
        percent_running=percent_running,
        pareto_data=pareto_data,
        red_alert=session.get("red_alert_active", False)
    )

@app.route('/reset', methods=['POST'])
def reset():
    save_data([])
    session.pop("red_alert_active", None)
    return redirect(url_for('summary'))

@app.route('/download')
def download():
    data = load_data()
    df = pd.DataFrame(data)
    csv = df.to_csv(index=False)
    buffer = io.StringIO(csv)
    return send_file(io.BytesIO(buffer.getvalue().encode()),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='andon_data.csv')

@app.route('/stop_alert', methods=['POST'])
def stop_alert():
    session["red_alert_active"] = False
    return redirect(url_for('summary'))

