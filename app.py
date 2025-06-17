from datetime import datetime
import json
import os
import csv
from collections import Counter
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify

app = Flask(__name__)
DATA_FILE = "andon_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/andon', methods=['POST'])
def andon():
    reason = request.form['reason']
    name = request.form['name']
    stopped_time = request.form['stopped_time']
    timestamp = datetime.now().isoformat()

    new_entry = {
        "timestamp": timestamp,
        "reason": reason,
        "name": name,
        "stopped_time": stopped_time
    }

    data = load_data()
    data.append(new_entry)
    save_data(data)

    return redirect(url_for('opr'))

@app.route('/opr')
def opr():
    entries = load_data()
    return render_template('opr.html', entries=entries)

@app.route('/summary')
def summary():
    data = load_data()

    total_stopped = 0
    reasons = []
    for entry in data:
        try:
            total_stopped += int(entry.get('stopped_time', 0))
            reasons.append(entry.get('reason', 'Unknown'))
        except ValueError:
            continue

    percent_stopped = round((total_stopped / (total_stopped + 1)) * 100, 2)
    percent_running = round(100 - percent_stopped, 2)

    top_reasons = Counter(reasons).most_common(3)

    reason_durations = Counter()
    for entry in data:
        try:
            reason_durations[entry['reason']] += int(entry.get('stopped_time', 0))
        except ValueError:
            continue

    sorted_items = reason_durations.most_common()
    labels = [r for r, _ in sorted_items]
    downtime = [d for _, d in sorted_items]
    cumulative = []
    running_sum = 0
    total = sum(downtime)
    for d in downtime:
        running_sum += d
        cumulative.append(round((running_sum / total) * 100, 2) if total else 0)

    pareto_data = {
        "labels": labels,
        "downtime": downtime,
        "cumulative": cumulative
    }

    return render_template("summary.html",
                           entries=data,
                           total_stopped=total_stopped,
                           percent_stopped=percent_stopped,
                           percent_running=percent_running,
                           top_reasons=top_reasons,
                           pareto_data=pareto_data)

@app.route('/reset', methods=['POST'])
def reset():
    with open(DATA_FILE, "w") as f:
        f.write("[]")
    return redirect(url_for('opr'))

@app.route('/download')
def download():
    return send_file(DATA_FILE, as_attachment=True)

@app.route('/summary-data')
def summary_data():
    entries = load_data()
    total_stopped = sum(int(e.get('stopped_time', 0)) for e in entries if e.get('stopped_time', '0').isdigit())
    percent_stopped = round((total_stopped / (total_stopped + 1)) * 100, 2)
    percent_running = round(100 - percent_stopped, 2)

    return jsonify({
        "entries": entries,
        "total_stopped": total_stopped,
        "percent_stopped": percent_stopped,
        "percent_running": percent_running
    })

if __name__ == '__main__':
    app.run()
