FROM python:3.11-slim-bullseye

WORKDIR /app

# Install essential system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/simpleguardhome /app/simpleguardhome/

# Set up health check
COPY healthcheck.py /usr/local/bin/
RUN chmod +x /usr/local/bin/healthcheck.py

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 /usr/local/bin/healthcheck.py

# Environment setup
ENV ADGUARD_HOST="http://localhost" \
    ADGUARD_PORT=3000

# Expose application port
EXPOSE 8000

# Copy and set up entrypoint
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]