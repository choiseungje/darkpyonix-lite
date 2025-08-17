# DarkPyonix_km/manager.py
from __future__ import annotations

import os
import uuid
import logging
from typing import Optional, Dict, Any

try:
    from jupyter_server.services.kernels.kernelmanager import MappingKernelManager
    from jupyter_server.services.sessions.sessionmanager import SessionManager
except ImportError:  # nbclassic compatibility
    from notebook.services.kernels.kernelmanager import MappingKernelManager  # type: ignore
    from notebook.services.sessions.sessionmanager import SessionManager  # type: ignore

DEFAULT_NAMESPACE = uuid.UUID("f2a57b34-7b27-43e9-87fd-1b7e9f9d5d6a")

# ---------- utils ----------
def _abs_norm(root_dir: Optional[str], raw_path: Optional[str]) -> str:
    """
    Convert relative path to absolute path and normalize it.

    Args:
        root_dir: Base directory (typically Jupyter server root)
        raw_path: Raw path that might be relative

    Returns:
        Normalized absolute path
    """
    if not raw_path:
        return ""
    base = root_dir or os.getcwd()
    p = raw_path if os.path.isabs(raw_path) else os.path.join(base, raw_path)
    p = os.path.abspath(os.path.realpath(p))
    if os.name == "nt":
        p = os.path.normcase(p)  # Windows case normalization
    return p

def _pick_path_from_kwargs(kwargs: Dict[str, Any]) -> str:
    """
    Extract notebook path from various sources in kwargs.

    Priority order:
    1. kwargs["path"] - Direct path
    2. kwargs["env"]["JPY_SESSION_NAME"] - Jupyter session name
    3. kwargs["env"]["NOTEBOOK_PATH"] - Environment variable path

    Args:
        kwargs: Keyword arguments from kernel start request

    Returns:
        Extracted path or empty string
    """
    raw = kwargs.get("path") or ""
    if raw:
        return raw
    env = kwargs.get("env") or {}
    return env.get("JPY_SESSION_NAME") or env.get("NOTEBOOK_PATH") or ""

def _stable_kernel_id(abs_path: str, kernel_name: str, ns: uuid.UUID) -> str:
    """
    Generate deterministic kernel ID based on file path and kernel type only (user-agnostic).

    Args:
        abs_path: Absolute file path
        kernel_name: Kernel type (e.g., "python3")
        ns: UUID namespace for hashing

    Returns:
        Deterministic kernel ID that's same for same file path
    """
    return str(uuid.uuid5(ns, f"{abs_path}|{kernel_name}"))

def _namespace() -> uuid.UUID:
    """
    Get UUID namespace from environment variable or use default.

    Returns:
        UUID namespace for kernel ID generation
    """
    v = os.environ.get("STICKYKM_NAMESPACE")
    try:
        return uuid.UUID(v) if v else DEFAULT_NAMESPACE
    except Exception:
        return DEFAULT_NAMESPACE

