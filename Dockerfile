# Use official Python base image
FROM python:3.11-slim-bullseye

# Set and create working directory
WORKDIR /app
RUN mkdir -p /app/src/simpleguardhome && \
    chmod -R 755 /app
# Install system dependencies with architecture-specific handling
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    --no-install-recommends \
    gcc \
    libc6-dev \
    python3-dev \
    python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Add architecture-specific compiler flags if needed
ENV ARCHFLAGS=""
    && python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Ensure pip is up to date
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Create necessary directories
RUN mkdir -p /app/src

# Copy source code first, maintaining directory structure
COPY setup.py requirements.txt /app/
COPY src /app/src/

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Verify directory structure
RUN ls -R /app

# Set up working directory and install requirements
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Install the package with additional error handling
RUN echo "Installing package..." && \
    pip uninstall -y simpleguardhome || true && \
    pip install --no-deps -v -e . && \
    pip install -e . && \
    echo "Installation complete, verifying..." && \
    pip show simpleguardhome && \
    echo "Package files:" && \
    find /app/src/simpleguardhome -type f && \
    echo "Testing import..." && \
    PYTHONPATH=/app/src python3 -c "import simpleguardhome; from simpleguardhome.main import app; print('Package successfully imported')"

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