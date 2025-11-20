// SafeBox CPU Monitor Frontend
let isRunning = false;
let checkInterval = null;
let killedCount = 0;
let logs = [];

const cpuThresholdInput = document.getElementById('cpuThreshold');
const checkIntervalInput = document.getElementById('checkInterval');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const statusText = document.getElementById('statusText');
const statusTime = document.getElementById('statusTime');
const processList = document.getElementById('processList');
const logContainer = document.getElementById('logContainer');
const clearLogsBtn = document.getElementById('clearLogsBtn');

// Event listeners
startBtn.addEventListener('click', startMonitoring);
stopBtn.addEventListener('click', stopMonitoring);
clearLogsBtn.addEventListener('click', clearLogs);

function addLog(message, type = 'info') {
    const time = new Date().toLocaleTimeString();
    logs.unshift({ time, message, type });

    if (logs.length > 100) logs.pop();

    renderLogs();
}

function renderLogs() {
    if (logs.length === 0) {
        logContainer.innerHTML = '<p class="log-empty">Waiting for activity...</p>';
        return;
    }

    logContainer.innerHTML = logs.map(log => {
        const className = log.type === 'kill' ? 'log-kill' : log.type === 'success' ? 'log-success' : 'log-info';
        return `<div class="log-entry"><span class="log-time">[${log.time}]</span> <span class="${className}">${log.message}</span></div>`;
    }).join('');

    logContainer.scrollTop = 0;
}

function clearLogs() {
    logs = [];
    renderLogs();
}

function startMonitoring() {
    isRunning = true;
    startBtn.disabled = true;
    stopBtn.disabled = false;

    const status = document.querySelector('.status-card');
    status.classList.remove('status-stopped');
    status.classList.add('status-running');
    statusText.textContent = 'Running';

    const threshold = parseFloat(cpuThresholdInput.value);
    const interval = parseFloat(checkIntervalInput.value);

    addLog(`🟢 Started monitoring with ${threshold}% threshold`, 'info');

    monitorProcesses(threshold, interval);
}

function stopMonitoring() {
    isRunning = false;
    if (checkInterval) clearInterval(checkInterval);

    startBtn.disabled = false;
    stopBtn.disabled = true;

    const status = document.querySelector('.status-card');
    status.classList.remove('status-running');
    status.classList.add('status-stopped');
    statusText.textContent = 'Stopped';

    addLog('🔴 Monitoring stopped', 'info');
}

function monitorProcesses(threshold, interval) {
    // First check immediately
    checkAndKillHighCpuProcesses(threshold);

    // Then check at intervals
    checkInterval = setInterval(() => {
        if (isRunning) {
            checkAndKillHighCpuProcesses(threshold);
        }
    }, interval * 1000);
}

async function checkAndKillHighCpuProcesses(threshold) {
    try {
        const response = await fetch('/api/processes');
        const data = await response.json();

        const processes = data.processes || [];
        const highCpuProcesses = processes.filter(p => p.cpu_percent >= threshold);

        // Update stats
        document.getElementById('totalProcesses').textContent = processes.length;
        document.getElementById('highCpuCount').textContent = highCpuProcesses.length;

        // Update time
        statusTime.textContent = new Date().toLocaleTimeString();

        // Display all high CPU processes
        if (highCpuProcesses.length > 0) {
            processList.innerHTML = highCpuProcesses.map(p => `
                <div class="process-item">
                    <div class="process-info">
                        <div class="process-name">⚠️ ${p.name}</div>
                        <div class="process-details">
                            <span>PID: ${p.pid}</span>
                            <span class="process-cpu">CPU: ${p.cpu_percent.toFixed(2)}%</span>
                            <span>Memory: ${p.memory_mb.toFixed(2)} MB</span>
                        </div>
                    </div>
                </div>
            `).join('');

            // Auto-kill high CPU processes
            for (const proc of highCpuProcesses) {
                killProcess(proc.pid, proc.name, proc.cpu_percent);
            }
        } else {
            processList.innerHTML = '<p class="empty-message">All processes below threshold ✓</p>';
        }

    } catch (error) {
        addLog(`Error: ${error.message}`, 'info');
    }
}

async function killProcess(pid, name, cpu) {
    try {
        const response = await fetch(`/api/kill-process/${pid}`, {
            method: 'POST'
        });

        if (response.ok) {
            killedCount++;
            document.getElementById('killedCount').textContent = killedCount;
            addLog(`💀 Killed ${name} (PID: ${pid}, CPU: ${cpu.toFixed(2)}%)`, 'kill');
        } else {
            addLog(`Failed to kill ${name}`, 'info');
        }
    } catch (error) {
        addLog(`Error killing ${name}: ${error.message}`, 'info');
    }
}

