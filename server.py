from flask import Flask, g, jsonify, request, make_response
import time
import logging
from db import get_db_connection
from users import user_bp
from accounts import account_bp
from health import health_bp
from transactions import transactions_bp
from transactions import transactions_bp




logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)

# Middleware to start the timer for access log
@app.before_request
def start_timer_for_access_log():
    g.start_time = time.time()

# Middleware for setting content type as JSON
@app.after_request
def set_json_content_type(response):
    response.headers['Content-Type'] = 'application/json'
    return response

# Middleware for access log
@app.after_request
def access_log_middleware(response):
    if hasattr(g, 'start_time'):
        latency_sec = time.time() - g.start_time
        latency_ms = latency_sec * 1000
        logging.info(f"Request: {request.method} {request.path} from {request.remote_addr}, "
                     f"Latency: {latency_ms:.2f} ms")
    return response

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/users')
app.register_blueprint(account_bp, url_prefix='/accounts')
app.register_blueprint(health_bp, url_prefix='/')
app.register_blueprint(transactions_bp, url_prefix='/transactions')


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5001)
