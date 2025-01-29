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

# Create necessary directories and set permissions
RUN mkdir -p /app/src/simpleguardhome && \
    chmod -R 755 /app

# Copy source code, maintaining directory structure
COPY . /app/

# Debug: Show the copied files and set execute permission for entrypoint script
RUN echo "Project structure:" && \
    tree /app && \
    echo "Package directory contents:" && \
    ls -la /app/src/simpleguardhome/ && \
    chmod +x /app/docker-entrypoint.sh && \
    cp /app/docker-entrypoint.sh /usr/local/bin/

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Install Python requirements and verify the package
RUN pip install --no-cache-dir -r requirements.txt && \
    set -e && \
    echo "Installing package..." && \
    pip uninstall -y simpleguardhome || true && \
    # Debug: Show package files
    echo "Python path:" && \
    python3 -c "import sys; print('\n'.join(sys.path))" && \
    echo "Source directory contents:" && \
    ls -R /app/src && \
    # Install package in editable mode with compatibility mode enabled
    pip install --use-pep517 -e . --config-settings editable_mode=compat && \
    echo "Verifying installation..." && \
    pip show simpleguardhome && \
    # List all package files
    echo "Package contents:" && \
    find /app/src/simpleguardhome -type f -ls && \
    # Verify package can be imported
    echo "Testing import..." && \
    python3 -c "import simpleguardhome; print(f'Package found at: {simpleguardhome.__file__}')" && \
    # Verify app can be imported
    echo "Testing app import..." && \
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