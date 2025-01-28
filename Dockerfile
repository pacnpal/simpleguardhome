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

# Install the package in editable mode
RUN pip install -e .

# Default environment variables
ENV ADGUARD_HOST="http://localhost" \
    ADGUARD_PORT=3000

# Expose the application port
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "simpleguardhome.main"]