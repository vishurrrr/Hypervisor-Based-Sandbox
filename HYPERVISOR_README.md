# SafeBox Hypervisor Sandbox - Complete Project Documentation

## Project Overview

**SafeBox Hypervisor Sandbox** is a comprehensive security solution combining:
1. **Real-time CPU Monitoring** - Track and manage high-CPU processes
2. **Hypervisor Sandbox Environment** - Isolated execution for malware analysis
3. **Malware Detection System** - Behavioral and signature-based threat analysis
4. **Web Dashboard** - Complete UI for monitoring and control

## Project Structure

```
/home/ubuntu/SafeBox/
├── web/                          # Web dashboard and Flask backend
│   ├── app.py                   # Original CPU monitor API
│   ├── app_hypervisor.py        # Hypervisor integrated Flask app
│   ├── index.html               # Dashboard UI
│   ├── style.css                # Original styles
│   ├── hypervisor.css           # Hypervisor dashboard styles
│   ├── monitor.js               # Original monitor frontend
│   ├── monitor_hypervisor.js    # Hypervisor dashboard frontend
│   ├── requirements.txt         # Python dependencies
│   ├── venv/                    # Python virtual environment
│   └── start.sh                 # Start script
│
├── sandbox/                      # Sandbox isolation and analysis
│   ├── __init__.py              # Module initialization
│   ├── sandbox_core.py          # Core isolation engine
│   ├── malware_detector.py      # Malware detection system
│   ├── sandbox_manager.py       # Sandbox orchestration
│   ├── sandbox_api.py           # Flask REST API
│   ├── test_sandbox.py          # Example tests
│   └── README.md                # Sandbox documentation
│
├── src/                          # Source code
│   └── host/
│       ├── main.cpp
│       ├── safebox.cpp
│       └── safebox.h
│
├── tests/                        # Test files
├── agent/                        # Python agent
└── ...
```

## Installation

### Prerequisites
- Python 3.8+
- Flask 2.3.3
- psutil 5.9.5
- Linux/Unix OS

### Setup

1. **Clone/Navigate to project:**
```bash
cd /home/ubuntu/SafeBox
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install Flask==2.3.3 Flask-CORS==4.0.0 psutil==5.9.5
```

4. **Create sandbox reports directory:**
```bash
mkdir -p sandbox-reports/{reports,quarantine}
```

## Running the Application

### Option 1: Original CPU Monitor
```bash
cd /home/ubuntu/SafeBox/web
python3 app.py
```
Access at: http://localhost:5000

### Option 2: Hypervisor Sandbox (Recommended)
```bash
cd /home/ubuntu/SafeBox/web
python3 app_hypervisor.py
```
Access at: http://localhost:5000

The hypervisor version includes:
- CPU monitoring (original features)
- Sandbox creation and execution
- Malware analysis
- File pre-scanning

## Core Components

### 1. CPU Monitor (`web/app.py`)

**Features:**
- Real-time process monitoring
- High-CPU detection and alerting
- Process termination (graceful + force)
- Web dashboard interface

**API Endpoints:**
- `GET /api/processes` - Get all processes with CPU/memory info
- `POST /api/kill-process/<pid>` - Terminate a process

**Usage:**
```python
# The dashboard automatically fetches processes
# every N seconds (configurable) and displays high-CPU processes
# Click "Kill" to terminate a process
```

### 2. Sandbox Core (`sandbox/sandbox_core.py`)

**Features:**
- Process isolation
- Resource limits (CPU, memory, processes)
- Timeout protection
- Process hierarchy monitoring
- Anomaly detection
- Report generation

**Key Classes:**
- `SandboxConfig` - Configuration settings
- `SandboxEnvironment` - Core isolation engine
- `SandboxProcess` - Process information
- `SandboxReport` - Execution report

**Example:**
```python
from sandbox import create_sandbox

sandbox = create_sandbox(
    max_cpu=20.0,           # 20% CPU limit
    max_memory_mb=256,      # 256 MB limit
    max_duration=300        # 5 minute timeout
)

return_code = sandbox.execute_program(
    '/path/to/program',
    args=['arg1', 'arg2']
)

usage = sandbox.monitor_resource_usage()
anomalies = sandbox.check_anomalies()
report = sandbox.generate_report('completed', return_code)
```

