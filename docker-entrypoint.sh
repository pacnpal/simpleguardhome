#!/bin/bash
set -e

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting SimpleGuardHome..."

# Verify package can be imported
echo "Verifying package installation..."
python3 -c "import simpleguardhome" || exit 1

# Start the application
echo "Starting SimpleGuardHome server..."
exec python3 -m simpleguardhome.main