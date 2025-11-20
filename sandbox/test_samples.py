#!/usr/bin/env python3
"""
SafeBox Test Malware Samples - Safe test files for sandbox testing
Includes harmless malware simulation and behavior patterns
"""

import os
import json
from pathlib import Path
from typing import Dict, List

class TestMalwareSample:
    """Represents a test malware sample"""
    
    def __init__(self, name: str, behavior: str, severity: str):
        self.name = name
        self.behavior = behavior
        self.severity = severity
        self.created_at = None
    
    def to_dict(self):
        return {
            'name': self.name,
            'behavior': self.behavior,
            'severity': self.severity
        }

# Test samples simulating different malware behaviors
TEST_SAMPLES = {
    'cpu_hog': TestMalwareSample(
        name='cpu_hog.sh',
        behavior='Consumes 100% CPU in infinite loop',
        severity='MEDIUM'
    ),
    'memory_leak': TestMalwareSample(
        name='memory_leak.sh',
        behavior='Allocates memory without freeing (simulated)',
        severity='MEDIUM'
    ),
    'process_spawner': TestMalwareSample(
        name='process_spawner.sh',
        behavior='Spawns multiple child processes',
        severity='HIGH'
    ),
    'file_writer': TestMalwareSample(
        name='file_writer.sh',
        behavior='Creates multiple files rapidly',
        severity='LOW'
    ),
    'network_scanner': TestMalwareSample(
        name='network_scanner.sh',
        behavior='Attempts network connections (simulated)',
        severity='HIGH'
    ),
    'disk_filler': TestMalwareSample(
        name='disk_filler.sh',
        behavior='Fills disk with data (limited)',
        severity='MEDIUM'
    ),
    'trojan': TestMalwareSample(
        name='trojan_backdoor.sh',
        behavior='Establishes backdoor and persistence mechanisms',
        severity='CRITICAL'
    ),
    'ransomware': TestMalwareSample(
        name='ransomware_simulator.sh',
        behavior='Simulates encryption and ransom note creation',
        severity='CRITICAL'
    ),
    'worm': TestMalwareSample(
        name='worm_propagate.sh',
        behavior='Self-propagates via network shares',
        severity='HIGH'
    ),
    'botnet': TestMalwareSample(
        name='botnet_agent.sh',
        behavior='Connects to C&C server for command execution',
        severity='CRITICAL'
    ),
    'spyware': TestMalwareSample(
        name='spyware_keylogger.sh',
        behavior='Logs keystrokes and exfiltrates data',
        severity='HIGH'
    ),
    'rootkit': TestMalwareSample(
        name='rootkit_kernel.sh',
        behavior='Hides processes at kernel level',
        severity='CRITICAL'
    ),
    'adware': TestMalwareSample(
        name='adware_popups.sh',
        behavior='Injects advertisements and modifies browser',
        severity='MEDIUM'
    ),
    'cryptominer': TestMalwareSample(
        name='cryptominer.sh',
        behavior='Uses CPU for cryptocurrency mining',
        severity='MEDIUM'
    ),
}

# Test scripts that simulate malware behavior
TEST_SCRIPTS = {
    'cpu_hog.sh': '''#!/bin/bash
# CPU Hog - Consumes CPU resources
echo "Starting CPU hog test..."
for i in {1..5}; do
    (while true; do echo ""; done) &
done
sleep 10
pkill -P $$
echo "CPU hog test completed"
''',
    
    'memory_leak.sh': '''#!/bin/bash
# Memory Leak Simulator - Allocates increasing memory
echo "Starting memory leak simulation..."
for i in {1..10}; do
    dd if=/dev/zero bs=1M count=50 2>/dev/null | head -c 1M > /tmp/leak_$i &
done
sleep 8
rm -f /tmp/leak_* 2>/dev/null
echo "Memory leak test completed"
''',
    
    'process_spawner.sh': '''#!/bin/bash
# Process Spawner - Creates child processes
echo "Starting process spawner test..."
for i in {1..20}; do
    (sleep 5) &
done
wait
echo "Process spawner test completed"
''',
    
    'file_writer.sh': '''#!/bin/bash
# File Writer - Creates multiple files
echo "Starting file writer test..."
mkdir -p /tmp/sandbox_files
for i in {1..100}; do
    echo "Test data $i" > /tmp/sandbox_files/file_$i.txt
done
echo "File writer test completed"
ls /tmp/sandbox_files | wc -l
''',
    
    'network_scanner.sh': '''#!/bin/bash
# Network Scanner Simulator
echo "Starting network scanner simulation..."
echo "Scanning 192.168.1.0/24..."
for i in {1..10}; do
    echo "Attempting connection to 192.168.1.$i:22..."
done
echo "Network scanner test completed"
''',
    
    'disk_filler.sh': '''#!/bin/bash
# Disk Filler - Limited disk write test
echo "Starting disk filler test..."
dd if=/dev/zero bs=1M count=100 of=/tmp/disk_test.bin 2>/dev/null
echo "Disk filler test completed"
du -h /tmp/disk_test.bin
rm -f /tmp/disk_test.bin
''',
}

