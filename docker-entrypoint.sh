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

# Verify package can be imported
echo "Verifying package installation..."
python3 -c "import simpleguardhome" || exit 1

# Start the application
echo "Starting SimpleGuardHome server..."
exec python3 -m simpleguardhome.main

# Store child PID
child=$!

# Wait for process to complete
wait "$child"