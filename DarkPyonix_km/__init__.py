"""
DarkPyonix-lite - Sticky Kernel Manager for Jupyter
"""

from .manager import StickyMappingKernelManager, StickySessionManager
from .config import create_config, check_installation

__version__ = "1.0.0"

__all__ = [
    "StickyMappingKernelManager",
    "StickySessionManager",
    "create_config",
    "check_installation"
]