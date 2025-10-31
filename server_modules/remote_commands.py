import sys
import subprocess

def execute_remote_command(data, pc_id, log_event_func):
    """Execute remote command"""
    cmd_type = data.get('type')
    
    try:
        if cmd_type == 'shutdown':
            log_event_func("remote_command", {"type": "shutdown"}, pc_id)
            subprocess.Popen(['shutdown', '/s', '/t', '10'], shell=False)
            return {"status": "success", "message": "Shutdown initiated in 10 seconds"}
        
        elif cmd_type == 'restart':
            log_event_func("remote_command", {"type": "restart"}, pc_id)
            subprocess.Popen(['shutdown', '/r', '/t', '10'], shell=False)
            return {"status": "success", "message": "Restart initiated in 10 seconds"}
        
        elif cmd_type == 'launch':
            app_path = data.get('path')
            if not app_path or not isinstance(app_path, str):
                return ({"error": "Invalid application path"}, 400)
            
            log_event_func("remote_command", {"type": "launch", "path": app_path}, pc_id)
            
            try:
                process = subprocess.Popen(
                    app_path,
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
                )
                return {
                    "status": "success",
                    "message": f"Application launched",
                    "pid": process.pid
                }
            except Exception as e:
                return ({"error": f"Failed to launch application: {str(e)}"}, 500)
            
        elif cmd_type == 'shell':
            command = data.get('command')
            timeout = data.get('timeout', 30)
            
            if not command or not isinstance(command, str):
                return ({"error": "Invalid command"}, 400)
            
            try:
                timeout = int(timeout)
                if timeout < 1 or timeout > 300:
                    timeout = 30
            except:
                timeout = 30
                
            log_event_func("remote_command", {"type": "shell", "command": command}, pc_id)
            
            try:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                
                try:
                    stdout, stderr = process.communicate(timeout=timeout)
                    exit_code = process.returncode
                    
                    return {
                        "status": "success",
                        "exit_code": exit_code,
                        "stdout": stdout,
                        "stderr": stderr,
                        "returncode": exit_code
                    }
                    
                except subprocess.TimeoutExpired:
                    process.kill()
                    try:
                        stdout, stderr = process.communicate(timeout=2)
                    except:
                        stdout, stderr = "", ""
                    
                    return ({
                        "error": f"Command timed out after {timeout} seconds",
                        "stdout": stdout,
                        "stderr": stderr
                    }, 408)
                    
            except Exception as e:
                return ({"error": f"Command execution failed: {str(e)}"}, 500)
        
        else:
            return ({"error": f"Unknown command type: {cmd_type}"}, 400)
    
    except Exception as e:
        return ({"error": f"Command failed: {str(e)}"}, 500)