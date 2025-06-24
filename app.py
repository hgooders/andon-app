from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, session
from datetime import datetime, timedelta
from collections import Counter
import os, json, pandas as pd, io

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
def index():
    return render_template('index.html')

@app.route('/opr', methods=['GET', 'POST'])
def opr():
    data = load_data()
    if request.method == 'POST':
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        reason = request.form['reason']
        name = request.form['name']
        stopped_time = int(request.form['stopped_time'])

        data.append({
            'timestamp': timestamp,
            'reason': reason,
            'name': name,
            'stopped_time': stopped_time
        })
        save_data(data)

        if reason == "Health and Safety":
            session['alert'] = True
            session['alert_start'] = datetime.now().isoformat()

        return redirect(url_for('opr'))

    alert_active = session.get('alert', False)
    alert_start = session.get('alert_start')
    if alert_start:
        elapsed = datetime.now() - datetime.fromisoformat(alert_start)
        if elapsed > timedelta(minutes=10):
            alert_active = False
            session['alert'] = False

    return render_template('opr.html', alert=alert_active)

@app.route('/stop_alert', methods=['POST'])
def stop_alert():
    session['alert'] = False
    return redirect(url_for('opr'))

@app.route('/summary')
def summary():
    data = load_data()
    total_stopped = 0
    reasons = {}
    entries = []

    for entry in data:
        reason = entry.get('reason', 'Missing')
        stopped_time = int(entry.get('stopped_time', 0))
        total_stopped += stopped_time

        if reason not in reasons:
            reasons[reason] = 0
        reasons[reason] += stopped_time

        entries.append(entry)

    sorted_reasons = sorted(reasons.items(), key=lambda x: x[1], reverse=True)
    top_reasons = sorted_reasons[:3]
    top_names = ["🥇", "🥈", "🥉"]
    top_reasons = [(f"{top_names[i]} {r[0]}", r[1]) for i, r in enumerate(top_reasons)]

    shift_minutes = 480
    percent_stopped = round((total_stopped / shift_minutes) * 100, 2)
    percent_running = 100 - percent_stopped

    labels = [r[0] for r in sorted_reasons]
    downtime = [r[1] for r in sorted_reasons]
    cumulative = []
    cum_sum = 0
    for t in downtime:
        cum_sum += t
        cumulative.append(round((cum_sum / total_stopped) * 100, 2))

    pareto_data = {
        "labels": labels,
        "downtime": downtime,
        "cumulative": cumulative
    }

    return render_template('summary.html', entries=entries, top_reasons=top_reasons,
                           total_stopped=total_stopped, percent_stopped=percent_stopped,
                           percent_running=percent_running, pareto_data=pareto_data)

@app.route('/download')
def download():
    data = load_data()
    df = pd.DataFrame(data)
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv',
                     as_attachment=True, download_name='andon_data.csv')

@app.route('/reset', methods=['POST'])
def reset():
    save_data([])
    return redirect(url_for('summary'))

if __name__ == '__main__':
    app.run(debug=True)