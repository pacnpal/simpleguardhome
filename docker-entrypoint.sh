#!/bin/bash
set -e

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting SimpleGuardHome..."

# Run the app with src in Python path to find the module
PYTHONPATH=/app/src exec python3 -m uvicorn simpleguardhome.main:app --host 0.0.0.0 --port 8000