import psutil
import sys
from typing import List, Dict, Optional

def get_processes_list() -> List[Dict]:
    """Get detailed list of all running processes"""
    processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info', 'create_time']):
        try:
            info = proc.info
            processes.append({
                'pid': info['pid'],
                'name': info['name'],
                'username': info.get('username', 'Unknown'),
                'cpu_percent': info.get('cpu_percent', 0),
                'memory_mb': info['memory_info'].rss / (1024 * 1024) if info.get('memory_info') else 0,
                'create_time': info.get('create_time', 0)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return processes


def kill_process_by_pid(pid: int, force: bool = False) -> Dict:
    """
    Kill a specific process by PID
    
    Args:
        pid: Process ID to kill
        force: If True, use kill() instead of terminate()
    
    Returns:
        Dict with status and message
    """
    try:
        proc = psutil.Process(pid)
        process_name = proc.name()
        
        if force:
            proc.kill()
            action = "killed (forced)"
        else:
            proc.terminate()
            action = "terminated"
        
        # Wait up to 3 seconds for process to die
        try:
            proc.wait(timeout=3)
        except psutil.TimeoutExpired:
            # If it didn't die, force kill it
            proc.kill()
            action = "killed (forced after timeout)"
        
        return {
            "success": True,
            "pid": pid,
            "name": process_name,
            "action": action,
            "message": f"Process {process_name} (PID {pid}) {action}"
        }
        
    except psutil.NoSuchProcess:
        return {
            "success": False,
            "error": f"Process with PID {pid} not found",
            "pid": pid
        }
    except psutil.AccessDenied:
        return {
            "success": False,
            "error": f"Access denied to process {pid} (requires admin/root)",
            "pid": pid
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to kill PID {pid}: {str(e)}",
            "pid": pid
        }


def kill_process_by_name(name: str, force: bool = False, kill_all: bool = True) -> Dict:
    """
    Kill process(es) by name
    
    Args:
        name: Process name (e.g., "spotify.exe", "chrome.exe")
        force: If True, use kill() instead of terminate()
        kill_all: If True, kill all instances. If False, kill only first found.
    
    Returns:
        Dict with results for all matching processes
    """
    # Normalize name
    if not name.lower().endswith('.exe') and not '.' in name:
        name = f"{name}.exe"
    
    killed = []
    failed = []
    found_count = 0
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'].lower() == name.lower():
                found_count += 1
                result = kill_process_by_pid(proc.info['pid'], force=force)
                
                if result['success']:
                    killed.append(result)
                else:
                    failed.append(result)
                
                # If not kill_all, stop after first one
                if not kill_all and killed:
                    break
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if found_count == 0:
        return {
            "success": False,
            "error": f"No process named '{name}' found",
            "name": name,
            "killed_count": 0,
            "failed_count": 0
        }
    
    return {
        "success": len(killed) > 0,
        "name": name,
        "found_count": found_count,
        "killed_count": len(killed),
        "failed_count": len(failed),
        "killed": killed,
        "failed": failed,
        "message": f"Killed {len(killed)}/{found_count} instances of {name}"
    }


def kill_process_tree(pid: int) -> Dict:
    """
    Kill a process and all its children
    
    Args:
        pid: Parent process ID
    
    Returns:
        Dict with results
    """
    killed = []
    failed = []
    
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        
        # Kill children first
        for child in children:
            result = kill_process_by_pid(child.pid, force=False)
            if result['success']:
                killed.append(result)
            else:
                failed.append(result)
        
        # Then kill parent
        result = kill_process_by_pid(pid, force=False)
        if result['success']:
            killed.append(result)
        else:
            failed.append(result)
        
        return {
            "success": True,
            "killed_count": len(killed),
            "failed_count": len(failed),
            "killed": killed,
            "failed": failed,
            "message": f"Killed process tree: {len(killed)} processes"
        }
        
    except psutil.NoSuchProcess:
        return {
            "success": False,
            "error": f"Process {pid} not found"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def search_processes(query: str) -> List[Dict]:
    """
    Search for processes by name substring
    
    Args:
        query: Search string (case-insensitive)
    
    Returns:
        List of matching processes
    """
    query_lower = query.lower()
    matches = []
    
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info']):
        try:
            if query_lower in proc.info['name'].lower():
                matches.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'username': proc.info.get('username', 'Unknown'),
                    'cpu_percent': proc.info.get('cpu_percent', 0),
                    'memory_mb': proc.info['memory_info'].rss / (1024 * 1024) if proc.info.get('memory_info') else 0
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return matches


def get_process_instances(name: str) -> List[Dict]:
    """
    Get all instances of a specific process
    
    Args:
        name: Process name
    
    Returns:
        List of all matching process instances
    """
    if not name.lower().endswith('.exe') and not '.' in name:
        name = f"{name}.exe"
    
    instances = []
    
    for proc in psutil.process_iter(['pid', 'name', 'username', 'create_time', 'memory_info']):
        try:
            if proc.info['name'].lower() == name.lower():
                instances.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'username': proc.info.get('username', 'Unknown'),
                    'create_time': proc.info.get('create_time', 0),
                    'memory_mb': proc.info['memory_info'].rss / (1024 * 1024) if proc.info.get('memory_info') else 0
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return instances