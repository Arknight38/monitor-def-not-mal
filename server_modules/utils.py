import socket
import subprocess

def get_local_ip():
    """Get the local IPv4 address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        pass
    
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        if local_ip.startswith('127.'):
            raise Exception("Got loopback")
        return local_ip
    except:
        pass
    
    return "0.0.0.0"

def get_all_local_ips():
    """Get all local IP addresses"""
    ips = []
    try:
        result = subprocess.run(['ipconfig'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        for line in lines:
            if 'IPv4 Address' in line or 'IPv4' in line:
                if ':' in line:
                    ip = line.split(':')[-1].strip()
                    ip = ip.replace('(Preferred)', '').strip()
                    if not ip.startswith('127.') and not ip.startswith('169.254.'):
                        if ip not in ips:
                            ips.append(ip)
    except:
        pass
    return ips