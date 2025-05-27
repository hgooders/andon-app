from flask import Flask, render_template, redirect, url_for
import json
import csv
from datetime import datetime
import os

app = Flask(__name__)
DATA_FILE = 'andon_log.json'

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

def log_andon(reason, name, timestamp):
    with open(DATA_FILE, 'r+') as f:
        data = json.load(f)
        data.append({
            "reason": reason,
            "name": name,
            "timestamp": timestamp
        })
        f.seek(0)
        json.dump(data, f, indent=2)




def get_andon_data():
    with open(DATA_FILE) as f:
        return json.load(f)

@app.route('/')
def home():
    return render_template('home.html')

from flask import request  # Make sure this is already imported at the top

@app.route('/andon', methods=['POST'])
def andon():
    reason = request.form['reason']
    name = request.form['name']
    timestamp = datetime.now().isoformat()
    log_andon(reason, name, timestamp)
    return redirect(url_for('opr'))



@app.route("/opr")
def opr():
    entries = []
    reason_counts = {}

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            for entry in data:
                timestamp = entry.get("timestamp", "Missing")
                description = entry.get("description", "Missing")
                entries.append({"timestamp": timestamp, "description": description})

                # Count how many times each description appears
                if description in reason_counts:
                    reason_counts[description] += 1
                else:
                    reason_counts[description] = 1

    return render_template("opr.html", entries=entries, reasons=reason_counts)




if __name__ == '__main__':
    app.run()
