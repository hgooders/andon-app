from flask import Flask, render_template, redirect, url_for
import json
from datetime import datetime
import os

app = Flask(__name__)
DATA_FILE = 'andon_log.json'

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

def log_andon():
    with open(DATA_FILE, 'r+') as f:
        data = json.load(f)
        data.append({"timestamp": datetime.now().isoformat()})
        f.seek(0)
        json.dump(data, f, indent=2)

def get_andon_data():
    with open(DATA_FILE) as f:
        return json.load(f)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/andon', methods=['POST'])
def andon():
    log_andon()
    return redirect(url_for('opr'))

@app.route('/opr')
def opr():
    data = get_andon_data()
    return render_template('opr.html', data=data, count=len(data))

if __name__ == '__main__':
    app.run()
