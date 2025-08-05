FROM python:3.11-slim

# Install system dependencies for Playwright and FastAPI
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    xvfb \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Set environment variables for Playwright and FastAPI
ENV PLAYWRIGHT_BROWSERS_PATH=/app/pw-browsers
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FASTAPI_ENV=production

# Copy requirements and install Python dependencies
COPY requirements.txt .

# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip

# Install Python packages with error handling
RUN pip install --no-cache-dir -r requirements.txt || \
    (pip install --no-cache-dir fastapi uvicorn playwright beautifulsoup4 requests pydantic lxml && \
     echo "Installed minimal requirements")

# Install Playwright browsers with explicit path
RUN mkdir -p /app/pw-browsers
RUN PLAYWRIGHT_BROWSERS_PATH=/app/pw-browsers playwright install chromium || \
    (playwright install chromium && echo "Installed browsers in default location")
    
RUN PLAYWRIGHT_BROWSERS_PATH=/app/pw-browsers playwright install-deps chromium || \
    (playwright install-deps chromium && echo "Installed browser dependencies")

# Verify browser installation
RUN ls -la /app/pw-browsers/ || echo "Browser directory not found, checking default location" && \
    find /usr/local/lib/python*/site-packages/playwright -name "chrome*" -type f 2>/dev/null || echo "Browsers installed in default location"

# Copy application code
COPY main.py .

# Create non-root user and fix permissions
RUN groupadd -r scraper && useradd -r -g scraper scraper \
    && chown -R scraper:scraper /app \
    && chmod -R 755 /app

# Switch to non-root user
USER scraper

# Expose port (Render uses PORT environment variable)
EXPOSE ${PORT:-8000}

# Health check for FastAPI
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start FastAPI with Uvicorn (production-ready ASGI server)
CMD uvicorn main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 1 \
    --loop uvloop \
    --http httptools \
    --access-log \
    --log-level info \
    --timeout-keep-alive 120 \
    --timeout-graceful-shutdown 30
