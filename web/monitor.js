// SafeBox Dashboard - CPU Monitor + Malware Detection

let monitoring = false;
let monitoringInterval = null;
let killedProcesses = new Set();
let testSamples = {};
let detectionStats = {
    detected: 0,
    terminated: 0
};

// ===== LOGGING SYSTEM =====
function addLog(message, type = 'info') {
    const container = document.getElementById('logContainer');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    const timestamp = new Date().toLocaleTimeString();
    entry.textContent = `[${timestamp}] ${message}`;
    container.insertBefore(entry, container.firstChild);

    // Keep only last 50 logs
    while (container.children.length > 50) {
        container.removeChild(container.lastChild);
    }

    if (container.querySelector('.log-empty')) {
        container.querySelector('.log-empty').remove();
    }
}

// ===== SIDEBAR NAVIGATION =====
function initSidebar() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            const sectionId = item.dataset.section;

            // Remove active class from all
            navItems.forEach(nav => nav.classList.remove('active'));
            document.querySelectorAll('.section').forEach(sec => sec.classList.remove('active'));

            // Add active class to clicked
            item.classList.add('active');
            document.getElementById(sectionId).classList.add('active');

            addLog(`Navigated to ${sectionId}`, 'info');
        });
    });
}

// ===== CPU MONITORING =====
function startMonitoring() {
    if (monitoring) return;

    monitoring = true;
    document.getElementById('startBtn').disabled = true;
    document.getElementById('stopBtn').disabled = false;
    updateStatus(true);

    const threshold = parseInt(document.getElementById('cpuThreshold').value);
    const interval = parseFloat(document.getElementById('checkInterval').value) * 1000;

    addLog(`CPU monitoring started (Threshold: ${threshold}%, Interval: ${interval}ms)`, 'success');

    monitoringInterval = setInterval(() => {
        checkAndKillHighCpuProcesses(threshold);
    }, interval);

    // Initial check
    checkAndKillHighCpuProcesses(threshold);
}

function stopMonitoring() {
    if (!monitoring) return;

    monitoring = false;
    clearInterval(monitoringInterval);
    document.getElementById('startBtn').disabled = false;
    document.getElementById('stopBtn').disabled = true;
    updateStatus(false);

    addLog('CPU monitoring stopped', 'info');
}

function updateStatus(running) {
    const statusCard = document.querySelector('.status-card');
    const statusText = document.getElementById('statusText');
    const statusLabel = document.getElementById('statusLabel');
    const statusDot = document.getElementById('statusDot');

    if (running) {
        statusCard.classList.add('status-running');
        statusCard.classList.remove('status-stopped');
        statusText.textContent = '▶️ Running';
        statusLabel.textContent = 'Running';
        statusDot.classList.add('running');
    } else {
        statusCard.classList.remove('status-running');
        statusCard.classList.add('status-stopped');
        statusText.textContent = '⏹️ Stopped';
        statusLabel.textContent = 'Stopped';
        statusDot.classList.remove('running');
    }

    document.getElementById('statusTime').textContent = new Date().toLocaleTimeString();
}

async function checkAndKillHighCpuProcesses(threshold) {
    try {
        const response = await fetch('/api/processes');
        const data = await response.json();
        const processes = data.processes || [];

        document.getElementById('totalProcesses').textContent = processes.length;

        const highCpuProcesses = processes.filter(p => p.cpu_percent > threshold);
        document.getElementById('highCpuCount').textContent = highCpuProcesses.length;

        // Display process list
        const processList = document.getElementById('processList');
        processList.innerHTML = '';

        if (processes.length === 0) {
            processList.innerHTML = '<p class="empty-message">No processes found</p>';
            return;
        }

        // Show top 20 processes by CPU
        processes.slice(0, 20).forEach(proc => {
            const item = document.createElement('div');
            item.className = 'process-item';

            const isHighCpu = proc.cpu_percent > threshold;
            const color = isHighCpu ? 'color: #fca5a5' : 'color: #86efac';

            item.innerHTML = `
                <div>
                    <strong>${proc.name}</strong><br>
                    PID: ${proc.pid} | CPU: <span style="${color}">${proc.cpu_percent.toFixed(1)}%</span> | Memory: ${proc.memory_mb.toFixed(1)}MB
                </div>
                ${isHighCpu ? `<button class="btn btn-small" style="background: #ef4444" onclick="killProcess(${proc.pid}, '${proc.name}')">Kill</button>` : ''}
            `;
            processList.appendChild(item);
        });

        // Kill high CPU processes
        for (const proc of highCpuProcesses) {
            if (!killedProcesses.has(proc.pid)) {
                await killProcess(proc.pid, proc.name);
            }
        }

    } catch (error) {
        addLog(`Error checking processes: ${error.message}`, 'error');
    }
}

