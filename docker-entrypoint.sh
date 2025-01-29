#!/bin/bash
set -e

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting SimpleGuardHome..."

# Verify the package is importable
if ! python3 -c "from simpleguardhome.main import app"; then
    echo "Error: Failed to import SimpleGuardHome package"
    exit 1
fi

# Start the application
exec python3 -m uvicorn simpleguardhome.main:app --host 0.0.0.0 --port 8000