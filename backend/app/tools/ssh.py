"""
SSH execution tools for orchestrator.

Provides remote command execution via SSH.
"""

from typing import Dict, Any, Optional


async def ssh_exec(
    host: str,
    command: str,
    user: Optional[str] = None,
    port: int = 22,
    timeout: int = 30,
    **kwargs
) -> Dict[str, Any]:
    """
    Execute command on remote host via SSH.
    
    Args:
        host: Target hostname or IP
        command: Shell command to execute
        user: SSH username (defaults to current user)
        port: SSH port
        timeout: Command timeout in seconds
        
    Returns:
        Dictionary with stdout, stderr, and exit_code
    """
    # TODO: Integrate with actual SSH service
    # For now, return mock response
    return {
        "host": host,
        "command": command,
        "stdout": "Mock SSH output",
        "stderr": "",
        "exit_code": 0,
        "duration_ms": 100
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
    
    Args:
        host: Target hostname or IP
        command: Safe read-only command
        user: SSH username
        port: SSH port
        
    Returns:
        Dictionary with stdout and metadata
    """
    # Allowlist of safe commands
    safe_commands = {"ls", "cat", "ps", "df", "du", "head", "tail", "grep"}
    cmd_parts = command.split()
    
    if not cmd_parts or cmd_parts[0] not in safe_commands:
        cmd_name = cmd_parts[0] if cmd_parts else ''
        return {
            "error": f"Command '{cmd_name}' not allowed in peek mode",
            "allowed_commands": list(safe_commands)
        }
    
    # Execute with timeout
    result = await ssh_exec(host, command, user, port, timeout=10)
    return result
