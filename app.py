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
from flask import Flask, jsonify, render_template_string, request
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 1000px;
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
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        .status-card {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .status-indicator {
            display: inline-block;
            width: 15px;
            height: 15px;
            border-radius: 50%;
            margin-right: 12px;
            vertical-align: middle;
        }
        .online { 
            background-color: #4CAF50; 
            box-shadow: 0 0 15px #4CAF50;
            animation: pulse 2s infinite;
        }
        .offline { 
            background-color: #f44336;
            box-shadow: 0 0 10px #f44336;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin: 25px 0;
        }
        .info-box {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            transition: transform 0.3s;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .info-box:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.15);
        }
        .info-box h4 {
            margin-top: 0;
            color: #ddd;
            font-size: 1em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .info-box p {
            font-size: 1.8em;
            font-weight: bold;
            margin: 10px 0 0 0;
        }
        .controls {
            display: flex;
            gap: 12px;
            justify-content: center;
            margin: 30px 0;
            flex-wrap: wrap;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            color: white;
            padding: 14px 28px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 1em;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        button:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }
        button:active {
            transform: translateY(-1px);
        }
        .url-box {
            background: rgba(0, 0, 0, 0.25);
            padding: 15px;
            border-radius: 10px;
            margin: 12px 0;
            border-left: 4px solid #667eea;
        }
        code {
            background: rgba(0, 0, 0, 0.3);
            padding: 10px 15px;
            border-radius: 8px;
            font-family: 'Consolas', 'Monaco', monospace;
            display: block;
            margin: 8px 0;
            overflow-x: auto;
            white-space: nowrap;
            font-size: 0.9em;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .copy-btn {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.8em;
            margin-left: 10px;
            transition: background 0.3s;
        }
        .copy-btn:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        .section-title {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        .emoji {
            font-size: 1.5em;
        }
        .instructions {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            font-size: 0.95em;
            line-height: 1.6;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9em;
        }
        .alert {
            background: rgba(255, 193, 7, 0.15);
            border: 1px solid rgba(255, 193, 7, 0.3);
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .alert::before {
            content: "⚠️";
            font-size: 1.2em;
        }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <h1><i class="fas fa-firefox-browser"></i> Firefox Browser 24/7</h1>
        
        <div class="status-card">
            <h3>
                <span class="status-indicator {{ 'online' if browser_running else 'offline' }}"></span>
                Browser Status: <strong>{{ 'RUNNING' if browser_running else 'STOPPED' }}</strong>
            </h3>
            {% if browser_running %}
                <p><i class="fas fa-check-circle"></i> Firefox is running in headless mode</p>
                <p><i class="fas fa-microchip"></i> Process ID: {{ pid if pid else 'N/A' }}</p>
            {% else %}
                <p><i class="fas fa-times-circle"></i> Firefox is not running. Click "Start Browser" to begin.</p>
            {% endif %}
        </div>
        
        <div class="info-grid">
            <div class="info-box">
                <h4><i class="far fa-clock"></i> Uptime</h4>
                <p>{{ uptime }}</p>
            </div>
            <div class="info-box">
                <h4><i class="far fa-eye"></i> Page Views</h4>
                <p>{{ page_views }}</p>
            </div>
            <div class="info-box">
                <h4><i class="fas fa-memory"></i> Memory Usage</h4>
                <p>{{ memory_usage }}</p>
            </div>
            <div class="info-box">
                <h4><i class="fas fa-heartbeat"></i> Health</h4>
                <p>{{ 'Healthy' if browser_running else 'Stopped' }}</p>
            </div>
        </div>
        
        <div class="controls">
            <button onclick="fetch('/start-browser').then(r => location.reload())">
                <i class="fas fa-play"></i> Start Browser
            </button>
            <button onclick="fetch('/stop-browser').then(r => location.reload())">
                <i class="fas fa-stop"></i> Stop Browser
            </button>
            <button onclick="fetch('/restart-browser').then(r => location.reload())">
                <i class="fas fa-redo"></i> Restart
            </button>
            <button onclick="fetch('/visit-google').then(r => location.reload())">
                <i class="fas fa-globe"></i> Visit Site
            </button>
            <button onclick="fetch('/simulate-activity').then(r => location.reload())">
                <i class="fas fa-sync"></i> Simulate Activity
            </button>
        </div>
        
        <div class="alert">
            <strong>Note:</strong> Free Render instances sleep after 15 minutes of inactivity. 
            Use Uptime Robot to ping the health endpoint regularly.
        </div>
        
        <div class="section-title">
            <span class="emoji">📡</span>
            <h3>Uptime Robot Configuration</h3>
        </div>
        <div class="instructions">
            <p>To keep your Firefox instance running 24/7, configure Uptime Robot with these settings:</p>
            <div class="url-box">
                <strong>Monitoring URL:</strong>
                <code id="health-url">{{ base_url }}/health</code>
                <button class="copy-btn" onclick="copyToClipboard('{{ base_url }}/health')">
                    <i class="far fa-copy"></i> Copy
                </button>
            </div>
            <p><strong>Recommended settings:</strong></p>
            <ul>
                <li>Monitor Type: HTTP(s)</li>
                <li>Check Interval: 5 minutes</li>
                <li>Alert Contacts: Add your email</li>
            </ul>
        </div>
        
        <div class="section-title">
            <span class="emoji">🔧</span>
            <h3>API Endpoints</h3>
        </div>
        <div class="info-grid">
            <div class="url-box">
                <strong>Health Check</strong>
                <code>{{ base_url }}/health</code>
                <button class="copy-btn" onclick="copyToClipboard('{{ base_url }}/health')">
                    <i class="far fa-copy"></i> Copy
                </button>
            </div>
            <div class="url-box">
                <strong>Simple Ping</strong>
                <code>{{ base_url }}/ping</code>
                <button class="copy-btn" onclick="copyToClipboard('{{ base_url }}/ping')">
                    <i class="far fa-copy"></i> Copy
                </button>
            </div>
            <div class="url-box">
                <strong>Status Info</strong>
                <code>{{ base_url }}/status</code>
                <button class="copy-btn" onclick="copyToClipboard('{{ base_url }}/status')">
                    <i class="far fa-copy"></i> Copy
                </button>
            </div>
        </div>
        
        <div class="section-title">
            <span class="emoji">🚀</span>
            <h3>Quick Actions</h3>
        </div>
        <div class="instructions">
            <p>Use these direct links for quick actions:</p>
            <div class="controls">
                <a href="/start-browser" style="text-decoration: none;">
                    <button><i class="fas fa-rocket"></i> Quick Start</button>
                </a>
                <a href="/status" style="text-decoration: none;" target="_blank">
                    <button><i class="fas fa-info-circle"></i> JSON Status</button>
                </a>
                <a href="https://uptimerobot.com" style="text-decoration: none;" target="_blank">
                    <button><i class="fas fa-external-link-alt"></i> Uptime Robot</button>
                </a>
            </div>
        </div>
        
        <div class="footer">
            <p><i class="fas fa-code"></i> Firefox 24/7 Service | Running on Render</p>
            <p>Auto-refreshes every 30 seconds | Last refresh: <span id="current-time">{{ current_time }}</span></p>
        </div>
    </div>
    
    <script>
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
        
        // Copy to clipboard function
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                // Show temporary feedback
                const originalText = event.target.innerHTML;
                event.target.innerHTML = '<i class="fas fa-check"></i> Copied!';
                event.target.style.background = '#4CAF50';
                setTimeout(() => {
                    event.target.innerHTML = originalText;
                    event.target.style.background = '';
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy: ', err);
                alert('Failed to copy to clipboard. Please copy manually.');
            });
        }
        
        // Simulate activity every 2 minutes
        function simulateActivity() {
            fetch('/simulate-activity')
                .then(response => response.json())
                .then(data => {
                    console.log('Activity simulated:', data);
                })
                .catch(error => console.error('Error simulating activity:', error));
        }
        
        // Start periodic activity simulation (every 2 minutes)
        setInterval(simulateActivity, 120000);
        
        // Initial activity simulation
        setTimeout(simulateActivity, 10000);
        
        // Add keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+S to start browser
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                fetch('/start-browser').then(r => location.reload());
            }
            // Ctrl+R to restart browser
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                fetch('/restart-browser').then(r => location.reload());
            }
            // Ctrl+D to simulate activity
            if (e.ctrlKey && e.key === 'd') {
                e.preventDefault();
                fetch('/simulate-activity').then(r => location.reload());
            }
        });
        
        // Show keyboard shortcuts help
        console.log('Keyboard shortcuts:');
        console.log('Ctrl+S - Start browser');
        console.log('Ctrl+R - Restart browser');
        console.log('Ctrl+D - Simulate activity');
    </script>
