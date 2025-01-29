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

# Verify package files exist
echo "Verifying package files..."
if [ ! -d "/app/src/simpleguardhome" ]; then
    echo "ERROR: Package directory not found!"
    exit 1
fi

if [ ! -f "/app/src/simpleguardhome/__init__.py" ]; then
    echo "ERROR: Package __init__.py not found!"
    exit 1
fi

if [ ! -f "/app/src/simpleguardhome/main.py" ]; then
    echo "ERROR: Package main.py not found!"
    exit 1
fi

# Print environment information
echo "Environment:"
echo "PYTHONPATH=$PYTHONPATH"
echo "Current directory: $(pwd)"
echo "Package contents:"
ls -R /app/src/simpleguardhome/

# Verify package can be imported
echo "Verifying package import..."
if ! python3 -c "import simpleguardhome; from simpleguardhome.main import app; print('Package imported successfully')"; then
    echo "ERROR: Failed to import package!"
    exit 1
fi

echo "All checks passed. Starting server..."

# Start the application
echo "Starting SimpleGuardHome server..."
exec python3 -c "from simpleguardhome import start; start()"

# Store child PID
child=$!

# Wait for process to complete
wait "$child"