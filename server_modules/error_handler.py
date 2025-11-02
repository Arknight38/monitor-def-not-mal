"""
Advanced Error Handling and Recovery System
Provides robust error recovery and comprehensive logging
"""
import logging
import traceback
import sys
import os
import json
import time
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
import threading

class AdvancedErrorHandler:
    """Comprehensive error handling and recovery system"""
    
    def __init__(self, log_dir="monitor_data/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Error tracking
        self.error_counts = {}
        self.recent_errors = []
        self.recovery_attempts = {}
        
        # Setup logging
        self.setup_logging()
        
        # Recovery strategies
        self.recovery_strategies = {
            'ConnectionError': self._recover_connection,
            'TimeoutError': self._recover_timeout,
            'PermissionError': self._recover_permission,
            'FileNotFoundError': self._recover_file_missing,
            'ImportError': self._recover_import,
            'JSONDecodeError': self._recover_json,
            'MemoryError': self._recover_memory,
            'OSError': self._recover_os_error
        }
        
        self.logger = logging.getLogger('ErrorHandler')
        
    def setup_logging(self):
        """Setup comprehensive logging system"""
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # File handlers
        self._setup_file_handlers(detailed_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
        
        # Error file handler
        error_handler = logging.FileHandler(self.log_dir / "errors.log")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
    
    def _setup_file_handlers(self, formatter):
        """Setup rotating file handlers"""
        try:
            from logging.handlers import RotatingFileHandler
            
            # Main log file (rotating)
            main_handler = RotatingFileHandler(
                self.log_dir / "monitor.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            main_handler.setLevel(logging.DEBUG)
            main_handler.setFormatter(formatter)
            logging.getLogger().addHandler(main_handler)
            
            # Critical errors log
            critical_handler = RotatingFileHandler(
                self.log_dir / "critical.log",
                maxBytes=5*1024*1024,  # 5MB
                backupCount=3
            )
            critical_handler.setLevel(logging.CRITICAL)
            critical_handler.setFormatter(formatter)
            logging.getLogger().addHandler(critical_handler)
            
        except ImportError:
            # Fallback to basic file handler
            file_handler = logging.FileHandler(self.log_dir / "monitor.log")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logging.getLogger().addHandler(file_handler)
    
    def handle_error(self, error, context="Unknown", attempt_recovery=True):
        """Handle error with context and optional recovery"""
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Track error occurrence
        self._track_error(error_type, error_msg, context)
        
        # Log the error
        self.logger.error(
            f"Error in {context}: {error_type}: {error_msg}",
            exc_info=True
        )
        
        # Add to recent errors
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': error_msg,
            'context': context,
            'traceback': traceback.format_exc()
        }
        
        self.recent_errors.append(error_info)
        if len(self.recent_errors) > 100:  # Keep last 100 errors
            self.recent_errors = self.recent_errors[-100:]
        
        # Attempt recovery if enabled
        if attempt_recovery:
            return self._attempt_recovery(error_type, error, context)
        
        return False
    
    def _track_error(self, error_type, error_msg, context):
        """Track error occurrence for analysis"""
        key = f"{error_type}:{context}"
        
        if key not in self.error_counts:
            self.error_counts[key] = {
                'count': 0,
                'first_seen': datetime.now(),
                'last_seen': datetime.now(),
                'messages': set()
            }
        
        self.error_counts[key]['count'] += 1
        self.error_counts[key]['last_seen'] = datetime.now()
        self.error_counts[key]['messages'].add(error_msg)
    
    def _attempt_recovery(self, error_type, error, context):
        """Attempt to recover from error"""
        recovery_key = f"{error_type}:{context}"
        
        # Check if we've tried too many times recently
        if recovery_key in self.recovery_attempts:
            last_attempt, count = self.recovery_attempts[recovery_key]
            if datetime.now() - last_attempt < timedelta(minutes=5) and count >= 3:
                self.logger.warning(f"Too many recovery attempts for {recovery_key}, skipping")
                return False
        
        # Update recovery attempts
        if recovery_key in self.recovery_attempts:
            self.recovery_attempts[recovery_key] = (datetime.now(), self.recovery_attempts[recovery_key][1] + 1)
        else:
            self.recovery_attempts[recovery_key] = (datetime.now(), 1)
        
        # Try specific recovery strategy
        if error_type in self.recovery_strategies:
            try:
                self.logger.info(f"Attempting recovery for {error_type} in {context}")
                success = self.recovery_strategies[error_type](error, context)
                
                if success:
                    self.logger.info(f"Successfully recovered from {error_type}")
                    return True
                else:
                    self.logger.warning(f"Recovery failed for {error_type}")
                    
            except Exception as recovery_error:
                self.logger.error(f"Recovery attempt failed: {recovery_error}")
        
        return False
    
    def _recover_connection(self, error, context):
        """Recover from connection errors"""
        try:
            # Wait and retry connection
            time.sleep(5)
            
            # Try to restart connection stability manager
            from server_modules.connection_stability import ConnectionStabilityManager
            from server_modules.config import load_callback_config
            
            callback_config = load_callback_config()
            stability = ConnectionStabilityManager(callback_config)
            return stability.attempt_reconnection(force=True)
            
        except Exception:
            return False
    
    def _recover_timeout(self, error, context):
        """Recover from timeout errors"""
        # Increase timeout values temporarily
        time.sleep(2)
        return True
    
    def _recover_permission(self, error, context):
        """Recover from permission errors"""
        try:
            # Try to elevate privileges if possible
            if "screenshot" in context.lower():
                # For screenshot permissions, try alternative method
                return True
            return False
        except Exception:
            return False
    
    def _recover_file_missing(self, error, context):
        """Recover from missing file errors"""
        try:
            # Try to create missing directories/files
            error_msg = str(error)
            if "config" in error_msg.lower():
                # Recreate config files
                from server_modules.config import load_config
                load_config()  # This will create default config
                return True
            return False
        except Exception:
            return False
    
    def _recover_import(self, error, context):
        """Recover from import errors"""
        try:
            # Try to install missing module
            module_name = str(error).split("'")[1] if "'" in str(error) else None
            if module_name:
                self.logger.info(f"Attempting to install missing module: {module_name}")
                # Note: In production, this should be more controlled
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
                return True
        except Exception:
            pass
        return False
    
    def _recover_json(self, error, context):
        """Recover from JSON decode errors"""
        try:
            # If it's a config file, recreate it
            if "config" in context.lower():
                from server_modules.config import load_config
                load_config()
                return True
        except Exception:
            pass
        return False
    
    def _recover_memory(self, error, context):
        """Recover from memory errors"""
        try:
            # Force garbage collection
            import gc
            gc.collect()
            
            # Try to free up memory
            from server_modules.resource_optimizer import ResourceOptimizer
            optimizer = ResourceOptimizer()
            optimizer._optimize_memory()
            
            return True
        except Exception:
            return False
    
    def _recover_os_error(self, error, context):
        """Recover from OS errors"""
        try:
            # Wait and retry for temporary OS issues
            time.sleep(3)
            return True
        except Exception:
            return False
    
    def get_error_summary(self):
        """Get summary of errors and recovery attempts"""
        return {
            'total_error_types': len(self.error_counts),
            'recent_errors_count': len(self.recent_errors),
            'recovery_attempts': len(self.recovery_attempts),
            'most_common_errors': sorted(
                self.error_counts.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:5],
            'recent_errors': self.recent_errors[-10:]  # Last 10 errors
        }
    
    def export_error_report(self, filename=None):
        """Export detailed error report"""
        if filename is None:
            filename = self.log_dir / f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': self.get_error_summary(),
            'error_details': {
                key: {
                    'count': info['count'],
                    'first_seen': info['first_seen'].isoformat(),
                    'last_seen': info['last_seen'].isoformat(),
                    'unique_messages': list(info['messages'])
                }
                for key, info in self.error_counts.items()
            },
            'recent_errors': self.recent_errors
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        return filename


def with_error_handling(context="Unknown", attempt_recovery=True):
    """Decorator for automatic error handling"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_error(e, context, attempt_recovery)
                return None
        return wrapper
    return decorator


def safe_execute(func, *args, default=None, context="Unknown", **kwargs):
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_error(e, context)
        return default


# Global error handler instance
error_handler = AdvancedErrorHandler()

# Setup global exception handler
def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Global exception handler"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Don't handle keyboard interrupts
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_handler.handle_error(exc_value, "Global Exception", attempt_recovery=False)

# Install global exception handler
sys.excepthook = global_exception_handler