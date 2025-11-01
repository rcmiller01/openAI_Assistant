"""
Gmail tools - Pure functions for Gmail operations.

Can be called from FastAPI orchestrator or n8n workflows.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


async def triage_gmail(
    query: str,
    label: Optional[str] = None,
    dry_run: bool = True,
    max_results: int = 20,
    **kwargs
) -> Dict[str, Any]:
    """
    Search and optionally label Gmail messages.
    
    Pure function for Gmail triage operations.
    In dry_run mode, returns preview without making changes.
    
    Args:
        query: Gmail search query (e.g., "is:unread older_than:2d")
        label: Label ID to apply (optional)
        dry_run: If True, preview without applying changes
        max_results: Maximum messages to process
        
    Returns:
        Dictionary with operation results
    """
    logger.info(
        f"Gmail triage query='{query}' label={label} dry_run={dry_run}",
        extra={"query": query, "label": label, "dry_run": dry_run}
    )
    
    # TODO: Integrate with actual Gmail API
    # For now, return mock data
    
    if dry_run:
        return {
            "dry_run": True,
            "query": query,
            "found": 15,  # Mock count
            "would_apply_label": label,
            "preview": [
                {
                    "id": "msg_abc123",
                    "from": "sender@example.com",
                    "subject": "Example Email",
                    "snippet": "This is a preview...",
                    "date": "2025-10-30T10:00:00Z"
                }
            ],
            "note": "No changes made. Set dry_run=false to apply label."
        }
    else:
        # Execute operation
        return {
            "dry_run": False,
            "query": query,
            "found": 15,
            "labeled": 15 if label else 0,
            "label_id": label,
            "message_ids": [
                "msg_abc123",
                "msg_def456",
                # ... more IDs
            ],
            "note": f"Applied label '{label}' to 15 messages." if label else "No label provided."
        }


async def search_gmail(
    query: str,
    max_results: int = 20,
    **kwargs
) -> Dict[str, Any]:
    """
    Search Gmail messages.
    
    Pure function for Gmail search.
    
    Args:
        query: Gmail search query
        max_results: Maximum messages to return
        
    Returns:
        Dictionary with search results
    """
    logger.info(
        f"Gmail search query='{query}' max={max_results}",
        extra={"query": query}
    )
    
    # TODO: Integrate with actual Gmail API
    return {
        "query": query,
        "count": 0,
        "messages": [],
        "note": "Gmail API integration pending"
    }


async def get_recent_gmail(
    since: str = "24h",
    labels: Optional[List[str]] = None,
    max_results: int = 50
) -> Dict[str, Any]:
    """
    Get recent Gmail messages.
    
    Args:
        since: Time range (e.g., "24h", "1d", "1w")
        labels: Filter by label IDs
        max_results: Maximum messages to return
        
    Returns:
        Dictionary with recent messages
    """
    logger.info(
        f"Gmail recent since={since} labels={labels}",
        extra={"since": since, "labels": labels}
    )
    
    # TODO: Integrate with actual Gmail API
    return {
        "since": since,
        "labels": labels,
        "count": 0,
        "messages": [],
        "note": "Gmail API integration pending"
    }
