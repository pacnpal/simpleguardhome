#!/bin/bash
set -e

# Function to handle termination signals
handle_term() {
  echo "Received SIGTERM/SIGINT, shutting down gracefully..."
  kill -TERM "$child"
  wait "$child"
  exit 0
}

# Set up signal handlers
trap handle_term SIGTERM SIGINT

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check package installation
check_package() {
    log "System information:"
    uname -a
    
    log "Python version:"
    python3 --version
    
    log "Directory structure:"
    tree /app
    
    log "Verifying package files..."
    if [ ! -d "/app/src/simpleguardhome" ]; then
        log "ERROR: Package directory not found at /app/src/simpleguardhome!"
        exit 1
    fi

    # Check critical files
    required_files=(
        "__init__.py"
        "main.py"
        "adguard.py"
        "config.py"
        "templates/index.html"
        "favicon.ico"
    )

    for file in "${required_files[@]}"; do
        if [ ! -f "/app/src/simpleguardhome/$file" ]; then
            log "ERROR: Required file $file not found!"
            exit 1
        fi
    done

    log "Environment:"
    echo "PYTHONPATH: $PYTHONPATH"
    echo "PWD: $(pwd)"
    
    log "Testing package import..."
    if ! python3 -c "
import sys
print('Python paths:', sys.path)
import simpleguardhome
print('Package found at:', simpleguardhome.__file__)
from simpleguardhome.main import app
print('Package imported successfully')
"; then
        log "ERROR: Package import failed!"
        exit 1
    fi
}

# Run checks
check_package

log "All checks passed. Starting server..."

# Start the application
exec python3 -m uvicorn simpleguardhome.main:app --host 0.0.0.0 --port 8000

# Store child PID
child=$!

# Wait for process to complete
wait "$child"