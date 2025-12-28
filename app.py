#!/usr/bin/env python3
"""
Real Visible Firefox Browser 24/7
Simple web interface to control Firefox
"""

import os
import sys
import subprocess
import threading
import time
import signal
import logging
import json
from flask import Flask, jsonify, render_template_string, request, Response
from datetime import datetime

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
browser_process = None
service_running = False
start_time = None
browser_url = "about:blank"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>🦊 Real Firefox Browser 24/7</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            padding: 30px 0;
        }
        h1 {
            font-size: 2.8em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 30px;
        }
        .status-bar {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            display: flex;
            justify-content: space-around;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }
        .status-item {
            text-align: center;
            min-width: 150px;
        }
        .status-label {
            font-size: 0.9em;
            opacity: 0.8;
            margin-bottom: 5px;
        }
        .status-value {
            font-size: 1.4em;
            font-weight: bold;
        }
        .status-online {
            color: #4CAF50;
        }
        .status-offline {
            color: #f44336;
        }
        .control-panel {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 30px;
            margin: 20px 0;
        }
        .url-input {
            width: 100%;
            padding: 15px;
            border-radius: 10px;
            border: 2px solid rgba(255,255,255,0.2);
            background: rgba(0,0,0,0.3);
            color: white;
            font-size: 1.1em;
            margin-bottom: 20px;
            box-sizing: border-box;
        }
        .url-input:focus {
            outline: none;
            border-color: #667eea;
        }
        .button-group {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }
        .btn {
            padding: 15px 30px;
            border-radius: 10px;
            border: none;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            flex: 1;
            min-width: 150px;
        }
        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        .btn-start { background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); }
        .btn-stop { background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%); }
        .btn-restart { background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%); }
        .btn-visit { background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%); }
        
        .screenshots {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .screenshot {
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            overflow: hidden;
            text-align: center;
            padding: 20px;
        }
        .screenshot img {
            max-width: 100%;
            border-radius: 5px;
            border: 2px solid rgba(255,255,255,0.1);
        }
        .screenshot-title {
            margin: 15px 0 5px 0;
            font-weight: bold;
        }
        .instructions {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            border-left: 5px solid #4CAF50;
        }
        .instructions h3 {
            margin-top: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .instructions ol {
            padding-left: 20px;
        }
        .instructions li {
            margin: 10px 0;
            line-height: 1.6;
        }
        .url-display {
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
            word-break: break-all;
            font-family: monospace;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4CAF50;
            color: white;
            padding: 15px 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            display: none;
            z-index: 1000;
        }
        footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
            color: rgba(255,255,255,0.7);
            font-size: 0.9em;
        }
        .websites-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .website-btn {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 10px;
            padding: 15px;
            color: white;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .website-btn:hover {
            background: rgba(255,255,255,0.2);
            transform: translateY(-2px);
        }
        .refresh-btn {
            background: rgba(255,255,255,0.1);
            border: none;
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            cursor: pointer;
            margin-left: 10px;
        }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <header>
            <h1><i class="fab fa-firefox-browser"></i> Real Firefox Browser 24/7</h1>
            <div class="subtitle">Control Firefox remotely with this web interface</div>
        </header>
        
        <div class="status-bar">
            <div class="status-item">
                <div class="status-label">Browser Status</div>
                <div class="status-value {{ 'status-online' if service_running else 'status-offline' }}">
                    {{ 'RUNNING' if service_running else 'STOPPED' }}
                </div>
            </div>
            <div class="status-item">
                <div class="status-label">Current URL</div>
                <div class="status-value">{{ browser_url[:50] + '...' if browser_url|length > 50 else browser_url }}</div>
            </div>
            <div class="status-item">
                <div class="status-label">Uptime</div>
                <div class="status-value">{{ uptime }}</div>
            </div>
            <div class="status-item">
                <div class="status-label">Process ID</div>
                <div class="status-value">{{ pid if pid else 'N/A' }}</div>
            </div>
        </div>
        
        <div class="control-panel">
            <h2><i class="fas fa-gamepad"></i> Browser Control</h2>
            
            <div class="button-group">
                <button class="btn btn-start" onclick="controlBrowser('start')">
                    <i class="fas fa-play"></i> Start Firefox
                </button>
                <button class="btn btn-stop" onclick="controlBrowser('stop')">
                    <i class="fas fa-stop"></i> Stop Firefox
                </button>
                <button class="btn btn-restart" onclick="controlBrowser('restart')">
                    <i class="fas fa-redo"></i> Restart Firefox
                </button>
                <button class="btn" onclick="refreshStatus()">
                    <i class="fas fa-sync"></i> Refresh Status
                </button>
            </div>
            
            <h3><i class="fas fa-globe"></i> Visit Website</h3>
            <input type="text" class="url-input" id="urlInput" 
                   placeholder="https://example.com" 
                   value="{{ browser_url }}">
            <div class="button-group">
                <button class="btn btn-visit" onclick="visitURL()">
                    <i class="fas fa-external-link-alt"></i> Go to URL
                </button>
                <button class="btn" onclick="takeScreenshot()">
                    <i class="fas fa-camera"></i> Take Screenshot
                </button>
            </div>
            
            <div class="websites-grid">
                <div class="website-btn" onclick="quickVisit('https://www.google.com')">
                    <i class="fab fa-google"></i> Google
                </div>
                <div class="website-btn" onclick="quickVisit('https://www.youtube.com')">
                    <i class="fab fa-youtube"></i> YouTube
                </div>
                <div class="website-btn" onclick="quickVisit('https://www.github.com')">
                    <i class="fab fa-github"></i> GitHub
                </div>
                <div class="website-btn" onclick="quickVisit('https://www.reddit.com')">
                    <i class="fab fa-reddit"></i> Reddit
                </div>
                <div class="website-btn" onclick="quickVisit('https://www.twitter.com')">
                    <i class="fab fa-twitter"></i> Twitter
                </div>
                <div class="website-btn" onclick="quickVisit('https://chat.openai.com')">
                    <i class="fas fa-robot"></i> ChatGPT
                </div>
            </div>
        </div>
        
        <div class="instructions">
            <h3><i class="fas fa-graduation-cap"></i> How to Use This Service</h3>
            <ol>
                <li><strong>Click "Start Firefox"</strong> to launch the browser</li>
                <li><strong>Enter any URL</strong> in the input field and click "Go to URL"</li>
                <li><strong>Use quick links</strong> to visit popular websites instantly</li>
                <li><strong>Click "Take Screenshot"</strong> to capture the current page</li>
                <li><strong>Bookmark this page</strong> for easy access to your remote browser</li>
                <li><strong>Set up Uptime Robot</strong> with URL: <code>{{ base_url }}/health</code> to keep service alive 24/7</li>
            </ol>
            
            <div class="url-display">
                <strong>Health Check URL for Uptime Robot:</strong><br>
                {{ base_url }}/health
                <button class="refresh-btn" onclick="copyToClipboard('{{ base_url }}/health')">
                    <i class="far fa-copy"></i> Copy
                </button>
            </div>
        </div>
        
        <div class="screenshots">
            <div class="screenshot">
                <div class="screenshot-title">Browser Preview</div>
                <div id="screenshot-container" style="min-height: 200px; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.2); border-radius: 5px;">
                    <div style="text-align: center;">
                        <i class="fas fa-camera" style="font-size: 3em; opacity: 0.5;"></i>
                        <div style="margin-top: 10px;">Click "Take Screenshot" to capture</div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer>
            <p><i class="fas fa-code"></i> Real Firefox Browser 24/7 | Powered by Flask & Render</p>
            <p>Auto-refreshes every 30 seconds | Last updated: <span id="current-time">{{ current_time }}</span></p>
        </footer>
    </div>
    
    <div class="notification" id="notification"></div>
    
    <script>
        function showNotification(message, type = 'success') {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.style.background = type === 'success' ? '#4CAF50' : '#f44336';
            notification.style.display = 'block';
            setTimeout(() => {
                notification.style.display = 'none';
            }, 3000);
        }
        
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                showNotification('Copied to clipboard!');
            });
        }
        
        async function controlBrowser(action) {
            const endpoint = action === 'start' ? '/start' : 
                            action === 'stop' ? '/stop' : '/restart';
            
            try {
                const response = await fetch(endpoint);
                const data = await response.json();
                showNotification(data.message, data.success ? 'success' : 'error');
                setTimeout(() => location.reload(), 1000);
            } catch (error) {
                showNotification('Error: ' + error.message, 'error');
            }
        }
        
        async function visitURL() {
            const url = document.getElementById('urlInput').value;
            if (!url) {
                showNotification('Please enter a URL', 'error');
                return;
            }
            
            try {
                const response = await fetch('/visit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });
                const data = await response.json();
                showNotification(data.message, data.success ? 'success' : 'error');
                setTimeout(() => location.reload(), 1000);
            } catch (error) {
                showNotification('Error: ' + error.message, 'error');
            }
        }
        
        function quickVisit(url) {
            document.getElementById('urlInput').value = url;
            visitURL();
        }
        
        async function takeScreenshot() {
            try {
                const response = await fetch('/screenshot');
                const data = await response.json();
                
                if (data.success && data.screenshot) {
                    const container = document.getElementById('screenshot-container');
                    container.innerHTML = `<img src="data:image/png;base64,${data.screenshot}" style="max-width: 100%;">`;
                    showNotification('Screenshot captured!', 'success');
                } else {
                    showNotification('Screenshot failed: ' + data.message, 'error');
                }
            } catch (error) {
                showNotification('Error: ' + error.message, 'error');
            }
        }
        
        function refreshStatus() {
            location.reload();
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
        
        // Auto-ping health endpoint every 2 minutes
        setInterval(() => {
            fetch('/ping').catch(() => console.log('Ping failed'));
        }, 120000);
        
        // Auto-start browser on page load (if not running)
        window.addEventListener('load', () => {
            setTimeout(() => {
                if (!{{ 'true' if service_running else 'false' }}) {
                    fetch('/ping').catch(() => console.log('Initial ping'));
                }
            }, 3000);
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+Enter to visit URL
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                visitURL();
            }
            // Ctrl+S to start browser
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                controlBrowser('start');
            }
            // Ctrl+P to take screenshot
            if (e.ctrlKey && e.key === 'p') {
                e.preventDefault();
                takeScreenshot();
            }
        });
        
        console.log('Keyboard shortcuts:');
        console.log('Ctrl+Enter - Visit current URL');
        console.log('Ctrl+S - Start browser');
        console.log('Ctrl+P - Take screenshot');
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

