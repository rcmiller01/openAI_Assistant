# Orchestrator Implementation Summary

## What We Built

A unified webhook orchestration system with a single `/orchestrate` endpoint that intelligently routes intents to the appropriate execution engine.

## Architecture

### Core Components

1. **Orchestrate Router** (`app/routers/orchestrate.py`)
   - Single POST `/orchestrate` endpoint
   - Sync execution with 8s timeout
   - Async execution with background tasks + callbacks
   - Job status polling via GET `/jobs/{job_id}`
   - Callback ingestion via POST `/callbacks/ingest`
   - In-memory job store (production: Redis/Postgres)
   - Idempotency via SHA256 key hashing

2. **Orchestrator Core** (`app/core/orchestrator.py`)
   - Mode enum: flow, mcp, agent, auto
   - `run_flow()` - n8n/ActivePieces webhook integration
   - `run_agent()` - Local tool execution with safety checks
   - `run_mcp()` - MCP adapter (stubbed)
   - `auto_select_mode()` - Heuristic routing
   - `dispatch()` - Main routing function

3. **Tool System** (`app/tools/`)
   - `memory.py` - Memory store/search operations
   - `ssh.py` - SSH exec with peek mode for read-only
   - `__init__.py` - Tool registry with get_tool()/list_tools()

## Request Flow

```
Client → POST /orchestrate
  ↓
Parse & validate request
  ↓
Check idempotency key
  ↓
Try sync execution (8s timeout)
  ↓
If timeout → Background task + callback
  ↓
dispatch() selects mode (flow/mcp/agent/auto)
  ↓
Execute via appropriate runner
  ↓
Return result or job_id
```

## Example Usage

### Memory Write (Agent Mode)

**Request:**
```json
POST /orchestrate
{
  "intent": "memory.write",
  "inputs": {
    "text": "The Eiffel Tower is in Paris",
    "tags": ["geography", "landmarks"]
  },
  "mode": "agent"
}
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "item_id": "mem_12345",
    "status": "stored",
    "text_length": 30,
    "tags": ["geography", "landmarks"]
  },
  "mode": "agent",
  "duration_ms": 45
}
```

### SSH Peek (Agent Mode)

**Request:**
```json
POST /orchestrate
{
  "intent": "ssh.exec.peek",
  "inputs": {
    "host": "server.example.com",
    "command": "ls -la /var/log"
  },
  "mode": "agent"
}
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "host": "server.example.com",
    "command": "ls -la /var/log",
    "stdout": "drwxr-xr-x 15 root root...",
    "stderr": "",
    "exit_code": 0,
    "duration_ms": 120
  }
}
```

### Gmail Triage (Flow Mode)

**Request:**
```json
POST /orchestrate
{
  "intent": "gmail.triage",
  "inputs": {
    "since": "1 hour ago",
    "labels": ["inbox", "important"]
  },
  "mode": "flow",
  "callback_url": "https://myapp.com/webhooks/results"
}
```

**Response (Async):**
```json
{
  "status": "accepted",
  "job_id": "job_a1b2c3",
  "message": "Job accepted for async processing",
  "mode": "flow",
  "callback_url": "https://myapp.com/webhooks/results"
}
```

**Later (Callback):**
```json
POST https://myapp.com/webhooks/results
{
  "job_id": "job_a1b2c3",
  "status": "success",
  "result": {
    "processed": 15,
    "archived": 8,
    "replied": 3,
    "flagged": 4
  },
  "duration_ms": 45000
}
```

## Safety Features

### 1. SSH Command Restrictions

```python
# Dangerous command blocked by default
{
  "intent": "ssh.exec",
  "inputs": {"host": "server", "command": "rm -rf /"}
}
# → {"dry_run": true, "note": "Set confirm_dangerous=true"}

# Use peek for read-only
{
  "intent": "ssh.exec.peek",
  "inputs": {"host": "server", "command": "cat /etc/hosts"}
}
# → Executes with allowlist validation
```

### 2. Idempotency

```python
# Same inputs = same result (cached)
key = SHA256(intent + inputs)
if key in job_store:
    return cached_result
```

### 3. Timeout Handling

```python
# Fast: sync execution
if execution_time < 8s:
    return result immediately

# Slow: async with callback
else:
    return job_id, execute in background
```

## Integration Points

### ChatGPT Actions

Single action definition:

```json
{
  "operationId": "orchestrate",
  "summary": "Execute any intent (memory, ssh, workflows)",
  "requestBody": {
    "content": {
      "application/json": {
        "schema": {
          "type": "object",
          "properties": {
            "intent": {"type": "string"},
            "inputs": {"type": "object"},
            "mode": {"enum": ["auto", "flow", "mcp", "agent"]}
          },
          "required": ["intent", "inputs"]
        }
      }
    }
  }
}
```

### n8n Workflows

Map intents to webhook URLs:

```python
INTENT_FLOW_MAP = {
    "gmail.triage": "http://n8n:5678/webhook/gmail-triage",
    "slack.summarize": "http://n8n:5678/webhook/slack-summarize",
    "calendar.schedule": "http://n8n:5678/webhook/calendar-schedule"
}
```

### MCP Integration (Coming Soon)

```python
async def run_mcp(intent, inputs, trace):
    # Start MCP client subprocess
    # Call tool via stdio protocol
    # Return result and cleanup
    pass
```

## File Structure

```
backend/
├── app/
│   ├── core/
│   │   └── orchestrator.py        # Main routing logic
│   ├── routers/
│   │   └── orchestrate.py         # FastAPI endpoint
│   ├── tools/
│   │   ├── __init__.py            # Tool registry
│   │   ├── memory.py              # Memory operations
│   │   └── ssh.py                 # SSH operations
│   └── main.py                    # Mount orchestrate router
├── test_orchestrator.py           # Test suite
└── ORCHESTRATOR.md                # Documentation
```

## Testing

Run all tests:
```bash
python backend/test_orchestrator.py
```

Tests cover:
- Memory write/search
- SSH peek mode
- SSH dangerous command blocking
- Auto mode selection
- Idempotency
- Job status polling

## Next Steps

### Short Term
1. ✅ Create tool modules (memory, ssh)
2. ✅ Create tool registry
3. ✅ Update orchestrator to use registry
4. ✅ Create test suite
5. ✅ Write documentation
6. 🔄 Test with live server
7. 🔄 Create n8n flow examples

### Medium Term
- Replace in-memory job store with Redis
- Implement HMAC signature validation
- Add metrics/monitoring
- Create more tool modules (fs, fetch, etc)
- Build n8n workflows for common intents

### Long Term
- Complete MCP adapter
- Add streaming responses
- Build ChatGPT Actions schema generator
- Create dashboard for job monitoring
- Add circuit breakers for external services

## Benefits

1. **Simplified Integration** - One endpoint instead of many
2. **Flexible Execution** - Choose best engine per intent
3. **Safety Built-in** - Allowlists, confirmations, dry-run
4. **Async Support** - Handle long-running jobs gracefully
5. **Idempotent** - Safe to retry failed requests
6. **Extensible** - Add new tools via simple registry
7. **Observable** - Tracing and job status built-in

## Conclusion

The orchestrator provides a clean abstraction over multiple execution engines while maintaining safety, observability, and ease of use. It's ready for testing and integration with ChatGPT Actions and n8n workflows.
