"""SSH command execution router with security controls."""

import os
import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.deps.auth import AuthenticatedUser
from app.core.allowlists import is_safe_command, validate_hostname
from app.schemas.common import DryRunResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ssh", tags=["ssh"])

# Get SSH hosts allowlist from environment
SSH_HOSTS_ALLOWLIST = os.getenv("SSH_HOSTS_ALLOWLIST", "").split(",")
SSH_HOSTS_ALLOWLIST = [h.strip() for h in SSH_HOSTS_ALLOWLIST if h.strip()]


class SSHExecIn(BaseModel):
    """SSH command execution request."""
    host: str = Field(..., description="Target hostname")
    cmd: str = Field(..., description="Command to execute")
    timeout_sec: int = Field(10, ge=1, le=30, description="Timeout in seconds")
    confirm: bool = Field(False, description="Confirm execution")


class SSHExecOut(BaseModel):
    """SSH command execution response."""
    host: str
    cmd: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    executed: bool


@router.post("/exec", response_model=SSHExecOut | DryRunResponse)
async def execute_ssh_command(
    request: SSHExecIn,
    _token: AuthenticatedUser
) -> SSHExecOut | DryRunResponse:
    """
    Execute a command on a remote host via SSH.
    
    Security controls:
    - Host must be in allowlist
    - Command must be in safe command list
    - Requires confirm=true to actually execute
    
    Args:
        request: SSH execution request
        
    Returns:
        SSHExecOut or DryRunResponse: Command result or dry-run preview
    """
    try:
        # Validate hostname
        if not validate_hostname(request.host, SSH_HOSTS_ALLOWLIST):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Host not in allowlist: {request.host}"
            )
        
        # Validate command
        if not is_safe_command(request.cmd):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Command not allowed: {request.cmd}"
            )
        
        # Dry-run mode if not confirmed
        if not request.confirm:
            return DryRunResponse(
                dry_run=True,
                operation="ssh_exec",
                would_affect={
                    "host": request.host,
                    "cmd": request.cmd,
                    "timeout_sec": request.timeout_sec
                },
                confirmation_required=True
            )
        
        # Execute command via SSH
        logger.info(f"Executing SSH command on {request.host}: {request.cmd}")
        
        try:
            # Build SSH command
            # Note: This assumes SSH keys are configured and available
            ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", 
                      request.host, request.cmd]
            
            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                *ssh_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=request.timeout_sec
                )
                
                stdout = stdout_bytes.decode('utf-8', errors='replace')
                stderr = stderr_bytes.decode('utf-8', errors='replace')
                exit_code = process.returncode
                
            except asyncio.TimeoutError:
                process.kill()
                await process.communicate()
                raise HTTPException(
                    status_code=status.HTTP_408_REQUEST_TIMEOUT,
                    detail=f"Command timed out after {request.timeout_sec}s"
                )
            
            return SSHExecOut(
                host=request.host,
                cmd=request.cmd,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                executed=True
            )
            
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SSH client not found on server"
            )
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Permission denied to execute SSH"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SSH execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SSH execution failed"
        )
