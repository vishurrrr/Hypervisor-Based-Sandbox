// SafeBox Hypervisor Frontend - CPU Monitor & Sandbox Dashboard

let isMonitoring = false;
let monitorInterval = null;
let killedCount = 0;
let logs = [];
let activeSandboxes = {};

// Tab switching
function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));

    document.getElementById(tabName + '-tab').classList.add('active');
    event.target.classList.add('active');

    if (tabName === 'sandbox') {
        refreshSandboxList();
    }
}

// ============ MONITOR TAB ============

function startMonitoring() {
    if (isMonitoring) return;

    isMonitoring = true;
    addLog('🟢 CPU Monitor started', 'info');

    checkAndKillHighCpuProcesses();

    const interval = parseFloat(document.getElementById('checkInterval').value) * 1000;
    monitorInterval = setInterval(checkAndKillHighCpuProcesses, interval);
}

function stopMonitoring() {
    if (!isMonitoring) return;

    isMonitoring = false;
    clearInterval(monitorInterval);
    addLog('🔴 CPU Monitor stopped', 'info');
}

async function checkAndKillHighCpuProcesses() {
    const threshold = parseFloat(document.getElementById('cpuThreshold').value);

    try {
        const response = await fetch('/api/processes', { timeout: 15000 });
        const data = await response.json();

        if (!data.success || !data.processes) {
            addLog('❌ Failed to fetch processes', 'error');
            return;
        }

        // Update stats
        document.getElementById('totalProcesses').textContent = data.total;

        // Filter high CPU processes
        const highCpuProcesses = data.processes.filter(p => p.cpu_percent >= threshold);
        document.getElementById('highCpuCount').textContent = highCpuProcesses.length;

        // Display high CPU processes
        displayHighCpuProcesses(highCpuProcesses);

        // Kill if auto-kill is enabled
        if (isMonitoring) {
            for (const proc of highCpuProcesses) {
                if (proc.cpu_percent >= threshold * 1.5) {
                    killProcess(proc.pid);
                }
            }
        }

    } catch (error) {
        addLog(`❌ Monitor error: ${error.message}`, 'error');
    }
}

function displayHighCpuProcesses(processes) {
    const tbody = document.getElementById('processTableBody');
    tbody.innerHTML = '';

    processes.forEach(proc => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${proc.pid}</td>
            <td>${proc.name}</td>
            <td class="cpu-warning">${proc.cpu_percent.toFixed(2)}%</td>
            <td>${proc.memory_mb.toFixed(1)}MB</td>
            <td>
                <button class="btn-small" onclick="killProcess(${proc.pid})">Kill</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function killProcess(pid) {
    if (!confirm(`Kill process ${pid}?`)) return;

    fetch(`/api/kill-process/${pid}`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                killedCount++;
                document.getElementById('killedCount').textContent = killedCount;
                addLog(`✅ Killed process: ${data.name} (PID: ${pid})`, 'success');
            } else {
                addLog(`❌ Failed to kill process: ${data.error}`, 'error');
            }
        })
        .catch(e => addLog(`❌ Error: ${e.message}`, 'error'));
}

function clearLogs() {
    logs = [];
    renderLogs();
    addLog('🗑️ Logs cleared', 'info');
}

function addLog(message, type = 'info') {
    const time = new Date().toLocaleTimeString();
    logs.unshift({ time, message, type });

    if (logs.length > 100) logs.pop();
    renderLogs();
}

function renderLogs() {
    const container = document.getElementById('logContainer') ||
        (document.querySelector('.activity-log') &&
            document.querySelector('.activity-log').querySelector('[id="logContainer"]'));

    if (!container) return;

    container.innerHTML = logs.map(log => `
        <div class="log-line log-${log.type}">
            <span class="log-time">${log.time}</span>
            <span class="log-message">${log.message}</span>
        </div>
    `).join('');
}

// Update threshold display
document.addEventListener('DOMContentLoaded', () => {
    const cpuInput = document.getElementById('cpuThreshold');
    const intervalInput = document.getElementById('checkInterval');

    if (cpuInput) {
        cpuInput.addEventListener('change', () => {
            document.getElementById('cpuValue').textContent = cpuInput.value + '%';
        });
    }

    if (intervalInput) {
        intervalInput.addEventListener('change', () => {
            document.getElementById('intervalValue').textContent = intervalInput.value + 's';
        });
    }
});

// ============ SANDBOX TAB ============

