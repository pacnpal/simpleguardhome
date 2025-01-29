#!/usr/bin/env python3
import sys
import httpx
import os

def check_health():
    try:
        host = os.environ.get('ADGUARD_HOST', 'http://localhost')
        port = os.environ.get('ADGUARD_PORT', '8000')
        with httpx.Client() as client:
            response = client.get('http://localhost:8000/health')
            response.raise_for_status()
        print('✅ Service is healthy')
        sys.exit(0)
    except Exception as e:
        print(f'❌ Health check failed: {str(e)}')
        sys.exit(1)

if __name__ == '__main__':
    check_health()