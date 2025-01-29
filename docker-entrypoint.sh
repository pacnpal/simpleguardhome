#!/bin/bash

# ULTIMATE SAFETY CONTROL SYSTEM V9000

# If we're not in ANY recovery mode, exit on ANY error
if [[ "$RESCUE_MODE" != "1" && "$EMERGENCY_MODE" != "1" && "$LAST_RESORT_MODE" != "1" && "$ULTRA_SAFE_MODE" != "1" ]]; then
    set -e
fi

# Colors for ALL THE WARNINGS
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging with timestamps, colors, and BACKUP LOGGING
log() {
    local msg="$1"
    local color="${2:-$NC}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${color}[${timestamp}] $msg${NC}"
    
    # Write to ALL log files for redundancy!
    for backup in main backup1 backup2 backup3 backup4 rescue emergency last_resort ultrabackup; do
        echo "[${timestamp}] $msg" >> "/app/$backup/logs/system.log"
    done
}

# ULTRA monitoring of EVERYTHING
monitor_everything() {
    while true; do
        # Monitor the process
        if [ -n "$1" ]; then
            cpu_usage=$(ps -p $1 -o %cpu | tail -1)
            mem_usage=$(ps -p $1 -o %mem | tail -1)
            if (( $(echo "$cpu_usage > 90" | bc -l) )) || (( $(echo "$mem_usage > 90" | bc -l) )); then
                log "⚠️ HIGH RESOURCE USAGE - CPU: ${cpu_usage}%, MEM: ${mem_usage}%" $YELLOW
            fi
        fi

        # Monitor the monitoring system
        if ! pgrep -f "/app/monitor/monitor.py" > /dev/null; then
            log "🚨 MONITOR SYSTEM DOWN - RESTARTING!" $RED
            python3 /app/monitor/monitor.py &
        fi

        # Verify ALL backups
        for backup in main backup1 backup2 backup3 backup4 rescue emergency last_resort ultrabackup; do
            if [ ! -d "/app/$backup/src/simpleguardhome" ]; then
                log "💥 BACKUP MISSING: $backup - INITIATING RECOVERY!" $RED
                # Try to restore from another backup
                for source in main backup1 backup2 backup3 backup4 rescue emergency last_resort ultrabackup; do
                    if [ "$source" != "$backup" ] && [ -d "/app/$source/src/simpleguardhome" ]; then
                        cp -r "/app/$source/src/simpleguardhome" "/app/$backup/src/"
                        log "🔄 Restored $backup from $source" $GREEN
                        break
                    fi
                done
            fi
        done

        # Verify checksums
        for backup in main backup1 backup2 backup3 backup4 rescue emergency last_resort ultrabackup; do
            if [ -f "/app/$backup/checksums.md5" ]; then
                if ! (cd "/app/$backup" && md5sum -c --quiet checksums.md5 2>/dev/null); then
                    log "🚨 CHECKSUM FAILURE IN $backup - INITIATING REPAIR!" $RED
                    repair_backup "$backup"
                fi
            fi
        done

        sleep 5
    done
}

# EMERGENCY debug with EVERYTHING
emergency_debug() {
    log "🚨 ULTRA EMERGENCY DEBUG ACTIVATED 🚨" $RED
    
    # System state
    log "System Status:" $YELLOW
    uptime
    log "Memory Usage:" $YELLOW
    free -h
    log "Disk Usage:" $YELLOW
    df -h
    log "Process Tree:" $YELLOW
    pstree -p
    log "Network Status:" $YELLOW
    netstat -tulpn
    log "File Systems:" $YELLOW
    lsof
    
    # Backup verification
    log "Backup Status:" $YELLOW
    for backup in main backup1 backup2 backup3 backup4 rescue emergency last_resort ultrabackup; do
        log "Checking $backup:" $BLUE
        tree "/app/$backup"
        if [ -f "/app/$backup/checksums.md5" ]; then
            (cd "/app/$backup" && md5sum -c checksums.md5) || log "❌ Checksum verification failed for $backup" $RED
        fi
    done
    
    # Monitor status
    log "Monitor Status:" $YELLOW
    if [ -f "/app/monitor/stats.json" ]; then
        cat "/app/monitor/stats.json"
    fi
}

