# Use official Python base image
FROM python:3.11-slim

# Set and create working directory
WORKDIR /app
RUN mkdir -p /app/src/simpleguardhome && \
    chmod -R 755 /app

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

# Create necessary directories
RUN mkdir -p /app/src

# Copy source code first, maintaining directory structure
COPY setup.py requirements.txt /app/
COPY src /app/src/

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Verify directory structure
RUN ls -R /app

# Install requirements
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Install the package in development mode with verbose output
RUN echo "Installing package..." && \
    pip uninstall -y simpleguardhome || true && \
    pip install -e . && \
    echo "Verifying package files..." && \
    ls -R /app/src/simpleguardhome/ && \
    echo "Checking package installation..." && \
    pip show simpleguardhome && \
    echo "Verifying import..." && \
    python3 -c "import simpleguardhome; from simpleguardhome.main import app; print('Package imported successfully')"

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