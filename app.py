from flask import Flask, render_template
from src.report_generator import generate_reports

app = Flask(__name__)

@app.route('/')
def index():
    # Generate reports
    reports = generate_reports()
    return render_template('index.html', reports=reports)

if __name__ == '__main__':
    app.run(debug=True)
