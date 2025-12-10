"""
🎯 Prometheus Metrics Middleware for Flask
===========================================
Copy this file to each service directory:
- account-service/metrics_middleware.py
- transaction-service/metrics_middleware.py
- notification-service/metrics_middleware.py
"""

from flask import request, g
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import re

# ==========================================
# Metrics Definitions
# ==========================================

# Counter: Total number of HTTP requests
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

# Histogram: Request duration in seconds
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

# Counter: Total errors (4xx, 5xx)
http_requests_errors_total = Counter(
    'http_requests_errors_total',
    'Total HTTP error requests',
    ['method', 'endpoint', 'status_code']
)


def normalize_path(path):
    """
    Normalize URL paths to avoid too many unique labels
    Examples:
    - /accounts/550e8400-e29b-41d4-a716-446655440000 -> /accounts/<id>
    - /transactions/123/deposit -> /transactions/<id>/deposit
    """
    # Replace UUIDs with <id>
    path = re.sub(r'/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '/<id>', path)
    # Replace numeric IDs with <id>
    path = re.sub(r'/\d+', '/<id>', path)
    return path


def setup_metrics(app):
    """
    Setup Prometheus metrics middleware for Flask app
    Call this function in your app.py after creating the Flask app
    """
    
    @app.before_request
    def before_request():
        """Record start time before each request"""
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """Record metrics after each request"""
        # Skip metrics endpoint itself
        if request.path == '/metrics':
            return response
        
        # Calculate request duration
        request_latency = time.time() - g.start_time
        
        # Normalize endpoint path
        endpoint = normalize_path(request.path)
        
        # Update metrics
        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(request_latency)
        
        # Track errors separately
        if response.status_code >= 400:
            http_requests_errors_total.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code
            ).inc()
        
        return response
    
    @app.route('/metrics')
    def metrics():
        """
        Prometheus metrics endpoint
        Prometheus will scrape this endpoint every 15 seconds
        """
        return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST} 
