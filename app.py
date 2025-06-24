from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta
import os, json

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'devsecret')
DATA_FILE = 'andon_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            try: return json.load(f)
            except: return []
    return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/opr', methods=['GET'])
def opr():
    alert = session.get('alert_until') and datetime.utcnow() < datetime.fromisoformat(session['alert_until'])
    return render_template('opr.html', alert_active=alert, names=['Alice','Bob','Charlie'])

@app.route('/andon', methods=['POST'])
def andon():
    name = request.form['name']
    reason = request.form['reason']
    stopped = int(request.form.get('stopped_time', 0))
    ts = datetime.utcnow().isoformat()
    
    data = load_data()
    data.append({'timestamp': ts, 'name': name, 'reason': reason, 'stopped_time': stopped})
    save_data(data)
    
    if reason == 'Health and Safety':
        session['alert_until'] = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    return redirect(url_for('opr'))

@app.route('/stop_alert', methods=['POST'])
def stop_alert():
    session.pop('alert_until', None)
    return redirect(url_for('opr'))

@app.route('/summary')
def summary():
    data = load_data()
    total = sum(int(e.get('stopped_time', 0)) for e in data)
    reasons = {}
    for e in data:
        r = e.get('reason')
        reasons[r] = reasons.get(r, 0) + int(e.get('stopped_time',0))
    top = sorted(reasons.items(), key=lambda x: -x[1])[:3]
    return render_template('summary.html', total_stopped=total, top_reasons=top, entries=data)

if __name__ == '__main__':
    app.run()

