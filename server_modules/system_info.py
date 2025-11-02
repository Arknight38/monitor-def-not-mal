"""
System Information Collector
Comprehensive hardware specs and performance data collection
"""
import psutil
import platform
import socket
import subprocess
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Optional imports with fallbacks
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False
    wmi = None

try:
    import cpuinfo
    CPUINFO_AVAILABLE = True
except ImportError:
    CPUINFO_AVAILABLE = False
    cpuinfo = None

class SystemInfoCollector:
    """Collect comprehensive system information"""
    
    def __init__(self):
        self.wmi_available = WMI_AVAILABLE
        if self.wmi_available:
            try:
                self.wmi_conn = wmi.WMI()
            except Exception:
                self.wmi_available = False
                self.wmi_conn = None
        else:
            self.wmi_conn = None
    
    def get_basic_info(self) -> Dict:
        """Get basic system information"""
        try:
            # Platform information
            uname = platform.uname()
            
            basic_info = {
                "system": uname.system,
                "node_name": uname.node,
                "release": uname.release,
                "version": uname.version,
                "machine": uname.machine,
                "processor": uname.processor,
                "platform": platform.platform(),
                "architecture": platform.architecture(),
                "hostname": socket.gethostname(),
                "fqdn": socket.getfqdn(),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                "current_time": datetime.now().isoformat(),
                "timezone": str(datetime.now().astimezone().tzinfo)
            }
            
            # User information
            try:
                basic_info["current_user"] = os.getlogin()
            except:
                basic_info["current_user"] = os.environ.get('USERNAME', 'Unknown')
            
            # Windows specific information
            if platform.system().lower() == 'windows':
                try:
                    basic_info["windows_edition"] = platform.win32_edition()
                    basic_info["windows_version"] = platform.win32_ver()
                except:
                    pass
            
            return {"success": True, "basic_info": basic_info}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_cpu_info(self) -> Dict:
        """Get detailed CPU information"""
        try:
            cpu_info = {
                "physical_cores": psutil.cpu_count(logical=False),
                "logical_cores": psutil.cpu_count(logical=True),
                "current_frequency": psutil.cpu_freq().current if psutil.cpu_freq() else None,
                "min_frequency": psutil.cpu_freq().min if psutil.cpu_freq() else None,
                "max_frequency": psutil.cpu_freq().max if psutil.cpu_freq() else None,
                "cpu_percent": psutil.cpu_percent(interval=1),
                "cpu_percent_per_core": psutil.cpu_percent(interval=1, percpu=True),
                "cpu_times": psutil.cpu_times()._asdict(),
                "cpu_stats": psutil.cpu_stats()._asdict()
            }
            
            # Get detailed CPU info using cpuinfo library
            if CPUINFO_AVAILABLE:
                try:
                    detailed_cpu = cpuinfo.get_cpu_info()
                    cpu_info.update({
                        "brand": detailed_cpu.get('brand_raw', ''),
                        "vendor": detailed_cpu.get('vendor_id_raw', ''),
                        "family": detailed_cpu.get('family', ''),
                        "model": detailed_cpu.get('model', ''),
                        "stepping": detailed_cpu.get('stepping', ''),
                        "flags": detailed_cpu.get('flags', []),
                        "hz_advertised": detailed_cpu.get('hz_advertised_friendly', ''),
                        "hz_actual": detailed_cpu.get('hz_actual_friendly', ''),
                        "cache_size_l1": detailed_cpu.get('l1_data_cache_size', ''),
                        "cache_size_l2": detailed_cpu.get('l2_cache_size', ''),
                        "cache_size_l3": detailed_cpu.get('l3_cache_size', '')
                    })
                except Exception:
                    pass
            
            # WMI CPU information (Windows only)
            if self.wmi_available:
                try:
                    for processor in self.wmi_conn.Win32_Processor():
                        cpu_info.update({
                            "name": processor.Name,
                            "manufacturer": processor.Manufacturer,
                            "description": processor.Description,
                            "max_clock_speed": processor.MaxClockSpeed,
                            "current_clock_speed": processor.CurrentClockSpeed,
                            "socket_designation": processor.SocketDesignation,
                            "voltage": processor.CurrentVoltage,
                            "external_clock": processor.ExtClock,
                            "l2_cache_size": processor.L2CacheSize,
                            "l3_cache_size": processor.L3CacheSize
                        })
                        break  # Take first processor
                except Exception:
                    pass
            
            return {"success": True, "cpu_info": cpu_info}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_memory_info(self) -> Dict:
        """Get detailed memory information"""
        try:
            # Virtual memory
            vmem = psutil.virtual_memory()
            memory_info = {
                "total": vmem.total,
                "available": vmem.available,
                "used": vmem.used,
                "free": vmem.free,
                "percent": vmem.percent,
                "active": getattr(vmem, 'active', None),
                "inactive": getattr(vmem, 'inactive', None),
                "buffers": getattr(vmem, 'buffers', None),
                "cached": getattr(vmem, 'cached', None),
                "shared": getattr(vmem, 'shared', None)
            }
            
            # Swap memory
            swap = psutil.swap_memory()
            memory_info["swap"] = {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent": swap.percent,
                "sin": swap.sin,
                "sout": swap.sout
            }
            
            # WMI memory information (Windows only)
            if self.wmi_available:
                try:
                    memory_modules = []
                    for memory in self.wmi_conn.Win32_PhysicalMemory():
                        module_info = {
                            "capacity": int(memory.Capacity) if memory.Capacity else None,
                            "speed": memory.Speed,
                            "manufacturer": memory.Manufacturer,
                            "part_number": memory.PartNumber,
                            "serial_number": memory.SerialNumber,
                            "memory_type": memory.MemoryType,
                            "form_factor": memory.FormFactor,
                            "device_locator": memory.DeviceLocator,
                            "bank_label": memory.BankLabel
                        }
                        memory_modules.append(module_info)
                    
                    memory_info["physical_modules"] = memory_modules
                    memory_info["total_physical_slots"] = len(memory_modules)
                except Exception:
                    pass
            
            return {"success": True, "memory_info": memory_info}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_disk_info(self) -> Dict:
        """Get detailed disk information"""
        try:
            disk_info = {
                "partitions": [],
                "disk_usage": {},
                "disk_io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
            }
            
            # Partition information
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partition_info = {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "opts": partition.opts,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": (usage.used / usage.total) * 100 if usage.total > 0 else 0
                    }
                    disk_info["partitions"].append(partition_info)
                    disk_info["disk_usage"][partition.device] = partition_info
                except PermissionError:
                    continue
            
            # Per-disk I/O statistics
            try:
                disk_io_per_disk = psutil.disk_io_counters(perdisk=True)
                disk_info["disk_io_per_disk"] = {k: v._asdict() for k, v in disk_io_per_disk.items()}
            except Exception:
                pass
            
            # WMI disk information (Windows only)
            if self.wmi_available:
                try:
                    physical_disks = []
                    for disk in self.wmi_conn.Win32_DiskDrive():
                        disk_details = {
                            "model": disk.Model,
                            "size": int(disk.Size) if disk.Size else None,
                            "interface_type": disk.InterfaceType,
                            "media_type": disk.MediaType,
                            "serial_number": disk.SerialNumber,
                            "firmware_revision": disk.FirmwareRevision,
                            "partitions": disk.Partitions,
                            "status": disk.Status
                        }
                        physical_disks.append(disk_details)
                    
                    disk_info["physical_disks"] = physical_disks
                except Exception:
                    pass
            
            return {"success": True, "disk_info": disk_info}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_network_info(self) -> Dict:
        """Get network interface information"""
        try:
            network_info = {
                "interfaces": {},
                "io_counters": {}
            }
            
            # Network interface addresses and stats
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            
            for interface_name in net_if_addrs:
                interface_info = {
                    "addresses": [],
                    "stats": {}
                }
                
                # Get addresses
                for addr in net_if_addrs[interface_name]:
                    addr_info = {
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast,
                        "ptp": addr.ptp
                    }
                    interface_info["addresses"].append(addr_info)
                
                # Get stats
                if interface_name in net_if_stats:
                    stats = net_if_stats[interface_name]
                    interface_info["stats"] = {
                        "isup": stats.isup,
                        "duplex": stats.duplex,
                        "speed": stats.speed,
                        "mtu": stats.mtu
                    }
                
                network_info["interfaces"][interface_name] = interface_info
            
            # Network I/O counters
            try:
                net_io = psutil.net_io_counters(pernic=True)
                network_info["io_counters"] = {k: v._asdict() for k, v in net_io.items()}
            except Exception:
                pass
            
            return {"success": True, "network_info": network_info}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_process_info(self) -> Dict:
        """Get running process information"""
        try:
            processes = []
            total_memory = 0
            total_cpu = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                           'memory_info', 'create_time', 'status', 'num_threads']):
                try:
                    proc_info = proc.info.copy()
                    proc_info['create_time'] = datetime.fromtimestamp(proc_info['create_time']).isoformat()
                    proc_info['memory_mb'] = proc_info['memory_info'].rss / 1024 / 1024
                    
                    total_memory += proc_info['memory_percent'] or 0
                    total_cpu += proc_info['cpu_percent'] or 0
                    
                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            process_info = {
                "total_processes": len(processes),
                "top_processes": processes[:20],  # Top 20 processes
                "total_cpu_percent": total_cpu,
                "total_memory_percent": total_memory
            }
            
            return {"success": True, "process_info": process_info}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_gpu_info(self) -> Dict:
        """Get GPU information (Windows WMI)"""
        gpu_info = {"gpus": []}
        
        if not self.wmi_available:
            return {"success": False, "error": "WMI not available"}
        
        try:
            for gpu in self.wmi_conn.Win32_VideoController():
                gpu_details = {
                    "name": gpu.Name,
                    "adapter_ram": int(gpu.AdapterRAM) if gpu.AdapterRAM else None,
                    "driver_version": gpu.DriverVersion,
                    "driver_date": gpu.DriverDate,
                    "video_processor": gpu.VideoProcessor,
                    "video_memory_type": gpu.VideoMemoryType,
                    "current_horizontal_resolution": gpu.CurrentHorizontalResolution,
                    "current_vertical_resolution": gpu.CurrentVerticalResolution,
                    "current_refresh_rate": gpu.CurrentRefreshRate,
                    "min_refresh_rate": gpu.MinRefreshRate,
                    "max_refresh_rate": gpu.MaxRefreshRate,
                    "status": gpu.Status
                }
                gpu_info["gpus"].append(gpu_details)
            
            return {"success": True, "gpu_info": gpu_info}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_motherboard_info(self) -> Dict:
        """Get motherboard information (Windows WMI)"""
        if not self.wmi_available:
            return {"success": False, "error": "WMI not available"}
        
        try:
            for board in self.wmi_conn.Win32_BaseBoard():
                motherboard_info = {
                    "manufacturer": board.Manufacturer,
                    "product": board.Product,
                    "version": board.Version,
                    "serial_number": board.SerialNumber
                }
                
                # Get BIOS information
                for bios in self.wmi_conn.Win32_BIOS():
                    motherboard_info.update({
                        "bios_manufacturer": bios.Manufacturer,
                        "bios_version": bios.Version,
                        "bios_release_date": bios.ReleaseDate,
                        "bios_serial_number": bios.SerialNumber
                    })
                    break
                
                return {"success": True, "motherboard_info": motherboard_info}
            
            return {"success": False, "error": "No motherboard information found"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        try:
            # CPU usage over 5 seconds
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
            
            # Memory usage
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            
            # Network I/O
            net_io = psutil.net_io_counters()
            
            # Load average (Unix-like systems)
            load_avg = None
            try:
                load_avg = os.getloadavg()
            except:
                pass
            
            performance = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "per_core": cpu_per_core,
                    "load_avg": load_avg
                },
                "memory": {
                    "percent": memory.percent,
                    "used_gb": memory.used / 1024**3,
                    "available_gb": memory.available / 1024**3,
                    "total_gb": memory.total / 1024**3
                },
                "swap": {
                    "percent": swap.percent,
                    "used_gb": swap.used / 1024**3,
                    "total_gb": swap.total / 1024**3
                },
                "disk_io": {
                    "read_bytes": disk_io.read_bytes if disk_io else 0,
                    "write_bytes": disk_io.write_bytes if disk_io else 0,
                    "read_count": disk_io.read_count if disk_io else 0,
                    "write_count": disk_io.write_count if disk_io else 0
                },
                "network_io": {
                    "bytes_sent": net_io.bytes_sent if net_io else 0,
                    "bytes_recv": net_io.bytes_recv if net_io else 0,
                    "packets_sent": net_io.packets_sent if net_io else 0,
                    "packets_recv": net_io.packets_recv if net_io else 0
                }
            }
            
            return {"success": True, "performance": performance}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_complete_system_info(self) -> Dict:
        """Get complete comprehensive system information"""
        try:
            complete_info = {
                "collection_time": datetime.now().isoformat(),
                "basic_info": self.get_basic_info(),
                "cpu_info": self.get_cpu_info(),
                "memory_info": self.get_memory_info(),
                "disk_info": self.get_disk_info(),
                "network_info": self.get_network_info(),
                "process_info": self.get_process_info(),
                "gpu_info": self.get_gpu_info(),
                "motherboard_info": self.get_motherboard_info(),
                "performance_metrics": self.get_performance_metrics()
            }
            
            return {"success": True, "system_info": complete_info}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global system info collector instance
system_collector = SystemInfoCollector()