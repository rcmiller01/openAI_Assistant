"""
SSH execution tools - Pure functions for remote commands.

Provides safe SSH execution with command allowlists.
"""

import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Allowlisted commands (read-only by default)
SAFE_COMMANDS = {
    "ls", "cat", "head", "tail", "grep", "find",
    "ps", "top", "df", "du", "free", "uptime",
    "whoami", "hostname", "date", "pwd"
}

# Allowlisted hosts (configurable via env)
ALLOWED_HOSTS = os.getenv(
    "SSH_ALLOWED_HOSTS",
    "localhost,127.0.0.1"
).split(",")


def is_command_safe(command: str) -> bool:
    """Check if command is in safe allowlist."""
    cmd_parts = command.strip().split()
    if not cmd_parts:
        return False
    return cmd_parts[0] in SAFE_COMMANDS


def is_host_allowed(host: str) -> bool:
    """Check if host is in allowlist."""
    return host in ALLOWED_HOSTS


async def ssh_exec(
    host: str,
    command: str,
    user: Optional[str] = None,
    port: int = 22,
    timeout: int = 30,
    confirm_dangerous: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Execute command on remote host via SSH.
    
    Requires confirm_dangerous=True for non-safe commands.
    
    Args:
        host: Target hostname or IP
        command: Shell command to execute
        user: SSH username (defaults to current user)
        port: SSH port
        timeout: Command timeout in seconds
        confirm_dangerous: Must be True for non-safe commands
        
    Returns:
        Dictionary with stdout, stderr, and exit_code
    """
    # Check host allowlist
    if not is_host_allowed(host):
        logger.warning(
            f"Blocked SSH to non-allowed host: {host}",
            extra={"host": host, "command": command}
        )
        return {
            "error": f"Host not allowed: {host}",
            "allowed_hosts": ALLOWED_HOSTS,
            "hint": "Add host to SSH_ALLOWED_HOSTS environment variable"
        }
    
    # Check command safety
    if not is_command_safe(command) and not confirm_dangerous:
        logger.warning(
            f"Blocked dangerous SSH command: {command}",
            extra={"host": host, "command": command}
        )
        return {
            "dry_run": True,
            "would_execute": {
                "host": host,
                "command": command,
                "user": user
            },
            "error": "Command not in safe list",
            "note": "Set confirm_dangerous=true to execute",
            "hint": "Use ssh.exec.peek for read-only operations",
            "safe_commands": list(SAFE_COMMANDS)
        }
    
    # TODO: Integrate with actual SSH client
    # For now, return mock response
    logger.info(
        f"SSH exec host={host} command='{command[:50]}'",
        extra={"host": host, "command": command}
    )
    
    return {
        "host": host,
        "command": command,
        "user": user,
        "stdout": "Mock SSH output",
        "stderr": "",
        "exit_code": 0,
        "duration_ms": 100,
        "note": "SSH integration pending"
    }


async def ssh_exec_peek(
    host: str,
    command: str,
    user: Optional[str] = None,
    port: int = 22,
    **kwargs
) -> Dict[str, Any]:
    """
    Execute read-only command on remote host.
    
    Only allows safe commands like ls, cat, ps, etc.
    Automatically validates against safe command list.
    
    Args:
        host: Target hostname or IP
        command: Safe read-only command
        user: SSH username
        port: SSH port
        
    Returns:
        Dictionary with stdout and metadata
    """
    # Check host allowlist
    if not is_host_allowed(host):
        return {
            "error": f"Host not allowed: {host}",
            "allowed_hosts": ALLOWED_HOSTS
        }
    
    # Validate command is safe
    if not is_command_safe(command):
        cmd_name = command.strip().split()[0] if command.strip() else ''
        logger.warning(
            f"Blocked unsafe peek command: {command}",
            extra={"host": host, "command": command}
        )
        return {
            "error": f"Command '{cmd_name}' not allowed in peek mode",
            "allowed_commands": list(SAFE_COMMANDS),
            "hint": "Use ssh.exec with confirm_dangerous=true for write operations"
        }
    
    # Execute with timeout (read-only, so safe)
    logger.info(
        f"SSH peek host={host} command='{command}'",
        extra={"host": host, "command": command}
    )
    
    result = await ssh_exec(
        host=host,
        command=command,
        user=user,
        port=port,
        timeout=10,
        confirm_dangerous=True  # Safe commands pre-validated
    )
    
    return result
