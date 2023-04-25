from datetime import datetime, timedelta
from flask import Flask, render_template
from src.report_generator import generate_reports

app = Flask(__name__)

# Set the initial time to one hour ago
last_fetch_time = datetime.now() - timedelta(hours=1)

@app.route('/')
def index():
    global last_fetch_time

    # Generate reports
    reports = generate_reports(last_fetch_time)
    return render_template('index.html', reports=reports)

if __name__ == '__main__':
    app.run(debug=True)
