#!/bin/bash
set -e

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting SimpleGuardHome..."

# Ensure proper Python path
export PYTHONPATH="/app:${PYTHONPATH:-}"

# Verify package can be imported
echo "Verifying package installation..."
python3 -c "import simpleguardhome; print('Package found at:', simpleguardhome.__file__)"

# Start the application
echo "Starting SimpleGuardHome server..."
exec python3 -m simpleguardhome.main