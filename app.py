#!/usr/bin/env python3
"""
Real Firefox Browser 24/7 with VNC Web Access
Access via: https://your-app.onrender.com/vnc.html
"""

import os
import sys
import subprocess
import threading
import time
import signal
import logging
import socket
from flask import Flask, jsonify, render_template_string, request, send_from_directory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

app = Flask(__name__)

# Global variables
vnc_process = None
firefox_process = None
xvfb_process = None
service_running = False
start_time = None
connections = 0

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>🦊 Real Firefox Browser 24/7</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: white;
            font-size: 2.8em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        .hero {
            text-align: center;
            padding: 40px 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            margin-bottom: 30px;
        }
        .hero h2 {
            font-size: 2em;
            margin-bottom: 20px;
        }
        .access-button {
            display: inline-block;
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            padding: 20px 40px;
            border-radius: 15px;
            text-decoration: none;
            font-size: 1.3em;
            font-weight: bold;
            margin: 20px 0;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
            transition: all 0.3s;
        }
        .access-button:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
            background: linear-gradient(135deg, #45a049 0%, #4CAF50 100%);
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .status-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s;
        }
        .status-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.15);
        }
        .status-icon {
            font-size: 2.5em;
            margin-bottom: 15px;
        }
        .status-title {
            font-size: 1.1em;
            color: #ddd;
            margin-bottom: 10px;
        }
        .status-value {
            font-size: 1.8em;
            font-weight: bold;
        }
        .controls {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin: 30px 0;
            flex-wrap: wrap;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            color: white;
            padding: 15px 30px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            transition: all 0.3s;
        }
        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }
        .instructions {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 15px;
            padding: 25px;
            margin: 30px 0;
            border-left: 5px solid #667eea;
        }
        .instructions h3 {
            color: #fff;
            margin-top: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .url-box {
            background: rgba(0, 0, 0, 0.3);
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            font-family: monospace;
            word-break: break-all;
        }
        .alert {
            background: rgba(255, 193, 7, 0.15);
            border: 1px solid rgba(255, 193, 7, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .alert-icon {
            font-size: 1.5em;
        }
        .vnc-container {
            width: 100%;
            height: 600px;
            background: #000;
            border-radius: 10px;
            overflow: hidden;
            margin: 20px 0;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9em;
        }
        .connection-info {
            background: rgba(76, 175, 80, 0.15);
            border: 1px solid rgba(76, 175, 80, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
        .password-box {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            font-family: monospace;
        }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <h1><i class="fab fa-firefox-browser"></i> Real Firefox Browser 24/7</h1>
        
        <div class="hero">
            <h2>Access Your Personal Firefox Browser Anywhere</h2>
            <p>Full graphical browser with VNC remote access. Use it like a regular desktop browser!</p>
            
            {% if service_running %}
            <a href="/vnc.html" class="access-button" target="_blank">
                <i class="fas fa-desktop"></i> Launch Firefox Browser Now
            </a>
            {% else %}
            <button class="access-button" onclick="startService()">
                <i class="fas fa-play-circle"></i> Start Browser Service
            </button>
            {% endif %}
        </div>
        
        <div class="connection-info">
            <h3><i class="fas fa-info-circle"></i> Connection Information</h3>
            <p><strong>VNC Password:</strong> <span class="password-box">firefox123</span></p>
            <p><strong>Direct VNC URL:</strong> <span class="url-box">{{ base_url }}/vnc.html?password=firefox123</span></p>
            <p><em>Bookmark this URL for quick access to your browser!</em></p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <div class="status-icon"><i class="fas fa-satellite-dish"></i></div>
                <div class="status-title">Service Status</div>
                <div class="status-value">{{ 'RUNNING' if service_running else 'STOPPED' }}</div>
            </div>
            <div class="status-card">
                <div class="status-icon"><i class="far fa-clock"></i></div>
                <div class="status-title">Uptime</div>
                <div class="status-value">{{ uptime }}</div>
            </div>
            <div class="status-card">
                <div class="status-icon"><i class="fas fa-users"></i></div>
                <div class="status-title">Active Connections</div>
                <div class="status-value">{{ connections }}</div>
            </div>
            <div class="status-card">
                <div class="status-icon"><i class="fas fa-memory"></i></div>
                <div class="status-title">Memory Usage</div>
                <div class="status-value">{{ memory_usage }}</div>
            </div>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="fetch('/start-service').then(r => location.reload())">
                <i class="fas fa-play"></i> Start Service
            </button>
            <button class="btn" onclick="fetch('/stop-service').then(r => location.reload())">
                <i class="fas fa-stop"></i> Stop Service
            </button>
            <button class="btn" onclick="fetch('/restart-service').then(r => location.reload())">
                <i class="fas fa-redo"></i> Restart Service
            </button>
            <button class="btn" onclick="window.open('/vnc.html', '_blank')">
                <i class="fas fa-external-link-alt"></i> Open VNC
            </button>
            <button class="btn" onclick="fetch('/health').then(r => alert('Health check: ' + r.status))">
                <i class="fas fa-heartbeat"></i> Health Check
            </button>
        </div>
        
        <div class="instructions">
            <h3><i class="fas fa-graduation-cap"></i> How to Use</h3>
            <ol>
                <li><strong>Click "Launch Firefox Browser Now"</strong> to open the VNC interface</li>
                <li><strong>Enter password:</strong> <code>firefox123</code></li>
                <li><strong>Double-click Firefox icon</strong> on the desktop to launch browser</li>
                <li><strong>Bookmark</strong> the VNC URL for future access</li>
                <li><strong>Use Uptime Robot</strong> with URL: <code>{{ base_url }}/health</code> to keep service alive</li>
            </ol>
        </div>
        
        <div class="alert">
            <div class="alert-icon">⚠️</div>
            <div>
                <strong>Important:</strong> Free Render instances sleep after 15 minutes of inactivity. 
                Use <a href="https://uptimerobot.com" target="_blank" style="color: #4CAF50;">Uptime Robot</a> to ping the health endpoint every 5 minutes.
            </div>
        </div>
        
        <div class="instructions">
            <h3><i class="fas fa-cogs"></i> Technical Details</h3>
            <div class="status-grid">
                <div class="status-card">
                    <div class="status-title">VNC Server</div>
                    <div class="status-value">TigerVNC</div>
                </div>
                <div class="status-card">
                    <div class="status-title">Web Interface</div>
                    <div class="status-value">noVNC</div>
                </div>
                <div class="status-card">
                    <div class="status-title">Display</div>
                    <div class="status-value">Xvfb 1024x768</div>
                </div>
                <div class="status-card">
                    <div class="status-title">Desktop</div>
                    <div class="status-value">XFCE</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p><i class="fas fa-code"></i> Real Firefox Browser 24/7 | Powered by Render + VNC</p>
            <p>Auto-refreshes every 30 seconds | Current time: <span id="current-time"></span></p>
        </div>
    </div>
    
    <script>
        function startService() {
            fetch('/start-service')
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    location.reload();
                });
        }
        
        // Update current time
        function updateTime() {
            const now = new Date();
            document.getElementById('current-time').textContent = 
                now.toLocaleTimeString('en-US', { 
                    hour12: false,
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });
        }
        updateTime();
        setInterval(updateTime, 1000);
        
        // Auto-refresh page every 30 seconds
        setTimeout(() => location.reload(), 30000);
        
        // Ping health endpoint every 2 minutes to keep service alive
        setInterval(() => {
            fetch('/ping').catch(() => console.log('Ping failed'));
        }, 120000);
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+Enter to start service
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                startService();
            }
            // Ctrl+V to open VNC
            if (e.ctrlKey && e.key === 'v') {
                e.preventDefault();
                window.open('/vnc.html', '_blank');
            }
        });
        
        console.log('Keyboard shortcuts:');
        console.log('Ctrl+Enter - Start service');
        console.log('Ctrl+V - Open VNC interface');
    </script>
