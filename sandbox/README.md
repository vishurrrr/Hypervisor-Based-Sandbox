# SafeBox Hypervisor Sandbox Environment

Complete hypervisor sandbox system for malware analysis and safe execution of untrusted code.

## Features

### 1. **Core Sandbox Isolation** (`sandbox_core.py`)
- **Resource Limits**: CPU, memory, and process limits
- **Isolated Filesystem**: Temporary sandbox directory per execution
- **Process Management**: Monitor and control child processes
- **Timeout Protection**: Automatic termination after max duration
- **Comprehensive Reports**: Detailed execution logs and metrics

### 2. **Malware Detection** (`malware_detector.py`)
- **Signature Matching**: Known malware pattern detection
- **Behavior Analysis**: Suspicious behavior pattern matching
- **Resource Anomaly Detection**: CPU/memory abuse detection
- **Threat Scoring**: Risk-based classification system
- **Multiple Threat Levels**: SAFE, SUSPICIOUS, DANGEROUS, CRITICAL

### 3. **Sandbox Management** (`sandbox_manager.py`)
- **Pre-Analysis Scanning**: File analysis before execution
- **Multi-Sandbox Support**: Run multiple sandboxes simultaneously
- **File Quarantine**: Isolate suspicious files
- **Report Generation**: JSON reports with full analysis
- **Hash-based Detection**: SHA256 fingerprinting

### 4. **Web API Integration** (`sandbox_api.py`)
- **Flask RESTful API**: Complete REST endpoints
- **Pre-scan Endpoint**: `/api/sandbox/pre-scan`
- **Sandbox Creation**: `/api/sandbox/create`
- **Execution Endpoint**: `/api/sandbox/execute`
- **Status Monitoring**: `/api/sandbox/status/<sandbox_id>`
- **File Quarantine**: `/api/sandbox/quarantine`

## Usage

### Create and Run Sandbox
```python
from sandbox import create_sandbox, SandboxManager

# Create sandbox
sandbox = create_sandbox(
    max_cpu=20.0,        # 20% CPU limit
    max_memory_mb=256,   # 256 MB memory limit
    max_duration=300     # 5 minute timeout
)

# Execute program
return_code = sandbox.execute_program(
    '/path/to/program',
    args=['--arg1', 'value1']
)

# Get resource usage
usage = sandbox.monitor_resource_usage()
print(f"CPU: {usage['cpu_percent']}%")
print(f"Memory: {usage['memory_mb']:.1f}MB")

# Check for anomalies
anomalies = sandbox.check_anomalies()
if anomalies:
    print("Suspicious activity detected!")

# Generate report
report = sandbox.generate_report('completed', return_code)
```

### Malware Detection
```python
from sandbox import MalwareDetector

detector = MalwareDetector()

# Scan file
result = detector.scan(
    filename='suspicious.exe',
    behaviors=['CreateRemoteThread', 'WriteProcessMemory'],
    cpu=85.5,
    memory=512,
    num_processes=15
)

print(f"Threat Level: {result['threat_level']}")
print(f"Risk Assessment: {result['risk']}")
for detection in result['detections']:
    print(f"  - {detection}")
```

### Sandbox Manager
```python
from sandbox import SandboxManager

manager = SandboxManager()

# Pre-analyze file
pre_analysis = manager.pre_analyze_file('/path/to/file.exe')
print(f"Safe: {pre_analysis['safe']}")

# Create sandbox
sandbox_id = manager.create_sandbox()

# Execute in sandbox
result = manager.execute_in_sandbox(sandbox_id, '/path/to/program')

# Quarantine suspicious file
quarantine_path = manager.quarantine_file(
    '/path/to/malware',
    reason='Detected as ransomware'
)
```

## API Endpoints

### Pre-Scan File
```
POST /api/sandbox/pre-scan
Content-Type: application/json

{
  "file_path": "/path/to/file"
}

Response:
{
  "success": true,
  "analysis": {
    "file": "malware.exe",
    "hash": "abc123...",
    "analysis": {
      "threat_score": 150,
      "threat_level": "critical",
      "detections": ["Signature match: Generic Ransomware"],
      "risk": "EXTREMELY HIGH RISK - IMMEDIATE ISOLATION RECOMMENDED"
    },
    "safe": false
  }
}
```

### Create Sandbox
```
POST /api/sandbox/create
Content-Type: application/json

{
  "max_cpu": 20.0,
  "max_memory_mb": 256,
  "max_duration": 300
}

Response:
{
  "success": true,
  "sandbox_id": "a1b2c3d4"
}
```