# ---------- MappingKernelManager ----------
class StickyMappingKernelManager(MappingKernelManager):
    """
    Kernel manager that reuses kernels based on absolute file path.
    All users share the same kernel_id for the same notebook file.
    """

    _path_to_kernel_id: Dict[str, str]

    def __init__(self, *a, **kw):
        """Initialize the sticky kernel manager with logging setup."""
        super().__init__(*a, **kw)
        self._path_to_kernel_id = {}
        self.sticky_logger = logging.getLogger("StickyKM")
        if not self.sticky_logger.handlers:
            h = logging.StreamHandler()
            h.setFormatter(logging.Formatter("[%(name)s] %(asctime)s - %(levelname)s - %(message)s"))
            self.sticky_logger.addHandler(h)
        self.sticky_logger.setLevel(logging.INFO)
        if getattr(self, "log", None):
            self.log.info("[StickyKM] initialized (root_dir=%s)", getattr(self.parent, "root_dir", None))
        self.sticky_logger.info("initialized (root_dir=%s)", getattr(self.parent, "root_dir", None))

    def _debug(self, msg: str):
        """Log debug message to both custom logger and Jupyter's built-in logger."""
        self.sticky_logger.info(msg)
        if getattr(self, "log", None):
            self.log.info(f"[StickyKM] {msg}")

    def _propose_id(self, abs_path: str, kernel_name: str) -> str:
        """
        Propose kernel ID based on file path and kernel type (excluding user info).

        Args:
            abs_path: Absolute file path
            kernel_name: Kernel type

        Returns:
            Proposed deterministic kernel ID
        """
        return _stable_kernel_id(abs_path, kernel_name, _namespace())

    def start_kernel(self, **kwargs):
        """
        Start kernel with reuse logic. If kernel for the same file exists, reuse it.

        Args:
            **kwargs: Kernel start parameters including potential path info

        Returns:
            Kernel ID (either reused or newly created)
        """
        self._debug(
            "start_kernel kwargs={"
            + ", ".join(f"{k}={'...env...' if k=='env' else repr(v)}" for k, v in kwargs.items())
            + "}"
        )
        kernel_id = kwargs.pop("kernel_id", None)
        kernel_name = kwargs.get("kernel_name", "python3")

        # Extract and normalize file path
        raw_path = _pick_path_from_kwargs(kwargs)
        abs_path = _abs_norm(getattr(self.parent, "root_dir", None) if hasattr(self, "parent") else None, raw_path)
        self._debug(f"chosen raw_path='{raw_path}', abs_path='{abs_path}', kernel_name='{kernel_name}'")

        if abs_path:
            kwargs["path"] = abs_path  # Pass absolute path downstream

        # Apply reuse logic if no specific kernel_id and we have a file path
        if kernel_id is None and abs_path:
            proposed = self._propose_id(abs_path, kernel_name)
            if proposed in self._kernels:
                km = self._kernels[proposed]
                try:
                    alive = km.is_alive()
                except Exception:
                    alive = True  # Assume alive if can't check
                if alive:
                    self._debug(f"Reusing shared kernel_id={proposed} for abs_path={abs_path}")
                    return proposed
                self._debug(f"Kernel {proposed} dead; starting new.")

            kernel_id = proposed

        # Start new kernel or use provided kernel_id
        self._debug(f"Starting kernel (final id={kernel_id})")
        rid = kernel_id if kernel_id is not None else "<parent-generated>"
        out = super().start_kernel(kernel_id=kernel_id, **kwargs)
        self._debug(f"Started kernel; id={rid}")
        return out

    async def start_kernel_async(self, **kwargs):
        """
        Async version of start_kernel with same reuse logic.

        Args:
            **kwargs: Kernel start parameters including potential path info

        Returns:
            Kernel ID (either reused or newly created)
        """
        self._debug(
            "start_kernel_async kwargs={"
            + ", ".join(f"{k}={'...env...' if k=='env' else repr(v)}" for k, v in kwargs.items())
            + "}"
        )
        kernel_id = kwargs.pop("kernel_id", None)
        kernel_name = kwargs.get("kernel_name", "python3")

        # Extract and normalize file path
        raw_path = _pick_path_from_kwargs(kwargs)
        abs_path = _abs_norm(getattr(self.parent, "root_dir", None) if hasattr(self, "parent") else None, raw_path)
        self._debug(f"(async) chosen raw_path='{raw_path}', abs_path='{abs_path}', kernel_name='{kernel_name}'")

        if abs_path:
            kwargs["path"] = abs_path

        # Apply reuse logic if no specific kernel_id and we have a file path
        if kernel_id is None and abs_path:
            proposed = self._propose_id(abs_path, kernel_name)
            if proposed in self._kernels:
                km = self._kernels[proposed]
                try:
                    alive = km.is_alive()
                except Exception:
                    alive = True  # Assume alive if can't check
                if alive:
                    self._debug(f"(async) Reusing shared kernel_id={proposed} for abs_path={abs_path}")
                    return proposed
            kernel_id = proposed

        # Start new kernel asynchronously
        self._debug(f"(async) Starting kernel (final id={kernel_id})")
        out = await super().start_kernel_async(kernel_id=kernel_id, **kwargs)
        rid = kernel_id if kernel_id is not None else "<parent-generated>"
        self._debug(f"(async) Started kernel; id={rid}")
        return out
