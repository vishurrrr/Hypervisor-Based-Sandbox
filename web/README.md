# SafeBox CPU Monitor - Web Dashboard

Beautiful web interface to monitor and auto-kill processes exceeding CPU threshold.

## Quick Start

### 1. Run the web server:
```bash
cd /home/ubuntu/SafeBox/web
chmod +x start.sh
./start.sh
```

### 2. Open in browser:
```
http://localhost:5000
```

### 3. Set CPU threshold and click "Start Monitoring"

## Features

✅ Beautiful web dashboard (HTML/CSS/JavaScript)  
✅ Real-time process monitoring  
✅ Auto-kill processes exceeding CPU threshold  
✅ Live activity logs  
✅ Process statistics  
✅ Graceful shutdown + force kill support  

## How It Works

1. Set CPU threshold percentage (1-100%)
2. Click "Start Monitoring"
3. Dashboard auto-kills any process exceeding threshold
4. View logs of killed processes
5. See real-time stats

## Example Output

```
🔒 SafeBox CPU Monitor - Starting
📊 Threshold: 30%
⏱️  Check interval: 2s
⚠️  Will auto-kill processes exceeding threshold
──────────────────────────────────────────────────

⏰ [14:23:45] Found 1 high-CPU process(es):

  🔴 PID:    1234 | Firefox           | CPU:  45.20% | MEM:   512.50 MB
       → Terminating...
       ✓ Terminated successfully
```

## Requirements

- Python 3.6+
- psutil library
- Linux/macOS/Windows

## Permissions

To kill all processes (including system processes), run with sudo:
```bash
sudo python3 cpu_monitor.py 30
```

## Notes

- Gracefully terminates processes first (SIGTERM)
- Force kills (SIGKILL) if graceful termination fails
- Safe - requires your confirmation before running
- Shows process name, PID, CPU%, and memory
