#!/usr/bin/env python3
"""
SafeBox Sandbox - Example usage and testing
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sandbox_core import create_sandbox
from malware_detector import MalwareDetector
from sandbox_manager import SandboxManager

def test_malware_detector():
    """Test malware detection system"""
    print("\n" + "="*60)
    print("🔍 MALWARE DETECTION TEST")
    print("="*60)
    
    detector = MalwareDetector()
    
    # Test 1: Ransomware detection
    print("\n[Test 1] Ransomware Detection")
    result = detector.scan(
        filename='wannacry.exe',
        behaviors=['encrypt', 'ransom', 'crypt'],
        cpu=90.0,
        memory=450,
        num_processes=5
    )
    print(f"Threat Level: {result['threat_level']}")
    print(f"Risk: {result['risk']}")
    print(f"Detections: {result['detections']}")
    
    # Test 2: Suspicious file
    print("\n[Test 2] Suspicious File Detection")
    result = detector.scan(
        filename='malware.bat',
        behaviors=['CreateRemoteThread', 'WriteProcessMemory'],
        cpu=45.0,
        memory=200,
        num_processes=8
    )
    print(f"Threat Level: {result['threat_level']}")
    print(f"Risk: {result['risk']}")
    
    # Test 3: Safe file
    print("\n[Test 3] Safe File Detection")
    result = detector.scan(
        filename='notepad.exe',
        behaviors=[],
        cpu=5.0,
        memory=50,
        num_processes=1
    )
    print(f"Threat Level: {result['threat_level']}")
    print(f"Risk: {result['risk']}")

def test_sandbox_creation():
    """Test sandbox creation"""
    print("\n" + "="*60)
    print("🔬 SANDBOX CREATION TEST")
    print("="*60)
    
    try:
        sandbox = create_sandbox(
            max_cpu=20.0,
            max_memory_mb=256,
            max_duration=60
        )
        
        print(f"\n✅ Sandbox Created")
        print(f"   ID: {sandbox.config.sandbox_id}")
        print(f"   Max CPU: {sandbox.config.max_cpu_percent}%")
        print(f"   Max Memory: {sandbox.config.max_memory_mb}MB")
        print(f"   Max Duration: {sandbox.config.max_duration_seconds}s")
        print(f"   Directory: {sandbox.sandbox_dir}")
        
        # Monitor resources
        usage = sandbox.monitor_resource_usage()
        print(f"\n📊 Resource Usage:")
        print(f"   CPU: {usage['cpu_percent']}%")
        print(f"   Memory: {usage['memory_mb']:.1f}MB")
        print(f"   Processes: {usage['num_processes']}")
        
        # Cleanup
        sandbox.terminate()
        print(f"\n✅ Sandbox terminated and cleaned up")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_sandbox_manager():
    """Test sandbox manager"""
    print("\n" + "="*60)
    print("🏢 SANDBOX MANAGER TEST")
    print("="*60)
    
    try:
        manager = SandboxManager()
        
        # Pre-analyze a common system file
        print("\n[Test] Pre-analyzing system file")
        print("   Note: Using /bin/ls as a safe test file")
        
        if os.path.exists('/bin/ls'):
            result = manager.pre_analyze_file('/bin/ls')
            print(f"\n   File: {result['file']}")
            print(f"   Size: {result['size_kb']:.1f}KB")
            print(f"   Hash: {result['hash'][:16]}...")
            print(f"   Threat Level: {result['analysis']['threat_level']}")
            print(f"   Safe: {result['safe']}")
        
        # Create sandbox
        print("\n[Test] Creating sandbox instance")
        sandbox_id = manager.create_sandbox(
            max_cpu=15.0,
            max_memory_mb=200,
            max_duration=30
        )
        print(f"   Sandbox ID: {sandbox_id}")
        
        # List sandboxes
        sandboxes = manager.list_sandboxes()
        print(f"\n   Active Sandboxes: {len(sandboxes)}")
        for sb in sandboxes:
            print(f"     - {sb['sandbox_id']}")
        
        # Stop sandbox
        print(f"\n[Test] Stopping sandbox")
        manager.stop_sandbox(sandbox_id)
        print("   ✅ Sandbox stopped")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🔒 SafeBox Hypervisor Sandbox - Example Tests")
    print("="*60)
    
    test_malware_detector()
    test_sandbox_creation()
    test_sandbox_manager()
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