</body>
</html>
'''

def get_memory_usage():
    """Get current memory usage"""
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if hasattr(resource, 'getpagesize'):
            usage = usage * resource.getpagesize() / 1024 / 1024
        return f"{usage:.1f} MB"
    except:
        return "N/A"

def get_uptime():
    """Calculate uptime string"""
    if not start_time:
        return "Not started"
    
    uptime_seconds = int(time.time() - start_time)
    
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m {seconds}s"

def start_vnc_service():
    """Start VNC server with Firefox desktop"""
    global vnc_process, firefox_process, xvfb_process, service_running, start_time
    
    try:
        logging.info("Starting VNC service with Firefox desktop...")
        
        # Create directories for VNC
        os.makedirs("/tmp/.X11-unix", exist_ok=True)
        os.makedirs("/tmp/.ICE-unix", exist_ok=True)
        
        # Install required packages first
        logging.info("Installing required packages...")
        packages = [
            'x11vnc', 'xvfb', 'xfce4', 'xfce4-goodies',
            'firefox-esr', 'novnc', 'websockify'
        ]
        
        # Update and install packages
        subprocess.run(['apt-get', 'update'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
        
        for pkg in packages:
            try:
                subprocess.run(['apt-get', 'install', '-y', pkg],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
                logging.info(f"Installed: {pkg}")
            except:
                logging.warning(f"Failed to install {pkg}")
        
        # Start Xvfb (virtual display)
        logging.info("Starting Xvfb...")
        xvfb_cmd = ['Xvfb', ':99', '-screen', '0', '1024x768x24', '-ac']
        xvfb_process = subprocess.Popen(
            xvfb_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Set DISPLAY environment variable
        os.environ['DISPLAY'] = ':99'
        
        # Start x11vnc server
        logging.info("Starting x11vnc server...")
        vnc_cmd = [
            'x11vnc',
            '-display', ':99',
            '-forever',
            '-shared',
            '-noxdamage',
            '-passwd', 'firefox123',
            '-bg',
            '-nopw',  # Also allow no password for easier access
            '-quiet'
        ]
        
        vnc_process = subprocess.Popen(
            vnc_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Start noVNC websocket proxy
        logging.info("Starting noVNC websocket proxy...")
        novnc_cmd = [
            'websockify',
            '--web', '/usr/share/novnc/',
            '6080',
            'localhost:5900'
        ]
        
        # Start in background
        subprocess.Popen(
            novnc_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Start Firefox after a delay
        def start_firefox_delayed():
            time.sleep(5)
            try:
                # Start Firefox maximized
                firefox_cmd = ['firefox', '--display=:99']
                firefox_process = subprocess.Popen(
                    firefox_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                logging.info("Firefox started on display :99")
            except Exception as e:
                logging.error(f"Failed to start Firefox: {e}")
        
        firefox_thread = threading.Thread(target=start_firefox_delayed, daemon=True)
        firefox_thread.start()
        
        service_running = True
        start_time = time.time()
        logging.info("VNC service started successfully!")
        logging.info(f"VNC Password: firefox123")
        logging.info(f"Access URL: http://localhost:6080/vnc.html")
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to start VNC service: {e}")
        service_running = False
        return False

def stop_vnc_service():
    """Stop VNC service"""
    global vnc_process, firefox_process, xvfb_process, service_running
    
    try:
        # Stop all processes
        processes = [vnc_process, firefox_process, xvfb_process]
        
        for proc in processes:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except:
                    try:
                        proc.kill()
                    except:
                        pass
        
        vnc_process = None
        firefox_process = None
        xvfb_process = None
        service_running = False
        
        logging.info("VNC service stopped")
        return True
        
    except Exception as e:
        logging.error(f"Error stopping VNC service: {e}")
        return False

# Flask Routes
@app.route('/')
def index():
    """Main dashboard"""
    base_url = request.url_root.rstrip('/')
    return render_template_string(
        HTML_TEMPLATE,
        service_running=service_running,
        uptime=get_uptime(),
        connections=connections,
        memory_usage=get_memory_usage(),
        base_url=base_url
    )

@app.route('/health')
def health():
    """Health check endpoint for Uptime Robot"""
    if service_running:
        return jsonify({
            'status': 'healthy',
            'service': 'running',
            'uptime': get_uptime(),
            'vnc': 'available',
            'url': f"{request.url_root.rstrip('/')}/vnc.html",
            'timestamp': time.time()
        }), 200
    else:
        return jsonify({
            'status': 'starting',
            'service': 'starting',
            'timestamp': time.time()
        }), 200

@app.route('/ping')
def ping():
    """Simple ping endpoint"""
    return jsonify({'status': 'pong', 'timestamp': time.time()}), 200

@app.route('/start-service')
def start_service():
    """Start VNC service"""
    if not service_running:
        success = start_vnc_service()
        return jsonify({
            'success': success,
            'message': 'VNC service started' if success else 'Failed to start service'
        })
    return jsonify({'success': True, 'message': 'Service already running'})

@app.route('/stop-service')
def stop_service():
    """Stop VNC service"""
    stop_vnc_service()
    return jsonify({'success': True, 'message': 'Service stopped'})

@app.route('/restart-service')
def restart_service():
    """Restart VNC service"""
    stop_vnc_service()
    time.sleep(2)
    success = start_vnc_service()
    return jsonify({
        'success': success,
        'message': 'Service restarted' if success else 'Failed to restart'
    })

@app.route('/status')
def status():
    """Get service status"""
    return jsonify({
        'service_running': service_running,
        'uptime': get_uptime(),
        'vnc_port': 6080,
        'firefox': 'ready',
        'memory_usage': get_memory_usage(),
        'timestamp': time.time()
    })

@app.route('/vnc.html')
def vnc_page():
    """Serve noVNC interface"""
    try:
        # Return noVNC interface
        novnc_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Firefox Browser VNC</title>
            <meta charset="utf-8">
            <style>
                body { margin: 0; padding: 0; background: #000; }
                #noVNC_container { width: 100vw; height: 100vh; }
            </style>
            <script type="module">
                import { RFB } from 'https://cdn.jsdelivr.net/npm/@novnc/novnc@1.4.0/core/rfb.min.js';
                
                window.addEventListener('load', () => {
                    const host = window.location.hostname;
                    const port = 6080;
                    const password = 'firefox123';
                    const path = 'websockify';
                    
                    const rfb = new RFB(document.getElementById('noVNC_container'), 
                                       `ws://${host}:${port}/${path}`);
                    rfb.credentials = { password: password };
                    rfb.scaleViewport = true;
                    rfb.resizeSession = true;
                    
                    console.log('Connecting to VNC server...');
                });
            </script>
        </head>
        <body>
            <div id="noVNC_container"></div>
        </body>
        </html>
        '''
        return novnc_html
    except Exception as e:
        return f"VNC interface error: {e}", 500

def cleanup(signum, frame):
    """Cleanup on shutdown"""
    logging.info("Shutting down...")
    stop_vnc_service()
    sys.exit(0)

if __name__ == '__main__':
    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Start Flask app
    port = int(os.environ.get('PORT', 5000))
    logging.info(f"Starting Real Firefox Browser service on port {port}")
    
    # Start VNC service in background thread
    def start_vnc_delayed():
        time.sleep(5)
        logging.info("Auto-starting VNC service...")
        start_vnc_service()
    
    vnc_thread = threading.Thread(target=start_vnc_delayed, daemon=True)
    vnc_thread.start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
