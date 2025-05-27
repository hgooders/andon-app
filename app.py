from flask import Flask, render_template, redirect, url_for
import json
from datetime import datetime
import os

app = Flask(__name__)
DATA_FILE = 'andon_log.json'

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

def log_andon(description):
    with open(DATA_FILE, 'r+') as f:
        data = json.load(f)
        data.append({
            "timestamp": datetime.now().isoformat(),
            "description": description
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
    description = request.form['description']
    log_andon(description)
    return redirect(url_for('opr'))


@app.route("/opr")
def opr():
    entries = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    timestamp, description = row[0], row[1]
                    entries.append({"timestamp": timestamp, "description": description})
    return render_template("opr.html", entries=entries)

if __name__ == '__main__':
    app.run()