async function killProcess(pid, name) {
    try {
        const response = await fetch(`/api/kill-process/${pid}`, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            killedProcesses.add(pid);
            document.getElementById('killedCount').textContent = killedProcesses.size;
            addLog(`✅ Killed process: ${name} (PID: ${pid})`, 'success');

            // Also log as threat termination
            detectionStats.terminated++;
            document.getElementById('threatsTerminated').textContent = detectionStats.terminated;
        }
    } catch (error) {
        addLog(`Error killing ${name}: ${error.message}`, 'error');
    }
}

// ===== MALWARE DETECTION & AUTO-TERMINATION =====
async function scanForMalware() {
    if (!document.getElementById('autoDetect').checked) return;

    try {
        const response = await fetch('/api/processes');
        const data = await response.json();
        const processes = data.processes || [];

        // Simulate malware detection (in production, use signature database)
        for (const proc of processes) {
            const isMalicious = checkMaliciousBehavior(proc.name);

            if (isMalicious) {
                detectionStats.detected++;
                document.getElementById('threatsDetected').textContent = detectionStats.detected;

                // Auto-terminate
                await killProcess(proc.pid, proc.name);

                // Add to threats list
                displayThreat(proc.name, proc.pid, 'Malicious behavior detected');

                addLog(`🚨 THREAT DETECTED & TERMINATED: ${proc.name}`, 'error');
            }
        }

        updateDetectionRate();
    } catch (error) {
        console.error('Malware scan error:', error);
    }
}

function checkMaliciousBehavior(processName) {
    // Signature detection
    const signatures = [
        /^temp/i, /^tmp/i, /^malware/i, /^virus/i,
        /^trojan/i, /^ransomware/i, /^spyware/i,
        /^worm/i, /^botnet/i, /^rootkit/i
    ];

    return signatures.some(sig => sig.test(processName));
}

function displayThreat(name, pid, behavior) {
    const threatsList = document.getElementById('threatsList');

    if (threatsList.querySelector('.empty-message')) {
        threatsList.innerHTML = '';
    }

    const threatItem = document.createElement('div');
    threatItem.className = 'threat-item';
    threatItem.innerHTML = `
        <div>
            <strong style="color: #f87171">${name}</strong><br>
            <small>PID: ${pid}</small><br>
            <small style="color: #f87171">${behavior}</small>
        </div>
        <span style="color: #86efac; font-weight: 600">✓ Terminated</span>
    `;
    threatsList.insertBefore(threatItem, threatsList.firstChild);
}

function updateDetectionRate() {
    const total = detectionStats.detected || 1;
    const rate = Math.round((detectionStats.terminated / total) * 100);
    document.getElementById('detectionRate').textContent = `${rate}%`;
}