def start_firefox(url="about:blank"):
    """Start Firefox browser with visible display"""
    global browser_process, service_running, start_time, browser_url
    
    try:
        logging.info(f"Starting Firefox with URL: {url}")
        
        # Set up display environment
        os.environ['DISPLAY'] = ':99'
        
        # Start Xvfb if not running
        xvfb_check = subprocess.run(['pgrep', '-f', 'Xvfb'], capture_output=True)
        if xvfb_check.returncode != 0:
            logging.info("Starting Xvfb virtual display...")
            xvfb_cmd = ['Xvfb', ':99', '-screen', '0', '1024x768x24', '-ac']
            subprocess.Popen(xvfb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)
        
        # Install Firefox if not present
        try:
            subprocess.run(['which', 'firefox'], check=True, capture_output=True)
        except:
            logging.info("Installing Firefox...")
            subprocess.run(['apt-get', 'update'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['apt-get', 'install', '-y', 'firefox-esr', 'xvfb', 'x11-apps'],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Start Firefox with the specified URL
        firefox_cmd = ['firefox', '--display=:99', url]
        
        browser_process = subprocess.Popen(
            firefox_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        service_running = True
        start_time = time.time()
        browser_url = url
        logging.info(f"Firefox started successfully. PID: {browser_process.pid}")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_browser, daemon=True)
        monitor_thread.start()
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to start Firefox: {e}")
        service_running = False
        return False

def monitor_browser():
    """Monitor browser process"""
    global browser_process, service_running
    
    while service_running and browser_process:
        try:
            if browser_process.poll() is not None:
                logging.warning("Firefox process stopped")
                service_running = False
                break
            time.sleep(10)
        except:
            time.sleep(10)

def stop_firefox():
    """Stop Firefox browser"""
    global browser_process, service_running
    
    if browser_process:
        try:
            browser_process.terminate()
            try:
                browser_process.wait(timeout=5)
                logging.info("Firefox stopped gracefully")
            except:
                browser_process.kill()
                browser_process.wait()
                logging.warning("Firefox killed forcibly")
        except Exception as e:
            logging.error(f"Error stopping Firefox: {e}")
        
        browser_process = None
    
    service_running = False
    return True

def take_screenshot():
    """Take a screenshot of the current display"""
    try:
        # Install xwd and convert if needed
        try:
            subprocess.run(['which', 'xwd'], check=True, capture_output=True)
        except:
            subprocess.run(['apt-get', 'install', '-y', 'x11-apps', 'imagemagick'],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Take screenshot
        timestamp = int(time.time())
        xwd_file = f"/tmp/screenshot_{timestamp}.xwd"
        png_file = f"/tmp/screenshot_{timestamp}.png"
        
        # Capture screen
        subprocess.run(['xwd', '-root', '-display', ':99', '-out', xwd_file],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Convert to PNG
        subprocess.run(['convert', xwd_file, png_file],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Read and encode as base64
        with open(png_file, 'rb') as f:
            import base64
            screenshot_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Clean up
        os.remove(xwd_file)
        os.remove(png_file)
        
        return True, screenshot_data
        
    except Exception as e:
        logging.error(f"Screenshot failed: {e}")
        return False, str(e)

# Flask Routes
@app.route('/')
def index():
    """Main dashboard"""
    base_url = request.url_root.rstrip('/')
    return render_template_string(
        HTML_TEMPLATE,
        service_running=service_running,
        uptime=get_uptime(),
        browser_url=browser_url,
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
            'current_url': browser_url,
            'timestamp': datetime.now().isoformat()
        }), 200
    else:
        return jsonify({
            'status': 'starting',
            'browser': 'stopped',
            'timestamp': datetime.now().isoformat()
        }), 200

@app.route('/ping')
def ping():
    """Simple ping endpoint"""
    return jsonify({'status': 'pong', 'timestamp': datetime.now().isoformat()}), 200

@app.route('/start')
def start_browser():
    """Start Firefox browser"""
    if not service_running:
        success = start_firefox()
        return jsonify({
            'success': success,
            'message': 'Firefox started successfully' if success else 'Failed to start Firefox'
        })
    return jsonify({'success': True, 'message': 'Firefox already running'})

@app.route('/stop')
def stop_browser():
    """Stop Firefox browser"""
    success = stop_firefox()
    return jsonify({'success': success, 'message': 'Firefox stopped'})

@app.route('/restart')
def restart_browser():
    """Restart Firefox browser"""
    stop_firefox()
    time.sleep(2)
    success = start_firefox()
    return jsonify({
        'success': success,
        'message': 'Firefox restarted' if success else 'Failed to restart Firefox'
    })

@app.route('/visit', methods=['POST'])
def visit_url():
    """Visit a URL in Firefox"""
    data = request.get_json()
    url = data.get('url', 'about:blank')
    
    if not service_running:
        success = start_firefox(url)
        return jsonify({
            'success': success,
            'message': f'Started Firefox with URL: {url}' if success else 'Failed to start Firefox'
        })
    else:
        # We need to restart Firefox with new URL
        stop_firefox()
        time.sleep(2)
        success = start_firefox(url)
        return jsonify({
            'success': success,
            'message': f'Navigated to: {url}' if success else 'Failed to navigate'
        })

@app.route('/screenshot')
def get_screenshot():
    """Take a screenshot"""
    if not service_running:
        return jsonify({'success': False, 'message': 'Firefox is not running'})
    
    success, data = take_screenshot()
    if success:
        return jsonify({'success': True, 'screenshot': data})
    else:
        return jsonify({'success': False, 'message': data})

@app.route('/status')
def status():
    """Get current status"""
    return jsonify({
        'service_running': service_running,
        'uptime': get_uptime(),
        'current_url': browser_url,
        'pid': browser_process.pid if browser_process else None,
        'memory_usage': get_memory_usage(),
        'timestamp': datetime.now().isoformat()
    })

def cleanup(signum, frame):
    """Cleanup on shutdown"""
    logging.info("Shutting down...")
    stop_firefox()
    sys.exit(0)

if __name__ == '__main__':
    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Start Flask app
    port = int(os.environ.get('PORT', 5000))
    logging.info(f"Starting Real Firefox Browser service on port {port}")
    
    # Auto-start Firefox after delay
    def auto_start_firefox():
        time.sleep(5)
        if not service_running:
            logging.info("Auto-starting Firefox...")
            start_firefox()
    
    auto_start_thread = threading.Thread(target=auto_start_firefox, daemon=True)
    auto_start_thread.start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
