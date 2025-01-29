#!/bin/bash
set -e

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting SimpleGuardHome..."

# Start the application
exec python3 -m uvicorn simpleguardhome.main:app --host 0.0.0.0 --port 8000