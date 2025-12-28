#!/bin/bash
echo "Updating system packages..."
apt-get update -y

echo "Installing Firefox and dependencies..."
apt-get install -y \
    firefox-esr \
    xvfb \
    x11-apps \
    imagemagick \
    python3 \
    python3-pip \
    python3-venv

echo "Installing Python dependencies..."
pip3 install flask gunicorn

echo "Setup complete!"
