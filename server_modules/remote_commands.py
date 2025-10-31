"""
Remote Commands Module - Fixed Version
Properly executes shell commands and system operations
"""
import sys
import os
import subprocess
import platform

def execute_remote_command(data, pc_id, log_event_func):
    """Execute remote command with proper error handling"""
    cmd_type = data.get('type')
    
    try:
        if cmd_type == 'shutdown':
            log_event_func("remote_command", {"type": "shutdown"}, pc_id)
            
            if platform.system() == 'Windows':
                subprocess.Popen(['shutdown', '/s', '/t', '10'], 
                               shell=False, 
                               creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(['shutdown', '-h', '+1'])
            
            return {"status": "success", "message": "Shutdown initiated in 10 seconds"}
        
        elif cmd_type == 'restart':
            log_event_func("remote_command", {"type": "restart"}, pc_id)
            
            if platform.system() == 'Windows':
                subprocess.Popen(['shutdown', '/r', '/t', '10'], 
                               shell=False,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(['shutdown', '-r', '+1'])
            
            return {"status": "success", "message": "Restart initiated in 10 seconds"}
        
        elif cmd_type == 'launch':
            app_path = data.get('path')
            if not app_path or not isinstance(app_path, str):
                return ({"error": "Invalid application path"}, 400)
            
            log_event_func("remote_command", {"type": "launch", "path": app_path}, pc_id)
            
            try:
                if platform.system() == 'Windows':
                    # Use START command for better Windows compatibility
                    process = subprocess.Popen(
                        f'start "" "{app_path}"',
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    process = subprocess.Popen(app_path, shell=True)
                
                return {
                    "status": "success",
                    "message": f"Application launched: {app_path}",
                    "pid": process.pid
                }
            except Exception as e:
                return ({"error": f"Failed to launch application: {str(e)}"}, 500)
            
        elif cmd_type == 'shell':
            command = data.get('command')
            timeout = data.get('timeout', 30)
            
            if not command or not isinstance(command, str):
                return ({"error": "Invalid command"}, 400)
            
            # Validate timeout
            try:
                timeout = int(timeout)
                if timeout < 1 or timeout > 300:
                    timeout = 30
            except:
                timeout = 30
            
            log_event_func("remote_command", {"type": "shell", "command": command}, pc_id)
            
            try:
                # Determine shell based on platform
                if platform.system() == 'Windows':
                    shell_cmd = ['cmd.exe', '/c', command]
                    creation_flags = subprocess.CREATE_NO_WINDOW
                else:
                    shell_cmd = ['/bin/bash', '-c', command]
                    creation_flags = 0
                
                # Execute command
                process = subprocess.Popen(
                    shell_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True,
                    creationflags=creation_flags if platform.system() == 'Windows' else 0
                )
                
                try:
                    stdout, stderr = process.communicate(timeout=timeout)
                    exit_code = process.returncode
                    
                    return {
                        "status": "success",
                        "exit_code": exit_code,
                        "stdout": stdout if stdout else "",
                        "stderr": stderr if stderr else "",
                        "command": command
                    }
                    
                except subprocess.TimeoutExpired:
                    # Kill process if timeout
                    process.kill()
                    try:
                        stdout, stderr = process.communicate(timeout=2)
                    except:
                        stdout, stderr = "", "Process killed (timeout)"
                    
                    return ({
                        "error": f"Command timed out after {timeout} seconds",
                        "stdout": stdout if stdout else "",
                        "stderr": stderr if stderr else "",
                        "command": command
                    }, 408)
                    
            except FileNotFoundError:
                return ({"error": "Shell not found or command invalid"}, 500)
            except Exception as e:
                return ({"error": f"Command execution failed: {str(e)}"}, 500)
        
        else:
            return ({"error": f"Unknown command type: {cmd_type}"}, 400)
    
    except Exception as e:
        return ({"error": f"Command handler failed: {str(e)}"}, 500)


def execute_powershell_command(command, timeout=30):
    """Execute PowerShell command (Windows only)"""
    if platform.system() != 'Windows':
        return {"error": "PowerShell only available on Windows"}, 400
    
    try:
        process = subprocess.Popen(
            ['powershell.exe', '-NoProfile', '-Command', command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        stdout, stderr = process.communicate(timeout=timeout)
        
        return {
            "status": "success",
            "exit_code": process.returncode,
            "stdout": stdout,
            "stderr": stderr
        }
    except subprocess.TimeoutExpired:
        process.kill()
        return {"error": f"PowerShell command timed out after {timeout}s"}, 408
    except Exception as e:
        return {"error": f"PowerShell execution failed: {str(e)}"}, 500