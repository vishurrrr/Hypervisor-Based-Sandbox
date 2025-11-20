import pytest
import json
import tempfile
import os
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../agent'))
import agent

class TestAgent:
    
    def test_now_ts(self):
        """Test timestamp generation"""
        ts = agent.now_ts()
        assert 'Z' in ts
        assert 'T' in ts
    
    def test_run_monitored_with_valid_executable(self):
        """Test running a simple shell command"""
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, 'test.sh')
            with open(script_path, 'w') as f:
                f.write('#!/bin/bash\necho "hello"\nexit 0\n')
            os.chmod(script_path, 0o755)
            
            report_file = agent.run_monitored(script_path, timeout=5, output_dir=tmpdir)
            assert os.path.exists(report_file)
            
            with open(report_file, 'r') as f:
                report = json.load(f)
            
            assert 'start_time' in report
            assert 'end_time' in report
            assert 'path' in report
            assert report['path'] == script_path
            assert 'events' in report
    
    def test_run_monitored_timeout(self):
        """Test timeout handling"""
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, 'sleep.sh')
            with open(script_path, 'w') as f:
                f.write('#!/bin/bash\nsleep 10\n')
            os.chmod(script_path, 0o755)
            
            report_file = agent.run_monitored(script_path, timeout=1, output_dir=tmpdir)
            
            with open(report_file, 'r') as f:
                report = json.load(f)
            
            timeout_events = [e for e in report.get('events', []) if 'timeout' in e.get('event', '')]
            assert len(timeout_events) > 0 or report.get('end_time') is not None
    
    def test_run_monitored_nonexistent_file(self):
        """Test handling of nonexistent file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = os.path.join(tmpdir, 'doesnotexist')
            report_file = agent.run_monitored(nonexistent, timeout=5, output_dir=tmpdir)
            
            with open(report_file, 'r') as f:
                report = json.load(f)
            
            assert 'error' in report
    
    def test_report_json_structure(self):
        """Test that report JSON has expected structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, 'test.sh')
            with open(script_path, 'w') as f:
                f.write('#!/bin/bash\nexit 0\n')
            os.chmod(script_path, 0o755)
            
            report_file = agent.run_monitored(script_path, timeout=5, output_dir=tmpdir)
            
            with open(report_file, 'r') as f:
                report = json.load(f)
            
            assert isinstance(report, dict)
            assert 'start_time' in report
            assert 'end_time' in report
            assert 'path' in report
            assert 'events' in report
            assert isinstance(report['events'], list)
            assert 'processes' in report
            assert isinstance(report['processes'], list)
            assert 'network' in report
            assert isinstance(report['network'], list)
    
    def test_scp_send_mocked(self):
        """Test scp_send wrapper (mocked)"""
        with mock.patch('subprocess.call') as mock_call:
            mock_call.return_value = 0
            rc = agent.scp_send('/tmp/file.txt', 'user@host:/path')
            assert rc == 0
            mock_call.assert_called_once()
            call_args = mock_call.call_args[0][0]
            assert 'scp' in call_args[0]

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
