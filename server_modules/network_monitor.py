"""
Network Monitor Module
Real-time network monitoring with bandwidth tracking and connection analysis
"""
import psutil
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque, defaultdict
import socket
import subprocess
import json

class NetworkMonitor:
    """Monitor network activity, bandwidth, and connections"""
    
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.bandwidth_history = deque(maxlen=300)  # Keep 5 minutes of data (1 sample/sec)
        self.connection_history = deque(maxlen=100)  # Keep last 100 connection snapshots
        self.interface_stats = {}
        self.process_network_usage = defaultdict(lambda: {"bytes_sent": 0, "bytes_recv": 0})
        self.start_time = None
        self.last_stats = None
        
    def start_monitoring(self):
        """Start network monitoring"""
        if self.monitoring:
            return {"success": False, "message": "Network monitoring already running"}
        
        self.monitoring = True
        self.start_time = datetime.now()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        return {"success": True, "message": "Network monitoring started"}
    
    def stop_monitoring(self):
        """Stop network monitoring"""
        if not self.monitoring:
            return {"success": False, "message": "Network monitoring not running"}
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        return {"success": True, "message": "Network monitoring stopped"}
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Collect bandwidth data
                self._collect_bandwidth_data()
                
                # Collect connection data every 5 seconds
                if len(self.bandwidth_history) % 5 == 0:
                    self._collect_connection_data()
                
                time.sleep(1)  # Sample every second
                
            except Exception as e:
                print(f"Network monitor error: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _collect_bandwidth_data(self):
        """Collect bandwidth usage data"""
        try:
            # Get network I/O stats
            net_io = psutil.net_io_counters()
            current_time = datetime.now()
            
            if self.last_stats:
                # Calculate rates (bytes per second)
                time_diff = (current_time - self.last_stats['timestamp']).total_seconds()
                if time_diff > 0:
                    bytes_sent_rate = (net_io.bytes_sent - self.last_stats['bytes_sent']) / time_diff
                    bytes_recv_rate = (net_io.bytes_recv - self.last_stats['bytes_recv']) / time_diff
                    packets_sent_rate = (net_io.packets_sent - self.last_stats['packets_sent']) / time_diff
                    packets_recv_rate = (net_io.packets_recv - self.last_stats['packets_recv']) / time_diff
                else:
                    bytes_sent_rate = bytes_recv_rate = packets_sent_rate = packets_recv_rate = 0
            else:
                bytes_sent_rate = bytes_recv_rate = packets_sent_rate = packets_recv_rate = 0
            
            # Store bandwidth data
            bandwidth_data = {
                'timestamp': current_time.isoformat(),
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'bytes_sent_rate': bytes_sent_rate,
                'bytes_recv_rate': bytes_recv_rate,
                'packets_sent_rate': packets_sent_rate,
                'packets_recv_rate': packets_recv_rate,
                'total_rate': bytes_sent_rate + bytes_recv_rate
            }
            
            self.bandwidth_history.append(bandwidth_data)
            
            # Update last stats
            self.last_stats = {
                'timestamp': current_time,
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
            
        except Exception as e:
            print(f"Error collecting bandwidth data: {e}")
    
    def _collect_connection_data(self):
        """Collect network connection data"""
        try:
            connections = psutil.net_connections(kind='inet')
            connection_summary = {
                'timestamp': datetime.now().isoformat(),
                'total_connections': len(connections),
                'by_status': defaultdict(int),
                'by_type': defaultdict(int),
                'by_process': defaultdict(int),
                'remote_ips': set(),
                'local_ports': set(),
                'connections': []
            }
            
            for conn in connections:
                try:
                    # Count by status
                    connection_summary['by_status'][conn.status] += 1
                    
                    # Count by type (TCP/UDP)
                    conn_type = 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP'
                    connection_summary['by_type'][conn_type] += 1
                    
                    # Get process info
                    try:
                        if conn.pid:
                            process = psutil.Process(conn.pid)
                            process_name = process.name()
                            connection_summary['by_process'][process_name] += 1
                        else:
                            process_name = 'Unknown'
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        process_name = 'Unknown'
                    
                    # Collect IP addresses and ports
                    if conn.laddr:
                        connection_summary['local_ports'].add(conn.laddr.port)
                    
                    if conn.raddr:
                        connection_summary['remote_ips'].add(conn.raddr.ip)
                    
                    # Store detailed connection info (limit to important ones)
                    if conn.status in ['ESTABLISHED', 'LISTEN'] and len(connection_summary['connections']) < 50:
                        conn_info = {
                            'local_addr': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                            'remote_addr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                            'status': conn.status,
                            'type': conn_type,
                            'pid': conn.pid,
                            'process': process_name
                        }
                        connection_summary['connections'].append(conn_info)
                        
                except Exception as e:
                    continue
            
            # Convert sets to lists for JSON serialization
            connection_summary['remote_ips'] = list(connection_summary['remote_ips'])
            connection_summary['local_ports'] = list(connection_summary['local_ports'])
            connection_summary['by_status'] = dict(connection_summary['by_status'])
            connection_summary['by_type'] = dict(connection_summary['by_type'])
            connection_summary['by_process'] = dict(connection_summary['by_process'])
            
            self.connection_history.append(connection_summary)
            
        except Exception as e:
            print(f"Error collecting connection data: {e}")
    
    def get_current_bandwidth(self) -> Dict:
        """Get current bandwidth usage"""
        if not self.bandwidth_history:
            return {"success": False, "error": "No bandwidth data available"}
        
        latest = self.bandwidth_history[-1]
        
        return {
            "success": True,
            "timestamp": latest['timestamp'],
            "bytes_sent_rate": latest['bytes_sent_rate'],
            "bytes_recv_rate": latest['bytes_recv_rate'],
            "total_rate": latest['total_rate'],
            "bytes_sent_rate_mbps": latest['bytes_sent_rate'] * 8 / 1000000,  # Convert to Mbps
            "bytes_recv_rate_mbps": latest['bytes_recv_rate'] * 8 / 1000000,
            "total_rate_mbps": latest['total_rate'] * 8 / 1000000,
            "packets_sent_rate": latest['packets_sent_rate'],
            "packets_recv_rate": latest['packets_recv_rate']
        }
    
    def get_bandwidth_history(self, minutes: int = 5) -> Dict:
        """Get bandwidth history for specified minutes"""
        if not self.bandwidth_history:
            return {"success": False, "error": "No bandwidth data available"}
        
        # Calculate how many samples to include (1 sample per second)
        samples_needed = minutes * 60
        history_data = list(self.bandwidth_history)[-samples_needed:]
        
        return {
            "success": True,
            "history": history_data,
            "samples": len(history_data),
            "duration_minutes": minutes
        }
    
    def get_network_interfaces(self) -> Dict:
        """Get network interface information"""
        try:
            interfaces = {}
            
            # Get interface stats
            net_if_stats = psutil.net_if_stats()
            net_if_addrs = psutil.net_if_addrs()
            
            for interface_name, stats in net_if_stats.items():
                interface_info = {
                    'name': interface_name,
                    'is_up': stats.isup,
                    'duplex': stats.duplex,
                    'speed': stats.speed,  # Mbps
                    'mtu': stats.mtu,
                    'addresses': []
                }
                
                # Get addresses
                if interface_name in net_if_addrs:
                    for addr in net_if_addrs[interface_name]:
                        addr_info = {
                            'family': addr.family.name,
                            'address': addr.address
                        }
                        if addr.netmask:
                            addr_info['netmask'] = addr.netmask
                        if addr.broadcast:
                            addr_info['broadcast'] = addr.broadcast
                        
                        interface_info['addresses'].append(addr_info)
                
                interfaces[interface_name] = interface_info
            
            return {
                "success": True,
                "interfaces": interfaces,
                "count": len(interfaces)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_active_connections(self) -> Dict:
        """Get current active network connections"""
        if not self.connection_history:
            return {"success": False, "error": "No connection data available"}
        
        latest = self.connection_history[-1]
        
        return {
            "success": True,
            "timestamp": latest['timestamp'],
            "total_connections": latest['total_connections'],
            "by_status": latest['by_status'],
            "by_type": latest['by_type'],
            "by_process": latest['by_process'],
            "remote_ips": latest['remote_ips'],
            "local_ports": latest['local_ports'],
            "connections": latest['connections']
        }
    
    def get_network_summary(self) -> Dict:
        """Get comprehensive network summary"""
        try:
            # Get current stats
            net_io = psutil.net_io_counters()
            
            # Calculate uptime
            uptime_seconds = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            
            # Get interface info
            interfaces_result = self.get_network_interfaces()
            
            # Get current bandwidth
            bandwidth_result = self.get_current_bandwidth()
            
            # Get connections
            connections_result = self.get_active_connections()
            
            summary = {
                "success": True,
                "monitoring_active": self.monitoring,
                "uptime_seconds": uptime_seconds,
                "total_bytes_sent": net_io.bytes_sent,
                "total_bytes_recv": net_io.bytes_recv,
                "total_packets_sent": net_io.packets_sent,
                "total_packets_recv": net_io.packets_recv,
                "current_bandwidth": bandwidth_result if bandwidth_result["success"] else None,
                "active_connections": connections_result if connections_result["success"] else None,
                "interfaces": interfaces_result["interfaces"] if interfaces_result["success"] else {},
                "samples_collected": len(self.bandwidth_history)
            }
            
            return summary
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_top_network_processes(self, limit: int = 10) -> Dict:
        """Get processes with highest network usage"""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    # Get network connections for this process
                    connections = proc.net_connections()
                    
                    proc_info = {
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'connection_count': len(connections),
                        'established_connections': len([c for c in connections if c.status == 'ESTABLISHED']),
                        'listening_ports': len([c for c in connections if c.status == 'LISTEN'])
                    }
                    
                    if proc_info['connection_count'] > 0:
                        processes.append(proc_info)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort by connection count
            processes.sort(key=lambda x: x['connection_count'], reverse=True)
            
            return {
                "success": True,
                "processes": processes[:limit],
                "total_processes_with_connections": len(processes)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global network monitor instance
network_monitor = NetworkMonitor()