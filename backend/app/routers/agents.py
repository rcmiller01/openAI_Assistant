"""Agent orchestration endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import AuthenticatedUser
from app.deps.db import get_async_db
from app.schemas.agents import (
    AgentResolveIn,
    AgentResolveOut,
    AgentCreateIn,
    AgentCreateOut,
    AgentRunIn,
    AgentRunOut,
    SecretLinkIn,
    SecretLinkOut,
    AgentOut,
)
from app.schemas.common import DryRunResponse
# from app.core.n8n_client import n8n_client  # TODO: Implement
# from app.core.vaultwarden_client import vaultwarden_client  # TODO


router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/resolve", response_model=AgentResolveOut)
async def resolve_agent(
    data: AgentResolveIn,
    _token: AuthenticatedUser,
    db: AsyncSession = Depends(get_async_db),
) -> AgentResolveOut:
    """
    Resolve agent by query. Returns existing agent or proposes new manifest.
    
    - Searches agent table by name/description/tags
    - If found, returns agent_id and metadata
    - If not found, returns proposed AgentManifest for creation
    """
    # TODO: Implement DB query for agent search
    # For now, return not found with proposal placeholder
    return AgentResolveOut(
        found=False,
        proposal=None,  # Would contain LLM-generated manifest
    )


@router.post("/create", response_model=AgentCreateOut)
async def create_agent(
    data: AgentCreateIn,
    _token: AuthenticatedUser,
    db: AsyncSession = Depends(get_async_db),
) -> AgentCreateOut | DryRunResponse:
    """
    Create new agent workflow (dry-run by default).
    
    - Validates manifest
    - Creates n8n workflow
    - Stores agent in DB
    - Returns agent_id and workflow_id
    """
    if not data.confirm:
        return DryRunResponse(
            operation="create_agent",
            would_affect={
                "name": data.manifest.name,
                "workflow_config": data.manifest.workflow_config,
            },
        )

    # TODO: Implement agent creation logic
    # 1. Create n8n workflow via n8n_client.create_workflow()
    # 2. Insert agent record in DB
    # 3. Return agent_id and workflow_id
    raise HTTPException(
        status_code=501,
        detail="Agent creation not yet implemented",
    )


@router.post("/run", response_model=AgentRunOut)
async def run_agent(
    data: AgentRunIn,
    _token: AuthenticatedUser,
    db: AsyncSession = Depends(get_async_db),
) -> AgentRunOut | DryRunResponse:
    """
    Execute agent workflow (dry-run by default).
    
    - Validates agent_id exists
    - Triggers n8n workflow execution
    - Returns execution_id and status
    """
    if not data.confirm:
        return DryRunResponse(
            operation="run_agent",
            would_affect={
                "agent_id": data.agent_id,
                "params": data.params,
            },
        )

    # TODO: Implement agent execution logic
    # 1. Lookup agent by agent_id
    # 2. Trigger n8n workflow via n8n_client.run_workflow()
    # 3. Return execution_id and status
    raise HTTPException(
        status_code=501,
        detail="Agent execution not yet implemented",
    )


@router.post("/secrets/link", response_model=SecretLinkOut)
async def link_secret(
    data: SecretLinkIn,
    _token: AuthenticatedUser,
    db: AsyncSession = Depends(get_async_db),
) -> SecretLinkOut | DryRunResponse:
    """
    Link Vaultwarden secret to n8n credential (dry-run by default).
    
    - Fetches secret from Vaultwarden
    - Creates/updates n8n credential
    - Links credential to agent workflow
    """
    if not data.confirm:
        return DryRunResponse(
            operation="link_secret",
            would_affect={
                "agent_id": data.agent_id,
                "secret_ref": data.secret_ref,
                "credential_name": data.credential_name,
            },
        )

    # TODO: Implement secret linking logic
    # 1. Fetch secret via vaultwarden_client.fetch_secret()
    # 2. Upsert n8n credential via n8n_client.upsert_credential()
    # 3. Return credential name and linked status
    raise HTTPException(
        status_code=501,
        detail="Secret linking not yet implemented",
    )


@router.get("/{agent_id}", response_model=AgentOut)
async def get_agent(
    agent_id: int,
    _token: AuthenticatedUser,
    db: AsyncSession = Depends(get_async_db),
) -> AgentOut:
    """Get agent details by ID."""
    # TODO: Implement DB query
    raise HTTPException(
        status_code=404,
        detail=f"Agent {agent_id} not found",
    )


@router.get("/", response_model=List[AgentOut])
async def list_agents(
    _token: AuthenticatedUser,
    db: AsyncSession = Depends(get_async_db),
) -> List[AgentOut]:
    """List all agents."""
    # TODO: Implement DB query
    return []
