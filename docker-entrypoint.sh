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

# Print diagnostic information
echo "Verifying package installation..."
echo "Python path:"
python3 -c "import sys; print('\n'.join(sys.path))"
echo "Installed packages:"
pip list
echo "Attempting to import simpleguardhome..."
python3 -c "import simpleguardhome; print('Successfully imported simpleguardhome')" || exit 1

# Start the application
echo "Starting SimpleGuardHome server..."
exec python3 -m simpleguardhome.main

# Store child PID
child=$!

# Wait for process to complete
wait "$child"