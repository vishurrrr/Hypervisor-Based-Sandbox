#!/usr/bin/env python3
"""
Agent for running suspicious file and collecting metrics inside the VM.

Usage:
python3 agent.py --file /path/to/file --output /path/to/output --timeout 60
"""

import argparse
import json
import os
import subprocess
import time
import datetime
import psutil
import shutil


def now_ts():
    return datetime.datetime.utcnow().isoformat() + 'Z'


def run_monitored(path, timeout, poll_interval=0.5, output_dir='.'):
    os.makedirs(output_dir, exist_ok=True)
    report = {'start_time': now_ts(), 'path': path, 'events': [], 'processes': [], 'network': []}

    baseline_pids = set(p.pid for p in psutil.process_iter())

    try:
        proc = subprocess.Popen([path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        report['error'] = f'failed to start: {e}'
        report['end_time'] = now_ts()
        fname = os.path.join(output_dir, f'report-{int(time.time())}.json')
        with open(fname, 'w') as f:
            json.dump(report, f, indent=2)
        return fname

    start = time.time()
    try:
        while True:
            elapsed = time.time() - start
            if elapsed > timeout:
                proc.terminate()
                report['events'].append({'time': now_ts(), 'event': 'timeout-kill'})
                break

            if proc.poll() is not None:
                report['events'].append({'time': now_ts(), 'event': 'process-exited', 'returncode': proc.returncode})
                break

            # collect CPU/memory for process
            try:
                p = psutil.Process(proc.pid)
                cpu = p.cpu_percent(interval=None)
                mem = p.memory_info()._asdict()
                report['processes'].append({'time': now_ts(), 'pid': proc.pid, 'cpu_percent': cpu, 'memory': mem})
            except psutil.NoSuchProcess:
                pass

            # detect new processes
            current_pids = set(p.pid for p in psutil.process_iter())
            new = current_pids - baseline_pids
            if new:
                for pid in new:
                    try:
                        pp = psutil.Process(pid)
                        report['events'].append({'time': now_ts(), 'event': 'process-created', 'pid': pid, 'cmdline': pp.cmdline()})
                    except Exception:
                        report['events'].append({'time': now_ts(), 'event': 'process-created', 'pid': pid})
                baseline_pids = baseline_pids.union(new)

            # collect network connections
            try:
                conns = []
                for c in psutil.net_connections(kind='inet'):
                    conns.append({'fd': c.fd, 'family': str(c.family), 'type': str(c.type), 'laddr': str(c.laddr), 'raddr': str(c.raddr), 'status': c.status, 'pid': c.pid})
                report['network'].append({'time': now_ts(), 'connections': conns})
            except Exception:
                pass

            time.sleep(poll_interval)

    except KeyboardInterrupt:
        proc.terminate()
        report['events'].append({'time': now_ts(), 'event': 'keyboard-interrupt'})

    # finalize
    report['end_time'] = now_ts()
    fname = os.path.join(output_dir, f'report-{int(time.time())}.json')
    with open(fname, 'w') as f:
        json.dump(report, f, indent=2)

    # collect stdout/stderr
    try:
        out, err = proc.communicate(timeout=1)
        with open(os.path.join(output_dir, f'out-{proc.pid}.log'), 'wb') as f:
            f.write(out or b'')
        with open(os.path.join(output_dir, f'err-{proc.pid}.log'), 'wb') as f:
            f.write(err or b'')
    except Exception:
        pass

    return fname


def scp_send(local_path, target):
    cmd = ['scp', '-o', 'StrictHostKeyChecking=no', local_path, target]
    return subprocess.call(cmd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True, help='Path to suspicious file to execute')
    parser.add_argument('--output', required=True, help='Directory to write output into')
    parser.add_argument('--timeout', type=int, default=60, help='Execution timeout (seconds)')
    parser.add_argument('--send-back', default=None, help='Optional scp target')
    args = parser.parse_args()

    try:
        st = os.stat(args.file)
        os.chmod(args.file, st.st_mode | 0o111)
    except Exception:
        pass

    report = run_monitored(args.file, args.timeout, output_dir=args.output)
    print(f'Report written to {report}')

    if args.send_back:
        target = args.send_back.rstrip('/') + '/'
        scp_send(report, args.send_back)
        for fname in os.listdir(args.output):
            if fname.startswith('out-') or fname.startswith('err-'):
                scp_send(os.path.join(args.output, fname), args.send_back)
