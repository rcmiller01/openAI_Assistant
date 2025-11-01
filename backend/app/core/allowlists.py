"""Command allowlists for security."""

import logging
from typing import List, Set

logger = logging.getLogger(__name__)

# Safe commands allowed for SSH execution
SAFE_COMMANDS: Set[str] = {
    "uptime",
    "df -h", 
    "whoami",
    "hostname",
    "date",
    "pwd",
    "ls -la",
    "free -h",
    "ps aux",
    "top -bn1",
    "systemctl status"
}

# Safe file extensions for filesystem access
SAFE_FILE_EXTENSIONS: Set[str] = {
    ".txt", ".md", ".json", ".yaml", ".yml", ".ini", ".conf", 
    ".log", ".csv", ".py", ".js", ".html", ".css", ".xml"
}

# Dangerous patterns to block
DANGEROUS_PATTERNS: List[str] = [
    "rm ", "delete", "del ", "format", "mkfs", 
    "dd if=", ">/dev/", "curl", "wget", "nc ", 
    "netcat", "sudo", "su ", "chmod", "chown"
]


def is_safe_command(cmd: str) -> bool:
    """
    Check if a command is safe to execute.
    
    Args:
        cmd: The command string to validate
        
    Returns:
        bool: True if command is safe, False otherwise
    """
    if not cmd or not cmd.strip():
        return False
        
    cmd_lower = cmd.lower().strip()
    
    # Check if it's in the allowlist
    if cmd_lower in SAFE_COMMANDS:
        return True
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if pattern in cmd_lower:
            logger.warning(f"Blocked dangerous command pattern '{pattern}' in: {cmd}")
            return False
    
    # For now, be conservative - only allow explicitly safe commands
    logger.warning(f"Command not in allowlist: {cmd}")
    return False


def is_safe_file_extension(filename: str) -> bool:
    """
    Check if a file extension is safe for reading.
    
    Args:
        filename: The filename to check
        
    Returns:
        bool: True if extension is safe, False otherwise
    """
    if not filename:
        return False
        
    # Get file extension
    if '.' not in filename:
        return False
        
    ext = '.' + filename.split('.')[-1].lower()
    return ext in SAFE_FILE_EXTENSIONS


def validate_hostname(hostname: str, allowlist: List[str]) -> bool:
    """
    Validate hostname against allowlist.
    
    Args:
        hostname: The hostname to validate
        allowlist: List of allowed hostnames
        
    Returns:
        bool: True if hostname is allowed, False otherwise
    """
    if not hostname or not allowlist:
        return False
        
    return hostname.lower() in [h.lower() for h in allowlist]