### Execute in Sandbox
```
POST /api/sandbox/execute
Content-Type: application/json

{
  "sandbox_id": "a1b2c3d4",
  "program_path": "/path/to/program",
  "args": ["--arg1", "value1"]
}

Response:
{
  "success": true,
  "result": {
    "sandbox_id": "a1b2c3d4",
    "return_code": 0,
    "resource_usage": {
      "cpu_percent": 15.5,
      "memory_mb": 128.3,
      "num_processes": 3
    },
    "anomalies": [],
    "report": {...}
  }
}
```

### Get Sandbox Status
```
GET /api/sandbox/status/a1b2c3d4

Response:
{
  "success": true,
  "report": {
    "sandbox_id": "a1b2c3d4",
    "status": "running",
    "total_processes": 3,
    "total_cpu_used": 15.5,
    "total_memory_used": 128.3,
    "anomalies_detected": [],
    ...
  }
}
```

### Stop Sandbox
```
POST /api/sandbox/stop/a1b2c3d4

Response:
{
  "success": true,
  "message": "Sandbox a1b2c3d4 stopped"
}
```

### Quarantine File
```
POST /api/sandbox/quarantine
Content-Type: application/json

{
  "file_path": "/path/to/malware",
  "reason": "Detected as ransomware"
}

Response:
{
  "success": true,
  "quarantine_path": "/tmp/safebox-sandboxes/quarantine/uuid_filename",
  "message": "File quarantined"
}
```

## Threat Levels

### SAFE (Score: 0-29)
- No malware indicators detected
- Normal resource usage
- No suspicious behaviors

### SUSPICIOUS (Score: 30-99)
- Some malware indicators present
- Slightly elevated resource usage
- Requires monitoring

### DANGEROUS (Score: 100-149)
- Multiple malware indicators
- Significant resource anomalies
- Isolation recommended

### CRITICAL (Score: 150+)
- Strong malware indicators
- Severe resource abuse
- Immediate isolation required

## Detection Patterns

### File Operations
- Executable file creation (.exe, .dll, .sys)
- System file access
- Boot sector modification

### Process Operations
- Remote thread injection
- Process memory modification
- Privilege escalation
- Hook installation

### Network Operations
- Unauthorized network connections
- Command & control callbacks
- Data exfiltration attempts
- Port scanning

### Persistence Mechanisms
- Auto-start registry entries
- Startup folder modification
- Scheduled task creation
- Service installation

### Resource Abuse
- Fork bombs (excessive process creation)
- Memory exhaustion
- CPU intensive operations
- Disk space exhaustion

## Security Considerations

1. **Isolation Level**: Process-level isolation with resource limits
2. **Timeout**: Automatic termination prevents infinite loops
3. **Filesystem**: Temporary isolated directory per sandbox
4. **Network**: Can be disabled for untrusted code
5. **Cleanup**: Automatic resource cleanup on termination

## Limitations

- Process-level isolation (not full VM isolation)
- Requires Linux/Unix OS
- Resource limits are soft limits
- Cannot detect zero-day exploits
- Behavioral patterns are signature-based

## Files

- `sandbox_core.py` - Core isolation engine
- `malware_detector.py` - Malware detection system
- `sandbox_manager.py` - Sandbox orchestration
- `sandbox_api.py` - Flask REST API
- `__init__.py` - Module initialization

## Example Workflow

```
1. User uploads suspicious file
   ↓
2. Pre-analysis scan performed
   ↓
3. If threat detected:
   - File quarantined
   - Alert generated
   ↓
4. If analysis enabled:
   - Sandbox created
   - Program executed with limits
   ↓
5. Execution monitored:
   - Resource usage tracked
   - Behavior analyzed
   - Anomalies detected
   ↓
6. Report generated:
   - Execution summary
   - Resource metrics
   - Threat assessment
   ↓
7. File quarantined if needed
```

## Integration with CPU Monitor

The sandbox integrates with the main CPU monitor:

- **CPU Monitor**: Tracks all system processes
- **Sandbox**: Isolates untrusted code
- **Combined**: Comprehensive system security

The web dashboard provides:
- Real-time CPU monitoring
- Process management
- Sandbox creation and control
- Malware analysis
- Threat reporting

## Future Enhancements

- Full VM-based isolation
- Network traffic monitoring
- Binary code analysis
- Machine learning threat detection
- Distributed sandbox network
- Custom signature creation
- Behavioral recording and playback
