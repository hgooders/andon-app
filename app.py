from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from datetime import datetime, timedelta
from collections import Counter
import os
import json

app = Flask(__name__)
app.secret_key = 'something'
DATA_FILE = 'andon_data.json'
ALARM_FILE = 'alarm.json'

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

def load_alarm_state():
    if os.path.exists(ALARM_FILE):
        with open(ALARM_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"active": False, "start_time": None}
    return {"active": False, "start_time": None}

def save_alarm_state(state):
    with open(ALARM_FILE, 'w') as f:
        json.dump(state, f)

@app.route('/')
def home():
    return redirect(url_for('opr'))

@app.route('/opr', methods=['GET', 'POST'])
def opr():
    if request.method == 'POST':
        name = request.form['name']
        reason = request.form['reason']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        stopped_time = int(request.form.get('stopped_time', 0))
        entry = {
            "name": name,
            "reason": reason,
            "timestamp": timestamp,
            "stopped_time": stopped_time
        }
        data = load_data()
        data.append(entry)
        save_data(data)

        # Trigger red alert if reason is Health and Safety
        if reason.lower() == "health and safety":
            alarm_state = {
                "active": True,
                "start_time": datetime.now().isoformat()
            }
            save_alarm_state(alarm_state)

        return redirect(url_for('opr'))

    alarm_state = load_alarm_state()
    alarm_active = False
    if alarm_state['active']:
        start_time = datetime.fromisoformat(alarm_state['start_time'])
        if datetime.now() - start_time < timedelta(minutes=10):
            alarm_active = True
        else:
            alarm_state['active'] = False
            save_alarm_state(alarm_state)

    return render_template('opr.html', alarm_active=alarm_active)

@app.route('/stop_alarm', methods=['POST'])
def stop_alarm():
    save_alarm_state({"active": False, "start_time": None})
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)