async function createAndExecuteSandbox() {
    const programPath = document.getElementById('programPath').value;
    const maxCpu = document.getElementById('sandboxMaxCpu').value;
    const maxMemory = document.getElementById('sandboxMaxMemory').value;
    const maxDuration = document.getElementById('sandboxMaxDuration').value;

    if (!programPath) {
        alert('Please enter a program path');
        return;
    }

    try {
        // Create sandbox
        const createResponse = await fetch('/api/sandbox/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                max_cpu: parseFloat(maxCpu),
                max_memory_mb: parseInt(maxMemory),
                max_duration: parseInt(maxDuration)
            })
        });

        const createData = await createResponse.json();
        if (!createData.success) {
            alert('Failed to create sandbox: ' + createData.error);
            return;
        }

        const sandboxId = createData.sandbox_id;
        addLog(`🆕 Sandbox created: ${sandboxId}`, 'info');

        // Execute in sandbox
        const execResponse = await fetch('/api/sandbox/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sandbox_id: sandboxId,
                program_path: programPath,
                args: []
            })
        });

        const execData = await execResponse.json();

        if (execData.success) {
            addLog(`✅ Program executed in sandbox ${sandboxId}`, 'success');
            addLog(`   Return code: ${execData.result.return_code}`, 'info');

            const usage = execData.result.resource_usage;
            addLog(`   CPU: ${usage.cpu_percent.toFixed(2)}%`, 'info');
            addLog(`   Memory: ${usage.memory_mb.toFixed(1)}MB`, 'info');
            addLog(`   Processes: ${usage.num_processes}`, 'info');

            if (execData.result.anomalies.length > 0) {
                addLog('⚠️ Anomalies detected:', 'warning');
                execData.result.anomalies.forEach(a => {
                    addLog(`   - ${a}`, 'warning');
                });
            }
        } else {
            addLog(`❌ Execution failed: ${execData.error || 'Unknown error'}`, 'error');
        }

        refreshSandboxList();

    } catch (error) {
        addLog(`❌ Sandbox error: ${error.message}`, 'error');
    }
}

async function refreshSandboxList() {
    try {
        const response = await fetch('/api/sandbox/list');
        const data = await response.json();

        if (data.success) {
            document.getElementById('activeSandboxes').textContent = data.count;
            displaySandboxList(data.sandboxes);
        }
    } catch (error) {
        console.error('Failed to refresh sandboxes:', error);
    }
}

function displaySandboxList(sandboxes) {
    const container = document.getElementById('sandboxList');

    if (sandboxes.length === 0) {
        container.innerHTML = '<p>No active sandboxes</p>';
        return;
    }

    container.innerHTML = sandboxes.map(sb => `
        <div class="sandbox-item">
            <div class="sandbox-id">${sb.sandbox_id}</div>
            <div class="sandbox-info">
                <span>CPU: ${sb.resource_usage.cpu_percent.toFixed(1)}%</span>
                <span>Memory: ${sb.resource_usage.memory_mb.toFixed(1)}MB</span>
                <span>Processes: ${sb.resource_usage.num_processes}</span>
            </div>
            <button class="btn-small" onclick="stopSandbox('${sb.sandbox_id}')">Stop</button>
        </div>
    `).join('');
}

async function stopSandbox(sandboxId) {
    try {
        const response = await fetch(`/api/sandbox/stop/${sandboxId}`, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            addLog(`🛑 Sandbox ${sandboxId} stopped`, 'info');
            refreshSandboxList();
        } else {
            addLog(`❌ Failed to stop sandbox: ${data.error}`, 'error');
        }
    } catch (error) {
        addLog(`❌ Error: ${error.message}`, 'error');
    }
}

// ============ ANALYSIS TAB ============

async function preScanFile() {
    const filePath = document.getElementById('filePath').value;

    if (!filePath) {
        alert('Please enter a file path');
        return;
    }

    try {
        const response = await fetch('/api/sandbox/pre-scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_path: filePath })
        });

        const data = await response.json();

        if (data.success) {
            const analysis = data.analysis;
            const result = document.getElementById('scanResult');

            const threatColor = {
                'safe': '#10b981',
                'suspicious': '#f59e0b',
                'dangerous': '#ef4444',
                'critical': '#dc2626'
            };

            result.innerHTML = `
                <div class="scan-result" style="border-left: 4px solid ${threatColor[analysis.analysis.threat_level]}">
                    <h4>${analysis.file}</h4>
                    <p><strong>Hash:</strong> ${analysis.hash}</p>
                    <p><strong>Size:</strong> ${analysis.size_kb.toFixed(1)}KB</p>
                    <p><strong>Safe:</strong> ${analysis.safe ? '✅ Yes' : '❌ No'}</p>
                    <p><strong>Threat Level:</strong> <span style="color: ${threatColor[analysis.analysis.threat_level]}">${analysis.analysis.threat_level.toUpperCase()}</span></p>
                    <p><strong>Risk:</strong> ${analysis.analysis.risk}</p>
                    <p><strong>Detections:</strong></p>
                    <ul>
                        ${analysis.analysis.detections.map(d => `<li>${d}</li>`).join('')}
                    </ul>
                </div>
            `;

            addLog(`🔍 Scanned: ${analysis.file} - ${analysis.analysis.threat_level.toUpperCase()}`, 'info');
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Scan error: ' + error.message);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    addLog('🔒 SafeBox Hypervisor Dashboard loaded', 'info');
});
