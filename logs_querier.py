import os
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Datadog configuration
DD_API_KEY = os.getenv('DD_API_KEY')
DD_APP_KEY = os.getenv('DD_APP_KEY')  # Optional, but often needed for some endpoints
DD_SITE = os.getenv('DD_SITE', 'datadoghq.com')  # Default to US site

# Logging configuration
ENABLE_PERIODIC_LOGGING = os.getenv('ENABLE_PERIODIC_LOGGING', 'true').lower() == 'true'
LOG_INTERVAL_SECONDS = int(os.getenv('LOG_INTERVAL_SECONDS', '30'))  # Log every 30 seconds by default
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', '/var/log/logs_querier/logs_querier.log')

if not DD_API_KEY:
    raise ValueError("DD_API_KEY environment variable is required")

# Setup structured logging
def setup_logging():
    """Configure structured logging for Datadog agent pickup"""
    global LOG_FILE_PATH  # Moved to the start of the function
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(LOG_FILE_PATH)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except PermissionError:
            # Fallback to current directory if can't create in /var/log
            LOG_FILE_PATH = './logs_querier.log'
    
    # Configure logger
    logger = logging.getLogger('logs_querier')
    logger.setLevel(logging.INFO)
    
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler for structured logs
    file_handler = logging.FileHandler(LOG_FILE_PATH)
    file_handler.setLevel(logging.INFO)
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # JSON formatter for structured logs
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'service': 'logs_querier',
                'version': '1.0.0'
            }
            
            # Add extra fields if present
            if hasattr(record, 'extra'):
                log_entry.update(record.extra)
            
            # Add exception info if present
            if record.exc_info:
                log_entry['exception'] = self.formatException(record.exc_info)
            
            return json.dumps(log_entry)
    
    file_handler.setFormatter(JsonFormatter())
    
    # Simple formatter for console
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Initialize logger
logger = setup_logging()

# Log startup
logger.info("logs_querier service starting up", extra={
    'dd_api_key_configured': bool(DD_API_KEY),
    'dd_site': DD_SITE,
    'periodic_logging_enabled': ENABLE_PERIODIC_LOGGING,
    'log_interval_seconds': LOG_INTERVAL_SECONDS,
    'log_file_path': LOG_FILE_PATH
})

class DatadogLogsClient:
    def __init__(self, api_key, app_key=None, site='datadoghq.com'):
        self.api_key = api_key
        self.app_key = app_key
        self.site = site
        self.base_url = f"https://api.{site}"
        
    def search_logs(self, query, start_time, end_time, limit=50):
        """
        Search logs using Datadog's logs search API
        """
        url = f"{self.base_url}/api/v1/logs-queries/list"
        
        headers = {
            'Content-Type': 'application/json',
            'DD-API-KEY': self.api_key
        }
        
        if self.app_key:
            headers['DD-APPLICATION-KEY'] = self.app_key
            
        payload = {
            "query": query,
            "time": {
                "from": start_time,
                "to": end_time
            },
            "sort": "timestamp",
            "limit": limit
        }
        
        # Log the API request
        logger.info("Making Datadog API request", extra={
            'url': url,
            'query': query,
            'time_range': {'from': start_time, 'to': end_time},
            'limit': limit,
            'request_type': 'logs_search'
        })
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            # Log successful response
            response_data = response.json()
            log_count = len(response_data.get('logs', []))
            logger.info("Datadog API request successful", extra={
                'query': query,
                'logs_returned': log_count,
                'response_status': response.status_code,
                'request_type': 'logs_search'
            })
            
            return response_data
        except requests.exceptions.RequestException as e:
            # Log API errors
            logger.error("Datadog API request failed", extra={
                'query': query,
                'error': str(e),
                'request_type': 'logs_search'
            })
            raise Exception(f"Error querying Datadog logs: {str(e)}")

# Initialize Datadog client
dd_client = DatadogLogsClient(DD_API_KEY, DD_APP_KEY, DD_SITE)

# Periodic logging function
def periodic_logger():
    """Background thread that logs periodic status information"""
    while True:
        try:
            # Log periodic status
            logger.info("Periodic status check", extra={
                'service_status': 'healthy',
                'uptime_check': True,
                'endpoints_available': ['health', 'logs/search', 'logs/search/timerange'],
                'dd_site': DD_SITE,
                'log_type': 'periodic_status'
            })
            
            time.sleep(LOG_INTERVAL_SECONDS)
        except Exception as e:
            logger.error("Error in periodic logger", extra={
                'error': str(e),
                'log_type': 'periodic_error'
            })
            time.sleep(LOG_INTERVAL_SECONDS)