class TestSampleManager:
    """Manages test malware samples"""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path or './test-samples')
        self.storage_path.mkdir(exist_ok=True)
        self._create_sample_scripts()
    
    def _create_sample_scripts(self):
        """Create test malware scripts"""
        scripts_dir = self.storage_path / 'scripts'
        scripts_dir.mkdir(exist_ok=True)
        
        # Create basic resource-usage scripts
        for script_name, script_content in TEST_SCRIPTS.items():
            script_path = scripts_dir / script_name
            if not script_path.exists():
                script_path.write_text(script_content)
                os.chmod(script_path, 0o755)
        
        # Copy fake malware samples if available
        fake_malware_dir = Path(__file__).parent.parent / 'test-samples' / 'fake-malware'
        if fake_malware_dir.exists():
            for malware_file in fake_malware_dir.glob('*.sh'):
                dest_path = scripts_dir / malware_file.name
                if not dest_path.exists():
                    import shutil
                    shutil.copy2(malware_file, dest_path)
    
    def get_all_samples(self) -> Dict[str, Dict]:
        """Get all test samples"""
        return {
            name: sample.to_dict()
            for name, sample in TEST_SAMPLES.items()
        }
    
    def get_sample(self, sample_id: str) -> Dict:
        """Get specific sample"""
        if sample_id in TEST_SAMPLES:
            return TEST_SAMPLES[sample_id].to_dict()
        return None
    
    def get_sample_script(self, sample_id: str) -> str:
        """Get sample script path"""
        sample = TEST_SAMPLES.get(sample_id)
        if sample:
            script_path = self.storage_path / 'scripts' / sample.name
            if script_path.exists():
                return str(script_path.absolute())
        return None
    
    def get_sample_by_severity(self, severity: str) -> List[Dict]:
        """Get samples by severity level"""
        return [
            sample.to_dict()
            for sample in TEST_SAMPLES.values()
            if sample.severity == severity
        ]
    
    def list_samples_by_behavior(self) -> Dict[str, List[Dict]]:
        """Group samples by behavior type"""
        behaviors = {}
        for sample_id, sample in TEST_SAMPLES.items():
            behavior_type = sample.behavior.split()[0]
            if behavior_type not in behaviors:
                behaviors[behavior_type] = []
            behaviors[behavior_type].append({
                'id': sample_id,
                'name': sample.name,
                'severity': sample.severity
            })
        return behaviors

if __name__ == '__main__':
    manager = TestSampleManager()
    print("📋 Available Test Malware Samples:")
    print("=" * 50)
    
    samples = manager.get_all_samples()
    for sample_id, sample in samples.items():
        print(f"\n{sample_id}:")
        print(f"  Name: {sample['name']}")
        print(f"  Behavior: {sample['behavior']}")
        print(f"  Severity: {sample['severity']}")
    
    print("\n\n🔍 Samples by Behavior:")
    print("=" * 50)
    for behavior, items in manager.list_samples_by_behavior().items():
        print(f"\n{behavior}:")
        for item in items:
            print(f"  - {item['name']} ({item['severity']})")
