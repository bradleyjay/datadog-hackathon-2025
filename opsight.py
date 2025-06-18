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
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', '/var/log/opsight/opsight.log')

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
            LOG_FILE_PATH = './opsight.log'
    
    # Configure logger
    logger = logging.getLogger('opsight')
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
                'service': 'opsight',
                'version': '1.0.0'
            }
            
            # Add extra fields if present - check both 'extra' attribute and direct attributes
            if hasattr(record, 'extra') and record.extra:
                log_entry.update(record.extra)
            
            # Also check for extra fields directly on the record
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                              'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                              'thread', 'threadName', 'processName', 'process', 'message', 'exc_info',
                              'exc_text', 'stack_info', 'extra']:
                    log_entry[key] = value
            
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
logger.info("opsight service starting up", extra={
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
        # self.base_url = f"https://api.datadoghq.com"
        
    def search_logs(self, query, start_time, end_time, limit=50):
        """
        Search logs using Datadog's logs search API v2
        """
        url = f"{self.base_url}/api/v2/logs/events/search"
        
        headers = {
            'Content-Type': 'application/json',
            'DD-API-KEY': self.api_key
        }
        
        if self.app_key:
            headers['DD-APPLICATION-KEY'] = self.app_key
        
        # Prepare the payload according to the v2 API documentation
        payload = {
            "filter": {
                "query": query,
                "from": start_time,
                "to": end_time
            },
            "sort": "-timestamp",
            "page": {
                "limit": min(limit, 1000)  # API max is 1000
            }
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
            log_count = len(response_data.get('data', []))
            logger.info("Datadog API request successful", extra={
                'query': query,
                'logs_returned': log_count,
                'response_status': response.status_code,
                'request_type': 'logs_search'
            })
            
            return response_data
        except requests.exceptions.RequestException as e:
            # Log API errors with more detail
            error_details = {
                'query': query,
                'error': str(e),
                'request_type': 'logs_search',
                'url': url,
                'payload': payload
            }
            
            if hasattr(e, 'response') and e.response is not None:
                error_details.update({
                    'status_code': e.response.status_code,
                    'response_text': e.response.text[:1000],  # More response text
                    'response_headers': dict(e.response.headers)
                })
                
                # Also print to console for immediate debugging
                print(f"DATADOG SEARCH FAILED:")
                print(f"Status Code: {e.response.status_code}")
                print(f"Response Text: {e.response.text}")
                print(f"Response Headers: {dict(e.response.headers)}")
                print(f"Request URL: {url}")
                print(f"Request Payload: {json.dumps(payload, indent=2)}")
            
            logger.error("Datadog API request failed", extra=error_details)
            raise Exception(f"Error querying Datadog logs: {str(e)}")

    def submit_log(self, log_data):
        """
        Submit logs to Datadog's logs intake API
        """
        url = f"https://http-intake.logs.{self.site}/api/v2/logs"
        
        headers = {
            'Content-Type': 'application/json',
            'DD-API-KEY': self.api_key
        }
        
        # Debug logging - log the request details
        logger.info("Attempting to submit logs to Datadog", extra={
            'url': url,
            'log_count': len(log_data) if isinstance(log_data, list) else 1,
            'dd_site': self.site,
            'api_key_length': len(self.api_key) if self.api_key else 0,
            'headers_count': len(headers)
        })
        
        # Ensure log_data is a list
        if not isinstance(log_data, list):
            log_data = [log_data]
            
        # Add timestamp if not present
        for log in log_data:
            if 'timestamp' not in log:
                log['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Log the payload being sent (without sensitive data)
        logger.info("Submitting log payload", extra={
            'payload_size': len(str(log_data)),
            'log_entries': len(log_data),
            'sample_log_keys': list(log_data[0].keys()) if log_data else []
        })
        
        try:
            response = requests.post(url, headers=headers, json=log_data, timeout=30)
            
            # Log response details regardless of success/failure
            logger.info("Datadog API response received", extra={
                'status_code': response.status_code,
                'response_headers': dict(response.headers),
                'response_size': len(response.text),
                'url': url,
                'request_type': 'log_submission'
            })
            
            # Log response content for debugging
            if response.status_code not in [200, 202]:  # 202 = Accepted is also success
                logger.warning("Non-success response from Datadog", extra={
                    'status_code': response.status_code,
                    'response_text': response.text[:1000],  # First 1000 chars
                    'url': url
                })
            
            response.raise_for_status()
            
            logger.info("Successfully submitted logs to Datadog", extra={
                'logs_submitted': len(log_data),
                'request_type': 'log_submission',
                'status_code': response.status_code,
                'response_text': response.text[:200] if response.text else 'No response body'
            })
            
            return True
            
        except requests.exceptions.RequestException as e:
            import traceback
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'traceback': traceback.format_exc(),
                'url': url,
                'request_type': 'log_submission',
                'dd_site': self.site,
                'api_key_length': len(self.api_key) if self.api_key else 0,
                'payload_sample': str(log_data)[:500] if log_data else 'No payload'
            }
            
            # Add response details if available
            if hasattr(e, 'response') and e.response is not None:
                error_details.update({
                    'status_code': e.response.status_code,
                    'response_text': e.response.text[:1000],  # More response text for debugging
                    'response_headers': dict(e.response.headers)
                })
                
                # Also print to console for immediate visibility
                print(f"DATADOG SUBMISSION FAILED:")
                print(f"Status Code: {e.response.status_code}")
                print(f"Response Text: {e.response.text}")
                print(f"Response Headers: {dict(e.response.headers)}")
            
            logger.error("Failed to submit logs to Datadog", extra=error_details)
            raise Exception(f"Error submitting logs to Datadog: {str(e)}")

# Initialize Datadog client
dd_client = DatadogLogsClient(DD_API_KEY, DD_APP_KEY, DD_SITE)

# Periodic logging function
def periodic_logger():
    """Background thread that logs periodic status information"""
    while True:
        try:
            # Create status log
            status_log = {
                'message': 'Opsight periodic status check',
                'service': 'opsight',
                'status': 'info',
                'service_status': 'healthy',
                'uptime_check': True,
                'endpoints_available': ['health', 'logs/search', 'logs/search/timerange', 'logs/submit'],
                'dd_site': DD_SITE,
                'log_type': 'periodic_status',
                'ddsource': 'opsight',
                'ddtags': 'env:staging,monitor_type:health,service:opsight',
                'hostname': os.uname().nodename
            }
            
            # Submit log to Datadog
            try:
                print(f"[{datetime.utcnow().isoformat()}] Attempting periodic log submission...")
                dd_client.submit_log(status_log)
                print(f"[{datetime.utcnow().isoformat()}] ✅ Periodic log submission successful")
            except Exception as e:
                import traceback
                print(f"[{datetime.utcnow().isoformat()}] ❌ Periodic log submission failed: {str(e)}")
                logger.error("Failed to submit periodic status log to Datadog", extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'traceback': traceback.format_exc(),
                    'log_data': status_log,
                    'dd_site': DD_SITE,
                    'log_type': 'periodic_error'
                })
            
            # Also log locally for redundancy
            # Remove 'message' from extra data to avoid LogRecord conflict
            local_log_data = {k: v for k, v in status_log.items() if k != 'message'}
            logger.info("Periodic status check", extra=local_log_data)
            
            time.sleep(LOG_INTERVAL_SECONDS)
        except Exception as e:
            import traceback
            logger.error("Error in periodic logger", extra={
                'error_type': type(e).__name__,
                'error_message': str(e),
                'traceback': traceback.format_exc(),
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
    
    response_data = {"status": "healthy", "service": "opsight"}
    
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
        "query": "datadog-agent" (optional, defaults to "datadog-agent"),
        "start_time": "2024-01-01T00:00:00Z" (ISO format, optional),
        "end_time": "2024-01-01T23:59:59Z" (ISO format, optional),
        "limit": 5 (optional, default 5)
    }
    If start_time and end_time are not provided, searches 1 hour ago for a 5-minute window
    """
    try:
        data = request.get_json() or {}
        
        # Log incoming request
        logger.info("Logs search request received", extra={
            'endpoint': '/logs/search',
            'method': 'POST',
            'request_data': data,
            'log_type': 'api_request'
        })
        
        # Default parameters based on requirements
        query = data.get('query', 'datadog-agent')
        limit = data.get('limit', 5)
        
        # Calculate default time range: 1 hour ago, 5-minute window
        if 'start_time' not in data or 'end_time' not in data:
            now = datetime.utcnow()
            # Start time: 1 hour ago
            start_time = now - timedelta(hours=1)
            # End time: 5 minutes after start time
            end_time = start_time + timedelta(minutes=5)
            
            start_iso = start_time.isoformat() + 'Z'
            end_iso = end_time.isoformat() + 'Z'
        else:
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            
            # Validate and parse timestamps
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                
                # Convert to ISO format for Datadog API
                start_iso = start_dt.isoformat() + 'Z'
                end_iso = end_dt.isoformat() + 'Z'
                
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
            log_count = len(logs_response.get('data', []))
            logger.info("Logs search completed successfully", extra={
                'endpoint': '/logs/search',
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
            log_count = len(logs_response.get('data', []))
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

@app.route('/logs/submit', methods=['POST'])
def submit_logs():
    """
    Submit logs to Datadog
    Expected JSON payload:
    {
        "logs": [
            {
                "message": "log message",
                "service": "service name",  # Optional, will be prefixed with "opsight."
                "status": "info|warning|error",
                ... additional fields ...
            }
        ]
    }
    """
    try:
        data = request.get_json()
        
        # Log incoming request
        logger.info("Log submission request received", extra={
            'endpoint': '/logs/submit',
            'method': 'POST',
            'log_type': 'api_request'
        })
        
        if not data or 'logs' not in data:
            error_msg = "JSON payload with 'logs' array required"
            logger.warning("Bad request - invalid payload", extra={
                'endpoint': '/logs/submit',
                'error': error_msg,
                'log_type': 'api_error'
            })
            return jsonify({"error": error_msg}), 400
        
        logs = data['logs']
        if not isinstance(logs, list):
            logs = [logs]
            
        # Process each log entry
        for log in logs:
            if not isinstance(log, dict):
                error_msg = "Each log entry must be a JSON object"
                logger.warning("Bad request - invalid log format", extra={
                    'endpoint': '/logs/submit',
                    'error': error_msg,
                    'log_type': 'api_error'
                })
                return jsonify({"error": error_msg}), 400
                
            if 'message' not in log:
                error_msg = "Each log entry must contain a 'message' field"
                logger.warning("Bad request - missing message", extra={
                    'endpoint': '/logs/submit',
                    'error': error_msg,
                    'log_type': 'api_error'
                })
                return jsonify({"error": error_msg}), 400
            
            # Ensure service is set to opsight or prefixed with opsight.
            if 'service' not in log:
                log['service'] = 'opsight'
            elif log['service'] != 'opsight':
                log['service'] = f"opsight.{log['service']}"
        
        # Submit logs to Datadog
        try:
            dd_client.submit_log(logs)
            
            response_data = {
                "success": True,
                "message": f"Successfully submitted {len(logs)} log(s)"
            }
            
            logger.info("Logs submitted successfully", extra={
                'endpoint': '/logs/submit',
                'logs_count': len(logs),
                'log_type': 'api_response'
            })
            
            return jsonify(response_data)
            
        except Exception as e:
            error_msg = f"Failed to submit logs to Datadog: {str(e)}"
            logger.error("Datadog submission failed", extra={
                'endpoint': '/logs/submit',
                'error': error_msg,
                'log_type': 'api_error'
            })
            return jsonify({"error": error_msg}), 500
            
    except Exception as e:
        error_msg = f"Internal server error: {str(e)}"
        logger.error("Internal server error", extra={
            'endpoint': '/logs/submit',
            'error': error_msg,
            'log_type': 'api_error'
        })
        return jsonify({"error": error_msg}), 500

if __name__ == '__main__':
    print(f"Starting opsight service...")
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
    print(f"  POST /logs/submit")
    
    app.run(host='0.0.0.0', port=5000, debug=True) 