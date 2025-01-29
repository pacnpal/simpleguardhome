#!/usr/bin/env python3
import os
import sys
import psutil
import requests
import hashlib
import json
from pathlib import Path

def verify_all_backups():
    errors = []
    backups = ['main', 'backup1', 'backup2', 'backup3', 'backup4', 
               'rescue', 'emergency', 'last_resort', 'ultrabackup']
    
    # Check each backup
    for backup in backups:
        base = f'/app/{backup}/src/simpleguardhome'
        if not os.path.exists(base):
            errors.append(f'{backup} backup missing!')
            continue
            
        # Verify checksums
        try:
            with open(f'/app/{backup}/checksums.md5') as f:
                for line in f:
                    checksum, file = line.strip().split()
                    file_path = os.path.join('/app', file)
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            if hashlib.md5(f.read()).hexdigest() != checksum:
                                errors.append(f'Checksum mismatch in {backup}: {file}')
                    else:
                        errors.append(f'File missing in {backup}: {file}')
        except Exception as e:
            errors.append(f'Failed to verify {backup}: {str(e)}')
    
    # Check monitoring
    try:
        with open('/app/monitor/stats.json') as f:
            stats = json.load(f)
            if stats['cpu'] > 90 or stats['mem'] > 90 or stats['disk'] > 90:
                errors.append(f'Resource usage too high: CPU={stats["cpu"]}%, MEM={stats["mem"]}%, DISK={stats["disk"]}%')
    except Exception as e:
        errors.append(f'Monitoring system failure: {str(e)}')
    
    return errors

def main():
    try:
        errors = verify_all_backups()
        if errors:
            print('❌ HEALTH CHECK FAILED:')
            for error in errors:
                print(f'  • {error}')
            sys.exit(1)
        print('✅ ALL SYSTEMS OPERATIONAL')
        sys.exit(0)
    except Exception as e:
        print(f'💥 FATAL ERROR: {str(e)}')
        sys.exit(1)

if __name__ == '__main__':
    main()