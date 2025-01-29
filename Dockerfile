# Stage 1: Build dependencies and package
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

# Copy package files
COPY src/ /build/src/
COPY pyproject.toml setup.py MANIFEST.in README.md LICENSE ./

# Install requirements and build package
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install -e .

# Verify package installation in builder
RUN python3 -c "import simpleguardhome; print(f'Package installed at {simpleguardhome.__file__}')"

# Stage 2: Final image
FROM python:3.11-slim-bullseye

# Install runtime dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    --no-install-recommends \
    tree \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create source directory
RUN mkdir -p /app/src/simpleguardhome

# Copy package files from builder
COPY --from=builder /build/src/simpleguardhome/ /app/src/simpleguardhome/
COPY --from=builder /build/setup.py /build/pyproject.toml /build/MANIFEST.in /app/

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy and set permissions for entrypoint
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh && \
    cp /app/docker-entrypoint.sh /usr/local/bin/

# Debug: Show directory structure
RUN echo "Directory structure:" && \
    tree /app && \
    echo "Package contents:" && \
    ls -la /app/src/simpleguardhome/

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

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