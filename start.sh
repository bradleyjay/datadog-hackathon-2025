#!/bin/bash

# opsight Startup Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting opsight service...${NC}\n"

# Function to print colored messages
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed. Please install Python 3."
    exit 1
fi

print_status "Python 3 found: $(python3 --version)"

# Check if pip is available
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    print_error "pip is required but not installed. Please install pip."
    exit 1
fi

# Use pip3 if available, otherwise use pip
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
    PIP_CMD="pip"
fi

print_status "Using $PIP_CMD for package management"

# Check if virtual environment should be created
if [ "$1" = "--venv" ] || [ "$1" = "-v" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    print_status "Virtual environment activated"
    PIP_CMD="pip"  # Use pip inside venv
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found. Please ensure you're in the correct directory."
    exit 1
fi

# Install dependencies
print_info "Installing/updating dependencies..."
$PIP_CMD install -r requirements.txt

print_status "Dependencies installed successfully"

# Check for environment file
if [ ! -f ".env" ]; then
    if [ -f "env_example.txt" ]; then
        print_warning ".env file not found. Creating from template..."
        cp env_example.txt .env
        print_info "Please edit .env with your Datadog credentials:"
        print_info "  DD_API_KEY=your_actual_api_key"
        print_info "  DD_APP_KEY=your_actual_app_key (optional)"
        print_info "  DD_SITE=datadoghq.com (or your region)"
        echo
        read -p "Press Enter to continue after updating .env file..."
    else
        print_warning ".env file not found and no template available."
        print_info "You can set environment variables manually:"
        print_info "  export DD_API_KEY=your_actual_api_key"
    fi
fi

# Check if DD_API_KEY is set
if [ -z "$DD_API_KEY" ] && [ ! -f ".env" ]; then
    print_warning "DD_API_KEY environment variable not set and no .env file found."
    print_info "You can:"
    print_info "  1. Set it now: export DD_API_KEY=your_api_key"
    print_info "  2. Create a .env file with DD_API_KEY=your_api_key"
    echo
    read -p "Continue anyway? (y/N): " continue_choice
    if [[ ! $continue_choice =~ ^[Yy]$ ]]; then
        print_info "Exiting. Please set up your DD_API_KEY and try again."
        exit 1
    fi
fi

# Check if the main script exists
if [ ! -f "opsight.py" ]; then
    print_error "opsight.py not found. Please ensure you're in the correct directory."
    exit 1
fi

print_status "All checks passed!"
echo

# Warning about periodic logging
print_warning "PERIODIC LOGGING IS ENABLED BY DEFAULT"
print_info "The service will automatically log status updates every 30 seconds to:"
print_info "  /var/log/opsight/opsight.log (or ./opsight.log as fallback)"
print_info ""
print_info "This is designed for Datadog agent pickup and monitoring."
print_info "To disable periodic logging, set in your .env file:"
print_info "  ENABLE_PERIODIC_LOGGING=false"
print_info ""
print_info "To change log interval (default 30s), set:"
print_info "  LOG_INTERVAL_SECONDS=60"
echo

print_info "Starting opsight service on http://localhost:5000"
print_info "Available endpoints:"
print_info "  GET  /health"
print_info "  POST /logs/search"
print_info "  POST /logs/search/timerange"
echo
print_info "You can test the service with:"
print_info "  python cli.py health"
print_info "  python cli.py quick-search --service your-service"
print_info "  python cli.py logs  # View service logs"
echo
print_info "Press Ctrl+C to stop the service"
echo

# Start the service
python3 opsight.py