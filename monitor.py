#!/usr/bin/env python3
import os
import sys
import psutil
import time
import json
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def monitor_system():
    backups = [
        "main", "backup1", "backup2", "backup3", "backup4",
        "rescue", "emergency", "last_resort", "ultrabackup"
    ]
    
    while True:
        try:
            stats = {
                "cpu": psutil.cpu_percent(),
                "mem": psutil.virtual_memory().percent,
                "disk": psutil.disk_usage("/").percent,
                "timestamp": time.time()
            }

            # Check all backup directories
            for backup in backups:
                path = f"/app/{backup}/src/simpleguardhome"
                if not os.path.exists(path):
                    stats[f"{backup}_missing"] = True
                    logging.warning(f"Backup missing: {backup}")

            # Save stats
            try:
                with open("/app/monitor/stats.json", "w") as f:
                    json.dump(stats, f)
            except Exception as e:
                logging.error(f"Failed to write stats: {str(e)}")

            # Log warnings for high resource usage
            if stats["cpu"] > 80:
                logging.warning(f"High CPU usage: {stats['cpu']}%")
            if stats["mem"] > 80:
                logging.warning(f"High memory usage: {stats['mem']}%")
            if stats["disk"] > 80:
                logging.warning(f"High disk usage: {stats['disk']}%")

        except Exception as e:
            logging.error(f"Monitoring error: {str(e)}")

        time.sleep(5)

if __name__ == "__main__":
    logging.info("Starting system monitor...")
    try:
        monitor_system()
    except KeyboardInterrupt:
        logging.info("Shutting down monitor...")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        sys.exit(1)