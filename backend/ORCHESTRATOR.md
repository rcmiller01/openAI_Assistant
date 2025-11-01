# Orchestrator Architecture

## Overview

The orchestrator provides a unified `/orchestrate` webhook endpoint that routes intents to appropriate execution engines:

- **Flow Mode**: n8n or ActivePieces workflows
- **MCP Mode**: Model Context Protocol adapters  
- **Agent Mode**: Local in-process tool execution
- **Auto Mode**: Heuristic-based mode selection

## Quick Start

### Start the Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Test the Endpoint

```bash
python test_orchestrator.py
```

Or manually:

```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "memory.write",
    "inputs": {"text": "Hello World", "tags": ["test"]},
    "mode": "agent"
  }'
```

## Request Format

```json
{
  "intent": "memory.write",
  "inputs": {
    "text": "Data to store",
    "tags": ["example"]
  },
  "mode": "agent",
  "callback_url": "https://example.com/webhook",
  "context": {
    "user_id": "user_123",
    "session_id": "sess_abc"
  }
}
```

### Fields

- **intent** (required): Intent pattern like `memory.write`, `ssh.exec.peek`
- **inputs** (required): Intent-specific parameters
- **mode** (optional): Execution mode - `flow`, `mcp`, `agent`, or `auto` (default)
- **callback_url** (optional): URL for async result delivery
- **context** (optional): Additional metadata for tracing

## Response Format

### Sync Response (fast operations)

```json
{
  "status": "success",
  "result": {
    "item_id": "mem_12345",
    "status": "stored"
  },
  "mode": "agent",
  "duration_ms": 45
}
```

### Async Response (slow operations)

```json
{
  "status": "accepted",
  "job_id": "job_abc123",
  "message": "Job accepted for async processing",
  "mode": "flow",
  "callback_url": "https://example.com/webhook"
}
```

Poll status:
```bash
curl http://localhost:8000/jobs/job_abc123
```

## Execution Modes

### Agent Mode

Fast, local in-process execution. Best for:
- Memory operations (`memory.write`, `memory.search`)
- Read-only SSH commands (`ssh.exec.peek`)
- Operations under 8 seconds

**Available Tools:**
- `memory.write` - Store text with embeddings
- `memory.search` - Semantic + keyword search
- `ssh.exec` - Execute SSH command (requires `confirm_dangerous=true`)
- `ssh.exec.peek` - Safe read-only SSH operations

### Flow Mode

External workflow orchestration via n8n/ActivePieces. Best for:
- Complex multi-step workflows
- Gmail/Slack/API integrations
- Long-running processes

**Example Intents:**
- `gmail.triage` - Classify and respond to emails
- `slack.summarize` - Digest channel activity
- `calendar.schedule` - Smart meeting scheduling

### MCP Mode

Model Context Protocol integration (coming soon). Best for:
- Standardized tool discovery
- Multi-agent coordination
- Protocol-compliant systems

### Auto Mode

Heuristic selection:
- Local intents (`memory.*`, `ssh.exec.peek`) → **agent**
- Workflow intents (`gmail.*`, `slack.*`) → **flow**
- MCP protocol intents → **mcp**

## Safety Features

### SSH Command Safety

```python
# This will be blocked
{
  "intent": "ssh.exec",
  "inputs": {
    "host": "server.com",
    "command": "rm -rf /"
  }
}
# Response: {"dry_run": true, "note": "Set confirm_dangerous=true"}
```

### Idempotency

Same request = same response (cached for 1 hour):

```python
# Both requests return identical result
POST /orchestrate {"intent": "memory.write", "inputs": {...}}
POST /orchestrate {"intent": "memory.write", "inputs": {...}}
```

Idempotency key: `SHA256(intent + inputs)`

## Integration Examples

### ChatGPT Actions

```json
{
  "openapi": "3.0.0",
  "paths": {
    "/orchestrate": {
      "post": {
        "operationId": "orchestrate",
        "summary": "Execute any intent",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/OrchestrateRequest"
              }
            }
          }
        }
      }
    }
  }
}
```

