"""
Orchestrate endpoint - Unified webhook for all intents.

Single endpoint that routes to flow engines, MCP adapters, or local agents.
Supports sync and async execution with callbacks.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import hashlib
import json
import uuid
import logging
import asyncio
import httpx

from app.deps.auth import api_auth, security
from app.core.orchestrator import (
    dispatch,
    Mode,
    OrchestratorError,
    IntentNotFoundError
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["orchestrate"])

# In-memory job store (replace with Redis/Postgres for production)
_job_store: Dict[str, Dict[str, Any]] = {}


class OrchestrateRequest(BaseModel):
    """Request model for /orchestrate endpoint."""
    intent: str = Field(..., description="Intent name (e.g., gmail.triage)")
    inputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Intent-specific parameters"
    )
    mode: Mode = Field(
        default=Mode.auto,
        description="Execution mode: flow/mcp/agent/auto"
    )
    callback_url: Optional[str] = Field(
        None,
        description="URL to POST results when job completes"
    )
    trace: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tracing context (request_id, user_id, etc.)"
    )
    idempotency_key: Optional[str] = Field(
        None,
        description="Unique key for idempotent execution"
    )


class OrchestrateResponse(BaseModel):
    """Response model for /orchestrate endpoint."""
    job_id: str
    status: str  # "succeeded", "failed", "queued"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    will_callback: bool = False
    idempotency_key: Optional[str] = None


class JobCallbackPayload(BaseModel):
    """Payload sent to callback URL when job completes."""
    job_id: str
    intent: str
    status: str  # "succeeded" or "failed"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    logs: list = Field(default_factory=list)


def generate_idempotency_key(intent: str, inputs: Dict[str, Any]) -> str:
    """Generate idempotency key from intent and inputs."""
    payload = json.dumps(
        {"intent": intent, "inputs": inputs},
        sort_keys=True
    )
    return hashlib.sha256(payload.encode()).hexdigest()


async def execute_with_callback(
    job_id: str,
    intent: str,
    mode: Mode,
    inputs: Dict[str, Any],
    trace: Dict[str, Any],
    callback_url: Optional[str]
):
    """Execute job and send callback on completion."""
    import time
    start_time = time.time()
    
    try:
        result = await dispatch(mode, intent, inputs, trace)
        
        payload = JobCallbackPayload(
            job_id=job_id,
            intent=intent,
            status="succeeded",
            result=result,
            metrics={
                "latency_ms": int((time.time() - start_time) * 1000)
            }
        )
        
        # Store result
        _job_store[job_id] = payload.dict()
        
        logger.info(
            f"Job succeeded job_id={job_id} intent={intent}",
            extra={"trace": trace}
        )
        
    except IntentNotFoundError as e:
        payload = JobCallbackPayload(
            job_id=job_id,
            intent=intent,
            status="failed",
            error=f"Intent not found: {str(e)}",
            metrics={
                "latency_ms": int((time.time() - start_time) * 1000)
            }
        )
        _job_store[job_id] = payload.dict()
        
        logger.error(
            f"Job failed (intent not found) job_id={job_id} intent={intent}",
            extra={"trace": trace, "error": str(e)}
        )
        
    except Exception as e:
        payload = JobCallbackPayload(
            job_id=job_id,
            intent=intent,
            status="failed",
            error=str(e),
            metrics={
                "latency_ms": int((time.time() - start_time) * 1000)
            }
        )
        _job_store[job_id] = payload.dict()
        
        logger.error(
            f"Job failed job_id={job_id} intent={intent}",
            extra={"trace": trace, "error": str(e)}
        )
    
    # Send callback if URL provided
    if callback_url:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    callback_url,
                    json=payload.dict()
                )
                response.raise_for_status()
                
            logger.info(
                f"Callback sent job_id={job_id} url={callback_url}",
                extra={"trace": trace}
            )
            
        except Exception as e:
            logger.error(
                f"Callback failed job_id={job_id} url={callback_url}",
                extra={"trace": trace, "error": str(e)}
            )


@router.post("/orchestrate", response_model=OrchestrateResponse)
async def orchestrate(
    req: OrchestrateRequest,
    background_tasks: BackgroundTasks,
    _token: str = Depends(api_auth)
) -> OrchestrateResponse:
    """
    Unified orchestration endpoint.
    
    Routes intent to appropriate executor (flow/mcp/agent).
    Supports both sync and async execution patterns.
    
    - Fast operations (<8s): Returns result synchronously
    - Slow operations: Returns job_id, executes in background
    - Callbacks: POST result to callback_url when complete
    - Idempotency: Duplicate requests return cached result
    
    Requires: Bearer token authentication
    """
    from app.deps.auth import api_auth
    
    # Validate authentication
    try:
        await api_auth(authorization)
    except HTTPException:
        raise HTTPException(401, "Unauthorized")
    
    # Generate job ID
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    
    # Handle idempotency
    idem_key = req.idempotency_key or generate_idempotency_key(
        req.intent,
        req.inputs
    )
    
    # Check for existing result (24h TTL in production)
    for stored_job_id, stored_data in _job_store.items():
        if stored_data.get("idempotency_key") == idem_key:
            logger.info(
                f"Returning cached result job_id={stored_job_id} "
                f"idem={idem_key[:8]}..."
            )
            return OrchestrateResponse(
                job_id=stored_job_id,
                status=stored_data["status"],
                result=stored_data.get("result"),
                error=stored_data.get("error"),
                idempotency_key=idem_key
            )
    
    # Add job_id to trace
    trace = req.trace.copy()
    trace["job_id"] = job_id
    if "request_id" not in trace:
        trace["request_id"] = f"req_{uuid.uuid4().hex[:8]}"
    
    # Determine execution strategy
    # Fast operations: try sync first with timeout
    is_fast_intent = (
        req.intent.endswith(".peek") or
        req.intent.endswith(".read") or
        req.mode == Mode.agent
    )
    
    if is_fast_intent:
        # Try synchronous execution with timeout
        try:
            result = await asyncio.wait_for(
                dispatch(req.mode, req.intent, req.inputs, trace),
                timeout=8.0
            )
            
            # Store result
            job_data = {
                "job_id": job_id,
                "intent": req.intent,
                "status": "succeeded",
                "result": result,
                "idempotency_key": idem_key
            }
            _job_store[job_id] = job_data
            
            return OrchestrateResponse(
                job_id=job_id,
                status="succeeded",
                result=result,
                idempotency_key=idem_key
            )
            
        except asyncio.TimeoutError:
            # Fall through to async execution
            logger.info(
                f"Sync timeout, switching to async job_id={job_id}",
                extra={"trace": trace}
            )
        except IntentNotFoundError as e:
            raise HTTPException(404, f"Intent not found: {str(e)}")
        except OrchestratorError as e:
            raise HTTPException(500, f"Orchestration error: {str(e)}")
        except Exception as e:
            logger.error(
                f"Sync execution failed job_id={job_id}",
                extra={"trace": trace, "error": str(e)}
            )
            raise HTTPException(500, f"Execution failed: {str(e)}")
    
    # Async execution with callback
    background_tasks.add_task(
        execute_with_callback,
        job_id,
        req.intent,
        req.mode,
        req.inputs,
        trace,
        req.callback_url
    )
    
    # Store queued status
    _job_store[job_id] = {
        "job_id": job_id,
        "intent": req.intent,
        "status": "queued",
        "idempotency_key": idem_key
    }
    
    return OrchestrateResponse(
        job_id=job_id,
        status="queued",
        will_callback=bool(req.callback_url),
        idempotency_key=idem_key
    )


@router.get("/jobs/{job_id}", response_model=JobCallbackPayload)
async def get_job_status(
    job_id: str,
    _token: str = Depends(api_auth)
) -> JobCallbackPayload:
    """
    Get job status and result.
    
    Returns last known status and result for a job.
    Useful for polling when callback URL not provided.
    
    Requires: Bearer token authentication
    """
    
    if job_id not in _job_store:
        raise HTTPException(404, f"Job {job_id} not found")
    
    job_data = _job_store[job_id]
    return JobCallbackPayload(**job_data)


@router.post("/callbacks/ingest")
async def ingest_callback(
    payload: Dict[str, Any]
):
    """
    Callback ingestion endpoint.
    
    Receives results from external systems (n8n, ActivePieces).
    Stores result for later retrieval via /jobs/{id}.
    
    Optional: Validate HMAC signature for security.
    """
    # TODO: Add HMAC signature validation
    # signature = headers.get("X-Signature")
    # if not validate_hmac(payload, signature):
    #     raise HTTPException(401, "Invalid signature")
    
    job_id = payload.get("job_id")
    if not job_id:
        raise HTTPException(400, "Missing job_id in payload")
    
    # Store callback data
    _job_store[job_id] = payload
    
    logger.info(
        f"Callback ingested job_id={job_id}",
        extra={"payload": payload}
    )
    
    return {"status": "ok", "job_id": job_id}
