"""
SafeBox Sandbox Module
Complete hypervisor sandbox for malware analysis
"""

from .sandbox_core import SandboxEnvironment, SandboxConfig, create_sandbox
from .malware_detector import MalwareDetector, ThreatLevel, BehaviorIndicator
from .sandbox_manager import SandboxManager

__all__ = [
    'SandboxEnvironment',
    'SandboxConfig',
    'create_sandbox',
    'MalwareDetector',
    'ThreatLevel',
    'BehaviorIndicator',
    'SandboxManager'
]

__version__ = '1.0.0'