</body>
</html>
'''

def get_memory_usage():
    """Get current memory usage"""
    try:
        # Simple memory usage calculation without psutil
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
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m {seconds}s"

def start_firefox():
    """Start Firefox browser in headless mode"""
    global browser_process, browser_running, start_time
    
    try:
        logging.info("Starting Firefox in headless mode...")
        
        # Command to start Firefox
        firefox_cmd = [
            'firefox',
            '--headless',
            '--no-sandbox',
            '--disable-gpu',
            '--disable-dev-shm-usage',
            '--width=1920',
            '--height=1080',
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
            
            time.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            logging.error(f"Monitor error: {e}")
            time.sleep(30)

def auto_simulate_activity():
    """Automatically simulate browser activity"""
    while browser_running:
        try:
            time.sleep(120)  # Every 2 minutes
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
        pid=browser_process.pid if browser_process else None,
        current_time=datetime.now().strftime('%H:%M:%S')
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
            'timestamp': datetime.now().isoformat(),
            'service': 'Firefox 24/7'
        }), 200
    else:
        return jsonify({
            'status': 'degraded',
            'browser': 'stopped',
            'timestamp': datetime.now().isoformat(),
            'service': 'Firefox 24/7'
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
        'timestamp': datetime.now().isoformat(),
        'service': 'Firefox 24/7 on Render'
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
    
    # Start Firefox in background thread after a delay
    def start_firefox_delayed():
        time.sleep(5)  # Wait for Flask to start
        logging.info("Attempting to start Firefox...")
        start_firefox()
    
    firefox_thread = threading.Thread(target=start_firefox_delayed, daemon=True)
    firefox_thread.start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
