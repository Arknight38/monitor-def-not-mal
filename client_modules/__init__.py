"""Client modules - Unified Version"""
__version__ = "4.0.0"

# Import from unified client core module
from .client_core import (
    ConfigManager,
    APIClient,
    DialogManager,
    AddServerDialog,
    CallbackSettingsDialog,
    # Legacy compatibility functions
    load_config,
    save_config
)

__all__ = [
    'ConfigManager',
    'APIClient', 
    'DialogManager',
    'AddServerDialog',
    'CallbackSettingsDialog',
    'load_config',
    'save_config'
]