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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m pip install --no-cache-dir --upgrade "pip>=21.3" setuptools wheel

# Add architecture-specific compiler flags if needed
ENV ARCHFLAGS=""

# Create necessary directories and set permissions
RUN mkdir -p /app/src/simpleguardhome && \
    chmod -R 755 /app

# Copy source code, maintaining directory structure
COPY setup.py requirements.txt pyproject.toml /app/
COPY src /app/src/

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Install and verify the package
RUN set -e && \
    echo "Installing package..." && \
    pip uninstall -y simpleguardhome || true && \
    # Install package in editable mode with compatibility mode enabled
    pip install --use-pep517 -e . --config-settings editable_mode=compat && \
    echo "Verifying installation..." && \
    pip show simpleguardhome && \
    # List all package files
    echo "Package contents:" && \
    find /app/src/simpleguardhome -type f -ls && \
    # Verify import works
    echo "Testing import..." && \
    python3 -c "import simpleguardhome; from simpleguardhome.main import app; print(f'Package found at: {simpleguardhome.__file__}')" && \
    echo "Package installation successful"

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