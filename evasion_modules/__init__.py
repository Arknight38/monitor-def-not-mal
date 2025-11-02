"""Evasion modules - Unified Version"""
__version__ = "4.0.0"

# Import from unified evasion module
from .evasion import (
    EvasionManager,
    evasion_manager,
    # Legacy compatibility functions
    check_debugger,
    check_vm,
    check_analysis_tools,
    run_all_checks,
    is_safe_environment,
    obfuscate_string,
    deobfuscate_string
)

__all__ = [
    'EvasionManager',
    'evasion_manager',
    'check_debugger',
    'check_vm',
    'check_analysis_tools',
    'run_all_checks',
    'is_safe_environment',
    'obfuscate_string',
    'deobfuscate_string'
]