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
    
    # Debug: Show current directory and its contents
    log "Current directory: $(pwd)"
    log "Directory contents:"
    ls -la

    # Debug: Show all Python paths
    log "Python paths:"
    python3 -c "import sys; print('\n'.join(sys.path))"
    
    # Debug: Show package installation status
    log "Installed packages:"
    pip list
    
    log "Verifying package files..."
    if [ ! -d "/app/src/simpleguardhome" ]; then
        log "ERROR: Package directory not found at /app/src/simpleguardhome"
        log "Searching for package directory..."
        find / -name "simpleguardhome" -type d 2>/dev/null || echo "No simpleguardhome directory found"
        exit 1
    fi

    log "Checking critical files..."
    for file in "__init__.py" "main.py" "adguard.py" "config.py"; do
        if [ ! -f "/app/src/simpleguardhome/$file" ]; then
            log "ERROR: Required file $file not found!"
            exit 1
        fi
    done

    log "Package structure:"
    tree /app/src/simpleguardhome

    log "Environment variables:"
    echo "PYTHONPATH=$PYTHONPATH"
    echo "PWD=$(pwd)"
    
    log "Testing package import..."
    PYTHONPATH=/app/src python3 -c "
import sys
print('Python path:', sys.path)
import simpleguardhome
print('Package location:', simpleguardhome.__file__)
from simpleguardhome.main import app
print('Package imported successfully')
" || {
        log "ERROR: Package import failed!"
        exit 1
    }
}

# Run checks with error handling
if ! check_package; then
    log "Package verification failed"
    exit 1
fi

log "All checks passed. Starting server..."

# Start the application
echo "Starting SimpleGuardHome server..."
exec python3 -c "from simpleguardhome import start; start()"

# Store child PID
child=$!

# Wait for process to complete
wait "$child"