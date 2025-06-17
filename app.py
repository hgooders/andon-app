from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from datetime import datetime
from collections import Counter
import os
import json
import pandas as pd
import io

from flask import session



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

    total_stopped = sum(entry.get("stopped_time", 0) for entry in data)
    total_possible = 8 * 60  # Assuming 8-hour shift
    percent_stopped = round((total_stopped / total_possible) * 100, 1) if total_possible else 0
    percent_running = round(100 - percent_stopped, 1)

    reasons = [entry.get("reason", "Unknown") for entry in data]
    top_reasons = Counter(reasons).most_common(3)

    # Pareto chart data
    downtime_by_reason = {}
    for entry in data:
        reason = entry.get("reason", "Unknown")
        downtime_by_reason[reason] = downtime_by_reason.get(reason, 0) + entry.get("stopped_time", 0)

    sorted_reasons = sorted(downtime_by_reason.items(), key=lambda x: x[1], reverse=True)
    labels = [r[0] for r in sorted_reasons]
    downtime = [r[1] for r in sorted_reasons]
    total_downtime = sum(downtime)
    cumulative = []
    cumulative_sum = 0
    for d in downtime:
        cumulative_sum += d
        cumulative.append(round((cumulative_sum / total_downtime) * 100, 1) if total_downtime else 0)

    pareto_data = {
        "labels": labels,
        "downtime": downtime,
        "cumulative": cumulative
    }

    if top_reasons and top_reasons[0][0] == "Health and Safety":
    session.setdefault("red_alert_active", True)
else:
    session["red_alert_active"] = False

show_red_alert = session.get("red_alert_active", False)


    return render_template(
        "summary.html",
        entries=data,
        total_stopped=total_stopped,
        percent_stopped=percent_stopped,
        percent_running=percent_running,
        top_reasons=top_reasons,
        pareto_data=pareto_data,
        show_red_alert=show_red_alert
    )

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
    
@app.route("/stop_alert", methods=["POST"])
def stop_alert():
    session["red_alert_active"] = False
    return redirect(url_for("summary"))


