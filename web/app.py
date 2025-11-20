#!/usr/bin/env python3
"""
SafeBox CPU Monitor - Web Server with API
Serves HTML dashboard and provides process monitoring API
"""

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import psutil
import os
import sys
import json

# Set working directory to script location
script_dir = os.path.dirname(os.path.abspath(__file__)) or '/home/ubuntu/SafeBox/web'
os.chdir(script_dir)

# Add parent directory to path for sandbox imports
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

# Import sandbox module
try:
    from sandbox import SandboxManager
    from sandbox.test_samples import TestSampleManager
    from sandbox.kvm_manager import get_kvm_manager, VMConfig
    SANDBOX_AVAILABLE = True
    KVM_AVAILABLE = True
except ImportError as e:
    SANDBOX_AVAILABLE = False
    KVM_AVAILABLE = False
    print(f"⚠️  Sandbox module not available: {e}")
    TestSampleManager = None

app = Flask(__name__, static_folder=script_dir)
CORS(app)

# Serve static files
@app.route('/')
def index():
    return send_from_directory(script_dir, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(script_dir, path)

# API Endpoints
@app.route('/api/processes', methods=['GET'])
def get_processes():
    """Get all running processes with CPU and memory info"""
    try:
        processes = []
        # Get all processes with basic info
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                # Get memory info
                mem_info = proc.memory_info()
                memory_mb = mem_info.rss / (1024 * 1024)
                
                # Get CPU with non-blocking call
                cpu_percent = proc.cpu_percent(interval=None) or 0
                
                processes.append({
                    'pid': proc.pid,
                    'name': proc.name(),
                    'cpu_percent': float(cpu_percent),
                    'memory_mb': float(memory_mb)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Sort by CPU usage
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
        
        # Try graceful termination
        proc.terminate()
        try:
            proc.wait(timeout=2)
            return jsonify({
                'success': True,
                'message': f'Process {pid} terminated',
                'name': proc_name
            })
        except psutil.TimeoutExpired:
            # Force kill
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

# Sandbox API Endpoints
@app.route('/api/sandbox/status', methods=['GET'])
def sandbox_status():
    """Get sandbox status"""
    if not SANDBOX_AVAILABLE:
        return jsonify({'success': False, 'error': 'Sandbox not available'}), 503
    
    try:
        manager = SandboxManager()
        return jsonify({
            'success': True,
            'status': 'running',
            'total_sandboxes': len(manager.get_all_sandboxes()) if hasattr(manager, 'get_all_sandboxes') else 0,
            'features': ['malware_detection', 'behavior_monitoring', 'resource_limits']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sandbox/create', methods=['POST'])
def create_sandbox():
    """Create a new sandbox instance"""
    if not SANDBOX_AVAILABLE:
        return jsonify({'success': False, 'error': 'Sandbox not available'}), 503
    
    try:
        data = request.get_json()
        manager = SandboxManager()
        
        sandbox_config = {
            'name': data.get('name', 'malware-analysis'),
            'max_cpu': data.get('max_cpu', 50),
            'max_memory_mb': data.get('max_memory_mb', 512),
            'timeout': data.get('timeout', 300)
        }
        
        sandbox_id = manager.create_sandbox(
            name=sandbox_config['name'],
            config=sandbox_config
        )
        
        return jsonify({
            'success': True,
            'sandbox_id': sandbox_id,
            'config': sandbox_config
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sandbox/<sandbox_id>/execute', methods=['POST'])
def execute_in_sandbox(sandbox_id):
    """Execute a command in a sandbox"""
    if not SANDBOX_AVAILABLE:
        return jsonify({'success': False, 'error': 'Sandbox not available'}), 503
    
    try:
        data = request.get_json()
        manager = SandboxManager()
        
        result = manager.execute_in_sandbox(
            sandbox_id=sandbox_id,
            command=data.get('command'),
            timeout=data.get('timeout', 60)
        )
        
        return jsonify({
            'success': True,
            'sandbox_id': sandbox_id,
            'result': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sandbox/<sandbox_id>/report', methods=['GET'])
def get_sandbox_report(sandbox_id):
    """Get analysis report from sandbox"""
    if not SANDBOX_AVAILABLE:
        return jsonify({'success': False, 'error': 'Sandbox not available'}), 503
    
    try:
        manager = SandboxManager()
        report = manager.get_analysis_report(sandbox_id)
        
        return jsonify({
            'success': True,
            'sandbox_id': sandbox_id,
            'report': report
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Test Malware API Endpoints
@app.route('/api/test-malware/samples', methods=['GET'])
def get_test_samples():
    """Get list of test malware samples"""
    if not TestSampleManager:
        return jsonify({'success': False, 'error': 'Test samples not available'}), 503
    
    try:
        manager = TestSampleManager()
        samples = manager.get_all_samples()
        
        return jsonify({
            'success': True,
            'total': len(samples),
            'samples': samples
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test-malware/samples/<sample_id>', methods=['GET'])
def get_test_sample(sample_id):
    """Get specific test sample details"""
    if not TestSampleManager:
        return jsonify({'success': False, 'error': 'Test samples not available'}), 503
    
    try:
        manager = TestSampleManager()
        sample = manager.get_sample(sample_id)
        
        if not sample:
            return jsonify({'success': False, 'error': 'Sample not found'}), 404
        
        return jsonify({
            'success': True,
            'sample': sample
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test-malware/run', methods=['POST'])
def run_test_malware():
    """Run test malware sample in sandbox"""
    if not SANDBOX_AVAILABLE or not TestSampleManager:
        return jsonify({'success': False, 'error': 'Sandbox or test samples not available'}), 503
    
    try:
        data = request.get_json()
        sample_id = data.get('sample_id')
        
        if not sample_id:
            return jsonify({'success': False, 'error': 'sample_id required'}), 400
        
        # Get test sample
        test_manager = TestSampleManager()
        sample = test_manager.get_sample(sample_id)
        if not sample:
            return jsonify({'success': False, 'error': 'Test sample not found'}), 404
        
        script_path = test_manager.get_sample_script(sample_id)
        if not script_path:
            return jsonify({'success': False, 'error': 'Sample script not found'}), 404
        
        # Create sandbox and execute
        try:
            sandbox_manager = SandboxManager()
            sandbox_id = sandbox_manager.create_sandbox(
                max_cpu=data.get('max_cpu', 50),
                max_memory_mb=data.get('max_memory_mb', 512),
                max_duration=data.get('timeout', 30)
            )
            
            # Execute the test script
            result = sandbox_manager.execute_in_sandbox(
                sandbox_id=sandbox_id,
                program_path=script_path,
                args=[]
            )
            
            # Get analysis report
            report = sandbox_manager.get_analysis_report(sandbox_id)
            
            return jsonify({
                'success': True,
                'sandbox_id': sandbox_id,
                'sample': sample,
                'result': result,
                'report': report
            })
        except Exception as exec_error:
            return jsonify({
                'success': False,
                'error': f'Execution error: {str(exec_error)}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Request error: {str(e)}'
        }), 500

@app.route('/api/test-malware/severity/<severity>', methods=['GET'])
def get_samples_by_severity(severity):
    """Get test samples by severity level"""
    if not TestSampleManager:
        return jsonify({'success': False, 'error': 'Test samples not available'}), 503
    
    try:
        manager = TestSampleManager()
        samples = manager.get_sample_by_severity(severity.upper())
        
        return jsonify({
            'success': True,
            'severity': severity,
            'total': len(samples),
            'samples': samples
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test-malware/behaviors', methods=['GET'])
def get_behaviors():
    """Get samples grouped by behavior"""
    if not TestSampleManager:
        return jsonify({'success': False, 'error': 'Test samples not available'}), 503
    
    try:
        manager = TestSampleManager()
        behaviors = manager.list_samples_by_behavior()
        
        return jsonify({
            'success': True,
            'behaviors': behaviors
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# KVM Hypervisor Sandbox Endpoints
@app.route('/api/kvm/status', methods=['GET'])
def kvm_status():
    """Get KVM system status and availability"""
    if not KVM_AVAILABLE:
        return jsonify({
            'available': False,
            'error': 'KVM module not available'
        }), 503
    
    try:
        kvm = get_kvm_manager()
        return jsonify({
            'available': kvm.is_available(),
            'system_info': kvm.get_system_info()
        })
    except Exception as e:
        return jsonify({'available': False, 'error': str(e)}), 500

@app.route('/api/kvm/vms', methods=['GET'])
def list_kvm_vms():
    """List all virtual machines"""
    if not KVM_AVAILABLE:
        return jsonify({'success': False, 'error': 'KVM not available'}), 503
    
    try:
        kvm = get_kvm_manager()
        vms = kvm.list_vms()
        vm_statuses = []
        
        for vm_name in vms:
            status = kvm.get_vm_status(vm_name)
            if status:
                vm_statuses.append({
                    'name': status.name,
                    'state': status.state,
                    'uptime': status.uptime,
                    'memory_mb': status.memory_mb,
                    'vcpus': status.vcpus,
                    'disk_usage_gb': status.disk_usage_gb
                })
        
        return jsonify({
            'success': True,
            'total_vms': len(vms),
            'vms': vm_statuses
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/kvm/create', methods=['POST'])
def create_kvm_vm():
    """Create a new virtual machine"""
    if not KVM_AVAILABLE:
        return jsonify({'success': False, 'error': 'KVM not available'}), 503
    
    try:
        data = request.json
        config = VMConfig(
            name=data.get('name', 'SafeBox-VM'),
            vcpus=data.get('vcpus', 2),
            memory_mb=data.get('memory_mb', 512),
            disk_size_gb=data.get('disk_size_gb', 10),
            os_type=data.get('os_type', 'linux')
        )
        
        kvm = get_kvm_manager()
        success = kvm.create_vm(config)
        
        return jsonify({
            'success': success,
            'vm_name': config.name,
            'message': f"VM {config.name} created successfully" if success else "Failed to create VM"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/kvm/start/<vm_name>', methods=['POST'])
def start_kvm_vm(vm_name):
    """Start a virtual machine"""
    if not KVM_AVAILABLE:
        return jsonify({'success': False, 'error': 'KVM not available'}), 503
    
    try:
        kvm = get_kvm_manager()
        success = kvm.start_vm(vm_name)
        
        return jsonify({
            'success': success,
            'vm_name': vm_name,
            'message': f"VM {vm_name} started" if success else f"Failed to start {vm_name}"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/kvm/stop/<vm_name>', methods=['POST'])
def stop_kvm_vm(vm_name):
    """Stop a virtual machine"""
    if not KVM_AVAILABLE:
        return jsonify({'success': False, 'error': 'KVM not available'}), 503
    
    try:
        kvm = get_kvm_manager()
        success = kvm.stop_vm(vm_name)
        
        return jsonify({
            'success': success,
            'vm_name': vm_name,
            'message': f"VM {vm_name} stopped" if success else f"Failed to stop {vm_name}"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/kvm/delete/<vm_name>', methods=['POST'])
def delete_kvm_vm(vm_name):
    """Delete a virtual machine"""
    if not KVM_AVAILABLE:
        return jsonify({'success': False, 'error': 'KVM not available'}), 503
    
    try:
        kvm = get_kvm_manager()
        success = kvm.delete_vm(vm_name)
        
        return jsonify({
            'success': success,
            'vm_name': vm_name,
            'message': f"VM {vm_name} deleted" if success else f"Failed to delete {vm_name}"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/kvm/execute', methods=['POST'])
def execute_in_kvm():
    """Execute malware in VM"""
    if not KVM_AVAILABLE:
        return jsonify({'success': False, 'error': 'KVM not available'}), 503
    
    try:
        data = request.json
        vm_name = data.get('vm_name')
        malware_name = data.get('malware_name')
        
        if not vm_name or not malware_name:
            return jsonify({'success': False, 'error': 'Missing vm_name or malware_name'}), 400
        
        kvm = get_kvm_manager()
        result = kvm.execute_in_vm(vm_name, f"/tmp/{malware_name}")
        
        return jsonify({
            'success': result.success,
            'vm_name': result.vm_name,
            'malware_name': result.malware_name,
            'duration_seconds': result.duration_seconds,
            'exit_code': result.exit_code,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'start_time': result.start_time,
            'end_time': result.end_time
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/kvm/snapshot', methods=['POST'])
def create_kvm_snapshot():
    """Create VM snapshot"""
    if not KVM_AVAILABLE:
        return jsonify({'success': False, 'error': 'KVM not available'}), 503
    
    try:
        data = request.json
        vm_name = data.get('vm_name')
        snapshot_name = data.get('snapshot_name', f'snapshot-{int(__import__("time").time())}')
        
        kvm = get_kvm_manager()
        success = kvm.create_snapshot(vm_name, snapshot_name)
        
        return jsonify({
            'success': success,
            'vm_name': vm_name,
            'snapshot_name': snapshot_name
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/kvm/restore', methods=['POST'])
def restore_kvm_snapshot():
    """Restore VM from snapshot"""
    if not KVM_AVAILABLE:
        return jsonify({'success': False, 'error': 'KVM not available'}), 503
    
    try:
        data = request.json
        vm_name = data.get('vm_name')
        snapshot_name = data.get('snapshot_name')
        
        if not snapshot_name:
            return jsonify({'success': False, 'error': 'Missing snapshot_name'}), 400
        
        kvm = get_kvm_manager()
        success = kvm.restore_snapshot(vm_name, snapshot_name)
        
        return jsonify({
            'success': success,
            'vm_name': vm_name,
            'snapshot_name': snapshot_name
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/kvm/images', methods=['GET'])
def list_kvm_images():
    """List available VM images"""
    if not KVM_AVAILABLE:
        return jsonify({'success': False, 'error': 'KVM not available'}), 503
    
    try:
        kvm = get_kvm_manager()
        images = kvm.list_available_images()
        image_info = []
        for img in images:
            info = kvm.get_image_info(img.replace('.qcow2', ''))
            image_info.append(info)
        
        return jsonify({
            'success': True,
            'images': image_info,
            'total': len(image_info)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/kvm/execute', methods=['POST'])
def execute_in_kvm():
    """Execute malware sample in KVM VM"""
    if not KVM_AVAILABLE:
        return jsonify({'success': False, 'error': 'KVM not available'}), 503
    
    try:
        data = request.json
        vm_name = data.get('vm_name')
        command = data.get('command')
        malware_name = data.get('malware_name', 'unknown')
        
        if not vm_name or not command:
            return jsonify({'success': False, 'error': 'Missing vm_name or command'}), 400
        
        kvm = get_kvm_manager()
        result = kvm.execute_in_vm(vm_name, command)
        
        return jsonify({
            'success': result.success,
            'vm_name': result.vm_name,
            'malware_name': result.malware_name,
            'start_time': result.start_time,
            'end_time': result.end_time,
            'duration_seconds': result.duration_seconds,
            'exit_code': result.exit_code,
            'stdout': result.stdout,
            'stderr': result.stderr
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/kvm/from-image', methods=['POST'])
def create_vm_from_image():
    """Create VM from existing image"""
    if not KVM_AVAILABLE:
        return jsonify({'success': False, 'error': 'KVM not available'}), 503
    
    try:
        data = request.json
        vm_name = data.get('vm_name')
        image_name = data.get('image_name')
        vcpus = data.get('vcpus', 2)
        memory_mb = data.get('memory_mb', 512)
        
        if not vm_name or not image_name:
            return jsonify({'success': False, 'error': 'Missing vm_name or image_name'}), 400
        
        kvm = get_kvm_manager()
        success = kvm.create_vm_from_image(vm_name, image_name, vcpus, memory_mb)
        
        return jsonify({
            'success': success,
            'vm_name': vm_name,
            'image_name': image_name
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/kvm/cleanup/<vm_name>', methods=['POST'])
def cleanup_kvm_vm(vm_name):
    """Delete VM and cleanup resources"""
    if not KVM_AVAILABLE:
        return jsonify({'success': False, 'error': 'KVM not available'}), 503
    
    try:
        kvm = get_kvm_manager()
        success = kvm.delete_vm(vm_name)
        
        return jsonify({
            'success': success,
            'vm_name': vm_name,
            'message': 'VM deleted successfully' if success else 'Failed to delete VM'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🔒 SafeBox CPU Monitor - Web Server")
    print("📊 Dashboard: http://localhost:5000")
    print("⏹️  Press Ctrl+C to stop")
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