// ===== MALWARE TESTING SECTION =====

let testSamples = {};

async function loadTestSamples() {
    try {
        const response = await fetch('/api/test-malware/samples', { timeout: 5000 });
        const data = await response.json();
        testSamples = data.samples;

        // Populate select dropdown
        const select = document.getElementById('sampleSelect');
        select.innerHTML = '<option value="">-- Choose a sample --</option>';
        Object.entries(testSamples).forEach(([id, sample]) => {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = `${sample.name} (${sample.severity})`;
            select.appendChild(option);
        });

        // Display sample cards
        displaySampleCards();

        addLog('Test samples loaded', 'success');
    } catch (error) {
        addLog(`Error loading samples: ${error.message}`, 'error');
    }
}

function displaySampleCards() {
    const container = document.getElementById('samplesList');
    container.innerHTML = '';

    Object.entries(testSamples).forEach(([id, sample]) => {
        const card = document.createElement('div');
        card.className = 'sample-card';
        card.onclick = () => selectSample(id);

        const severityClass = sample.severity.toLowerCase();

        card.innerHTML = `
            <div class="sample-card-name">${sample.name}</div>
            <div class="sample-card-behavior">${sample.behavior}</div>
            <span class="sample-card-severity ${severityClass}" style="background: ${getSeverityColor(sample.severity)}">${sample.severity}</span>
        `;

        container.appendChild(card);
    });
}

function getSeverityColor(severity) {
    const colors = {
        'LOW': '#86efac',
        'MEDIUM': '#fbbf24',
        'HIGH': '#f87171'
    };
    return colors[severity] || '#a78bfa';
}

function selectSample(sampleId) {
    const sample = testSamples[sampleId];
    if (!sample) return;

    document.getElementById('sampleSelect').value = sampleId;

    // Show sample info
    const infoDiv = document.getElementById('sampleInfo');
    document.getElementById('sampleName').textContent = sample.name;
    document.getElementById('sampleBehavior').textContent = sample.behavior;
    document.getElementById('sampleSeverity').textContent = sample.severity;
    document.getElementById('sampleSeverity').className = `severity-badge ${sample.severity.toLowerCase()}`;
    infoDiv.style.display = 'block';
}

async function runMalwareTest() {
    const sampleId = document.getElementById('sampleSelect').value;
    if (!sampleId) {
        addLog('Please select a test sample', 'error');
        return;
    }

    const runBtn = document.getElementById('runTestBtn');
    runBtn.disabled = true;
    runBtn.textContent = 'Running...';

    try {
        addLog(`Starting malware test: ${testSamples[sampleId].name}...`, 'info');

        const response = await fetch('/api/test-malware/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sample_id: sampleId,
                timeout: 30
            })
        });

        const data = await response.json();

        if (data.success) {
            // Display results
            document.getElementById('resultSandboxId').textContent = data.sandbox_id;
            document.getElementById('resultReturnCode').textContent = data.result.return_code;
            document.getElementById('resultCpu').textContent = `${data.result.resource_usage.cpu_percent}%`;
            document.getElementById('resultMemory').textContent = `${data.result.resource_usage.memory_mb}MB`;
            document.getElementById('resultProcesses').textContent = data.result.resource_usage.num_processes;
            document.getElementById('testResults').style.display = 'block';

            addLog(`✅ Test completed: ${data.sample.name} (Sandbox: ${data.sandbox_id})`, 'success');
        } else {
            addLog(`❌ Test failed: ${data.error}`, 'error');
        }
    } catch (error) {
        addLog(`Error running test: ${error.message}`, 'error');
    } finally {
        runBtn.disabled = false;
        runBtn.textContent = 'Run in Sandbox';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('.status-card').classList.add('status-stopped');
    addLog('SafeBox CPU Monitor started', 'success');

    // Load test samples
    loadTestSamples();

    // Malware testing event listeners
    document.getElementById('refreshSamplesBtn').addEventListener('click', loadTestSamples);
    document.getElementById('runTestBtn').addEventListener('click', runMalwareTest);
    document.getElementById('sampleSelect').addEventListener('change', (e) => {
        if (e.target.value) {
            selectSample(e.target.value);
        }
    });
});
