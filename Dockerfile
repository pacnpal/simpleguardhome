# Use official Python base image
FROM python:3.11-slim-bullseye

# Set working directory
WORKDIR /app

# Install system dependencies with architecture-specific handling
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    --no-install-recommends \
    gcc \
    libc6-dev \
    python3-dev \
    python3-pip \
    tree \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m pip install --no-cache-dir --upgrade "pip>=21.3" setuptools wheel

# Add architecture-specific compiler flags if needed
ENV ARCHFLAGS=""

# Copy requirements first to leverage Docker cache
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . /app/

# Debug: Show project structure after copy
RUN echo "Project structure after copy:" && \
    tree /app && \
    echo "Verifying source directory:" && \
    if [ ! -d "/app/src/simpleguardhome" ]; then \
        echo "ERROR: Source directory missing!" && \
        exit 1; \
    fi && \
    echo "Source directory contents:" && \
    ls -la /app/src/simpleguardhome/

# Set permissions
RUN chmod -R 755 /app && \
    chmod +x /app/docker-entrypoint.sh && \
    cp /app/docker-entrypoint.sh /usr/local/bin/

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Install Python package in development mode
RUN set -e && \
    echo "Installing package..." && \
    pip install -e . && \
    echo "Verifying package installation..." && \
    python3 -c "import simpleguardhome; print('Package location:', simpleguardhome.__file__)" && \
    python3 -c "from simpleguardhome.main import app; print('App imported successfully')" && \
    echo "Package installation successful" && \
    # Create rules backup directory with proper permissions
    mkdir -p /app/rules_backup && \
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