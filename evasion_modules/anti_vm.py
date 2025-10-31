"""
Anti-VM Detection (Educational Demo)
Demonstrates awareness of virtualized environments
"""
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
            return indicator
    
    # Check system info
    try:
        system_info = platform.uname()
        system_str = ' '.join([system_info.system, system_info.node, 
                               system_info.release, system_info.version, 
                               system_info.machine]).upper()
        
        for indicator in vm_indicators:
            if indicator.upper() in system_str:
                return indicator
    except:
        pass
    
    return None

def check_vm_processes():
    """Check for VM-specific processes"""
    if not PSUTIL_AVAILABLE:
        return None
    
    vm_processes = {
        'vboxservice.exe': 'VirtualBox',
        'vboxtray.exe': 'VirtualBox',
        'vmtoolsd.exe': 'VMware',
        'vmwaretray.exe': 'VMware',
        'vmwareuser.exe': 'VMware',
        'qemu-ga.exe': 'QEMU'
    }
    
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and proc.info['name'].lower() in vm_processes:
                return vm_processes[proc.info['name'].lower()]
    except:
        pass
    
    return None

def check_vm_files():
    """Check for VM-specific files"""
    vm_files = {
        'C:\\Program Files\\VMware\\VMware Tools\\': 'VMware',
        'C:\\Program Files\\Oracle\\VirtualBox Guest Additions\\': 'VirtualBox',
        'C:\\Windows\\System32\\drivers\\vboxguest.sys': 'VirtualBox',
        'C:\\Windows\\System32\\drivers\\vmhgfs.sys': 'VMware'
    }
    
    for path, vendor in vm_files.items():
        if os.path.exists(path):
            return vendor
    
    return None

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

def check_virtual_environment():
    """
    Perform all VM detection checks
    Returns dict with results
    """
    results = {
        'is_virtual': False,
        'vendor': None,
        'vendor_string': False,
        'vm_process': False,
        'vm_files': False,
        'low_resources': False
    }
    
    vendor = check_vm_vendor_strings()
    if vendor:
        results['vendor_string'] = True
        results['is_virtual'] = True
        results['vendor'] = vendor
    
    vendor = check_vm_processes()
    if vendor:
        results['vm_process'] = True
        results['is_virtual'] = True
        if not results['vendor']:
            results['vendor'] = vendor
    
    vendor = check_vm_files()
    if vendor:
        results['vm_files'] = True
        results['is_virtual'] = True
        if not results['vendor']:
            results['vendor'] = vendor
    
    if check_low_resources():
        results['low_resources'] = True
    
    return results