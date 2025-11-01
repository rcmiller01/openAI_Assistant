"""
Tool registry for agent mode.

Maps intent patterns to tool functions.
"""

from typing import Dict, Callable, Optional
from app.tools import memory, ssh


# Tool function registry
TOOL_REGISTRY: Dict[str, Callable] = {
    # Memory operations
    "memory.write": memory.store_memory,
    "memory.store": memory.store_memory,
    "memory.search": memory.search_memory,
    "memory.query": memory.search_memory,
    
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