### n8n Workflow

1. Create webhook trigger: `http://n8n:5678/webhook/gmail-triage`
2. Set environment variable: `N8N_WEBHOOK_BASE=http://n8n:5678/webhook`
3. Call orchestrator:

```json
{
  "intent": "gmail.triage",
  "inputs": {"since": "1 hour ago"},
  "mode": "flow"
}
```

### Python Client

```python
import requests

def orchestrate(intent: str, inputs: dict, mode: str = "auto"):
    response = requests.post(
        "http://localhost:8000/orchestrate",
        json={
            "intent": intent,
            "inputs": inputs,
            "mode": mode
        }
    )
    return response.json()

# Use it
result = orchestrate("memory.write", {
    "text": "Important note",
    "tags": ["personal"]
})
print(result)
```

## Configuration

### Environment Variables

```bash
# n8n integration
N8N_WEBHOOK_BASE=http://n8n:5678/webhook

# ActivePieces integration  
ACTIVEPIECES_BASE=http://activepieces:3000/api/v1

# Timeouts
ORCHESTRATOR_SYNC_TIMEOUT=8  # Seconds before going async
ORCHESTRATOR_FLOW_TIMEOUT=120  # Max flow execution time
```

## Architecture Diagram

```
┌─────────────┐
│   ChatGPT   │
│   Actions   │
└──────┬──────┘
       │
       │ POST /orchestrate
       │
┌──────▼───────────────────────────────────┐
│         FastAPI Orchestrator             │
│  (app/routers/orchestrate.py)            │
└──────┬───────────────────────────────────┘
       │
       │ dispatch()
       │
┌──────▼─────────────────┐
│  Mode Selection        │
│  (auto/flow/mcp/agent) │
└──┬─────────┬─────────┬─┘
   │         │         │
   │         │         │
┌──▼──┐  ┌──▼──┐  ┌──▼──────┐
│ n8n │  │ MCP │  │  Agent  │
│Flow │  │Adptr│  │  Tools  │
└─────┘  └─────┘  └─────────┘
```

## Adding New Tools

### 1. Create Tool Module

```python
# app/tools/my_tool.py
async def my_operation(param1: str, param2: int) -> dict:
    """Execute my operation."""
    return {"status": "ok", "result": param1 * param2}
```

### 2. Register in Tools

```python
# app/tools/__init__.py
from app.tools import my_tool

TOOL_REGISTRY = {
    "my.operation": my_tool.my_operation,
    # ... existing tools
}
```

### 3. Test

```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "my.operation",
    "inputs": {"param1": "test", "param2": 5},
    "mode": "agent"
  }'
```

## Troubleshooting

### Tool Not Found

```json
{"error": "Intent 'xyz' not found. Available: [...]"}
```

Check `app/tools/__init__.py` registration.

### Timeout

Increase `ORCHESTRATOR_SYNC_TIMEOUT` or use async mode.

### SSH Blocked

Use `ssh.exec.peek` for read-only commands or set `confirm_dangerous=true` for writes.

### Idempotency Issues

Change inputs slightly to generate new idempotency key.

## Development

### Run Tests

```bash
python test_orchestrator.py
```

### Check Logs

```bash
tail -f logs/orchestrator.log
```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Production Deployment

See [DEPLOYMENT.md](../docker/DEPLOYMENT.md) for full production setup.

Quick checklist:
- ✅ Use environment variables for secrets
- ✅ Enable HMAC signature validation for callbacks
- ✅ Replace in-memory job store with Redis/Postgres
- ✅ Set up proper logging and monitoring
- ✅ Configure rate limiting
- ✅ Use HTTPS for all webhooks

## Future Enhancements

- [ ] Redis job store for multi-instance deployments
- [ ] Complete MCP adapter implementation
- [ ] HMAC signature validation for callbacks
- [ ] Streaming responses for long operations
- [ ] Tool usage analytics and monitoring
- [ ] Auto-retry with exponential backoff
- [ ] Circuit breakers for external services
- [ ] Tool cost tracking and quotas
