"""
Agent Orchestrator - Routes intents to flow runners, MCP adapters, or local agents.

Architecture:
- Single /orchestrate webhook endpoint
- Canonical request/response contract
- Supports n8n, ActivePieces, MCP, and local agents
- Async with callbacks for long-running jobs
- Idempotency and tracing built-in
"""

from enum import Enum
from typing import Dict, Any, Optional
import httpx
import logging
import os
from app.tools import get_tool, list_tools

logger = logging.getLogger(__name__)

# Configuration
N8N_WEBHOOK_BASE = os.getenv("N8N_WEBHOOK_BASE", "http://n8n:5678/webhook")
ACTIVEPIECES_BASE = os.getenv("ACTIVEPIECES_BASE", "http://activepieces:3000/api/v1")


class Mode(str, Enum):
    """Execution mode for orchestrator."""
    flow = "flow"      # n8n or ActivePieces workflow
    mcp = "mcp"        # Model Context Protocol adapter
    agent = "agent"    # In-process local agent
    auto = "auto"      # Heuristic-based selection


class OrchestratorError(Exception):
    """Base exception for orchestrator errors."""
    pass


class IntentNotFoundError(OrchestratorError):
    """Raised when intent is not recognized."""
    pass


async def run_flow(
    intent: str,
    inputs: Dict[str, Any],
    trace: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute intent via flow engine (n8n or ActivePieces).
    
    Maps intent to specific webhook URL and posts request.
    Flow must return JSON with result structure.
    
    Args:
        intent: Intent name (e.g., "gmail.triage")
        inputs: Intent-specific parameters
        trace: Tracing context (request_id, job_id, etc.)
        
    Returns:
        Result dictionary from flow execution
        
    Raises:
        OrchestratorError: If flow execution fails
    """
    # Intent to webhook mapping
    # TODO: Make this configurable via database or config file
    intent_routes = {
        "gmail.triage": f"{N8N_WEBHOOK_BASE}/gmail-triage",
        "gmail.send": f"{N8N_WEBHOOK_BASE}/gmail-send",
        "digest.daily": f"{N8N_WEBHOOK_BASE}/digest-daily",
        "memory.search": f"{N8N_WEBHOOK_BASE}/memory-search",
        "fs.analyze": f"{N8N_WEBHOOK_BASE}/fs-analyze",
    }
    
    # Fallback to generic webhook
    webhook_url = intent_routes.get(
        intent,
        f"{N8N_WEBHOOK_BASE}/orchestrate"
    )
    
    logger.info(
        f"Executing flow intent={intent} url={webhook_url}",
        extra={"trace": trace}
    )
    
    payload = {
        "intent": intent,
        "inputs": inputs,
        "trace": trace
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
            result = response.json()
            
        logger.info(
            f"Flow completed intent={intent}",
            extra={"trace": trace, "result": result}
        )
        return result
        
    except httpx.TimeoutException as e:
        logger.error(
            f"Flow timeout intent={intent}",
            extra={"trace": trace, "error": str(e)}
        )
        raise OrchestratorError(f"Flow execution timed out: {e}")
        
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Flow HTTP error intent={intent} status={e.response.status_code}",
            extra={"trace": trace, "error": str(e)}
        )
        raise OrchestratorError(
            f"Flow returned error {e.response.status_code}: {e.response.text}"
        )
        
    except Exception as e:
        logger.error(
            f"Flow execution failed intent={intent}",
            extra={"trace": trace, "error": str(e)}
        )
        raise OrchestratorError(f"Flow execution failed: {e}")


async def run_agent(
    intent: str,
    inputs: Dict[str, Any],
    trace: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute intent via local in-process agent.
    
    Fast path for simple operations that don't require external systems.
    Delegates to tools in tools/* module.
    
    Args:
        intent: Intent name
        inputs: Intent parameters
        trace: Tracing context
        
    Returns:
        Result dictionary from tool execution
        
    Raises:
        IntentNotFoundError: If intent not recognized
        OrchestratorError: If execution fails
    """
    logger.info(
        f"Executing agent intent={intent}",
        extra={"trace": trace}
    )
    
    # Get tool from registry
    tool = get_tool(intent)
    
    if not tool:
        available = list_tools()
        logger.error(
            f"Unknown intent={intent}",
            extra={"trace": trace, "available": available}
        )
        raise IntentNotFoundError(
            f"Intent '{intent}' not found. Available: {available}"
        )
    
    # Safety check for dangerous operations
    if intent == "ssh.exec" and not inputs.get("confirm_dangerous"):
        logger.warning(
            f"Blocking dangerous operation intent={intent}",
            extra={"trace": trace}
        )
        return {
            "dry_run": True,
            "would_execute": inputs,
            "note": "Set confirm_dangerous=true to execute",
            "hint": "Use ssh.exec.peek for read-only operations"
        }
    
    # Execute tool
    try:
        result = await tool(**inputs)
        logger.info(
            f"Agent completed intent={intent}",
            extra={"trace": trace, "result": result}
        )
        return result
        
    except Exception as e:
        logger.error(
            f"Agent execution failed intent={intent}",
            extra={"trace": trace, "error": str(e)}
        )
        raise OrchestratorError(f"Agent execution failed: {e}")


async def run_mcp(
    intent: str,
    inputs: Dict[str, Any],
    trace: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute intent via Model Context Protocol adapter.
    
    Thin adapter that starts MCP client, calls tool once, shuts down.
    Future integration path for standardized tool discovery.
    
    Args:
        intent: Intent name
        inputs: Intent parameters
        trace: Tracing context
        
    Returns:
        Result dictionary from MCP tool execution
        
    Raises:
        OrchestratorError: MCP not yet implemented
    """
    logger.warning(
        f"MCP path not yet implemented intent={intent}",
        extra={"trace": trace}
    )
    
    # TODO: Implement MCP adapter
    # 1. Start MCP client process
    # 2. Discover available tools
    # 3. Call matching tool with inputs
    # 4. Shutdown client
    # 5. Return result
    
    return {
        "note": "MCP path stubbed - not yet implemented",
        "intent": intent,
        "inputs": inputs,
        "trace": trace
    }


async def auto_select_mode(
    intent: str,
    inputs: Dict[str, Any]
) -> Mode:
    """
    Heuristic-based mode selection.
    
    Selection criteria:
    - agent: Fast operations (<2s), read-only, local tools
    - flow: Multi-system coordination, external integrations
    - mcp: When tool only exposed via MCP
    
    Args:
        intent: Intent name
        inputs: Intent parameters
        
    Returns:
        Selected execution mode
    """
    # Fast read-only operations -> agent
    if intent.endswith(".peek") or intent.endswith(".read"):
        return Mode.agent
    
    # Memory operations -> agent (fast local access)
    if intent.startswith("memory."):
        return Mode.agent
    
    # Multi-system workflows -> flow
    if intent.startswith(("gmail.", "digest.", "workflow.")):
        return Mode.flow
    
    # File system operations -> flow (may need external mounts)
    if intent.startswith("fs."):
        return Mode.flow
    
    # SSH operations -> agent (direct execution)
    if intent.startswith("ssh."):
        return Mode.agent
    
    # Default to flow for safety
    return Mode.flow


async def dispatch(
    mode: Mode,
    intent: str,
    inputs: Dict[str, Any],
    trace: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main orchestrator dispatch logic.
    
    Routes intent to appropriate executor based on mode.
    Handles auto mode selection.
    
    Args:
        mode: Execution mode (or auto for heuristic)
        intent: Intent name
        inputs: Intent parameters
        trace: Tracing context
        
    Returns:
        Execution result
        
    Raises:
        OrchestratorError: If execution fails
    """
    # Auto-select mode if requested
    if mode == Mode.auto:
        selected_mode = await auto_select_mode(intent, inputs)
        logger.info(
            f"Auto-selected mode={selected_mode} for intent={intent}",
            extra={"trace": trace}
        )
    else:
        selected_mode = mode
    
    # Route to appropriate executor
    if selected_mode == Mode.flow:
        return await run_flow(intent, inputs, trace)
    elif selected_mode == Mode.mcp:
        return await run_mcp(intent, inputs, trace)
    elif selected_mode == Mode.agent:
        return await run_agent(intent, inputs, trace)
    else:
        raise OrchestratorError(f"Unknown mode: {selected_mode}")
