#!/bin/bash
set -e

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting SimpleGuardHome..."

# Just run uvicorn pointing to the app
exec python3 -m uvicorn simpleguardhome.main:app --host 0.0.0.0 --port 8000