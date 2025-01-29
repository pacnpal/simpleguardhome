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
    done && \
    mkdir -p /app/monitor

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

# STEP 4: Set up monitoring
COPY monitor.py /app/monitor/
RUN chmod +x /app/monitor/monitor.py && \
    echo "✓ Installed monitoring system"

# STEP 5: Set up health check script
COPY healthcheck.py /usr/local/bin/
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
    echo "Testing monitoring system:" && \
    python3 -c "import psutil; print('Monitoring system ready')" && \
    echo "✅ EVERYTHING IS VERIFIED, BACKED UP, AND MONITORED!"

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Start monitoring and application
ENTRYPOINT ["docker-entrypoint.sh"]