# logs_querier

A Python service that provides a REST API interface for querying Datadog logs with built-in monitoring capabilities.

## 🌟 Features

- **🔍 Datadog Logs API Integration**
  - Search logs by service name
  - Support for absolute and relative time ranges
  - Custom query filtering
  - Automatic API key management

- **🚀 REST API Endpoints**
  - Health check endpoint
  - Logs search with specific timestamps
  - Logs search with relative timeranges (e.g., last hour)

- **📊 Built-in Monitoring**
  - Periodic status logging (enabled by default)
  - Structured JSON logs for Datadog agent pickup
  - API request/response tracking
  - Error and performance monitoring

- **🛠️ Interactive CLI**
  - Quick search commands
  - Log viewing capabilities
  - Real-time log following
  - Health check utilities

## 🚀 Quick Start

### Option 1: Using Startup Scripts (Recommended)

**Linux/macOS:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

**With Virtual Environment (Linux/macOS):**
```bash
./start.sh --venv
```

### Option 2: Manual Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   ```bash
   cp env_example.txt .env
   # Edit .env with your Datadog credentials
   ```

3. **Start the Service:**
   ```bash
   python logs_querier.py
   ```

## ⚙️ Configuration Options

### Required Environment Variables

- `DD_API_KEY` - Your Datadog API key
  ```bash
  DD_API_KEY=your_api_key_here
  ```

### Optional Environment Variables

- `DD_APP_KEY` - Datadog Application key (recommended)
  ```bash
  DD_APP_KEY=your_app_key_here
  ```

- `DD_SITE` - Datadog site (default: datadoghq.com)
  ```bash
  DD_SITE=datadoghq.eu  # For EU region
  ```

### Logging Configuration

- `ENABLE_PERIODIC_LOGGING` - Enable/disable periodic status logging
  ```bash
  ENABLE_PERIODIC_LOGGING=true  # default: true
  ```

- `LOG_INTERVAL_SECONDS` - How often to log status updates
  ```bash
  LOG_INTERVAL_SECONDS=30  # default: 30
  ```

- `LOG_FILE_PATH` - Where to write log files
  ```bash
  LOG_FILE_PATH=/var/log/logs_querier/logs_querier.log
  ```

## 🎯 API Endpoints

### Health Check
```http
GET /health
```

### Search Logs with Specific Timestamps
```http
POST /logs/search
Content-Type: application/json

{
    "service": "my-service",
    "start_time": "2024-01-01T00:00:00Z",
    "end_time": "2024-01-01T23:59:59Z",
    "limit": 50,
    "query": "status:error"  // Optional
}
```

### Search Logs with Relative Timerange
```http
POST /logs/search/timerange
Content-Type: application/json

{
    "service": "my-service",
    "timerange": "1h",
    "limit": 50,
    "query": "status:error"  // Optional
}
```

#### Available Timeranges
- `15m` - Last 15 minutes
- `30m` - Last 30 minutes
- `1h` - Last 1 hour
- `4h` - Last 4 hours
- `1d` - Last 1 day
- `7d` - Last 7 days

## 🛠️ CLI Commands

### Check Service Health
```bash
python cli.py health
```

### Quick Search (Last Hour)
```bash
python cli.py quick-search --service my-app
```

### Search with Timerange
```bash
python cli.py search-timerange --service my-app --timerange 4h --limit 20
```

### Search with Specific Timestamps
```bash
python cli.py search \
  --service my-app \
  --start 2024-01-01T00:00:00Z \
  --end 2024-01-01T23:59:59Z \
  --limit 50
```

### View Service Logs
```bash
# View last 20 lines
python cli.py logs

# View last 50 lines
python cli.py logs --lines 50

# Follow logs in real-time
python cli.py logs --follow
```

### Show All Examples
```bash
python cli.py examples
```

## 📊 Monitoring & Logs

### Log Types Generated

1. **Periodic Status Logs**
   ```json
   {
     "timestamp": "2024-01-15T10:30:00Z",
     "level": "INFO",
     "service": "logs_querier",
     "message": "Periodic status check",
     "service_status": "healthy",
     "endpoints_available": ["health", "logs/search", "logs/search/timerange"]
   }
   ```

2. **API Request Logs**
   ```json
   {
     "timestamp": "2024-01-15T10:30:15Z",
     "level": "INFO",
     "service": "logs_querier",
     "message": "Logs search request received",
     "endpoint": "/logs/search",
     "request_data": {"service": "my-app", "timerange": "1h"}
   }
   ```

3. **Error Logs**
   ```json
   {
     "timestamp": "2024-01-15T10:30:16Z",
     "level": "ERROR",
     "service": "logs_querier",
     "message": "Datadog API request failed",
     "error": "API key invalid"
   }
   ```

### Log File Locations

1. **Primary Location:**
   ```
   /var/log/logs_querier/logs_querier.log
   ```

2. **Fallback Location:**
   ```
   ./logs_querier.log
   ```

## 🔒 Security Notes

1. Never commit your `.env` file
2. Keep your Datadog API keys secure
3. Use environment variables in production
4. Consider using application keys with limited permissions

## 🐛 Troubleshooting

### Common Issues

1. **"DD_API_KEY environment variable is required"**
   - Ensure `.env` file exists and contains valid API key
   - Or set environment variable: `export DD_API_KEY=your_key`

2. **"Could not find logs_querier log file"**
   - Check file permissions in `/var/log/logs_querier/`
   - Service will fallback to current directory

3. **Connection Errors**
   - Verify network connectivity
   - Check if Datadog site is correct for your region
   - Ensure API key has proper permissions

### Getting Help

1. Check service health: `python cli.py health`
2. View service logs: `python cli.py logs`
3. Verify Datadog API key permissions
4. Check network connectivity to Datadog

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License - Feel free to use this code in your projects! 