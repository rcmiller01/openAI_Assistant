"""Filesystem access router - READ ONLY."""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, status, Query, Depends
from pydantic import BaseModel

from app.deps.auth import AuthenticatedUser
from app.core.allowlists import is_safe_file_extension

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/fs", tags=["filesystem"])

# Get FS_ROOT from environment
FS_ROOT = os.getenv("FS_ROOT", "/work")


class FileEntry(BaseModel):
    """File or directory entry."""
    name: str
    path: str
    type: str  # "file" or "directory"
    size: int | None = None
    modified: str | None = None


class FSListOut(BaseModel):
    """Filesystem list response."""
    path: str
    entries: List[FileEntry]
    total: int


class FSReadOut(BaseModel):
    """Filesystem read response."""
    path: str
    content: str
    size: int
    truncated: bool


def normalize_and_validate_path(requested_path: str) -> Path:
    """
    Normalize and validate a filesystem path.
    
    Args:
        requested_path: User-provided path
        
    Returns:
        Path: Validated absolute path
        
    Raises:
        HTTPException: If path is invalid or outside FS_ROOT
    """
    # Start with FS_ROOT
    root = Path(FS_ROOT).resolve()
    
    # Handle empty or root request
    if not requested_path or requested_path in ["/", "."]:
        return root
    
    # Remove leading slash and resolve relative to root
    clean_path = requested_path.lstrip("/")
    target = (root / clean_path).resolve()
    
    # Ensure target is under root (prevent directory traversal)
    try:
        target.relative_to(root)
    except ValueError:
        logger.warning(f"Path traversal attempt blocked: {requested_path}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Path traversal not allowed"
        )
    
    # Block symlinks
    if target.is_symlink():
        logger.warning(f"Symlink access blocked: {requested_path}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Symlink access not allowed"
        )
    
    return target


@router.get("/list", response_model=FSListOut)
async def list_directory(
    _token: AuthenticatedUser,
    path: str = Query("/", description="Directory path to list"),
    max_depth: int = Query(1, ge=1, le=3, description="Maximum depth")
) -> FSListOut:
    """
    List directory contents (read-only).
    
    Args:
        path: Directory path relative to FS_ROOT
        max_depth: Maximum recursion depth (currently unused, always 1)
        
    Returns:
        FSListOut: Directory listing
    """
    try:
        target = normalize_and_validate_path(path)
        
        if not target.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Path not found"
            )
        
        if not target.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path is not a directory"
            )
        
        # List entries
        entries = []
        try:
            for entry in sorted(target.iterdir()):
                try:
                    stat = entry.stat()
                    entries.append(FileEntry(
                        name=entry.name,
                        path=str(entry.relative_to(Path(FS_ROOT))),
                        type="directory" if entry.is_dir() else "file",
                        size=stat.st_size if entry.is_file() else None,
                        modified=str(stat.st_mtime)
                    ))
                except (PermissionError, OSError) as e:
                    logger.warning(f"Skipped entry {entry}: {e}")
                    continue
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        
        return FSListOut(
            path=str(target.relative_to(Path(FS_ROOT))),
            entries=entries,
            total=len(entries)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list directory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list directory"
        )


@router.get("/read", response_model=FSReadOut)
async def read_file(
    _token: AuthenticatedUser,
    path: str = Query(..., description="File path to read"),
    bytes: int = Query(65536, ge=1, le=1048576, description="Max bytes to read")
) -> FSReadOut:
    """
    Read file contents (text files only, read-only).
    
    Args:
        path: File path relative to FS_ROOT
        bytes: Maximum bytes to read
        
    Returns:
        FSReadOut: File content
    """
    try:
        target = normalize_and_validate_path(path)
        
        if not target.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        if not target.is_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path is not a file"
            )
        
        # Check file extension for safety
        if not is_safe_file_extension(target.name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="File type not allowed for reading"
            )
        
        # Get file size
        file_size = target.stat().st_size
        
        # Read file content
        try:
            with open(target, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(bytes)
                truncated = file_size > bytes
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File appears to be binary, not text"
            )
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        
        return FSReadOut(
            path=str(target.relative_to(Path(FS_ROOT))),
            content=content,
            size=file_size,
            truncated=truncated
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read file"
        )
