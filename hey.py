from flask import Flask, request, abort, jsonify, make_response, g
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL is not set")

logging.debug("DATABASE_URL:", DATABASE_URL)
engine = create_engine(DATABASE_URL.strip())

@app.before_request
def start_timer_for_access_log():
    g.start_time = time.time()

@app.before_request
def authentincation_middleware():
    api_key = request.headers.get('X-API-KEY')
    if not api_key or api_key != 'HelloWorld':
        logging.warning(f"Unauthorized access attempt: {request.remote_addr}")
        response = make_response(jsonify({
            "error": "Unauthorized",
            "message": "Invalid API key"
        }), 401)
        abort(response)

@app.after_request
def set_json_content_type(response):
    response.headers['Content-Type'] = 'application/json'
    return response

@app.after_request
def access_log_middleware(response):
    if hasattr(g, 'start_time'):
        latency_sec = time.time() - g.start_time
        latency_ms = latency_sec * 1000
        logging.info(f"Request: {request.method} {request.path} from {request.remote_addr}, "
                     f"Latency: {latency_ms:.2f} ms")
    return response

@app.route('/status', methods=['GET'])
def status():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1")).fetchone()
            return '{"status": "ok", "reason": "ok"}', 200

    except SQLAlchemyError as e:
        return '{"status": "failed", "reason": "'+ str(e) +'"}', 500, 500

@app.route('/version', methods=['GET'])
def version():
    return '{"version": "0.0.1"}', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
