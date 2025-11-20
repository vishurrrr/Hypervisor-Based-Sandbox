#!/usr/bin/env python3
"""
SafeBox Hypervisor - Complete Integration
Main application combining CPU monitoring, process management, and sandbox analysis
"""

from flask import Flask, jsonify, send_from_directory, request, render_template_string
from flask_cors import CORS
import psutil
import os
import sys

# Add sandbox module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sandbox'))

from sandbox.sandbox_api import sandbox_bp

# Set working directory
script_dir = os.path.dirname(os.path.abspath(__file__)) or '/home/ubuntu/SafeBox/web'
os.chdir(script_dir)

app = Flask(__name__, static_folder=script_dir)
CORS(app)

# Register sandbox blueprint
app.register_blueprint(sandbox_bp)

# HTML Dashboard Template
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SafeBox Hypervisor - CPU Monitor & Sandbox</title>
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <div class="header-content">
                <h1>🔒 SafeBox Hypervisor Sandbox</h1>
                <p>Advanced CPU Monitoring & Malware Sandbox Analysis</p>
            </div>
        </header>

        <!-- Navigation Tabs -->
        <div class="tabs">
            <button class="tab-button active" onclick="switchTab('monitor')">📊 Monitor</button>
            <button class="tab-button" onclick="switchTab('sandbox')">🔬 Sandbox</button>
            <button class="tab-button" onclick="switchTab('analysis')">🔍 Analysis</button>
        </div>

        <!-- Monitor Tab -->
        <div id="monitor-tab" class="tab-content active">
            <div class="control-panel">
                <div class="control-group">
                    <label>CPU Threshold (%):</label>
                    <input type="range" id="cpuThreshold" min="1" max="100" value="30">
                    <span id="cpuValue">30%</span>
                </div>
                <div class="control-group">
                    <label>Check Interval (s):</label>
                    <input type="range" id="checkInterval" min="0.5" max="60" step="0.5" value="2">
                    <span id="intervalValue">2s</span>
                </div>
                <button onclick="startMonitoring()" class="btn btn-primary">▶ Start Monitor</button>
                <button onclick="stopMonitoring()" class="btn btn-secondary">⏹ Stop</button>
                <button onclick="clearLogs()" class="btn btn-secondary">🗑 Clear Logs</button>
            </div>

            <div class="stats">
                <div class="stat-card">
                    <div class="stat-label">Total Processes</div>
                    <div class="stat-value" id="totalProcesses">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">High CPU Count</div>
                    <div class="stat-value" id="highCpuCount">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Killed Processes</div>
                    <div class="stat-value" id="killedCount">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Active Sandboxes</div>
                    <div class="stat-value" id="activeSandboxes">0</div>
                </div>
            </div>

            <div class="process-list">
                <h3>High CPU Processes</h3>
                <table id="processList">
                    <thead>
                        <tr>
                            <th>PID</th>
                            <th>Process Name</th>
                            <th>CPU %</th>
                            <th>Memory</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody id="processTableBody">
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Sandbox Tab -->
        <div id="sandbox-tab" class="tab-content">
            <div class="sandbox-panel">
                <h3>Create Sandbox</h3>
                <div class="control-group">
                    <label>Program Path:</label>
                    <input type="text" id="programPath" placeholder="/path/to/program">
                </div>
                <div class="control-group">
                    <label>Max CPU (%):</label>
                    <input type="number" id="sandboxMaxCpu" min="1" max="100" value="20">
                </div>
                <div class="control-group">
                    <label>Max Memory (MB):</label>
                    <input type="number" id="sandboxMaxMemory" min="64" max="2048" value="256">
                </div>
                <div class="control-group">
                    <label>Max Duration (s):</label>
                    <input type="number" id="sandboxMaxDuration" min="10" max="3600" value="300">
                </div>
                <button onclick="createAndExecuteSandbox()" class="btn btn-primary">🚀 Execute in Sandbox</button>
            </div>

            <div class="sandbox-list">
                <h3>Active Sandboxes</h3>
                <div id="sandboxList"></div>
            </div>
        </div>

        <!-- Analysis Tab -->
        <div id="analysis-tab" class="tab-content">
            <div class="analysis-panel">
                <h3>Pre-Scan File</h3>
                <div class="control-group">
                    <label>File Path:</label>
                    <input type="text" id="filePath" placeholder="/path/to/file">
                </div>
                <button onclick="preScanFile()" class="btn btn-primary">🔍 Scan File</button>
                <div id="scanResult"></div>
            </div>

            <div class="activity-log">
                <h3>Activity Log</h3>
                <div id="logContainer" class="log-container"></div>
            </div>
        </div>
    </div>

    <script src="/monitor.js"></script>
</body>
</html>
'''

# Serve static files
@app.route('/')
def index():
    return DASHBOARD_HTML

@app.route('/<path:path>')
def static_files(path):
    if path.endswith('.css') or path.endswith('.js'):
        return send_from_directory(script_dir, path)
    return send_from_directory(script_dir, 'index.html')

# API Endpoints
@app.route('/api/processes', methods=['GET'])
def get_processes():
    """Get all running processes"""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                mem_info = proc.memory_info()
                memory_mb = mem_info.rss / (1024 * 1024)
                cpu_percent = proc.cpu_percent(interval=None) or 0
                
                processes.append({
                    'pid': proc.pid,
                    'name': proc.name(),
                    'cpu_percent': float(cpu_percent),
                    'memory_mb': float(memory_mb)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        return jsonify({
            'success': True,
            'processes': processes,
            'total': len(processes)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/kill-process/<int:pid>', methods=['POST'])
def kill_process(pid):
    """Kill a process"""
    try:
        proc = psutil.Process(pid)
        proc_name = proc.name()
        
        proc.terminate()
        try:
            proc.wait(timeout=2)
            return jsonify({
                'success': True,
                'message': f'Process {pid} terminated',
                'name': proc_name
            })
        except psutil.TimeoutExpired:
            proc.kill()
            proc.wait()
            return jsonify({
                'success': True,
                'message': f'Process {pid} force killed',
                'name': proc_name
            })
    
    except psutil.NoSuchProcess:
        return jsonify({'success': False, 'error': 'Process not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🔒 SafeBox Hypervisor - Complete System")
    print("📊 Dashboard: http://localhost:5000")
    print("🔬 Sandbox: http://localhost:5000#sandbox")
    print("🔍 Analysis: http://localhost:5000#analysis")
    print("⏹️  Press Ctrl+C to stop")
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
