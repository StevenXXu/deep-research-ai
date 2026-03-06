# Use official Python runtime as a parent image
FROM python:3.11-slim

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
    && npm install -g markdown-pdf \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and Browsers
RUN pip install playwright && playwright install chromium --with-deps

# Copy backend code
COPY . .

# Expose port
EXPOSE 8080

# Run the server using python to trigger the __main__ block which handles PORT env
CMD ["python", "server.py"]