# Repair backup from ANY valid source
repair_backup() {
    local broken_backup=$1
    log "🔧 Attempting to repair $broken_backup..." $YELLOW
    
    for source in main backup1 backup2 backup3 backup4 rescue emergency last_resort ultrabackup; do
        if [ "$source" != "$broken_backup" ] && [ -d "/app/$source/src/simpleguardhome" ]; then
            if (cd "/app/$source" && md5sum -c --quiet checksums.md5 2>/dev/null); then
                log "Found valid source: $source" $GREEN
                cp -r "/app/$source/src/simpleguardhome"/* "/app/$broken_backup/src/simpleguardhome/"
                cp "/app/$source/checksums.md5" "/app/$broken_backup/"
                log "✅ Repaired $broken_backup from $source" $GREEN
                return 0
            fi
        fi
    done
    
    log "💥 CRITICAL: Could not repair $broken_backup from any source!" $RED
    return 1
}

# Verify EVERYTHING
verify_everything() {
    local error_count=0
    local repair_count=0
    
    log "=== 🔍 ULTRA VERIFICATION SYSTEM STARTING ===" $BLUE
    
    # 1. Verify ALL backup directories
    for backup in main backup1 backup2 backup3 backup4 rescue emergency last_resort ultrabackup; do
        if [ ! -d "/app/$backup/src/simpleguardhome" ]; then
            log "Missing $backup directory - attempting repair..." $RED
            if ! repair_backup "$backup"; then
                error_count=$((error_count + 1))
            else
                repair_count=$((repair_count + 1))
            fi
        fi
    done
    
    # 2. Verify ALL files in ALL backups
    local required_files=(
        "__init__.py"
        "main.py"
        "adguard.py"
        "config.py"
        "templates/index.html"
        "favicon.ico"
    )

    for backup in main backup1 backup2 backup3 backup4 rescue emergency last_resort ultrabackup; do
        for file in "${required_files[@]}"; do
            if [ ! -f "/app/$backup/src/simpleguardhome/$file" ]; then
                log "Missing $file in $backup - attempting repair..." $RED
                if ! repair_backup "$backup"; then
                    error_count=$((error_count + 1))
                else
                    repair_count=$((repair_count + 1))
                fi
                break
            fi
        done
    done
    
    # 3. Verify ALL checksums
    for backup in main backup1 backup2 backup3 backup4 rescue emergency last_resort ultrabackup; do
        if ! (cd "/app/$backup" && md5sum -c --quiet checksums.md5 2>/dev/null); then
            log "Checksum verification failed for $backup - attempting repair..." $RED
            if ! repair_backup "$backup"; then
                error_count=$((error_count + 1))
            else
                repair_count=$((repair_count + 1))
            fi
        fi
    done
    
    # 4. Verify Python imports from ALL backups
    for backup in main backup1 backup2 backup3 backup4 rescue emergency last_resort ultrabackup; do
        if ! PYTHONPATH="/app/$backup/src" python3 -c "
import sys
import simpleguardhome
from simpleguardhome.main import app
print(f'Successfully imported from {sys.path[0]}')
"; then
            log "Import verification failed for $backup" $RED
            error_count=$((error_count + 1))
        fi
    done

    # Final verdict with ALL safety modes
    if [ $error_count -gt 0 ]; then
        if [ "$ULTRA_SAFE_MODE" = "1" ]; then
            log "⚠️ ULTRA SAFE MODE: Continuing with $error_count errors" $PURPLE
            return 0
        elif [ "$LAST_RESORT_MODE" = "1" ]; then
            log "⚠️ LAST RESORT MODE: Continuing with $error_count errors" $RED
            return 0
        elif [ "$EMERGENCY_MODE" = "1" ]; then
            log "⚠️ EMERGENCY MODE: $error_count errors remain" $RED
            return 0
        elif [ "$RESCUE_MODE" = "1" ]; then
            log "⚠️ RESCUE MODE: $error_count errors remain" $YELLOW
            return 0
        else
            log "💥 FATAL: Found $error_count errors!" $RED
            log "Try: RESCUE_MODE=1, EMERGENCY_MODE=1, LAST_RESORT_MODE=1, or ULTRA_SAFE_MODE=1" $YELLOW
            return 1
        fi
    fi

    log "✅ ULTRA VERIFICATION PASSED! ($repair_count repairs performed)" $GREEN
    return 0
}

# Start monitoring system
python3 /app/monitor/monitor.py &

# Run verification with ALL safety modes
if ! verify_everything; then
    if [[ "$RESCUE_MODE" != "1" && "$EMERGENCY_MODE" != "1" && "$LAST_RESORT_MODE" != "1" && "$ULTRA_SAFE_MODE" != "1" ]]; then
        log "💥 FATAL: System verification failed!" $RED
        log "Available recovery modes:" $YELLOW
        log "  1. RESCUE_MODE=1 (Basic recovery)" $YELLOW
        log "  2. EMERGENCY_MODE=1 (Aggressive recovery)" $RED
        log "  3. LAST_RESORT_MODE=1 (Maximum tolerance)" $PURPLE
        log "  4. ULTRA_SAFE_MODE=1 (Nothing can stop it)" $CYAN
        exit 1
    fi
fi

log "🚀 Starting SimpleGuardHome with ULTRA SAFETY..." $GREEN

# Start with ALL safety features
if [ "$ULTRA_SAFE_MODE" = "1" ]; then
    log "👾 ULTRA SAFE MODE ACTIVATED" $PURPLE
    python3 -m debugpy --listen 0.0.0.0:5678 -m uvicorn simpleguardhome.main:app --host 0.0.0.0 --port 8000 &
elif [ "$RESCUE_MODE" = "1" ]; then
    log "🛠️ RESCUE MODE with debugger on port 5678" $YELLOW
    python3 -m debugpy --listen 0.0.0.0:5678 -m uvicorn simpleguardhome.main:app --host 0.0.0.0 --port 8000 &
elif [ "$EMERGENCY_MODE" = "1" ]; then
    log "🚨 EMERGENCY MODE with full monitoring" $RED
    python3 -m uvicorn simpleguardhome.main:app --host 0.0.0.0 --port 8000 &
else
    python3 -m uvicorn simpleguardhome.main:app --host 0.0.0.0 --port 8000 &
fi

# Get server PID and monitor EVERYTHING
server_pid=$!
monitor_everything $server_pid &
monitor_pid=$!

# Wait for server while monitoring the monitors
wait $server_pid