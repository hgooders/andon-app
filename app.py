from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, session
from datetime import datetime
from collections import Counter
import os
import json
import pandas as pd
import io

app = Flask(__name__)
app.secret_key = 'super_secret_key'
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
    return render_template('index.html')

@app.route('/andon', methods=['POST'])
def andon():
    data = load_data()
    reason = request.form['reason']
    name = request.form['name']
    stopped_time = int(request.form['stopped_time'])

    data.append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'reason': reason,
        'name': name,
        'stopped_time': stopped_time
    })

    save_data(data)

    if reason.lower() == 'health and safety':
        session['health_safety_alert'] = True
        session['alert_start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return redirect(url_for('opr'))

@app.route('/opr')
def opr():
    data = load_data()
    total_stopped = sum(int(entry.get('stopped_time', 0)) for entry in data)
    shift_minutes = 480  # example 8 hour shift
    percent_stopped = round((total_stopped / shift_minutes) * 100, 1)
    percent_running = 100 - percent_stopped

    return render_template('opr.html', total_stopped=total_stopped,
                           percent_stopped=percent_stopped,
                           percent_running=percent_running)

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

    top_reasons = sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:3]

    labels = []
    downtime = []
    cumulative = []
    running_total = 0

    for reason, time in sorted(reasons.items(), key=lambda x: x[1], reverse=True):
        labels.append(reason)
        downtime.append(time)
        running_total += time
        cumulative.append(round((running_total / total_stopped) * 100, 1) if total_stopped else 0)

    percent_stopped = round((total_stopped / 480) * 100, 1)
    percent_running = 100 - percent_stopped

    return render_template('summary.html',
                           entries=entries,
                           top_reasons=top_reasons,
                           total_stopped=total_stopped,
                           percent_stopped=percent_stopped,
                           percent_running=percent_running,
                           pareto_data={"labels": labels, "downtime": downtime, "cumulative": cumulative},
                           health_safety_alert=session.get('health_safety_alert', False))

@app.route('/reset', methods=['POST'])
def reset():
    save_data([])
    session.pop('health_safety_alert', None)
    session.pop('alert_start_time', None)
    return redirect(url_for('summary'))

@app.route('/stop_alert', methods=['POST'])
def stop_alert():
    session['health_safety_alert'] = False
    return jsonify({"status": "stopped"})

@app.route('/download')
def download():
    data = load_data()
    df = pd.DataFrame(data)
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='andon_data.csv')

if __name__ == '__main__':
    app.run(debug=True)
