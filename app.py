#!/usr/bin/env python3
"""
Firefox 24/7 on Render with Uptime Robot
Complete single file solution - FIXED VERSION
"""

import os
import sys
import subprocess
import threading
import time
import signal
import logging
from flask import Flask, jsonify, render_template_string, url_for
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
browser_running = False
start_time = None
page_views = 0

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Firefox 24/7 on Render</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }
        .status-card {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .online { background-color: #4CAF50; box-shadow: 0 0 10px #4CAF50; }
        .offline { background-color: #f44336; }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .info-box {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .controls {
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        button {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.3s;
        }
        button:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        .uptime {
            font-size: 1.2em;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
        }
        code {
            background: rgba(0, 0, 0, 0.3);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
            display: block;
            margin: 5px 0;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .url-box {
            background: rgba(0, 0, 0, 0.2);
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🦊 Firefox Browser 24/7</h1>
        
        <div class="status-card">
            <h3>
                <span class="status-indicator {{ 'online' if browser_running else 'offline' }}"></span>
                Browser Status: {{ 'RUNNING' if browser_running else 'STOPPED' }}
            </h3>
            {% if browser_running %}
                <p>✅ Firefox is running in headless mode</p>
                <p>PID: {{ pid if pid else 'N/A' }}</p>
            {% else %}
                <p>❌ Firefox is not running</p>
            {% endif %}
        </div>
        
        <div class="info-grid">
            <div class="info-box">
                <h4>Uptime</h4>
                <p>{{ uptime }}</p>
            </div>
            <div class="info-box">
                <h4>Page Views</h4>
                <p>{{ page_views }}</p>
            </div>
            <div class="info-box">
                <h4>Memory Usage</h4>
                <p>{{ memory_usage }}</p>
            </div>
        </div>
        
        <div class="controls">
            <button onclick="fetch('/start-browser').then(r => location.reload())">
                ▶ Start Browser
            </button>
            <button onclick="fetch('/stop-browser').then(r => location.reload())">
                ⏹ Stop Browser
            </button>
            <button onclick="fetch('/restart-browser').then(r => location.reload())">
                🔄 Restart
            </button>
            <button onclick="fetch('/visit-google').then(r => location.reload())">
                🌐 Visit Google
            </button>
        </div>
        
        <div class="status-card">
            <h3>📡 Uptime Robot Configuration</h3>
            <p>Add this URL to Uptime Robot:</p>
            <div class="url-box">
                <code>{{ base_url }}/health</code>
            </div>
            <p>Set monitoring interval to 5 minutes</p>
        </div>
        
        <div class="status-card">
            <h3>🔄 Auto-Restart URLs</h3>
            <p>Use these endpoints for automatic monitoring:</p>
            <div class="url-box">
                <code>{{ base_url }}/health</code> - Health check (returns JSON)
            </div>
            <div class="url-box">
                <code>{{ base_url }}/ping</code> - Simple ping endpoint
            </div>
            <div class="url-box">
                <code>{{ base_url }}</code> - Dashboard (this page)
            </div>
        </div>
        
        <div class="status-card">
            <h3>⚙️ API Endpoints</h3>
            <div class="url-box">
                <code>{{ base_url }}/status</code> - Get browser status (JSON)
            </div>
            <div class="url-box">
                <code>{{ base_url }}/simulate-activity</code> - Simulate browsing activity
            </div>
        </div>
    </div>
    
    <script>
        // Auto-refresh status every 30 seconds
        setTimeout(() => location.reload(), 30000);
        
        // Function to simulate browser activity
        function simulateActivity() {
            fetch('/simulate-activity');
        }
        // Simulate activity every 2 minutes
        setInterval(simulateActivity, 120000);
        
        // Copy URL functionality
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                alert('URL copied to clipboard!');
            });
        }
        
        // Add copy buttons to all code blocks
        document.querySelectorAll('code').forEach(code => {
            const button = document.createElement('button');
            button.textContent = 'Copy';
            button.style.cssText = 'margin-left: 10px; padding: 2px 8px; font-size: 0.8em;';
            button.onclick = () => copyToClipboard(code.textContent);
            code.parentNode.insertBefore(button, code.nextSibling);
        });
    </script>
</body>
</html>
'''

def get_memory_usage():
    """Get current memory usage"""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_mb = round(process.memory_info().rss / 1024 / 1024, 2)
        return f"{mem_mb} MB"
    except ImportError:
        try:
            # Try using psutil if installed
            import psutil
            process = psutil.Process(os.getpid())
            mem_mb = round(process.memory_info().rss / 1024 / 1024, 2)
            return f"{mem_mb} MB"
        except:
            return "N/A"
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
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    else:
        return f"{minutes}m {seconds}s"

def start_firefox():
    """Start Firefox browser in headless mode"""
    global browser_process, browser_running, start_time
    
    try:
        logging.info("Starting Firefox in headless mode...")
        
        # Check if Firefox is installed
        try:
            subprocess.run(['which', 'firefox'], check=True, capture_output=True)
        except:
            logging.warning("Firefox not found, attempting to install...")
            try:
                subprocess.run(['apt-get', 'update'], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
                subprocess.run(['apt-get', 'install', '-y', 'firefox-esr'],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            except:
                logging.error("Failed to install Firefox")
                return False
        
        # Start Firefox with optimized settings
        firefox_cmd = [
            'firefox',
            '--headless',
            '--no-sandbox',
            '--disable-gpu',
            '--disable-dev-shm-usage',
            '--remote-debugging-port=9222',
            'about:blank'
        ]
        
        # Start the browser process
        browser_process = subprocess.Popen(
            firefox_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        browser_running = True
        start_time = time.time()
        logging.info(f"Firefox started successfully. PID: {browser_process.pid}")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_browser, daemon=True)
        monitor_thread.start()
        
        # Start activity simulation thread
        activity_thread = threading.Thread(target=auto_simulate_activity, daemon=True)
        activity_thread.start()
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to start Firefox: {e}")
        browser_running = False
        return False

def monitor_browser():
    """Monitor browser process and restart if needed"""
    global browser_process, browser_running
    
    while browser_running and browser_process:
        try:
            # Check if process is still alive
            if browser_process.poll() is not None:
                logging.warning("Firefox process died. Attempting to restart...")
                stop_firefox()
                time.sleep(5)
                start_firefox()
                break
            
            # Read output
            try:
                for line in iter(browser_process.stdout.readline, ''):
                    if line:
                        logging.debug(f"Firefox: {line.strip()}")
            except:
                pass
            
            time.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            logging.error(f"Monitor error: {e}")
            time.sleep(30)

def auto_simulate_activity():
    """Automatically simulate browser activity"""
    while browser_running:
        try:
            time.sleep(300)  # Every 5 minutes
            if browser_running:
                simulate_browser_activity()
        except:
            pass

def stop_firefox():
    """Stop Firefox browser"""
    global browser_process, browser_running
    
    if browser_process:
        try:
            browser_process.terminate()
            try:
                browser_process.wait(timeout=5)
                logging.info("Firefox stopped gracefully")
            except subprocess.TimeoutExpired:
                browser_process.kill()
                browser_process.wait()
                logging.warning("Firefox killed forcibly")
        except Exception as e:
            logging.error(f"Error stopping Firefox: {e}")
        
        browser_process = None
    
    browser_running = False

def simulate_browser_activity():
    """Simulate browser activity"""
    global page_views
    
    try:
        # Just increment page views for simulation
        page_views += 1
        logging.info(f"Simulated browser activity. Total views: {page_views}")
        return True
        
    except Exception as e:
        logging.error(f"Activity simulation failed: {e}")
    
    return False

# Flask Routes
@app.route('/')
def index():
    """Main dashboard"""
    base_url = request.url_root.rstrip('/')
    return render_template_string(
        HTML_TEMPLATE,
        browser_running=browser_running,
        uptime=get_uptime(),
        page_views=page_views,
        memory_usage=get_memory_usage(),
        base_url=base_url,
        pid=browser_process.pid if browser_process else None
    )

@app.route('/health')
def health():
    """Health check endpoint for Uptime Robot"""
    if browser_running:
        return jsonify({
            'status': 'healthy',
            'browser': 'running',
            'uptime': get_uptime(),
            'page_views': page_views,
            'timestamp': datetime.now().isoformat()
        }), 200
    else:
        return jsonify({
            'status': 'degraded',
            'browser': 'stopped',
            'timestamp': datetime.now().isoformat()
        }), 200

@app.route('/ping')
def ping():
    """Simple ping endpoint"""
    return jsonify({'status': 'pong', 'timestamp': datetime.now().isoformat()}), 200

@app.route('/start-browser')
def start_browser_route():
    """Start the browser"""
    if not browser_running:
        success = start_firefox()
        return jsonify({
            'success': success,
            'message': 'Browser started' if success else 'Failed to start browser'
        })
    return jsonify({'success': True, 'message': 'Browser already running'})

@app.route('/stop-browser')
def stop_browser_route():
    """Stop the browser"""
    stop_firefox()
    return jsonify({'success': True, 'message': 'Browser stopped'})

@app.route('/restart-browser')
def restart_browser_route():
    """Restart the browser"""
    stop_firefox()
    time.sleep(2)
    success = start_firefox()
    return jsonify({
        'success': success,
        'message': 'Browser restarted' if success else 'Failed to restart'
    })

@app.route('/visit-google')
def visit_google():
    """Simulate visiting Google"""
    success = simulate_browser_activity()
    return jsonify({
        'success': success,
        'message': 'Simulated browser activity' if success else 'Failed to simulate activity',
        'page_views': page_views
    })

@app.route('/simulate-activity')
def simulate_activity():
    """Simulate browser activity"""
    success = simulate_browser_activity()
    return jsonify({'success': success, 'page_views': page_views})

@app.route('/status')
def status():
    """Get current status"""
    return jsonify({
        'browser_running': browser_running,
        'uptime': get_uptime(),
        'page_views': page_views,
        'memory_usage': get_memory_usage(),
        'pid': browser_process.pid if browser_process else None,
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
    logging.info(f"Starting Firefox 24/7 service on port {port}")
    
    # Start Firefox in background thread
    def start_firefox_delayed():
        time.sleep(3)  # Wait for Flask to start
        start_firefox()
    
    firefox_thread = threading.Thread(target=start_firefox_delayed, daemon=True)
    firefox_thread.start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