// ===== TEST SAMPLES MANAGEMENT =====
async function loadTestSamples() {
    try {
        const response = await fetch('/api/test-malware/samples');
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
            <span class="sample-card-severity" style="background: ${getSeverityColor(sample.severity)}">${sample.severity}</span>
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

// ===== KVM HYPERVISOR SANDBOX =====
async function initKVM() {
    try {
        const response = await fetch('/api/kvm/status');
        const data = await response.json();

        const statusElement = document.getElementById('kvmStatus');
        if (data.available) {
            statusElement.textContent = '✅ Online';
            statusElement.classList.add('available');
            statusElement.classList.remove('unavailable');
            addLog('KVM Hypervisor online', 'success');
        } else {
            statusElement.textContent = '❌ Offline';
            statusElement.classList.add('unavailable');
            statusElement.classList.remove('available');
            addLog('KVM not available (install with: sudo apt install qemu-kvm libvirt-daemon-system)', 'warning');
        }

        refreshKVMVMs();
        loadKVMMalwares();
    } catch (error) {
        addLog(`KVM initialization error: ${error.message}`, 'error');
        document.getElementById('kvmStatus').textContent = '❌ Error';
    }
}

async function refreshKVMVMs() {
    try {
        const response = await fetch('/api/kvm/vms');
        const data = await response.json();

        if (!data.success) {
            addLog(`Failed to refresh VMs: ${data.error}`, 'warning');
            return;
        }

        // Update VM counts
        const activeCount = data.vms.filter(vm => vm.state === 'running').length;
        document.getElementById('activeVMs').textContent = activeCount;
        document.getElementById('totalVMs').textContent = data.total_vms;

        // Populate VM list
        const vmsList = document.getElementById('vmsList');
        if (data.vms.length === 0) {
            vmsList.innerHTML = '<p class="empty-message">No VMs created yet</p>';
        } else {
            vmsList.innerHTML = '';
            data.vms.forEach(vm => {
                const vmCard = document.createElement('div');
                vmCard.className = 'vm-card';
                vmCard.innerHTML = `
                    <div class="vm-card-header">
                        <div class="vm-card-name">${vm.name}</div>
                        <div class="vm-card-state ${vm.state}">${vm.state.toUpperCase()}</div>
                    </div>
                    <div class="vm-card-details">
                        <div class="vm-detail-row">
                            <span class="vm-detail-label">CPU:</span>
                            <span class="vm-detail-value">${vm.vcpus} cores</span>
                        </div>
                        <div class="vm-detail-row">
                            <span class="vm-detail-label">Memory:</span>
                            <span class="vm-detail-value">${vm.memory_mb} MB</span>
                        </div>
                        <div class="vm-detail-row">
                            <span class="vm-detail-label">Uptime:</span>
                            <span class="vm-detail-value">${(vm.uptime / 60).toFixed(1)} min</span>
                        </div>
                    </div>
                    <div class="vm-card-actions">
                        ${vm.state === 'running' ?
                        `<button class="vm-action-btn danger" onclick="stopKVMVM('${vm.name}')">Stop</button>` :
                        `<button class="vm-action-btn" onclick="startKVMVM('${vm.name}')">Start</button>`
                    }
                        <button class="vm-action-btn danger" onclick="deleteKVMVM('${vm.name}')">Delete</button>
                    </div>
                `;
                vmsList.appendChild(vmCard);
            });
        }

        // Update VM selection dropdown
        const targetVmSelect = document.getElementById('targetVm');
        targetVmSelect.innerHTML = '';
        if (data.vms.length === 0) {
            targetVmSelect.innerHTML = '<option value="">-- No VMs available --</option>';
        } else {
            data.vms.forEach(vm => {
                const option = document.createElement('option');
                option.value = vm.name;
                option.textContent = `${vm.name} (${vm.state})`;
                targetVmSelect.appendChild(option);
            });
        }
    } catch (error) {
        addLog(`VM refresh error: ${error.message}`, 'error');
    }
}

async function createKVMVM() {
    try {
        const name = document.getElementById('vmName').value.trim();
        const cpus = parseInt(document.getElementById('vmCpus').value);
        const memory = parseInt(document.getElementById('vmMemory').value);

        if (!name) {
            addLog('VM name is required', 'warning');
            return;
        }

        addLog(`Creating KVM VM: ${name}...`, 'info');

        const response = await fetch('/api/kvm/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                vcpus: cpus,
                memory_mb: memory,
                disk_size_gb: 10,
                os_type: 'linux'
            })
        });

        const data = await response.json();
        if (data.success) {
            addLog(`✅ VM ${name} created successfully`, 'success');
            document.getElementById('vmName').value = `SafeBox-VM-${Date.now() % 1000}`;
            refreshKVMVMs();
        } else {
            addLog(`VM creation failed: ${data.error}`, 'error');
        }
    } catch (error) {
        addLog(`VM creation error: ${error.message}`, 'error');
    }
}

async function startKVMVM(vmName) {
    try {
        addLog(`Starting VM: ${vmName}...`, 'info');
        const response = await fetch(`/api/kvm/start/${vmName}`, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            addLog(`✅ VM ${vmName} started`, 'success');
            setTimeout(refreshKVMVMs, 1000);
        } else {
            addLog(`Failed to start VM: ${data.error}`, 'error');
        }
    } catch (error) {
        addLog(`VM start error: ${error.message}`, 'error');
    }
}

