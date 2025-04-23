from flask import Flask, render_template, request, jsonify
from utils.table_formatter import TableFormatter
from computations.emode import Emode
import webbrowser
import threading
import os

app = Flask(
    __name__,
    static_folder='static',
    template_folder='templates'
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    try:
        data = request.get_json(force=True)

        # Pull parameters
        latex     = data.get('latex')
        start     = float(data.get('start'))
        end       = float(data.get('end'))
        initial_y = float(data.get('initial_y'))
        step      = float(data.get('step'))

        # Validate
        if not latex:
            return jsonify(error='No LaTeX expression provided'), 400
        if step <= 0:
            return jsonify(error='Step must be > 0'), 400
        if end <= start:
            return jsonify(error='End must be greater than start'), 400

        # Instantiate solver
        solver = Emode(
            latex=latex,
            initial_x=start,
            initial_y=initial_y,
            step_size=step,
            desired_x=end
        )
        values = solver.euler()

        # Build response
        formatter  = TableFormatter(latex, initial_y, start, end, step)
        params_str = formatter.params_to_string()
        table_html = formatter.format_output(values)

        return jsonify(params=params_str, table=table_html)
    except Exception as e:
        return jsonify(error=str(e)), 400


def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == '__main__':
    # Only open browser if this is the actual server process, not the reloader
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.0, open_browser).start()
    app.run(debug=True)
