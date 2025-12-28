FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    python3 \
    python3-pip \
    python3-venv \
    x11vnc \
    xvfb \
    xfce4 \
    xfce4-goodies \
    firefox-esr \
    novnc \
    websockify \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy application files
COPY . .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Create directories
RUN mkdir -p /tmp/.X11-unix /tmp/.ICE-unix

# Set permissions
RUN chmod 1777 /tmp/.X11-unix /tmp/.ICE-unix

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting services..."\n\
Xvfb :99 -screen 0 1024x768x24 -ac &\n\
sleep 2\n\
export DISPLAY=:99\n\
x11vnc -display :99 -forever -shared -noxdamage -passwd firefox123 -bg -nopw -quiet &\n\
websockify --web /usr/share/novnc/ 6080 localhost:5900 &\n\
sleep 2\n\
firefox --display=:99 &\n\
sleep 2\n\
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose ports
EXPOSE $PORT 6080

# Start services
CMD ["/app/start.sh"]
