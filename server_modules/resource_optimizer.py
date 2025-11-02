"""
Resource Optimization Module
Reduces CPU/memory footprint and optimizes system performance
"""
import psutil
import threading
import time
import gc
import sys
import os
from collections import deque
import logging

class ResourceOptimizer:
    """Optimizes resource usage for better performance"""
    
    def __init__(self, target_cpu_limit=20, target_memory_limit=100):  # MB
        self.target_cpu_limit = target_cpu_limit  # Percentage
        self.target_memory_limit = target_memory_limit  # MB
        
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Performance metrics
        self.cpu_history = deque(maxlen=60)  # Last 60 readings
        self.memory_history = deque(maxlen=60)
        
        # Optimization settings
        self.sleep_intervals = {
            'idle': 1.0,      # When system is idle
            'normal': 0.5,    # Normal operation
            'high_load': 0.1  # High CPU/memory usage
        }
        
        self.current_mode = 'normal'
        self.logger = logging.getLogger('ResourceOptimizer')
        
        # Cache for expensive operations
        self._system_info_cache = {}
        self._cache_timeout = 30  # seconds
        
    def start_optimization(self):
        """Start resource optimization monitoring"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
            self.monitor_thread.start()
            self.logger.info("Resource optimization started")
            
            # Initial optimizations
            self._optimize_python_settings()
            self._optimize_memory()
    
    def stop_optimization(self):
        """Stop resource optimization"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Resource optimization stopped")
    
    def _monitor_resources(self):
        """Monitor and optimize resource usage"""
        while self.is_monitoring:
            try:
                # Get current usage
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_info = psutil.Process().memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                
                # Update history
                self.cpu_history.append(cpu_percent)
                self.memory_history.append(memory_mb)
                
                # Determine current mode
                self._update_operation_mode(cpu_percent, memory_mb)
                
                # Apply optimizations based on current usage
                if memory_mb > self.target_memory_limit:
                    self._optimize_memory()
                
                if cpu_percent > self.target_cpu_limit:
                    self._optimize_cpu_usage()
                
                # Clean up old cache entries
                self._cleanup_cache()
                
                # Adaptive sleep based on current mode
                time.sleep(self.sleep_intervals[self.current_mode])
                
            except Exception as e:
                self.logger.error(f"Resource monitoring error: {e}")
                time.sleep(5)
    
    def _update_operation_mode(self, cpu_percent, memory_mb):
        """Update operation mode based on resource usage"""
        if cpu_percent < 5 and memory_mb < self.target_memory_limit * 0.5:
            self.current_mode = 'idle'
        elif cpu_percent > 50 or memory_mb > self.target_memory_limit * 1.5:
            self.current_mode = 'high_load'
        else:
            self.current_mode = 'normal'
    
    def _optimize_python_settings(self):
        """Optimize Python runtime settings"""
        try:
            # Optimize garbage collection
            gc.set_threshold(700, 10, 10)  # More aggressive GC
            
            # Reduce thread stack size if possible
            if hasattr(threading, 'stack_size'):
                threading.stack_size(262144)  # 256KB instead of default 1MB
            
            # Optimize import system
            sys.dont_write_bytecode = True
            
            self.logger.info("Python runtime optimizations applied")
            
        except Exception as e:
            self.logger.warning(f"Could not apply all Python optimizations: {e}")
    
    def _optimize_memory(self):
        """Optimize memory usage"""
        try:
            # Force garbage collection
            collected = gc.collect()
            
            # Clear system info cache if it's getting large
            if len(self._system_info_cache) > 50:
                self._system_info_cache.clear()
            
            # Trim history if too long
            if len(self.cpu_history) > 60:
                self.cpu_history = deque(list(self.cpu_history)[-30:], maxlen=60)
            if len(self.memory_history) > 60:
                self.memory_history = deque(list(self.memory_history)[-30:], maxlen=60)
            
            if collected > 0:
                self.logger.debug(f"Freed {collected} objects from memory")
                
        except Exception as e:
            self.logger.error(f"Memory optimization error: {e}")
    
    def _optimize_cpu_usage(self):
        """Optimize CPU usage when high"""
        try:
            # Reduce thread priority for non-critical operations
            if hasattr(os, 'nice'):
                try:
                    os.nice(1)  # Lower priority slightly
                except PermissionError:
                    pass
            
            # Force a small sleep to yield CPU
            time.sleep(0.01)
            
            self.logger.debug("Applied CPU usage optimizations")
            
        except Exception as e:
            self.logger.error(f"CPU optimization error: {e}")
    
    def _cleanup_cache(self):
        """Clean up expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, (value, timestamp) in self._system_info_cache.items()
            if current_time - timestamp > self._cache_timeout
        ]
        
        for key in expired_keys:
            del self._system_info_cache[key]
    
    def get_cached_or_compute(self, key, compute_func, *args, **kwargs):
        """Get cached value or compute and cache it"""
        current_time = time.time()
        
        if key in self._system_info_cache:
            value, timestamp = self._system_info_cache[key]
            if current_time - timestamp < self._cache_timeout:
                return value
        
        # Compute new value
        try:
            value = compute_func(*args, **kwargs)
            self._system_info_cache[key] = (value, current_time)
            return value
        except Exception as e:
            self.logger.error(f"Error computing cached value for {key}: {e}")
            return None
    
    def get_resource_stats(self):
        """Get current resource statistics"""
        try:
            process = psutil.Process()
            
            return {
                'cpu_percent': process.cpu_percent(),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'memory_percent': process.memory_percent(),
                'thread_count': process.num_threads(),
                'open_files': len(process.open_files()),
                'connections': len(process.connections()),
                'current_mode': self.current_mode,
                'cpu_avg': sum(self.cpu_history) / len(self.cpu_history) if self.cpu_history else 0,
                'memory_avg': sum(self.memory_history) / len(self.memory_history) if self.memory_history else 0,
                'cache_size': len(self._system_info_cache)
            }
        except Exception as e:
            self.logger.error(f"Error getting resource stats: {e}")
            return {}
    
    def optimize_for_background(self):
        """Optimize settings for background operation"""
        self.target_cpu_limit = 10  # Lower CPU limit
        self.sleep_intervals = {
            'idle': 2.0,      # Longer idle sleep
            'normal': 1.0,    # Longer normal sleep
            'high_load': 0.5  # Still responsive for high load
        }
        self.logger.info("Optimized for background operation")
    
    def optimize_for_active(self):
        """Optimize settings for active monitoring"""
        self.target_cpu_limit = 30  # Higher CPU limit allowed
        self.sleep_intervals = {
            'idle': 0.5,      # Shorter idle sleep
            'normal': 0.2,    # Shorter normal sleep
            'high_load': 0.1  # Very responsive
        }
        self.logger.info("Optimized for active monitoring")


class MemoryManager:
    """Advanced memory management utilities"""
    
    @staticmethod
    def limit_memory_usage(max_memory_mb=150):
        """Limit memory usage of current process"""
        try:
            import resource
            max_memory_bytes = max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))
            return True
        except (ImportError, AttributeError):
            # Windows doesn't support resource module
            return False
    
    @staticmethod
    def get_memory_info():
        """Get detailed memory information"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': process.memory_percent(),
                'available_mb': psutil.virtual_memory().available / 1024 / 1024,
                'total_mb': psutil.virtual_memory().total / 1024 / 1024
            }
        except Exception:
            return {}


def setup_resource_optimization(background_mode=False):
    """Setup resource optimization"""
    optimizer = ResourceOptimizer()
    
    if background_mode:
        optimizer.optimize_for_background()
    else:
        optimizer.optimize_for_active()
    
    optimizer.start_optimization()
    return optimizer