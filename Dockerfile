FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99

# Install system dependencies and Firefox
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    firefox \
    xvfb \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver for Selenium
RUN wget -q "https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz" \
    && tar -xzf geckodriver-v0.34.0-linux64.tar.gz -C /usr/local/bin/ \
    && chmod +x /usr/local/bin/geckodriver \
    && rm geckodriver-v0.34.0-linux64.tar.gz

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting services..."\n\
# Start virtual display\n\
Xvfb :99 -screen 0 1024x768x24 -ac &\n\
sleep 2\n\
export DISPLAY=:99\n\
echo "Firefox is installed at: $(which firefox)"\n\
echo "Starting Flask application..."\n\
# Start Flask app\n\
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose port
EXPOSE $PORT

# Start application
CMD ["/app/start.sh"]
