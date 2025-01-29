#!/usr/bin/env python3
import sys
import httpx
import os

def check_health():
    try:
        host = os.environ.get('ADGUARD_HOST', 'localhost')
        port = os.environ.get('ADGUARD_PORT', '8000')
        url = f'http://{host}:{port}/health'
        with httpx.Client() as client:
            response = client.get(url)
            response.raise_for_status()
        print('✅ Service is healthy')
        sys.exit(0)
    except Exception as e:
        print(f'❌ Health check failed: {str(e)}')
        sys.exit(1)

if __name__ == '__main__':
    check_health()