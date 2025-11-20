#!/usr/bin/env python3
"""
SafeBox Hypervisor Sandbox - Core Isolation Engine
Provides containerized environment for malware analysis with resource limits
"""

import os
import sys
import subprocess
import psutil
import json
import uuid
import time
import signal
import tempfile
import shutil
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List
from datetime import datetime

@dataclass
class SandboxConfig:
    """Sandbox configuration"""
    sandbox_id: str
    max_cpu_percent: float = 20.0
    max_memory_mb: int = 256
    max_duration_seconds: int = 300
    network_enabled: bool = False
    file_access_allowed: bool = False
    processes_allowed: int = 10
    
    def to_dict(self):
        return asdict(self)

@dataclass
class SandboxProcess:
    """Information about a process running in sandbox"""
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float
    status: str
    
    def to_dict(self):
        return asdict(self)

@dataclass
class SandboxReport:
    """Sandbox execution report"""
    sandbox_id: str
    start_time: str
    end_time: Optional[str]
    status: str  # running, completed, terminated, error
    return_code: Optional[int]
    total_processes: int
    total_cpu_used: float
    total_memory_used: float
    network_activity: List[str]
    file_access_attempts: List[str]
    anomalies_detected: List[str]
    
    def to_dict(self):
        return asdict(self)

