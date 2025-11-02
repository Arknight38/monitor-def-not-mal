"""Persistence modules - Unified Version"""
__version__ = "4.0.0"

# Import from unified persistence module
from .persistence import (
    PersistenceManager,
    persistence_manager,
    # Legacy compatibility functions
    install_registry_persistence,
    remove_registry_persistence,
    check_registry_persistence,
    install_service,
    remove_service,
    check_single_instance,
    release_mutex
)

__all__ = [
    'PersistenceManager',
    'persistence_manager',
    'install_registry_persistence',
    'remove_registry_persistence', 
    'check_registry_persistence',
    'install_service',
    'remove_service',
    'check_single_instance',
    'release_mutex'
]