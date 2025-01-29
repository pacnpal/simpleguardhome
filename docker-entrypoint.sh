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
echo "PYTHONPATH environment variable:"
echo $PYTHONPATH
echo "Directory contents of /app/src:"
ls -la /app/src/
echo "Directory contents of /app/src/simpleguardhome:"
ls -la /app/src/simpleguardhome/
echo "Python sys.path:"
python3 -c "import sys; print('\n'.join(sys.path))"
echo "Installed packages:"
pip list | grep simpleguardhome
echo "Attempting to import and locate simpleguardhome..."
python3 -c "import simpleguardhome, os; print('Found at:', os.path.abspath(simpleguardhome.__file__)); print('Parent dir contents:', os.listdir(os.path.dirname(simpleguardhome.__file__)))" || exit 1

# Start the application
echo "Starting SimpleGuardHome server..."
exec python3 -c "from simpleguardhome import start; start()"

# Store child PID
child=$!

# Wait for process to complete
wait "$child"