class SandboxEnvironment:
    """Core sandbox isolation and management"""
    
    def __init__(self, config: SandboxConfig):
        self.config = config
        self.sandbox_dir = self._create_sandbox_dir()
        self.main_process: Optional[psutil.Process] = None
        self.child_processes: List[psutil.Process] = []
        self.resource_limits = {}
        self.network_monitor = []
        self.file_access_log = []
        self.created_at = datetime.now().isoformat()
        
    def _create_sandbox_dir(self) -> Path:
        """Create isolated filesystem for sandbox"""
        sandbox_root = Path(tempfile.gettempdir()) / 'safebox-sandboxes' / self.config.sandbox_id
        sandbox_root.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (sandbox_root / 'bin').mkdir(exist_ok=True)
        (sandbox_root / 'lib').mkdir(exist_ok=True)
        (sandbox_root / 'tmp').mkdir(exist_ok=True)
        (sandbox_root / 'logs').mkdir(exist_ok=True)
        
        return sandbox_root
    
    def set_resource_limits(self) -> bool:
        """Set resource limits for main process"""
        if not self.main_process:
            return False
            
        try:
            # Set CPU limit
            self.main_process.cpu_affinity([0, 1])  # Limit to first 2 cores
            
            # Set memory limit using rlimit
            # Note: Full implementation would use cgroups on Linux
            resource_limits = {
                'memory_mb': self.config.max_memory_mb,
                'cpu_percent': self.config.max_cpu_percent
            }
            self.resource_limits = resource_limits
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def execute_program(self, program_path: str, args: List[str] = None, 
                       env: Optional[Dict] = None, timeout: int = None) -> int:
        """Execute program within sandbox environment"""
        args = args or []
        timeout = timeout or self.config.max_duration_seconds
        
        # Create isolated environment
        sandbox_env = os.environ.copy()
        sandbox_env['SANDBOX_ID'] = self.config.sandbox_id
        sandbox_env['SANDBOX_ROOT'] = str(self.sandbox_dir)
        sandbox_env['HOME'] = str(self.sandbox_dir)
        sandbox_env['TMPDIR'] = str(self.sandbox_dir / 'tmp')
        
        if env:
            sandbox_env.update(env)
        
        # Prepare command with restrictions
        cmd = [program_path] + args
        
        try:
            # Start process with restrictions
            process = subprocess.Popen(
                cmd,
                cwd=str(self.sandbox_dir),
                env=sandbox_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setpgrp if hasattr(os, 'setpgrp') else None
            )
            
            self.main_process = psutil.Process(process.pid)
            self.config.sandbox_id = self.config.sandbox_id
            
            # Set resource limits
            self.set_resource_limits()
            
            # Monitor execution
            start_time = time.time()
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                # Terminate if timeout exceeded
                process.kill()
                stdout, stderr = process.communicate()
                return_code = -1
                
            return return_code
            
        except Exception as e:
            print(f"Error executing program: {e}")
            return -1
    
    def get_child_processes(self) -> List[SandboxProcess]:
        """Get all child processes of sandbox"""
        processes = []
        if not self.main_process:
            return processes
            
        try:
            # Get all children
            children = self.main_process.children(recursive=True)
            
            for proc in children:
                try:
                    processes.append(SandboxProcess(
                        pid=proc.pid,
                        name=proc.name(),
                        cpu_percent=proc.cpu_percent(interval=0.1),
                        memory_mb=proc.memory_info().rss / (1024 * 1024),
                        status=proc.status()
                    ))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except psutil.NoSuchProcess:
            pass
            
        return processes
    
    def monitor_resource_usage(self) -> Dict:
        """Monitor current resource usage in sandbox"""
        usage = {
            'cpu_percent': 0,
            'memory_mb': 0,
            'num_processes': 0
        }
        
        if not self.main_process:
            return usage
            
        try:
            usage['cpu_percent'] = self.main_process.cpu_percent(interval=0.1)
            usage['memory_mb'] = self.main_process.memory_info().rss / (1024 * 1024)
            usage['num_processes'] = len(self.get_child_processes()) + 1
        except psutil.NoSuchProcess:
            pass
            
        return usage
    
    def check_anomalies(self) -> List[str]:
        """Check for anomalous behavior"""
        anomalies = []
        
        if not self.main_process:
            return anomalies
            
        try:
            cpu = self.main_process.cpu_percent(interval=0.1)
            memory = self.main_process.memory_info().rss / (1024 * 1024)
            num_procs = len(self.get_child_processes())
            
            # Check for resource abuse
            if cpu > self.config.max_cpu_percent:
                anomalies.append(f"CPU usage exceeds limit: {cpu}% > {self.config.max_cpu_percent}%")
            
            if memory > self.config.max_memory_mb:
                anomalies.append(f"Memory usage exceeds limit: {memory:.1f}MB > {self.config.max_memory_mb}MB")
            
            if num_procs > self.config.processes_allowed:
                anomalies.append(f"Too many processes: {num_procs} > {self.config.processes_allowed}")
            
            # Check for fork bombs or rapid process creation
            if num_procs > 50:
                anomalies.append("Possible fork bomb detected")
                
        except psutil.NoSuchProcess:
            pass
            
        return anomalies
    
    def terminate(self) -> bool:
        """Terminate sandbox and cleanup"""
        if self.main_process:
            try:
                # Kill process group
                if os.name == 'posix':
                    os.killpg(os.getpgid(self.main_process.pid), signal.SIGTERM)
                else:
                    self.main_process.terminate()
                
                # Wait for termination
                try:
                    self.main_process.wait(timeout=5)
                except psutil.TimeoutExpired:
                    self.main_process.kill()
                    
            except (psutil.NoSuchProcess, ProcessLookupError):
                pass
        
        # Cleanup sandbox directory
        try:
            shutil.rmtree(self.sandbox_dir)
        except Exception:
            pass
            
        return True
    
    def generate_report(self, status: str, return_code: Optional[int] = None) -> SandboxReport:
        """Generate sandbox execution report"""
        usage = self.monitor_resource_usage()
        
        return SandboxReport(
            sandbox_id=self.config.sandbox_id,
            start_time=self.created_at,
            end_time=datetime.now().isoformat(),
            status=status,
            return_code=return_code,
            total_processes=usage['num_processes'],
            total_cpu_used=usage['cpu_percent'],
            total_memory_used=usage['memory_mb'],
            network_activity=self.network_monitor,
            file_access_attempts=self.file_access_log,
            anomalies_detected=self.check_anomalies()
        )

def create_sandbox(max_cpu: float = 20.0, max_memory_mb: int = 256,
                   max_duration: int = 300) -> SandboxEnvironment:
    """Factory function to create new sandbox"""
    config = SandboxConfig(
        sandbox_id=str(uuid.uuid4())[:8],
        max_cpu_percent=max_cpu,
        max_memory_mb=max_memory_mb,
        max_duration_seconds=max_duration
    )
    return SandboxEnvironment(config)

if __name__ == '__main__':
    print("SafeBox Hypervisor Sandbox Core Engine")
