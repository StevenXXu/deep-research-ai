# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables to ensure output is flushed immediately
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Install system dependencies for Playwright (Chrome) + PDF generation + Build Tools + Node.js
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    build-essential \
    python3-dev \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    # Install playwright globally for Node.js scripts to find it
    && npm install -g playwright \
    && rm -rf /var/lib/apt/lists/*

# Set NODE_PATH so scripts can find global modules
ENV NODE_PATH=/usr/lib/node_modules

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and Browsers
RUN pip install playwright && playwright install chromium --with-deps

# Force Cache Busting - Change this value to force a rebuild of the COPY step
ARG CACHEBUST=20260307_v8_PRO_FORMAT

# Copy backend code (This step will now definitely re-run)
COPY . .

# VERIFY: Check if server.py contains the deployment check signature
# If grep fails, the build will fail, preventing deployment of old code
# RUN grep -q "DEPLOYMENT CHECK: V2.0" server.py || (echo "ERROR: server.py is OLD! Aborting build." && exit 1)

# Expose port
EXPOSE 8080

# Run the server using python to trigger the __main__ block which handles PORT env
# Force a change to trigger Docker rebuild (v3 - Panic Fix)
CMD ["python", "server.py"]
