# run_production.py
from waitress import serve
from app import app  # Make sure app.py has the `app = Flask(...)` part

serve(app, host='0.0.0.0', port=10000, threads=8)