async function stopKVMVM(vmName) {
    try {
        addLog(`Stopping VM: ${vmName}...`, 'info');
        const response = await fetch(`/api/kvm/stop/${vmName}`, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            addLog(`✅ VM ${vmName} stopped`, 'success');
            setTimeout(refreshKVMVMs, 1000);
        } else {
            addLog(`Failed to stop VM: ${data.error}`, 'error');
        }
    } catch (error) {
        addLog(`VM stop error: ${error.message}`, 'error');
    }
}

async function deleteKVMVM(vmName) {
    if (!confirm(`Are you sure you want to delete VM "${vmName}"? This cannot be undone.`)) {
        return;
    }

    try {
        addLog(`Deleting VM: ${vmName}...`, 'info');
        const response = await fetch(`/api/kvm/delete/${vmName}`, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            addLog(`✅ VM ${vmName} deleted`, 'success');
            refreshKVMVMs();
        } else {
            addLog(`Failed to delete VM: ${data.error}`, 'error');
        }
    } catch (error) {
        addLog(`VM delete error: ${error.message}`, 'error');
    }
}

async function loadKVMMalwares() {
    try {
        const response = await fetch('/api/test-malware/samples');
        const data = await response.json();

        if (data.success && data.samples) {
            const select = document.getElementById('vmMalware');
            select.innerHTML = '';
            data.samples.forEach(sample => {
                const option = document.createElement('option');
                option.value = sample.name;
                option.textContent = `${sample.name} (${sample.severity})`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        addLog(`Failed to load malware samples: ${error.message}`, 'error');
    }
}

async function executeInKVM() {
    const vmName = document.getElementById('targetVm').value;
    const malwareName = document.getElementById('vmMalware').value;

    if (!vmName || !malwareName) {
        addLog('Select both VM and malware sample', 'warning');
        return;
    }

    try {
        addLog(`Executing ${malwareName} in ${vmName}...`, 'info');
        const response = await fetch('/api/kvm/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                vm_name: vmName,
                malware_name: malwareName
            })
        });

        const data = await response.json();
        if (data.success) {
            document.getElementById('vmExecVmName').textContent = data.vm_name;
            document.getElementById('vmExecMalwareName').textContent = data.malware_name;
            document.getElementById('vmExecDuration').textContent = `${data.duration_seconds.toFixed(2)}s`;
            document.getElementById('vmExecStatus').textContent = data.exit_code === 0 ? '✅ Success' : `❌ Exit Code: ${data.exit_code}`;
            document.getElementById('vmExecOutput').textContent = data.stdout || data.stderr || 'No output';
            document.getElementById('vmExecutionResults').style.display = 'block';

            addLog(`✅ Execution completed: ${malwareName} in ${vmName}`, 'success');
        } else {
            addLog(`Execution failed: ${data.error}`, 'error');
        }
    } catch (error) {
        addLog(`Execution error: ${error.message}`, 'error');
    }
}

// ===== EVENT LISTENERS =====
document.addEventListener('DOMContentLoaded', () => {
    // Initialize sidebar
    initSidebar();

    // CPU Monitor listeners
    document.getElementById('startBtn').addEventListener('click', startMonitoring);
    document.getElementById('stopBtn').addEventListener('click', stopMonitoring);
    document.getElementById('clearLogsBtn').addEventListener('click', () => {
        document.getElementById('logContainer').innerHTML = '<p class="log-empty">Waiting for activity...</p>';
    });

    // Malware detector listeners
    document.getElementById('autoDetect').addEventListener('change', () => {
        addLog('Auto-detection ' + (document.getElementById('autoDetect').checked ? 'enabled' : 'disabled'), 'info');
    });

    // Test samples listeners
    document.getElementById('refreshSamplesBtn').addEventListener('click', loadTestSamples);
    document.getElementById('runTestBtn').addEventListener('click', runMalwareTest);
    document.getElementById('sampleSelect').addEventListener('change', (e) => {
        if (e.target.value) {
            selectSample(e.target.value);
        }
    });

    // KVM listeners
    document.getElementById('createVmBtn').addEventListener('click', createKVMVM);
    document.getElementById('refreshVmBtn').addEventListener('click', refreshKVMVMs);
    document.getElementById('executeInVmBtn').addEventListener('click', executeInKVM);

    // Initial setup
    addLog('SafeBox Hypervisor Sandbox initialized', 'success');
    loadTestSamples();
    updateStatus(false);
    initKVM();

    // Continuous malware scanning
    setInterval(scanForMalware, 5000);

    // Refresh KVM status every 30 seconds
    setInterval(refreshKVMVMs, 30000);
});
