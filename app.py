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
    session['flashing'] = False
    return redirect(url_for('summary'))
@app.route('/summary')
def summary():
    data = load_data()

    from collections import Counter, defaultdict
    import time
    from flask import session

    # Total stopped time
    total_stopped = sum(int(entry['stopped_time']) for entry in data)
    shift_minutes = 420
    percent_stopped = round((total_stopped / shift_minutes) * 100, 1)
    percent_running = 100 - percent_stopped

    # Count and sort top reasons by stopped time
    reasons_count = Counter()
    reason_totals = defaultdict(int)
    for entry in data:
        reason = entry['reason']
        reasons_count[reason] += 1
        reason_totals[reason] += int(entry['stopped_time'])

    top_reasons = sorted(reason_totals.items(), key=lambda x: x[1], reverse=True)[:3]

    # Pareto chart data (highest to lowest)
    sorted_reasons = sorted(reason_totals.items(), key=lambda x: x[1], reverse=True)
    labels = [reason for reason, _ in sorted_reasons]
    downtime = [reason_totals[reason] for reason in labels]
    total_time = sum(downtime)
    cumulative = []
    running = 0
    for t in downtime:
        running += t
        cumulative.append(round((running / total_time) * 100, 1) if total_time else 0)

    pareto_data = {"labels": labels, "downtime": downtime, "cumulative": cumulative}

    # Red flashing alert status
    flashing = session.get('alert_active', False)

    # Top 3 users
    top_users = Counter(entry['name'] for entry in data if 'name' in entry).most_common(3)

    return render_template(
        'summary.html',
        entries=data,
        total_stopped=total_stopped,
        percent_stopped=percent_stopped,
        percent_running=percent_running,
        top_reasons=top_reasons,
        pareto_data=pareto_data,
        flashing=flashing,
        top_users=top_users
    )






@app.route('/andon', methods=['POST'])
def andon():
    data = load_data()

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    reason = request.form.get('reason')
    name = request.form.get('name')
    stopped_time = request.form.get('stopped_time')

    data.append({
        'timestamp': timestamp,
        'reason': reason,
        'name': name,
        'stopped_time': int(stopped_time)
    })

    save_data(data)

    # If reason is Health and Safety, set alert
    if reason == "Health and Safety":
        session['flashing'] = True
        session['alert_start_time'] = datetime.now().timestamp()

    return redirect(url_for('summary'))  # Redirect to summary page

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

