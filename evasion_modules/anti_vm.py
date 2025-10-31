import os
import platform

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

def check_vm_vendor_strings():
    """Check for VM vendor identifiers"""
    vm_indicators = ['VBOX', 'VirtualBox', 'VMware', 'QEMU', 'Xen', 'Hyper-V']
    
    # Check computer name
    computer_name = os.environ.get('COMPUTERNAME', '').upper()
    for indicator in vm_indicators:
        if indicator.upper() in computer_name:
            return True
    
    # Check system info
    try:
        system_info = platform.uname()
        system_str = ' '.join([system_info.system, system_info.node, 
                               system_info.release, system_info.version, 
                               system_info.machine]).upper()
        
        for indicator in vm_indicators:
            if indicator.upper() in system_str:
                return True
    except:
        pass
    
    return False

def check_vm_processes():
    """Check for VM-specific processes"""
    if not PSUTIL_AVAILABLE:
        return False
    
    vm_processes = [
        'vboxservice.exe', 'vboxtray.exe', 'vmtoolsd.exe', 
        'vmwaretray.exe', 'vmwareuser.exe', 'qemu-ga.exe'
    ]
    
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and proc.info['name'].lower() in vm_processes:
                return True
    except:
        pass
    
    return False

def check_vm_files():
    """Check for VM-specific files"""
    vm_files = [
        'C:\\Program Files\\VMware\\VMware Tools\\',
        'C:\\Program Files\\Oracle\\VirtualBox Guest Additions\\',
        'C:\\Windows\\System32\\drivers\\vboxguest.sys',
        'C:\\Windows\\System32\\drivers\\vmhgfs.sys'
    ]
    
    for path in vm_files:
        if os.path.exists(path):
            return True
    
    return False

def check_low_resources():
    """Check for suspiciously low resources (VM sandbox)"""
    if not PSUTIL_AVAILABLE:
        return False
    
    try:
        # Check CPU count
        if psutil.cpu_count() < 2:
            return True
        
        # Check RAM
        total_ram_gb = psutil.virtual_memory().total / (1024**3)
        if total_ram_gb < 4:
            return True
        
        # Check disk size
        disk = psutil.disk_usage('C:\\')
        disk_size_gb = disk.total / (1024**3)
        if disk_size_gb < 60:
            return True
    except:
        pass
    
    return False

def perform_vm_checks():
    """Perform all VM detection checks"""
    checks_failed = []
    
    if check_vm_vendor_strings():
        checks_failed.append("VM vendor string detected")
    
    if check_vm_processes():
        checks_failed.append("VM process detected")
    
    if check_vm_files():
        checks_failed.append("VM files detected")
    
    if check_low_resources():
        checks_failed.append("Low resources (possible VM)")
    
    return checks_failed