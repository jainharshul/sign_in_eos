from flask import Flask, render_template, jsonify
from main import run_automation
import threading

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_script():
    try:
        # Run script in background thread to avoid blocking
        thread = threading.Thread(target=run_automation)
        thread.start()
        return jsonify({'status': 'running', 'message': 'Automation started'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
