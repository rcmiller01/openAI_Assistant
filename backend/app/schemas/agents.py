"""Agent orchestration schemas."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class AgentManifest(BaseModel):
    """Agent workflow manifest."""
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    version: str = Field(default="1.0.0", description="Agent version")
    workflow_config: Dict[str, Any] = Field(..., description="n8n workflow config")
    required_secrets: List[str] = Field(
        default_factory=list,
        description="Required secret references"
    )
    tags: List[str] = Field(default_factory=list, description="Tags")


class AgentResolveIn(BaseModel):
    """Agent resolution request."""
    query: str = Field(..., description="Search query for agent")
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context"
    )


class AgentResolveOut(BaseModel):
    """Agent resolution response."""
    found: bool
    agent_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    proposal: Optional[AgentManifest] = None


class AgentCreateIn(BaseModel):
    """Agent creation request."""
    manifest: AgentManifest
    confirm: bool = Field(False, description="Confirm creation")


class AgentCreateOut(BaseModel):
    """Agent creation response."""
    agent_id: int
    name: str
    workflow_id: Optional[str] = None
    created: bool


class AgentRunIn(BaseModel):
    """Agent execution request."""
    agent_id: int = Field(..., description="Agent ID to run")
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution parameters"
    )
    confirm: bool = Field(False, description="Confirm execution")


class AgentRunOut(BaseModel):
    """Agent execution response."""
    agent_id: int
    execution_id: Optional[str] = None
    status: str
    result: Optional[Dict[str, Any]] = None


class SecretLinkIn(BaseModel):
    """Secret linking request."""
    agent_id: int = Field(..., description="Agent ID")
    secret_ref: str = Field(..., description="Vaultwarden secret reference")
    credential_name: str = Field(..., description="n8n credential name")
    confirm: bool = Field(False, description="Confirm secret linking")


class SecretLinkOut(BaseModel):
    """Secret linking response."""
    agent_id: int
    credential_name: str
    linked: bool


class AgentOut(BaseModel):
    """Agent details response."""
    id: int
    name: str
    description: str
    version: str
    workflow_id: Optional[str] = None
    tags: List[str]
    created_at: str
    updated_at: Optional[str] = None