# Start periodic logging if enabled
if ENABLE_PERIODIC_LOGGING:
    periodic_thread = threading.Thread(target=periodic_logger, daemon=True)
    periodic_thread.start()
    logger.info("Periodic logging thread started", extra={
        'interval_seconds': LOG_INTERVAL_SECONDS,
        'log_type': 'startup'
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    logger.info("Health check requested", extra={
        'endpoint': '/health',
        'method': 'GET',
        'log_type': 'api_request'
    })
    
    response_data = {"status": "healthy", "service": "logs_querier"}
    
    logger.info("Health check response", extra={
        'endpoint': '/health',
        'response': response_data,
        'log_type': 'api_response'
    })
    
    return jsonify(response_data)

@app.route('/logs/search', methods=['POST'])
def search_logs():
    """
    Search logs endpoint
    Expected JSON payload:
    {
        "service": "my-service",
        "start_time": "2024-01-01T00:00:00Z" (ISO format),
        "end_time": "2024-01-01T23:59:59Z" (ISO format),
        "limit": 50 (optional, default 50)
    }
    """
    try:
        data = request.get_json()
        
        # Log incoming request
        logger.info("Logs search request received", extra={
            'endpoint': '/logs/search',
            'method': 'POST',
            'request_data': data,
            'log_type': 'api_request'
        })
        
        if not data:
            error_msg = "JSON payload required"
            logger.warning("Bad request - no JSON payload", extra={
                'endpoint': '/logs/search',
                'error': error_msg,
                'log_type': 'api_error'
            })
            return jsonify({"error": error_msg}), 400
            
        # Required parameters
        service = data.get('service')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if not all([service, start_time, end_time]):
            error_msg = "Missing required parameters: service, start_time, end_time"
            logger.warning("Bad request - missing parameters", extra={
                'endpoint': '/logs/search',
                'error': error_msg,
                'provided_params': list(data.keys()) if data else [],
                'log_type': 'api_error'
            })
            return jsonify({"error": error_msg}), 400
        
        # Optional parameters
        limit = data.get('limit', 50)
        additional_query = data.get('query', '')
        
        # Build the query
        query = f"service:{service}"
        if additional_query:
            query += f" {additional_query}"
        
        # Validate and parse timestamps
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            # Convert to ISO format for Datadog API
            start_iso = start_dt.isoformat()
            end_iso = end_dt.isoformat()
            
        except ValueError as e:
            error_msg = f"Invalid timestamp format. Use ISO format (e.g., '2024-01-01T00:00:00Z'): {str(e)}"
            logger.warning("Bad request - invalid timestamp", extra={
                'endpoint': '/logs/search',
                'error': error_msg,
                'start_time': start_time,
                'end_time': end_time,
                'log_type': 'api_error'
            })
            return jsonify({"error": error_msg}), 400
        
        # Make request to Datadog
        try:
            logs_response = dd_client.search_logs(query, start_iso, end_iso, limit)
            
            response_data = {
                "success": True,
                "query": query,
                "time_range": {
                    "start": start_iso,
                    "end": end_iso
                },
                "data": logs_response
            }
            
            # Log successful response
            log_count = len(logs_response.get('logs', []))
            logger.info("Logs search completed successfully", extra={
                'endpoint': '/logs/search',
                'service': service,
                'query': query,
                'logs_returned': log_count,
                'time_range': {'start': start_iso, 'end': end_iso},
                'log_type': 'api_response'
            })
            
            return jsonify(response_data)
            
        except Exception as e:
            error_msg = f"Failed to query Datadog: {str(e)}"
            logger.error("Datadog query failed", extra={
                'endpoint': '/logs/search',
                'service': service,
                'query': query,
                'error': error_msg,
                'log_type': 'api_error'
            })
            return jsonify({"error": error_msg}), 500
            
    except Exception as e:
        error_msg = f"Internal server error: {str(e)}"
        logger.error("Internal server error", extra={
            'endpoint': '/logs/search',
            'error': error_msg,
            'log_type': 'api_error'
        })
        return jsonify({"error": error_msg}), 500

@app.route('/logs/search/timerange', methods=['POST'])
def search_logs_with_timerange():
    """
    Search logs with relative timerange endpoint
    Expected JSON payload:
    {
        "service": "my-service",
        "timerange": "1h" | "30m" | "1d" | "7d",
        "limit": 50 (optional, default 50)
    }
    """
    try:
        data = request.get_json()
        
        # Log incoming request
        logger.info("Logs timerange search request received", extra={
            'endpoint': '/logs/search/timerange',
            'method': 'POST',
            'request_data': data,
            'log_type': 'api_request'
        })
        
        if not data:
            error_msg = "JSON payload required"
            logger.warning("Bad request - no JSON payload", extra={
                'endpoint': '/logs/search/timerange',
                'error': error_msg,
                'log_type': 'api_error'
            })
            return jsonify({"error": error_msg}), 400
            
        # Required parameters
        service = data.get('service')
        timerange = data.get('timerange')
        
        if not all([service, timerange]):
            error_msg = "Missing required parameters: service, timerange"
            logger.warning("Bad request - missing parameters", extra={
                'endpoint': '/logs/search/timerange',
                'error': error_msg,
                'provided_params': list(data.keys()) if data else [],
                'log_type': 'api_error'
            })
            return jsonify({"error": error_msg}), 400
        
        # Parse timerange
        now = datetime.utcnow()
        timerange_map = {
            '1h': timedelta(hours=1),
            '30m': timedelta(minutes=30),
            '1d': timedelta(days=1),
            '7d': timedelta(days=7),
            '15m': timedelta(minutes=15),
            '4h': timedelta(hours=4),
            '24h': timedelta(hours=24)
        }
        
        if timerange not in timerange_map:
            error_msg = f"Invalid timerange. Supported values: {list(timerange_map.keys())}"
            logger.warning("Bad request - invalid timerange", extra={
                'endpoint': '/logs/search/timerange',
                'error': error_msg,
                'timerange': timerange,
                'log_type': 'api_error'
            })
            return jsonify({"error": error_msg}), 400
        
        start_time = now - timerange_map[timerange]
        end_time = now
        
        # Optional parameters
        limit = data.get('limit', 50)
        additional_query = data.get('query', '')
        
        # Build the query
        query = f"service:{service}"
        if additional_query:
            query += f" {additional_query}"
        
        # Convert to ISO format for Datadog API
        start_iso = start_time.isoformat()
        end_iso = end_time.isoformat()
        
        # Make request to Datadog
        try:
            logs_response = dd_client.search_logs(query, start_iso, end_iso, limit)
            
            response_data = {
                "success": True,
                "query": query,
                "timerange": timerange,
                "time_range": {
                    "start": start_iso,
                    "end": end_iso
                },
                "data": logs_response
            }
            
            # Log successful response
            log_count = len(logs_response.get('logs', []))
            logger.info("Logs timerange search completed successfully", extra={
                'endpoint': '/logs/search/timerange',
                'service': service,
                'query': query,
                'timerange': timerange,
                'logs_returned': log_count,
                'time_range': {'start': start_iso, 'end': end_iso},
                'log_type': 'api_response'
            })
            
            return jsonify(response_data)
            
        except Exception as e:
            error_msg = f"Failed to query Datadog: {str(e)}"
            logger.error("Datadog query failed", extra={
                'endpoint': '/logs/search/timerange',
                'service': service,
                'query': query,
                'timerange': timerange,
                'error': error_msg,
                'log_type': 'api_error'
            })
            return jsonify({"error": error_msg}), 500
            
    except Exception as e:
        error_msg = f"Internal server error: {str(e)}"
        logger.error("Internal server error", extra={
            'endpoint': '/logs/search/timerange',
            'error': error_msg,
            'log_type': 'api_error'
        })
        return jsonify({"error": error_msg}), 500

if __name__ == '__main__':
    print(f"Starting logs_querier service...")
    print(f"DD_API_KEY configured: {'Yes' if DD_API_KEY else 'No'}")
    print(f"DD_SITE: {DD_SITE}")
    print(f"Periodic logging: {'Enabled' if ENABLE_PERIODIC_LOGGING else 'Disabled'}")
    if ENABLE_PERIODIC_LOGGING:
        print(f"Log interval: {LOG_INTERVAL_SECONDS} seconds")
        print(f"Log file: {LOG_FILE_PATH}")
    print(f"Available endpoints:")
    print(f"  GET  /health")
    print(f"  POST /logs/search")
    print(f"  POST /logs/search/timerange")
    
    app.run(host='0.0.0.0', port=5000, debug=True) 