#!/usr/bin/env python3
"""
SafeBox Sandbox API Endpoints
Integrates sandbox management with Flask web interface
"""

from flask import Blueprint, request, jsonify
from sandbox_manager import SandboxManager
import os
from pathlib import Path

# Create blueprint for sandbox routes
sandbox_bp = Blueprint('sandbox', __name__, url_prefix='/api/sandbox')

# Initialize manager
manager = SandboxManager()

@sandbox_bp.route('/pre-scan', methods=['POST'])
def pre_scan_file():
    """Pre-analyze file before sandboxing"""
    try:
        data = request.json or {}
        file_path = data.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 400
        
        result = manager.pre_analyze_file(file_path)
        return jsonify({
            'success': True,
            'analysis': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sandbox_bp.route('/create', methods=['POST'])
def create_sandbox():
    """Create new sandbox instance"""
    try:
        data = request.json or {}
        
        sandbox_id = manager.create_sandbox(
            max_cpu=data.get('max_cpu', 20.0),
            max_memory_mb=data.get('max_memory_mb', 256),
            max_duration=data.get('max_duration', 300)
        )
        
        return jsonify({
            'success': True,
            'sandbox_id': sandbox_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sandbox_bp.route('/execute', methods=['POST'])
def execute_in_sandbox():
    """Execute program in sandbox"""
    try:
        data = request.json or {}
        sandbox_id = data.get('sandbox_id')
        program_path = data.get('program_path')
        args = data.get('args', [])
        
        if not sandbox_id or not program_path:
            return jsonify({
                'success': False,
                'error': 'Missing sandbox_id or program_path'
            }), 400
        
        result = manager.execute_in_sandbox(sandbox_id, program_path, args)
        
        return jsonify({
            'success': 'error' not in result,
            'result': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sandbox_bp.route('/list', methods=['GET'])
def list_sandboxes():
    """List active sandboxes"""
    try:
        sandboxes = manager.list_sandboxes()
        return jsonify({
            'success': True,
            'sandboxes': sandboxes,
            'count': len(sandboxes)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sandbox_bp.route('/status/<sandbox_id>', methods=['GET'])
def sandbox_status(sandbox_id):
    """Get sandbox status"""
    try:
        report = manager.get_report(sandbox_id)
        if not report:
            return jsonify({
                'success': False,
                'error': 'Sandbox not found'
            }), 404
        
        return jsonify({
            'success': True,
            'report': report
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sandbox_bp.route('/stop/<sandbox_id>', methods=['POST'])
def stop_sandbox(sandbox_id):
    """Stop sandbox"""
    try:
        success = manager.stop_sandbox(sandbox_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Sandbox not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': f'Sandbox {sandbox_id} stopped'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sandbox_bp.route('/quarantine', methods=['POST'])
def quarantine_file():
    """Quarantine suspicious file"""
    try:
        data = request.json or {}
        file_path = data.get('file_path')
        reason = data.get('reason', 'User requested')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 400
        
        quarantine_path = manager.quarantine_file(file_path, reason)
        
        return jsonify({
            'success': True,
            'quarantine_path': quarantine_path,
            'message': f'File quarantined'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("SafeBox Sandbox API Endpoints")
