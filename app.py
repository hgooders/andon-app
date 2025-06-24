from flask import Flask, render_template, request, redirect, url_for, session, send_file
from datetime import datetime, timedelta
from collections import Counter
import os, json, io
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your-secret-key'
DATA_FILE = 'andon_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/opr', methods=['GET', 'POST'])
def opr():
    if request.method == 'POST':
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'name': request.form['name'],
            'reason': request.form['reason'],
            'stopped_time': int(request.form.get('stopped_time', 0))
        }
        data = load_data()
        data.append(entry)
        save_data(data)

        if entry['reason'] == 'Health and Safety':
            session['alert_until'] = (datetime.utcnow() + timedelta(minutes=10)).isoformat()

        return redirect(url_for('opr'))

    alert = session.get('alert_until')
    if alert and datetime.utcnow() < datetime.fromisoformat(alert):
        alert_active = True
    else:
        alert_active = False
        session.pop('alert_until', None)

    names = ['Harry', 'Alice', 'Bob']  # You can update
    reasons = ['Quality', 'Technical', 'Health and Safety', 'Supply Issue', 'Other']
    return render_template('opr.html',
                           alert_active=alert_active,
                           names=names,
                           reasons=reasons)

@app.route('/stop_alert', methods=['POST'])
def stop_alert():
    session.pop('alert_until', None)
    return redirect(url_for('opr'))

@app.route('/summary')
def summary():
    data = load_data()
    total_stopped = sum(int(e['stopped_time']) for e in data)
    reasons_count = Counter()
    for e in data:
        reasons_count[e['reason']] += int(e['stopped_time'])

    top = reasons_count.most_common(3)
    shift_minutes = 480
    percent_stopped = round((total_stopped / shift_minutes) * 100, 1)
    percent_running = 100 - percent_stopped

    labels = list(reasons_count.keys())
    downtime = list(reasons_count.values())
    cum = []
    running = 0
    for t in downtime:
        running += t
        cum.append(round((running / total_stopped) * 100, 1) if total_stopped else 0)

    pareto_data = {"labels": labels, "downtime": downtime, "cumulative": cum}

    return render_template('summary.html',
                           entries=data,
                           total_stopped=total_stopped,
                           percent_stopped=percent_stopped,
                           percent_running=percent_running,
                           top_reasons=top,
                           pareto_data=pareto_data)

@app.route('/download')
def download():
    data = load_data()
    df = pd.DataFrame(data)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return send_file(io.BytesIO(buf.getvalue().encode()),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='andon_data.csv')

@app.route('/reset', methods=['POST'])
def reset():
    save_data([])
    session.pop('alert_until', None)
    return redirect(url_for('summary'))

if __name__ == '__main__':
    app.run()

