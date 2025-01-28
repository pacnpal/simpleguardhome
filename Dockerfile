# Use official Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY . .

# Set Python path to include src directory
ENV PYTHONPATH=/app/src

# Install the package in editable mode
RUN pip install -e .

# Verify package installation
RUN pip show simpleguardhome

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