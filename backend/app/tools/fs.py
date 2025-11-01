"""
Filesystem tools - Pure functions for safe file operations.

Read-only operations with path allowlists and byte caps.
"""

from typing import Dict, Any, List, Optional
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Allowlisted paths (configurable via env)
ALLOWED_PATHS = os.getenv(
    "FS_ALLOWED_PATHS",
    "/work,/tmp,/data"
).split(",")

# Max file size to read (10MB default)
MAX_READ_BYTES = int(os.getenv("FS_MAX_READ_BYTES", 10 * 1024 * 1024))


def is_path_allowed(path: str) -> bool:
    """Check if path is within allowed directories."""
    try:
        abs_path = Path(path).resolve()
        return any(
            str(abs_path).startswith(allowed)
            for allowed in ALLOWED_PATHS
        )
    except Exception:
        return False


async def list_directory(
    path: str,
    **kwargs
) -> Dict[str, Any]:
    """
    List directory contents (read-only).
    
    Args:
        path: Directory path to list
        
    Returns:
        Dictionary with directory contents
    """
    if not is_path_allowed(path):
        logger.warning(
            f"Blocked directory list: {path}",
            extra={"path": path, "allowed": ALLOWED_PATHS}
        )
        return {
            "error": f"Path not allowed: {path}",
            "allowed_paths": ALLOWED_PATHS
        }
    
    try:
        abs_path = Path(path).resolve()
        
        if not abs_path.exists():
            return {"error": f"Path not found: {path}"}
        
        if not abs_path.is_dir():
            return {"error": f"Not a directory: {path}"}
        
        items = []
        for item in abs_path.iterdir():
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None
            })
        
        logger.info(
            f"Listed directory path={path} items={len(items)}",
            extra={"path": path, "count": len(items)}
        )
        
        return {
            "path": str(abs_path),
            "count": len(items),
            "items": items
        }
        
    except Exception as e:
        logger.error(f"Failed to list directory: {e}")
        return {"error": str(e)}


async def read_file(
    path: str,
    max_bytes: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Read file contents (read-only, with byte cap).
    
    Args:
        path: File path to read
        max_bytes: Maximum bytes to read (defaults to MAX_READ_BYTES)
        
    Returns:
        Dictionary with file contents
    """
    if not is_path_allowed(path):
        logger.warning(
            f"Blocked file read: {path}",
            extra={"path": path}
        )
        return {
            "error": f"Path not allowed: {path}",
            "allowed_paths": ALLOWED_PATHS
        }
    
    try:
        abs_path = Path(path).resolve()
        
        if not abs_path.exists():
            return {"error": f"File not found: {path}"}
        
        if not abs_path.is_file():
            return {"error": f"Not a file: {path}"}
        
        file_size = abs_path.stat().st_size
        max_read = max_bytes or MAX_READ_BYTES
        
        if file_size > max_read:
            return {
                "error": f"File too large: {file_size} bytes",
                "max_bytes": max_read,
                "hint": "Increase max_bytes parameter or use head/tail"
            }
        
        # Read file
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read(max_read)
        
        logger.info(
            f"Read file path={path} size={len(content)}",
            extra={"path": path, "bytes": len(content)}
        )
        
        return {
            "path": str(abs_path),
            "content": content,
            "size": len(content),
            "truncated": len(content) >= max_read
        }
        
    except UnicodeDecodeError:
        return {"error": "File is not UTF-8 text"}
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        return {"error": str(e)}


async def head_file(
    path: str,
    lines: int = 10,
    **kwargs
) -> Dict[str, Any]:
    """
    Read first N lines of file.
    
    Args:
        path: File path
        lines: Number of lines to read
        
    Returns:
        Dictionary with file head
    """
    if not is_path_allowed(path):
        return {
            "error": f"Path not allowed: {path}",
            "allowed_paths": ALLOWED_PATHS
        }
    
    try:
        abs_path = Path(path).resolve()
        
        if not abs_path.is_file():
            return {"error": f"Not a file: {path}"}
        
        with open(abs_path, "r", encoding="utf-8") as f:
            content_lines = [f.readline() for _ in range(lines)]
        
        return {
            "path": str(abs_path),
            "lines": [line.rstrip("\n") for line in content_lines],
            "count": len(content_lines)
        }
        
    except Exception as e:
        return {"error": str(e)}
