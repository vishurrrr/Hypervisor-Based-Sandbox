#!/usr/bin/env python3
"""
SafeBox Sandbox Manager - High-level orchestration
Manages multiple sandboxes and coordinates analysis
"""

import os
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from .sandbox_core import SandboxEnvironment, SandboxConfig, create_sandbox
from .malware_detector import MalwareDetector

class SandboxManager:
    """Manages sandbox instances and analysis"""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path or './sandbox-reports')
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.active_sandboxes: Dict[str, SandboxEnvironment] = {}
        self.detector = MalwareDetector()
        self.analysis_history = []
        
    def pre_analyze_file(self, file_path: str) -> Dict:
        """Pre-analysis scan before running in sandbox"""
        if not os.path.exists(file_path):
            return {'error': 'File not found', 'safe': False}
        
        filename = os.path.basename(file_path)
        
        # Get file hash
        file_hash = self._get_file_hash(file_path)
        
        # Run detection
        result = self.detector.scan(
            filename=filename,
            file_hash=file_hash
        )
        
        return {
            'file': filename,
            'hash': file_hash,
            'size_kb': os.path.getsize(file_path) / 1024,
            'analysis': result,
            'safe': result['threat_level'] == 'safe'
        }
    
    def create_sandbox(self, max_cpu: float = 20.0, max_memory_mb: int = 256,
                       max_duration: int = 300) -> str:
        """Create and register new sandbox"""
        sandbox = create_sandbox(max_cpu, max_memory_mb, max_duration)
        self.active_sandboxes[sandbox.config.sandbox_id] = sandbox
        return sandbox.config.sandbox_id
    
    def execute_in_sandbox(self, sandbox_id: str, program_path: str, 
                          args: List[str] = None) -> Dict:
        """Execute program in sandbox and monitor"""
        if sandbox_id not in self.active_sandboxes:
            return {'error': 'Sandbox not found'}
        
        sandbox = self.active_sandboxes[sandbox_id]
        
        # Pre-analyze
        pre_analysis = self.pre_analyze_file(program_path)
        if 'error' in pre_analysis:
            return pre_analysis
        
        # Execute in sandbox
        return_code = sandbox.execute_program(program_path, args or [])
        
        # Post-analyze
        usage = sandbox.monitor_resource_usage()
        anomalies = sandbox.check_anomalies()
        
        # Generate report
        report = sandbox.generate_report('completed', return_code)
        
        # Save report
        report_path = self._save_report(report)
        
        return {
            'sandbox_id': sandbox_id,
            'return_code': return_code,
            'resource_usage': usage,
            'anomalies': anomalies,
            'report_path': str(report_path),
            'report': report.to_dict()
        }
    
    def list_sandboxes(self) -> List[Dict]:
        """List active sandboxes"""
        sandboxes = []
        for sandbox_id, sandbox in self.active_sandboxes.items():
            usage = sandbox.monitor_resource_usage()
            sandboxes.append({
                'sandbox_id': sandbox_id,
                'created': sandbox.created_at,
                'resource_usage': usage,
                'config': sandbox.config.to_dict()
            })
        return sandboxes
    
    def stop_sandbox(self, sandbox_id: str) -> bool:
        """Stop and cleanup sandbox"""
        if sandbox_id not in self.active_sandboxes:
            return False
        
        sandbox = self.active_sandboxes[sandbox_id]
        sandbox.terminate()
        del self.active_sandboxes[sandbox_id]
        return True
    
    def get_report(self, sandbox_id: str) -> Optional[Dict]:
        """Get sandbox execution report"""
        if sandbox_id not in self.active_sandboxes:
            return None
        
        sandbox = self.active_sandboxes[sandbox_id]
        report = sandbox.generate_report('running')
        return report.to_dict()
    
    def quarantine_file(self, file_path: str, reason: str) -> str:
        """Move suspicious file to quarantine"""
        quarantine_dir = self.storage_path / 'quarantine'
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        
        if not os.path.exists(file_path):
            return None
        
        filename = os.path.basename(file_path)
        quarantine_path = quarantine_dir / f"{uuid.uuid4()}_{filename}"
        
        # Copy file to quarantine
        import shutil
        shutil.move(file_path, quarantine_path)
        
        # Log quarantine
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'file': filename,
            'path': str(quarantine_path),
            'reason': reason
        }
        
        return str(quarantine_path)
    
    def _save_report(self, report) -> Path:
        """Save analysis report to disk"""
        report_dir = self.storage_path / 'reports'
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = report_dir / f"{report.sandbox_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        
        return report_file
    
    @staticmethod
    def _get_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
        """Calculate file hash"""
        import hashlib
        
        hash_obj = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()

if __name__ == '__main__':
    print("SafeBox Sandbox Manager")
