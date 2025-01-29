# Use official Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Upgrade pip and essential tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy source code first
COPY . /app/

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

# Install the package in development mode
RUN cd /app && \
    pip uninstall -y simpleguardhome || true && \
    pip install -e . && \
    echo "Verifying installation..." && \
    pip show simpleguardhome && \
    pip list | grep simpleguardhome && \
    python3 -c "import sys; print('Python path:', sys.path)" && \
    echo "Testing import..." && \
    python3 -c "import simpleguardhome; print('Found package at:', simpleguardhome.__file__)" && \
    ls -la /app/src/simpleguardhome/

# Copy and set up entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create rules backup directory with proper permissions
RUN mkdir -p /app/rules_backup && \
    chmod 777 /app/rules_backup

# Default environment variables
ENV ADGUARD_HOST="http://localhost" \
    ADGUARD_PORT=3000

# Expose the application port
EXPOSE 8000

# Volume for persisting rules backups
VOLUME ["/app/rules_backup"]

# Set entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]