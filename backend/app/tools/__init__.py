"""
Tool registry for agent mode.

Maps intent patterns to tool functions.
All tools are pure functions that can be called from FastAPI or n8n.
"""

from typing import Dict, Callable, Optional
from app.tools import memory, ssh, gmail, fs


# Tool function registry
TOOL_REGISTRY: Dict[str, Callable] = {
    # Memory operations
    "memory.write": memory.store_memory,
    "memory.store": memory.store_memory,
    "memory.search": memory.search_memory,
    "memory.query": memory.search_memory,
    "memory.list": memory.list_memories,
    
    # Gmail operations
    "gmail.triage": gmail.triage_gmail,
    "gmail.search": gmail.search_gmail,
    "gmail.recent": gmail.get_recent_gmail,
    
    # Filesystem operations (read-only)
    "fs.list": fs.list_directory,
    "fs.read": fs.read_file,
    "fs.head": fs.head_file,
    
    # SSH operations
    "ssh.exec": ssh.ssh_exec,
    "ssh.exec.peek": ssh.ssh_exec_peek,
    "ssh.run": ssh.ssh_exec,
}


def get_tool(intent: str) -> Optional[Callable]:
    """
    Get tool function for intent.
    
    Args:
        intent: Intent pattern (e.g., "memory.write")
        
    Returns:
        Tool function or None if not found
    """
    return TOOL_REGISTRY.get(intent)


def list_tools() -> list[str]:
    """
    List all registered tool intents.
    
    Returns:
        List of intent patterns
    """
    return list(TOOL_REGISTRY.keys())


def get_tools_by_prefix(prefix: str) -> Dict[str, Callable]:
    """
    Get all tools matching a prefix.
    
    Args:
        prefix: Prefix to match (e.g., "memory", "ssh")
        
    Returns:
        Dictionary of matching tools
    """
    return {
        intent: func
        for intent, func in TOOL_REGISTRY.items()
        if intent.startswith(prefix)
    }
