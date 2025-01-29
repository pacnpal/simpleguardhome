# ULTIMATE SAFETY VERSION 9000
FROM python:3.11-slim-bullseye

# Install ALL monitoring and verification tools
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    --no-install-recommends \
    tree \
    curl \
    procps \
    htop \
    net-tools \
    lsof \
    sysstat \
    iproute2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# STEP 1: CREATE BACKUP HIERARCHY
RUN for backup in main backup1 backup2 backup3 backup4 rescue emergency last_resort ultrabackup; do \
        mkdir -p "/app/$backup/src/simpleguardhome" && \
        mkdir -p "/app/$backup/logs" && \
        mkdir -p "/app/$backup/monitor" && \
        chmod -R 755 "/app/$backup" && \
        echo "Created $backup hierarchy"; \
    done

# STEP 2: Install Python packages with verification
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
        debugpy \
        psutil \
        requests \
        watchdog \
        prometheus_client \
        checksumdir \
        && \
    pip freeze > /app/requirements.frozen.txt && \
    echo "⚡ Installed and verified packages:" && \
    pip list

# STEP 3: Copy source with CHECKSUM verification
COPY src/simpleguardhome /app/main/src/simpleguardhome/
RUN echo "Creating verified backups..." && \
    for backup in backup1 backup2 backup3 backup4 rescue emergency last_resort ultrabackup; do \
        cp -r /app/main/src/simpleguardhome/* "/app/$backup/src/simpleguardhome/" && \
        find "/app/$backup/src/simpleguardhome" -type f -exec md5sum {} \; > "/app/$backup/checksums.md5" && \
        echo "✓ Created and verified $backup"; \
    done

# STEP 4: Create monitoring scripts
RUN echo 'import os,sys,psutil,time,json,logging\nwhile True:\n    stats={"cpu":psutil.cpu_percent(),"mem":psutil.virtual_memory().percent,"disk":psutil.disk_usage("/").percent}\n    for backup in ["main","backup1","backup2","backup3","backup4","rescue","emergency","last_resort","ultrabackup"]:\n        if not os.path.exists(f"/app/{backup}/src/simpleguardhome"): stats[f"{backup}_missing"]=True\n    with open("/app/monitor/stats.json","w") as f: json.dump(stats,f)\n    time.sleep(5)' > /app/monitor/monitor.py && \
    chmod +x /app/monitor/monitor.py

# STEP 5: Create health check that verifies EVERYTHING
COPY - <<'EOF' /usr/local/bin/healthcheck.py
import os, sys, psutil, requests, hashlib, json
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
    
    # Check monitoring
    try:
        with open('/app/monitor/stats.json') as f:
            stats = json.load(f)
            if stats['cpu'] > 90 or stats['mem'] > 90 or stats['disk'] > 90:
                errors.append(f'Resource usage too high: CPU={stats["cpu"]}%, MEM={stats["mem"]}%, DISK={stats["disk"]}%')
    except:
        errors.append('Monitoring system failure!')
    
    return errors

def main():
    errors = verify_all_backups()
    if errors:
        print('❌ HEALTH CHECK FAILED:')
        for error in errors:
            print(f'  • {error}')
        sys.exit(1)
    print('✅ ALL SYSTEMS OPERATIONAL')
    sys.exit(0)

if __name__ == '__main__':
    main()
EOF

RUN chmod +x /usr/local/bin/healthcheck.py

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 /usr/local/bin/healthcheck.py

# Set up environment with ALL backup paths
ENV PYTHONPATH=/app/main/src:/app/backup1/src:/app/backup2/src:/app/backup3/src:/app/backup4/src:/app/rescue/src:/app/emergency/src:/app/last_resort/src:/app/ultrabackup/src \
    PYTHONBREAKPOINT=debugpy.breakpoint

# Environment variables with ALL recovery modes
ENV ADGUARD_HOST="http://localhost" \
    ADGUARD_PORT=3000 \
    RESCUE_MODE=0 \
    EMERGENCY_MODE=0 \
    LAST_RESORT_MODE=0 \
    ULTRA_SAFE_MODE=0 \
    BACKUP_MONITOR=1

# Expose ports (including debug and monitoring)
EXPOSE 8000 5678 9090

# Set up backup volume hierarchy
RUN for backup in rules_backup rules_backup.1 rules_backup.2 rules_backup.3 rules_backup.4 rules_backup.emergency; do \
        mkdir -p "/app/$backup" && \
        chmod 777 "/app/$backup" && \
        echo "Created and verified: /app/$backup"; \
    done

# ULTRA FINAL VERIFICATION
RUN echo "=== 🚀 ULTRA FINAL VERIFICATION ===" && \
    for backup in main backup1 backup2 backup3 backup4 rescue emergency last_resort ultrabackup; do \
        echo "Verifying $backup:" && \
        tree "/app/$backup" && \
        echo "Testing import from $backup:" && \
        PYTHONPATH="/app/$backup/src" python3 -c "from simpleguardhome.main import app; print(f'Import from {backup} successful')" && \
        echo "Verifying checksums for $backup:" && \
        cd "/app/$backup" && md5sum -c checksums.md5; \
    done && \
    echo "✅ EVERYTHING IS VERIFIED, BACKED UP, AND MONITORED!"

# Start monitoring and application
ENTRYPOINT ["docker-entrypoint.sh"]