# API Reference

Complete API documentation for the OpenAI Assistant Orchestrator.

## Base URL

```
http://localhost:8000
```

## Authentication

All requests require an API key in the Authorization header:

```
Authorization: Bearer your-api-key
```

## Core Endpoints

### POST /orchestrate

Main orchestration endpoint for executing intents.

**Request Body:**

```json
{
  "intent": "string",        // Required: Intent to execute
  "inputs": {},              // Required: Intent-specific inputs
  "mode": "agent|flow|mcp|auto",  // Execution mode
  "flow_webhook": "string",  // Optional: n8n webhook URL
  "callback_url": "string",  // Optional: Async callback URL
  "metadata": {}             // Optional: Additional context
}
```

**Response:**

```json
{
  "job_id": "string",
  "status": "completed|pending|failed",
  "result": {},
  "error": null,
  "mode": "agent|flow|mcp",
  "duration_ms": 123
}
```

**Status Codes:**
- 200: Success
- 400: Invalid request
- 401: Unauthorized
- 429: Rate limit exceeded
- 500: Server error

### GET /jobs/{job_id}

Get status of an async job.

**Response:**

```json
{
  "id": "string",
  "intent": "string",
  "status": "pending|running|completed|failed",
  "result": {},
  "error": null,
  "created_at": "2025-11-01T00:00:00Z",
  "completed_at": "2025-11-01T00:00:05Z",
  "duration_seconds": 5.0
}
```

### POST /callbacks/ingest

Receive async callbacks from workflows.

**Headers:**
- `X-Signature`: HMAC signature (if enabled)

**Request Body:**

```json
{
  "job_id": "string",
  "status": "completed|failed",
  "result": {},
  "error": null
}
```

### GET /health

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```

## Intents

### Memory Intents

#### memory.write / memory.store

Store a memory item with vector embedding.

**Inputs:**

```json
{
  "text": "string",           // Required
  "tags": ["string"],         // Optional
  "speaker_id": "string"      // Optional
}
```

**Result:**

```json
{
  "item_id": "string",
  "status": "stored",
  "text_length": 123,
  "tags": ["string"],
  "created_at": "2025-11-01T00:00:00Z",
  "storage": "database|memory"
}
```

#### memory.search / memory.query

Search memories using hybrid BM25 + vector search.

**Inputs:**

```json
{
  "query": "string",          // Required
  "k": 10,                    // Optional: results count
  "tags": ["string"],         // Optional: tag filter
  "mode": "hybrid|vector|bm25|simple",  // Optional
  "bm25_weight": 0.5,         // Optional: 0-1
  "vector_weight": 0.5        // Optional: 0-1
}
```

**Result:**

```json
{
  "query": "string",
  "items": [
    {
      "id": "string",
      "text": "string",
      "tags": ["string"],
      "created_at": "2025-11-01T00:00:00Z",
      "bm25_score": 0.85,
      "vector_score": 0.92,
      "combined_score": 0.885
    }
  ],
  "total_items": 25,
  "mode": "hybrid",
  "storage": "database"
}
```

#### memory.list

List all memories with pagination.

**Inputs:**

```json
{
  "limit": 50,                // Optional: default 50
  "offset": 0,                // Optional: default 0
  "tags": ["string"]          // Optional: tag filter
}
```

**Result:**

```json
{
  "items": [...],
  "total": 100,
  "limit": 50,
  "offset": 0,
  "has_more": true,
  "storage": "database"
}
```

### Gmail Intents

#### gmail.triage

Triage Gmail messages with labels.

**Inputs:**

```json
{
  "query": "is:unread",       // Gmail search query
  "label": "Processed",       // Label to apply
  "dry_run": false,           // Preview mode
  "max_results": 20           // Max messages
}
```

**Result:**

```json
{
  "dry_run": false,
  "messages_found": 15,
  "messages_labeled": 15,
  "preview": [...],           // If dry_run=true
  "label": "Processed"
}
```

#### gmail.search

Search Gmail messages.

**Inputs:**

```json
{
  "query": "from:example@gmail.com",
  "max_results": 10
}
```

#### gmail.recent

Get recent Gmail messages.

**Inputs:**

```json
{
  "hours": 24,
  "label": "INBOX"
}
```

### Filesystem Intents

#### fs.list

List directory contents (within allowlist).

**Inputs:**

```json
{
  "path": "/work/data"
}
```

**Result:**

```json
{
  "path": "/work/data",
  "items": [
    {
      "name": "file.txt",
      "type": "file",
      "size": 1024
    }
  ],
  "total": 5
}
```

#### fs.read

Read file contents (within allowlist, byte cap).

**Inputs:**

```json
{
  "path": "/work/data/file.txt",
  "max_bytes": 10485760        // 10MB default
}
```

#### fs.head

Read first N lines of file.

**Inputs:**

```json
{
  "path": "/work/data/log.txt",
  "lines": 100
}
```

### SSH Intents

#### ssh.exec

Execute SSH command (requires confirmation for unsafe).

**Inputs:**

```json
{
  "host": "localhost",
  "command": "df -h",
  "confirm_dangerous": false   // Must be true for unsafe commands
}
```

#### ssh.exec.peek

Execute safe SSH command (auto-approved).

**Inputs:**

```json
{
  "host": "localhost",
  "command": "ls -la"
}
```

## Rate Limiting

When rate limiting is enabled:

**Headers in Response:**
- `X-RateLimit-Limit`: Max requests per window
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp for reset

**429 Response:**

```json
{
  "error": "Rate limit exceeded",
  "retry_after": 45,
  "limit": 60,
  "window_seconds": 60
}
```

## HMAC Signatures

When HMAC is enabled for callbacks:

**Generate Signature:**

```python
import hmac
import hashlib

payload = request.body  # Raw bytes
secret = "your-secret-key"
signature = hmac.new(
    secret.encode(),
    payload,
    hashlib.sha256
).hexdigest()

headers = {"X-Signature": signature}
```

**Verify Signature:**

```python
from app.core.hmac import verify_signature

is_valid = verify_signature(
    payload=request.body,
    signature=request.headers["X-Signature"]
)
```

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message",
  "detail": "Detailed explanation",
  "request_id": "string",
  "timestamp": "2025-11-01T00:00:00Z"
}
```

## Environment Variables

Key configuration options:

```bash
# API
API_KEY=your-secret-key
APP_ENV=production|development
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR

# Database
POSTGRES_HOST=localhost
POSTGRES_DB=opa
POSTGRES_USER=opa
POSTGRES_PASSWORD=password

# Redis
REDIS_URL=redis://localhost:6379

# Security
HMAC_SECRET=your-hmac-secret
RATE_LIMIT_ENABLED=true
DEFAULT_RATE_LIMIT=60

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSIONS=384

# Filesystem Security
FS_ALLOWED_PATHS=/work,/tmp,/data
FS_MAX_READ_BYTES=10485760

# SSH Security
SSH_ALLOWED_HOSTS=localhost,127.0.0.1
```

## Examples

See [TUTORIAL.md](TUTORIAL.md) for complete usage examples.
