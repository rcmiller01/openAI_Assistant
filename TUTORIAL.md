# Getting Started Tutorial

This tutorial will guide you through setting up and using the OpenAI Assistant Orchestrator.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- PostgreSQL 16+ with pgvector
- Redis 7+
- n8n (optional, for workflow automation)

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/openAI_Assistant.git
cd openAI_Assistant

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Start Services with Docker

```bash
# Development environment
docker-compose -f compose.dev.yml up -d

# Production environment
docker-compose -f compose.prod.yml up -d
```

### 3. Run Database Migrations

```bash
# Using psql directly
psql -U opa -d opa -f backend/migrations/001_initial_schema.sql
psql -U opa -d opa -f backend/migrations/002_hybrid_search_functions.sql

# Or using make
make migrate
```

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Store a memory
curl -X POST http://localhost:8000/orchestrate \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "memory.write",
    "inputs": {
      "text": "My first memory!",
      "tags": ["test", "tutorial"]
    },
    "mode": "agent"
  }'

# Search memories
curl -X POST http://localhost:8000/orchestrate \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "memory.search",
    "inputs": {
      "query": "first memory",
      "k": 5
    },
    "mode": "agent"
  }'
```

## Development Workflow

### Install Dependencies

```bash
# Using pip
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Or using make
make install
```

### Run Tests

```bash
# Unit tests
make test

# With coverage
make test-cov

# Smoke tests
make smoke
```

### Code Quality

```bash
# Format code
make fmt

# Run linters
make lint

# Type check
make type

# Run all checks
make pre-commit
```

## Using the Orchestrator

### Memory Operations

#### Store Memory

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/orchestrate",
        headers={"Authorization": "Bearer your-api-key"},
        json={
            "intent": "memory.write",
            "inputs": {
                "text": "Python is great for ML",
                "tags": ["coding", "ml"],
            },
            "mode": "agent",
        },
    )
    print(response.json())
```

#### Search Memory

```python
response = await client.post(
    "http://localhost:8000/orchestrate",
    headers={"Authorization": "Bearer your-api-key"},
    json={
        "intent": "memory.search",
        "inputs": {
            "query": "machine learning",
            "k": 10,
            "mode": "hybrid",  # hybrid, vector, bm25, or simple
        },
        "mode": "agent",
    },
)
```

### Gmail Operations

#### Triage Emails

```python
response = await client.post(
    "http://localhost:8000/orchestrate",
    headers={"Authorization": "Bearer your-api-key"},
    json={
        "intent": "gmail.triage",
        "inputs": {
            "query": "is:unread",
            "label": "Processed",
            "dry_run": True,  # Preview without applying
        },
        "mode": "flow",
        "flow_webhook": "http://n8n:5678/webhook/gmail-triage",
    },
)
```

### SSH Operations

```python
response = await client.post(
    "http://localhost:8000/orchestrate",
    headers={"Authorization": "Bearer your-api-key"},
    json={
        "intent": "ssh.exec.peek",
        "inputs": {
            "host": "localhost",
            "command": "df -h",
        },
        "mode": "agent",
    },
)
```

## Execution Modes

The orchestrator supports 4 execution modes:

1. **agent** - Direct execution in backend
2. **flow** - Delegate to n8n workflow
3. **mcp** - Use Model Context Protocol
4. **auto** - Automatically choose best mode

```python
{
    "intent": "memory.write",
    "inputs": {...},
    "mode": "auto"  # Let orchestrator decide
}
```

## Advanced Features

### Rate Limiting

```bash
# Enable in .env
RATE_LIMIT_ENABLED=true
DEFAULT_RATE_LIMIT=60  # 60 requests per minute
```

### HMAC Signatures

```bash
# Enable webhook security
HMAC_SECRET=your-secret-key

# Verify signatures in n8n
X-Signature: <hmac-sha256-signature>
```

### Observability

```bash
# Enable structured logging
LOG_FORMAT=json
LOG_LEVEL=INFO

# Enable OpenTelemetry tracing
ENABLE_TRACING=true
OTEL_EXPORTER_TYPE=otlp
OTEL_EXPORTER_ENDPOINT=http://jaeger:4318
```

### Hybrid Search Weights

```python
response = await client.post(
    "http://localhost:8000/orchestrate",
    json={
        "intent": "memory.search",
        "inputs": {
            "query": "python programming",
            "k": 10,
            "mode": "hybrid",
            "bm25_weight": 0.3,  # Keyword weight
            "vector_weight": 0.7,  # Semantic weight
        },
    },
)
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -h localhost -U opa -d opa -c "SELECT 1;"

# Check logs
docker logs opa_postgres
```

### Redis Connection Issues

```bash
# Test Redis
redis-cli ping

# Check connection
docker logs opa_redis
```

### API Errors

```bash
# Check backend logs
docker logs opa_backend

# Enable debug logging
export LOG_LEVEL=DEBUG
```

## Next Steps

- [Integration Guide](INTEGRATION_GUIDE.md) - Connect with ChatGPT, n8n
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [API Reference](API_REFERENCE.md) - Complete API documentation

## Support

- GitHub Issues: [Report a bug](https://github.com/yourusername/openAI_Assistant/issues)
- Discussions: [Ask questions](https://github.com/yourusername/openAI_Assistant/discussions)
