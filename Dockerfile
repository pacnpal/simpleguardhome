# Stage 1: Build dependencies
FROM python:3.11-slim-bullseye as builder

# Set working directory
WORKDIR /build

# Install build dependencies
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

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final image
FROM python:3.11-slim-bullseye

# Install runtime dependencies and tree for debugging
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    --no-install-recommends \
    tree \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Debug: Show current state
RUN echo "Initial directory structure:" && \
    tree /app || true

# Copy project files
COPY . /app/

# Debug: Show copied files
RUN echo "After copying project files:" && \
    tree /app && \
    echo "Listing src directory:" && \
    ls -la /app/src && \
    echo "Listing package directory:" && \
    ls -la /app/src/simpleguardhome

# Set permissions
RUN chmod -R 755 /app && \
    chmod +x /app/docker-entrypoint.sh && \
    cp /app/docker-entrypoint.sh /usr/local/bin/

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Install the package
RUN set -ex && \
    echo "Installing package..." && \
    pip install -e . && \
    echo "Verifying installation..." && \
    python3 -c "import sys; print('Python path:', sys.path)" && \
    python3 -c "import simpleguardhome; print('Package found at:', simpleguardhome.__file__)" && \
    python3 -c "from simpleguardhome.main import app; print('App imported successfully')"

# Create rules backup directory
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