### 3. Malware Detector (`sandbox/malware_detector.py`)

**Features:**
- Signature-based detection
- Behavioral pattern analysis
- Resource anomaly detection
- Threat scoring system
- Multiple threat levels

**Threat Levels:**
- **SAFE** (0-29): No indicators
- **SUSPICIOUS** (30-99): Some indicators
- **DANGEROUS** (100-149): Multiple indicators
- **CRITICAL** (150+): Severe indicators

**Detection Patterns:**
- File operations (executables, system files)
- Process operations (injection, hooks)
- Network operations (C&C, exfiltration)
- Persistence mechanisms (auto-start, services)
- Resource abuse (fork bombs, crypto mining)

**Example:**
```python
from sandbox import MalwareDetector

detector = MalwareDetector()

result = detector.scan(
    filename='suspicious.exe',
    behaviors=['CreateRemoteThread', 'WriteProcessMemory'],
    cpu=85.5,
    memory=512,
    num_processes=15
)

print(result['threat_level'])      # 'critical', 'dangerous', etc.
print(result['detections'])        # List of detected issues
print(result['risk'])              # Risk assessment text
```

### 4. Sandbox Manager (`sandbox/sandbox_manager.py`)

**Features:**
- Multi-sandbox orchestration
- Pre-analysis scanning
- File quarantine
- Report management
- Hash-based detection

**Example:**
```python
from sandbox import SandboxManager

manager = SandboxManager()

# Pre-analyze file
pre = manager.pre_analyze_file('/path/to/file.exe')
if not pre['safe']:
    print(f"Threat: {pre['analysis']['threat_level']}")

# Create sandbox
sandbox_id = manager.create_sandbox()

# Execute in sandbox
result = manager.execute_in_sandbox(sandbox_id, '/path/to/program')

# Quarantine if needed
if result['anomalies']:
    manager.quarantine_file('/path/to/file', 'Detected anomalies')
```

### 5. Web Dashboard (`web/app_hypervisor.py`)

**Three Main Tabs:**

**Monitor Tab:**
- Real-time CPU monitoring
- High-CPU process list
- Process termination
- Statistics (total processes, high CPU count, killed count)
- Activity logs

**Sandbox Tab:**
- Create new sandboxes
- Configure resource limits
- Execute programs safely
- Monitor active sandboxes
- Stop sandboxes

**Analysis Tab:**
- Pre-scan files
- View threat assessment
- See detection details
- Risk analysis

## API Reference

### CPU Monitor APIs

#### Get Processes
```
GET /api/processes

Response:
{
  "success": true,
  "processes": [
    {
      "pid": 1234,
      "name": "chrome",
      "cpu_percent": 25.5,
      "memory_mb": 512.3
    },
    ...
  ],
  "total": 297
}
```

#### Kill Process
```
POST /api/kill-process/1234

Response:
{
  "success": true,
  "message": "Process 1234 terminated",
  "name": "chrome"
}
```

### Sandbox APIs

#### Pre-Scan File
```
POST /api/sandbox/pre-scan
Content-Type: application/json

{
  "file_path": "/path/to/file.exe"
}

Response:
{
  "success": true,
  "analysis": {
    "file": "file.exe",
    "hash": "abc123...",
    "size_kb": 512.5,
    "analysis": {
      "threat_score": 150,
      "threat_level": "critical",
      "detections": [...],
      "risk": "EXTREMELY HIGH RISK"
    },
    "safe": false
  }
}
```

#### Create Sandbox
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

#### Execute in Sandbox
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

#### List Active Sandboxes
```
GET /api/sandbox/list

Response:
{
  "success": true,
  "sandboxes": [
    {
      "sandbox_id": "a1b2c3d4",
      "created": "2025-11-16T10:30:00",
      "resource_usage": {...},
      "config": {...}
    },
    ...
  ],
  "count": 2
}
```

#### Get Sandbox Status
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

