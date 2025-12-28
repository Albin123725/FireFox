#!/usr/bin/env python3
"""
Firefox Browser 24/7 - Simple Web Interface
Real Firefox browser running 24/7
"""

import os
import sys
import subprocess
import threading
import time
import signal
import logging
import json
from flask import Flask, jsonify, render_template_string, request
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

app = Flask(__name__)

# Global variables
browser_process = None
service_running = False
start_time = None
current_url = "about:blank"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>🔥 Firefox Browser 24/7</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a2980, #26d0ce);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            padding: 40px 20px;
        }
        h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .tagline {
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 30px;
        }
        .status-box {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            margin: 30px 0;
            border: 1px solid rgba(255,255,255,0.2);
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-item {
            background: rgba(0,0,0,0.2);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            transition: transform 0.3s;
        }
        .status-item:hover {
            transform: translateY(-5px);
            background: rgba(0,0,0,0.3);
        }
        .status-label {
            font-size: 0.9em;
            opacity: 0.8;
            margin-bottom: 8px;
        }
        .status-value {
            font-size: 1.8em;
            font-weight: bold;
        }
        .online { color: #00ff88; }
        .offline { color: #ff4444; }
        
        .control-panel {
            background: rgba(255,255,255,0.08);
            border-radius: 15px;
            padding: 30px;
            margin: 20px 0;
        }
        .url-input-container {
            margin-bottom: 25px;
        }
        .url-input {
            width: 100%;
            padding: 18px 20px;
            border-radius: 12px;
            border: 2px solid rgba(255,255,255,0.2);
            background: rgba(0,0,0,0.3);
            color: white;
            font-size: 1.1em;
            transition: all 0.3s;
        }
        .url-input:focus {
            outline: none;
            border-color: #00ff88;
            box-shadow: 0 0 0 3px rgba(0,255,136,0.1);
        }
        .btn-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .btn {
            padding: 18px 24px;
            border-radius: 12px;
            border: none;
            color: white;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }
        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        .btn-start { background: linear-gradient(135deg, #00b09b, #96c93d); }
        .btn-stop { background: linear-gradient(135deg, #ff416c, #ff4b2b); }
        .btn-restart { background: linear-gradient(135deg, #ff8008, #ffc837); }
        .btn-go { background: linear-gradient(135deg, #4776E6, #8E54E9); }
        
        .quick-links {
            margin: 30px 0;
        }
        .link-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 12px;
            margin-top: 15px;
        }
        .link-btn {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 10px;
            padding: 15px;
            color: white;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }
        .link-btn:hover {
            background: rgba(255,255,255,0.2);
            transform: translateY(-2px);
        }
        .link-icon {
            font-size: 1.5em;
        }
        
        .info-box {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            margin: 30px 0;
            border-left: 5px solid #00ff88;
        }
        .info-box h3 {
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .monitor-url {
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
            word-break: break-all;
        }
        
        footer {
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
            color: rgba(255,255,255,0.7);
            font-size: 0.9em;
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #00ff88;
            color: #000;
            padding: 15px 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            display: none;
            z-index: 1000;
            font-weight: bold;
        }
        
        .error { background: #ff4444 !important; color: white !important; }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link rel="icon" href="https://img.icons8.com/color/96/000000/firefox.png">
</head>
<body>
    <div class="notification" id="notification"></div>
    
    <div class="container">
        <header>
            <h1><i class="fab fa-firefox-browser"></i> Firefox 24/7</h1>
            <div class="tagline">Run Firefox browser continuously with remote control</div>
        </header>
        
        <div class="status-box">
            <div class="status-grid">
                <div class="status-item">
                    <div class="status-label">Browser Status</div>
                    <div class="status-value {{ 'online' if service_running else 'offline' }}">
                        {{ '🟢 ONLINE' if service_running else '🔴 OFFLINE' }}
                    </div>
                </div>
                <div class="status-item">
                    <div class="status-label">Current Page</div>
                    <div class="status-value">{{ current_url[:30] + '...' if current_url|length > 30 else current_url }}</div>
                </div>
                <div class="status-item">
                    <div class="status-label">Uptime</div>
                    <div class="status-value">{{ uptime }}</div>
                </div>
                <div class="status-item">
                    <div class="status-label">PID</div>
                    <div class="status-value">{{ pid if pid else 'N/A' }}</div>
                </div>
            </div>
            
            <div class="control-panel">
                <h2><i class="fas fa-gamepad"></i> Control Panel</h2>
                
                <div class="btn-grid">
                    <button class="btn btn-start" onclick="controlAction('start')" id="startBtn">
                        <i class="fas fa-play"></i> Start Browser
                    </button>
                    <button class="btn btn-stop" onclick="controlAction('stop')">
                        <i class="fas fa-stop"></i> Stop Browser
                    </button>
                    <button class="btn btn-restart" onclick="controlAction('restart')">
                        <i class="fas fa-redo"></i> Restart
                    </button>
                    <button class="btn" onclick="location.reload()">
                        <i class="fas fa-sync"></i> Refresh
                    </button>
                </div>
                
                <div class="url-input-container">
                    <h3><i class="fas fa-globe"></i> Visit Website</h3>
                    <input type="text" class="url-input" id="urlInput" 
                           placeholder="https://example.com" 
                           value="{{ current_url }}">
                    <div class="btn-grid">
                        <button class="btn btn-go" onclick="visitURL()">
                            <i class="fas fa-external-link-alt"></i> Go to URL
                        </button>
                    </div>
                </div>
                
                <div class="quick-links">
                    <h3><i class="fas fa-bolt"></i> Quick Links</h3>
                    <div class="link-grid">
                        <div class="link-btn" onclick="quickVisit('https://www.google.com')">
                            <i class="fab fa-google link-icon"></i>
                            <span>Google</span>
                        </div>
                        <div class="link-btn" onclick="quickVisit('https://www.youtube.com')">
                            <i class="fab fa-youtube link-icon"></i>
                            <span>YouTube</span>
                        </div>
                        <div class="link-btn" onclick="quickVisit('https://www.github.com')">
                            <i class="fab fa-github link-icon"></i>
                            <span>GitHub</span>
                        </div>
                        <div class="link-btn" onclick="quickVisit('https://www.reddit.com')">
                            <i class="fab fa-reddit link-icon"></i>
                            <span>Reddit</span>
                        </div>
                        <div class="link-btn" onclick="quickVisit('https://chat.openai.com')">
                            <i class="fas fa-robot link-icon"></i>
                            <span>ChatGPT</span>
                        </div>
                        <div class="link-btn" onclick="quickVisit('https://twitter.com')">
                            <i class="fab fa-twitter link-icon"></i>
                            <span>Twitter</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="info-box">
            <h3><i class="fas fa-info-circle"></i> Setup Instructions</h3>
            <p>To keep your Firefox browser running 24/7:</p>
            <ol style="margin-left: 20px; margin-top: 10px; line-height: 1.6;">
                <li><strong>Click "Start Browser"</strong> to launch Firefox</li>
                <li><strong>Enter any URL</strong> or use quick links to visit websites</li>
                <li><strong>Setup Uptime Robot</strong> with this URL:</li>
            </ol>
            <div class="monitor-url">
                {{ base_url }}/health
                <button onclick="copyToClipboard('{{ base_url }}/health')" 
                        style="background: rgba(255,255,255,0.2); border: none; color: white; padding: 5px 10px; border-radius: 5px; margin-left: 10px; cursor: pointer;">
                    <i class="far fa-copy"></i> Copy
                </button>
            </div>
            <p><strong>Uptime Robot Settings:</strong> HTTP monitor, 5-minute interval</p>
        </div>
        
        <footer>
            <p><i class="fas fa-code"></i> Firefox 24/7 | Powered by Flask & Docker</p>
            <p>Auto-refreshes every 30 seconds | Current time: <span id="current-time">{{ current_time }}</span></p>
        </footer>
    </div>
    
    <script>
        function showNotification(message, isError = false) {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.className = 'notification' + (isError ? ' error' : '');
            notification.style.display = 'block';
            setTimeout(() => {
                notification.style.display = 'none';
            }, 3000);
        }
        
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                showNotification('URL copied to clipboard!');
            });
        }
        
        async function controlAction(action) {
            const btn = document.getElementById('startBtn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span class="loading"></span> Please wait...';
            btn.disabled = true;
            
            try {
                const response = await fetch(`/${action}`);
                const data = await response.json();
                showNotification(data.message, !data.success);
                
                if (data.success) {
                    setTimeout(() => location.reload(), 1000);
                }
            } catch (error) {
                showNotification('Error: ' + error.message, true);
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }
        
        async function visitURL() {
            const url = document.getElementById('urlInput').value.trim();
            if (!url) {
                showNotification('Please enter a URL', true);
                return;
            }
            
            try {
                const response = await fetch('/visit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });
                const data = await response.json();
                showNotification(data.message, !data.success);
                
                if (data.success) {
                    setTimeout(() => location.reload(), 1000);
                }
            } catch (error) {
                showNotification('Error: ' + error.message, true);
            }
        }
        
        function quickVisit(url) {
            document.getElementById('urlInput').value = url;
            visitURL();
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
        
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
        
        // Auto-start browser after page load (if not running)
        window.addEventListener('load', () => {
            setTimeout(() => {
                if (!{{ 'true' if service_running else 'false' }}) {
                    // Auto-start after 3 seconds
                    setTimeout(() => controlAction('start'), 3000);
                }
            }, 1000);
        });
        
        // Ping health endpoint every 2 minutes
        setInterval(() => {
            fetch('/ping').catch(() => console.log('Health ping'));
        }, 120000);
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                visitURL();
            }
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                controlAction('start');
            }
            if (e.key === 'F5') {
                e.preventDefault();
                location.reload();
            }
        });
    </script>
</body>
</html>
'''

def get_uptime():
    """Calculate uptime string"""
    if not start_time:
        return "0s"
    
    uptime_seconds = int(time.time() - start_time)
    
    if uptime_seconds < 60:
        return f"{uptime_seconds}s"
    elif uptime_seconds < 3600:
        minutes = uptime_seconds // 60
        seconds = uptime_seconds % 60
        return f"{minutes}m {seconds}s"
    elif uptime_seconds < 86400:
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        return f"{days}d {hours}h"

def check_firefox_installed():
    """Check if Firefox is installed"""
    try:
        result = subprocess.run(['which', 'firefox'], 
                               capture_output=True, 
                               text=True)
        return result.returncode == 0
    except:
        return False

def install_firefox():
    """Install Firefox"""
    try:
        logging.info("Checking Firefox installation...")
        
        if check_firefox_installed():
            logging.info("Firefox is already installed")
            return True
            
        logging.info("Installing Firefox...")
        
        # Update package list
        subprocess.run(['apt-get', 'update'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
        
        # Install Firefox
        result = subprocess.run(['apt-get', 'install', '-y', 'firefox'],
                              capture_output=True,
                              text=True)
        
        if result.returncode == 0:
            logging.info("Firefox installed successfully")
            return True
        else:
            logging.error(f"Failed to install Firefox: {result.stderr}")
            return False
            
    except Exception as e:
        logging.error(f"Installation error: {e}")
        return False

def start_firefox_browser(url="about:blank"):
    """Start Firefox browser"""
    global browser_process, service_running, start_time, current_url
    
    try:
        # Ensure Firefox is installed
        if not check_firefox_installed():
            logging.info("Firefox not found, attempting to install...")
            if not install_firefox():
                return False
        
        # Set display environment
        os.environ['DISPLAY'] = ':99'
        
        # Start Firefox with the URL
        logging.info(f"Starting Firefox with URL: {url}")
        
        firefox_cmd = ['firefox', '--display=:99', url]
        
        browser_process = subprocess.Popen(
            firefox_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment to ensure Firefox starts
        time.sleep(3)
        
        # Check if process is running
        if browser_process.poll() is None:
            service_running = True
            start_time = time.time()
            current_url = url
            logging.info(f"Firefox started successfully! PID: {browser_process.pid}")
            return True
        else:
            stdout, stderr = browser_process.communicate()
            logging.error(f"Firefox failed to start. Stdout: {stdout}, Stderr: {stderr}")
            return False
            
    except Exception as e:
        logging.error(f"Error starting Firefox: {e}")
        return False

def stop_firefox_browser():
    """Stop Firefox browser"""
    global browser_process, service_running
    
    if browser_process:
        try:
            browser_process.terminate()
            browser_process.wait(timeout=5)
            logging.info("Firefox stopped gracefully")
        except:
            try:
                browser_process.kill()
                browser_process.wait()
                logging.warning("Firefox killed forcibly")
            except:
                pass
        finally:
            browser_process = None
    
    service_running = False
    return True

# Flask Routes
@app.route('/')
def index():
    """Main dashboard"""
    base_url = request.url_root.rstrip('/')
    return render_template_string(
        HTML_TEMPLATE,
        service_running=service_running,
        uptime=get_uptime(),
        current_url=current_url,
        base_url=base_url,
        pid=browser_process.pid if browser_process else None,
        current_time=datetime.now().strftime('%H:%M:%S')
    )

@app.route('/health')
def health():
    """Health check endpoint for Uptime Robot"""
    if service_running:
        return jsonify({
            'status': 'healthy',
            'browser': 'running',
            'uptime': get_uptime(),
            'current_url': current_url,
            'timestamp': datetime.now().isoformat(),
            'service': 'Firefox 24/7'
        }), 200
    else:
        return jsonify({
            'status': 'starting',
            'browser': 'stopped',
            'timestamp': datetime.now().isoformat(),
            'service': 'Firefox 24/7'
        }), 200

@app.route('/ping')
def ping():
    """Simple ping endpoint"""
    return jsonify({'status': 'pong', 'timestamp': datetime.now().isoformat()}), 200

@app.route('/start')
def start_browser():
    """Start Firefox browser"""
    if not service_running:
        success = start_firefox_browser()
        return jsonify({
            'success': success,
            'message': 'Firefox started successfully!' if success else 'Failed to start Firefox'
        })
    return jsonify({'success': True, 'message': 'Firefox is already running'})

@app.route('/stop')
def stop_browser():
    """Stop Firefox browser"""
    success = stop_firefox_browser()
    return jsonify({
        'success': success,
        'message': 'Firefox stopped successfully' if success else 'Failed to stop Firefox'
    })

@app.route('/restart')
def restart_browser():
    """Restart Firefox browser"""
    stop_firefox_browser()
    time.sleep(2)
    success = start_firefox_browser()
    return jsonify({
        'success': success,
        'message': 'Firefox restarted successfully!' if success else 'Failed to restart Firefox'
    })

@app.route('/visit', methods=['POST'])
def visit_url():
    """Visit a URL in Firefox"""
    data = request.get_json()
    url = data.get('url', 'about:blank')
    
    if not service_running:
        success = start_firefox_browser(url)
    else:
        # Restart Firefox with new URL
        stop_firefox_browser()
        time.sleep(2)
        success = start_firefox_browser(url)
    
    return jsonify({
        'success': success,
        'message': f'Navigated to: {url}' if success else f'Failed to navigate to: {url}'
    })

@app.route('/status')
def status():
    """Get current status"""
    return jsonify({
        'service_running': service_running,
        'uptime': get_uptime(),
        'current_url': current_url,
        'pid': browser_process.pid if browser_process else None,
        'firefox_installed': check_firefox_installed(),
        'timestamp': datetime.now().isoformat()
    })

def cleanup(signum, frame):
    """Cleanup on shutdown"""
    logging.info("Shutting down...")
    stop_firefox_browser()
    sys.exit(0)

if __name__ == '__main__':
    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Start Flask app
    port = int(os.environ.get('PORT', 5000))
    logging.info(f"🚀 Starting Firefox 24/7 Service on port {port}")
    
    # Check and install Firefox on startup
    logging.info("🔍 Checking Firefox installation...")
    if check_firefox_installed():
        logging.info("✅ Firefox is installed")
    else:
        logging.info("📦 Installing Firefox...")
        install_firefox()
    
    # Start Firefox automatically
    def auto_start():
        time.sleep(5)
        if not service_running:
            logging.info("⚡ Auto-starting Firefox...")
            start_firefox_browser()
    
    threading.Thread(target=auto_start, daemon=True).start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
