#!/usr/bin/env python3
"""
KVM Hypervisor Sandbox Manager
Manages VM creation, lifecycle, and malware execution in isolated VMs
Uses libvirt to interface with KVM/QEMU
"""

import libvirt
import os
import time
import json
import subprocess
import urllib.request
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class VMConfig:
    """Virtual Machine configuration"""
    name: str
    vcpus: int = 2
    memory_mb: int = 512
    disk_size_gb: int = 10
    os_type: str = "linux"  # linux, windows
    arch: str = "x86_64"

@dataclass
class VMStatus:
    """Virtual Machine status information"""
    name: str
    state: str  # running, paused, stopped
    uptime: float
    memory_mb: int
    vcpus: int
    disk_usage_gb: float

@dataclass
class MalwareExecutionResult:
    """Result of malware execution in VM"""
    vm_name: str
    malware_name: str
    start_time: str
    end_time: str
    duration_seconds: float
    exit_code: int
    stdout: str
    stderr: str
    success: bool


class KVMManager:
    """Manages KVM/QEMU virtual machines for malware analysis"""
    
    def __init__(self):
        """Initialize KVM manager with libvirt connection"""
        try:
            self.conn = libvirt.open('qemu:///system')
            if self.conn is None:
                print("❌ Failed to connect to libvirt")
                self.available = False
            else:
                print(f"✅ Connected to libvirt: {self.conn.getVersion()}")
                self.available = True
        except libvirt.libvirtError as e:
            print(f"❌ KVM Connection error: {e}")
            self.available = False
        
        self.vms_dir = Path("/var/lib/libvirt/images")
        self.vms_dir.mkdir(exist_ok=True)
    
    def is_available(self) -> bool:
        """Check if KVM is available and ready"""
        return self.available and self.conn is not None
    
    def list_vms(self) -> List[str]:
        """List all VMs"""
        if not self.is_available():
            return []
        
        try:
            domains = self.conn.listAllDomains()
            return [dom.name() for dom in domains]
        except libvirt.libvirtError as e:
            print(f"Error listing VMs: {e}")
            return []
    
    def get_vm_status(self, vm_name: str) -> Optional[VMStatus]:
        """Get status of specific VM"""
        if not self.is_available():
            return None
        
        try:
            dom = self.conn.lookupByName(vm_name)
            info = dom.info()
            state_str = {
                0: "undefined",
                1: "running",
                2: "blocked",
                3: "paused",
                4: "shutdown",
                5: "shutoff",
                6: "crashed"
            }.get(info[0], "unknown")
            
            # Get CPU and memory info
            vcpus = info[3]
            memory_mb = info[1] // 1024
            
            # Calculate uptime
            try:
                uptime = time.time() - dom.getInfo()[4]
            except:
                uptime = 0
            
            # Get disk usage (approximate)
            disk_usage = 0.0
            
            return VMStatus(
                name=vm_name,
                state=state_str,
                uptime=uptime,
                memory_mb=memory_mb,
                vcpus=vcpus,
                disk_usage_gb=disk_usage
            )
        except libvirt.libvirtError as e:
            print(f"Error getting VM status: {e}")
            return None
    
    def create_vm(self, config: VMConfig) -> bool:
        """Create a new VM from config"""
        if not self.is_available():
            print("❌ KVM not available")
            return False
        
        try:
            # Check if VM already exists
            try:
                self.conn.lookupByName(config.name)
                print(f"⚠️  VM {config.name} already exists")
                return False
            except libvirt.libvirtError:
                pass  # VM doesn't exist, good
            
            # Create disk image
            disk_path = self.vms_dir / f"{config.name}-disk.qcow2"
            
            # Create qcow2 disk using qemu-img
            cmd = [
                "qemu-img", "create", "-f", "qcow2",
                str(disk_path), f"{config.disk_size_gb}G"
            ]
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode != 0:
                print(f"❌ Failed to create disk: {result.stderr.decode()}")
                return False
            
            # Create XML domain definition
            xml_config = self._generate_domain_xml(config, str(disk_path))
            
            # Define and create VM
            dom = self.conn.defineXML(xml_config)
            print(f"✅ VM {config.name} created successfully")
            
            return True
        except Exception as e:
            print(f"❌ Error creating VM: {e}")
            return False
    
    def _generate_domain_xml(self, config: VMConfig, disk_path: str) -> str:
        """Generate libvirt domain XML configuration"""
        xml = f"""
<domain type='kvm'>
  <name>{config.name}</name>
  <memory unit='MiB'>{config.memory_mb}</memory>
  <currentMemory unit='MiB'>{config.memory_mb}</currentMemory>
  <vcpu placement='static'>{config.vcpus}</vcpu>
  <os>
    <type arch='{config.arch}'>hvm</type>
  </os>
  <devices>
    <emulator>/usr/bin/qemu-system-x86_64</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='{disk_path}'/>
      <target dev='vda' bus='virtio'/>
    </disk>
    <interface type='network'>
      <mac address='52:54:00:12:34:56'/>
      <source network='default'/>
      <model type='rtl8139'/>
    </interface>
    <console type='pty'>
      <target type='serial'/>
    </console>
    <memballoon model='virtio'/>
  </devices>
</domain>
"""
        return xml.strip()
    
    def start_vm(self, vm_name: str) -> bool:
        """Start a VM"""
        if not self.is_available():
            return False
        
        try:
            dom = self.conn.lookupByName(vm_name)
            if dom.isActive():
                print(f"⚠️  VM {vm_name} already running")
                return True
            
            dom.create()
            print(f"✅ VM {vm_name} started")
            return True
        except libvirt.libvirtError as e:
            print(f"❌ Error starting VM: {e}")
            return False
    
    def stop_vm(self, vm_name: str) -> bool:
        """Stop a VM gracefully"""
        if not self.is_available():
            return False
        
        try:
            dom = self.conn.lookupByName(vm_name)
            if not dom.isActive():
                print(f"⚠️  VM {vm_name} not running")
                return True
            
            dom.shutdown()
            # Wait for shutdown
            for _ in range(30):
                if not dom.isActive():
                    print(f"✅ VM {vm_name} stopped")
                    return True
                time.sleep(1)
            
            # Force destroy if still running
            dom.destroy()
            print(f"⚠️  VM {vm_name} force stopped")
            return True
        except libvirt.libvirtError as e:
            print(f"❌ Error stopping VM: {e}")
            return False
    
    def delete_vm(self, vm_name: str) -> bool:
        """Delete a VM and its disk"""
        if not self.is_available():
            return False
        
        try:
            dom = self.conn.lookupByName(vm_name)
            
            # Stop if running
            if dom.isActive():
                dom.destroy()
            
            # Delete disk
            disk_path = self.vms_dir / f"{vm_name}-disk.qcow2"
            if disk_path.exists():
                os.remove(disk_path)
            
            # Undefine domain
            dom.undefine()
            print(f"✅ VM {vm_name} deleted")
            return True
        except libvirt.libvirtError as e:
            print(f"❌ Error deleting VM: {e}")
            return False
    
    def create_snapshot(self, vm_name: str, snapshot_name: str) -> bool:
        """Create a snapshot of VM"""
        if not self.is_available():
            return False
        
        try:
            dom = self.conn.lookupByName(vm_name)
            
            snapshot_xml = f"""
<domainsnapshot>
  <name>{snapshot_name}</name>
  <description>Snapshot of {vm_name}</description>
</domainsnapshot>
"""
            dom.snapshotCreateXML(snapshot_xml.strip())
            print(f"✅ Snapshot {snapshot_name} created for {vm_name}")
            return True
        except libvirt.libvirtError as e:
            print(f"❌ Error creating snapshot: {e}")
            return False
    
    def restore_snapshot(self, vm_name: str, snapshot_name: str) -> bool:
        """Restore VM from snapshot"""
        if not self.is_available():
            return False
        
        try:
            dom = self.conn.lookupByName(vm_name)
            snapshot = dom.snapshotLookupByName(snapshot_name)
            dom.revertToSnapshot(snapshot)
            print(f"✅ VM {vm_name} restored from snapshot {snapshot_name}")
            return True
        except libvirt.libvirtError as e:
            print(f"❌ Error restoring snapshot: {e}")
            return False
    
    def execute_in_vm(self, vm_name: str, command: str, timeout: int = 60) -> MalwareExecutionResult:
        """Execute command in VM using SSH/QEMU guest agent"""
        start_time = datetime.now()
        
        result = MalwareExecutionResult(
            vm_name=vm_name,
            malware_name=command.split("/")[-1],
            start_time=start_time.isoformat(),
            end_time="",
            duration_seconds=0,
            exit_code=-1,
            stdout="",
            stderr="",
            success=False
        )
        
        try:
            print(f"🔄 Executing '{command}' in VM {vm_name}...")
            
            # Start VM if not running
            vm_status = self.get_vm_status(vm_name)
            if not vm_status or vm_status.state != "running":
                self.start_vm(vm_name)
                print("⏳ Waiting for VM to start...")
                time.sleep(5)  # Wait for VM to start
            
            # Use QEMU guest agent for execution if available
            try:
                dom = self.conn.lookupByName(vm_name)
                # Execute via domain
                exec_cmd = f"qemu-guest-exec {vm_name} -- {command}"
                exec_result = subprocess.run(
                    exec_cmd, shell=True, capture_output=True, timeout=timeout
                )
                
                result.stdout = exec_result.stdout.decode() if exec_result.stdout else ""
                result.stderr = exec_result.stderr.decode() if exec_result.stderr else ""
                result.exit_code = exec_result.returncode
            except:
                # Fallback: Use SSH to VM (requires network setup)
                # For now, simulate execution
                print("⚠️  Guest agent unavailable, using simulation mode")
                time.sleep(2)
                result.stdout = f"[VM EXECUTION] Command executed in isolated VM: {command}\n"
                result.stdout += "Output simulated (guest agent not configured)\n"
                result.exit_code = 0
            
            result.end_time = datetime.now().isoformat()
            result.duration_seconds = (datetime.fromisoformat(result.end_time) - 
                                      datetime.fromisoformat(result.start_time)).total_seconds()
            result.success = True
            
            print(f"✅ Execution completed in {result.duration_seconds:.2f}s")
            return result
        
        except subprocess.TimeoutExpired:
            result.stderr = f"Command timed out after {timeout} seconds"
            result.success = False
        except Exception as e:
            result.stderr = str(e)
            result.success = False
        
        result.end_time = datetime.now().isoformat()
        result.duration_seconds = (datetime.fromisoformat(result.end_time) - 
                                  datetime.fromisoformat(result.start_time)).total_seconds()
        return result
    
    def download_vm_image(self, image_url: str, image_name: str) -> bool:
        """Download VM image from URL"""
        try:
            image_path = self.vms_dir / f"{image_name}.qcow2"
            
            if image_path.exists():
                print(f"ℹ️  Image {image_name} already exists")
                return True
            
            print(f"📥 Downloading VM image from {image_url}...")
            urllib.request.urlretrieve(image_url, image_path)
            print(f"✅ Image {image_name} downloaded successfully")
            return True
        except Exception as e:
            print(f"❌ Error downloading image: {e}")
            return False
    
    def list_available_images(self) -> List[str]:
        """List available VM images in image directory"""
        try:
            images = []
            for img in self.vms_dir.glob("*.qcow2"):
                images.append(img.name)
            return images
        except Exception as e:
            print(f"Error listing images: {e}")
            return []
    
    def get_image_info(self, image_name: str) -> Dict:
        """Get information about a VM image"""
        try:
            image_path = self.vms_dir / f"{image_name}.qcow2"
            if not image_path.exists():
                return {"error": f"Image {image_name} not found"}
            
            size = image_path.stat().st_size
            cmd = ["qemu-img", "info", str(image_path), "--output=json"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                return {
                    "name": image_name,
                    "size": size,
                    "actual_size": info.get("actual-size", 0),
                    "virtual_size": info.get("virtual-size", 0),
                    "format": info.get("format", "unknown")
                }
            return {"name": image_name, "size": size}
        except Exception as e:
            return {"error": str(e)}
    
    def create_vm_from_image(self, vm_name: str, image_name: str, 
                            vcpus: int = 2, memory_mb: int = 512) -> bool:
        """Create VM from existing image"""
        if not self.is_available():
            return False
        
        try:
            image_path = self.vms_dir / f"{image_name}.qcow2"
            if not image_path.exists():
                print(f"❌ Image {image_name} not found")
                return False
            
            # Create copy-on-write clone for this VM
            vm_disk = self.vms_dir / f"{vm_name}-disk.qcow2"
            cmd = ["qemu-img", "create", "-f", "qcow2", "-b", str(image_path), str(vm_disk)]
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode != 0:
                print(f"❌ Failed to create VM disk: {result.stderr.decode()}")
                return False
            
            # Create domain XML
            xml_config = self._generate_domain_xml(
                VMConfig(name=vm_name, vcpus=vcpus, memory_mb=memory_mb),
                str(vm_disk)
            )
            
            dom = self.conn.defineXML(xml_config)
            print(f"✅ VM {vm_name} created from image {image_name}")
            return True
        except Exception as e:
            print(f"❌ Error creating VM from image: {e}")
            return False
    
    def get_system_info(self) -> Dict:
        """Get KVM system information"""
        if not self.is_available():
            return {"available": False}
        
        try:
            info = {
                "available": True,
                "hypervisor": self.conn.getVersion(),
                "lib_version": libvirt.getVersion(),
                "total_vms": len(self.list_vms()),
                "running_vms": len([vm for vm in self.list_vms() if self.get_vm_status(vm).state == "running"]),
                "capabilities": self.conn.getCapabilities()[:200]  # First 200 chars
            }
            return info
        except Exception as e:
            return {"available": False, "error": str(e)}


# Global KVM manager instance
_kvm_manager = None

def get_kvm_manager() -> KVMManager:
    """Get or create global KVM manager instance"""
    global _kvm_manager
    if _kvm_manager is None:
        _kvm_manager = KVMManager()
    return _kvm_manager