#### Stop Sandbox
```
POST /api/sandbox/stop/a1b2c3d4

Response:
{
  "success": true,
  "message": "Sandbox a1b2c3d4 stopped"
}
```

#### Quarantine File
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

## Testing

### Run Sandbox Tests
```bash
cd /home/ubuntu/SafeBox/sandbox
python3 test_sandbox.py
```

This runs:
1. **Malware Detection Tests** - Tests threat detection with various patterns
2. **Sandbox Creation Tests** - Creates and monitors sandboxes
3. **Sandbox Manager Tests** - Tests orchestration features

### Manual Testing

1. **Test CPU Monitor:**
   - Start dashboard
   - Set CPU threshold to 30%
   - Click "Start Monitor"
   - Observe process list updates

2. **Test Sandbox:**
   - Go to Sandbox tab
   - Enter program path: `/bin/ls`
   - Click "Execute in Sandbox"
   - View execution report

3. **Test Malware Detection:**
   - Go to Analysis tab
   - Enter file path
   - Click "Scan File"
   - View threat assessment

## Configuration

### Sandbox Configuration

Edit resource limits in `sandbox_core.py`:
```python
@dataclass
class SandboxConfig:
    max_cpu_percent: float = 20.0      # CPU limit
    max_memory_mb: int = 256           # Memory limit
    max_duration_seconds: int = 300    # Timeout
    network_enabled: bool = False      # Network access
    file_access_allowed: bool = False  # File access
    processes_allowed: int = 10        # Max processes
```

### Malware Detection Signatures

Add custom signatures in `malware_detector.py`:
```python
def _init_signatures(self) -> List[MalwareSignature]:
    signatures = [
        MalwareSignature(
            name="Custom Threat",
            description="Custom threat pattern",
            patterns=[r'.*pattern.*'],
            hashes=['known_hash'],
            threat_level=ThreatLevel.CRITICAL
        ),
        ...
    ]
```

## Security Considerations

### Isolation Levels
1. **Process-level isolation** - Separate processes, shared kernel
2. **Resource limits** - CPU, memory, process count
3. **Timeout protection** - Automatic termination
4. **Filesystem isolation** - Temporary sandbox directory

### Limitations
- Not full VM isolation (lighter weight)
- Kernel-level exploits can escape
- Cannot detect zero-day exploits
- Behavioral patterns are signature-based

### Best Practices
1. Run untrusted code in sandbox
2. Pre-scan suspicious files
3. Monitor for anomalies
4. Quarantine detected threats
5. Keep signatures updated
6. Review logs regularly

## Performance

### Resource Usage
- **Memory:** ~50-100MB for Flask server
- **CPU:** Minimal (<1%) when idle
- **Sandbox overhead:** ~5-10MB per sandbox
- **Typical scan time:** <1 second

### Scalability
- Can monitor 300+ processes
- Supports multiple concurrent sandboxes
- API response time: <100ms
- Database: File-based JSON reports

## Troubleshooting

### Dashboard Not Loading
```bash
# Check Flask is running
ps aux | grep python3 | grep app

# Verify port 5000
ss -tuln | grep 5000

# Check logs
cat /tmp/flask.log
```

### Sandbox Fails to Create
```bash
# Check permissions
ls -la /tmp

# Check disk space
df -h

# Verify Python
python3 --version
```

### Malware Detection False Positives
- Review detected patterns
- Add file to whitelist
- Adjust threat thresholds
- Update signatures

## Future Enhancements

1. **VM-Based Isolation** - Full hypervisor integration
2. **Network Monitoring** - Track network connections
3. **Binary Analysis** - Static code analysis
4. **Machine Learning** - AI-based threat detection
5. **Distributed Sandbox** - Multiple analysis nodes
6. **Custom Signatures** - User-defined patterns
7. **Threat Intelligence** - Real-time threat feeds
8. **Forensics** - Deep execution analysis

## Support

For issues or questions:
1. Check logs in `/tmp/flask.log`
2. Review sandbox reports in `./sandbox-reports/`
3. Run test suite: `python3 sandbox/test_sandbox.py`
4. Check API endpoint responses

## License

Same as SafeBox project

## Authors

SafeBox Hypervisor Sandbox Development Team
