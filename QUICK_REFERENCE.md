# Quick Reference: Orchestrator Commands

## Common Operations

### Memory Operations

**Store Information**
```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "memory.write",
    "inputs": {
      "text": "User prefers Python and dark mode",
      "tags": ["preferences", "user-profile"]
    }
  }'
```

**Search Memories**
```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "memory.search",
    "inputs": {
      "query": "programming language preference",
      "k": 5
    }
  }'
```

### Gmail Operations

**Triage Emails (Dry Run)**
```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "gmail.triage",
    "inputs": {
      "query": "is:unread older_than:2d",
      "label": "INBOX/Processed",
      "dry_run": true
    },
    "mode": "flow"
  }'
```

**Apply Labels (After Confirmation)**
```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "gmail.triage",
    "inputs": {
      "query": "is:unread older_than:2d",
      "label": "INBOX/Processed",
      "dry_run": false
    },
    "mode": "flow"
  }'
```

### SSH Operations

**Safe Read-Only Commands**
```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "ssh.exec.peek",
    "inputs": {
      "host": "server.example.com",
      "command": "df -h"
    }
  }'
```

**Check Command (Dry Run)**
```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "ssh.exec",
    "inputs": {
      "host": "server.example.com",
      "command": "systemctl restart nginx"
    }
  }'
# Returns dry_run preview
```

**Execute Command (Confirmed)**
```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "ssh.exec",
    "inputs": {
      "host": "server.example.com",
      "command": "systemctl restart nginx",
      "confirm_dangerous": true
    }
  }'
```

### Job Management

**Check Job Status**
```bash
curl http://localhost:8000/jobs/job_abc123 \
  -H "Authorization: Bearer $API_KEY"
```

**Poll Until Complete**
```bash
# Bash loop
while true; do
  STATUS=$(curl -s http://localhost:8000/jobs/job_abc123 \
    -H "Authorization: Bearer $API_KEY" | jq -r .status)
  echo "Status: $STATUS"
  [ "$STATUS" = "success" ] && break
  [ "$STATUS" = "error" ] && break
  sleep 2
done
```

## Test Payloads

**Using Test Files**
```bash
# Memory write
curl -X POST http://localhost:8000/orchestrate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d @backend/test_payloads/memory_write.json

# Gmail triage
curl -X POST http://localhost:8000/orchestrate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d @backend/test_payloads/gmail_triage.json

# SSH peek
curl -X POST http://localhost:8000/orchestrate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d @backend/test_payloads/ssh_peek.json
```

## Docker Commands

**Start Services**
```bash
cd backend/docker
docker-compose -f compose.core1.yml up -d
```

**View Logs**
```bash
# All services
docker-compose -f compose.core1.yml logs -f

# Specific service
docker logs backend -f
docker logs n8n -f
docker logs postgres -f
```

**Restart Service**
```bash
docker-compose -f compose.core1.yml restart backend
```

**Stop All**
```bash
docker-compose -f compose.core1.yml down
```

## n8n Commands

**Access n8n UI**
```
http://localhost:5678
```

**Import Workflow**
```
1. Workflows → Import from File
2. Select n8n_workflows/gmail-triage.json
3. Activate workflow
```

**Test Webhook**
```bash
curl -X POST http://localhost:5678/webhook/gmail-triage \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "intent": "gmail.triage",
      "inputs": {"query": "is:unread", "dry_run": true},
      "trace": {"request_id": "test", "job_id": "test"}
    }
  }'
```

## Development Commands

**Run Tests**
```bash
cd backend
python test_orchestrator.py
```

**Start Backend (Dev Mode)**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Check Health**
```bash
curl http://localhost:8000/health
```

**Check API Docs**
```
http://localhost:8000/docs
```

## Environment Variables

**Required Variables**
```bash
# .env
API_KEY=your-long-random-api-key
DATABASE_URL=postgresql://user:pass@postgres:5432/assistant
N8N_WEBHOOK_BASE=http://n8n:5678/webhook
```

**Optional Variables**
```bash
# Timeouts
ORCHESTRATOR_SYNC_TIMEOUT=8
ORCHESTRATOR_FLOW_TIMEOUT=120

# n8n Auth
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=secure-password

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

## Troubleshooting

**Check Service Status**
```bash
docker ps
curl http://localhost:8000/health
curl http://localhost:5678
```

**View Recent Errors**
```bash
docker logs backend --tail 50 | grep ERROR
```

**Clear Job Store**
```bash
# Restart backend (in-memory store will clear)
docker restart backend
```

**Reset Database**
```bash
docker exec -it postgres psql -U user -d assistant
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
# Then restart backend to rebuild tables
```

## Common Intent Patterns

| Intent | Mode | Speed | Use Case |
|--------|------|-------|----------|
| `memory.write` | agent | Fast | Store information |
| `memory.search` | agent | Fast | Retrieve context |
| `gmail.triage` | flow | Slow | Organize emails |
| `ssh.exec.peek` | agent | Fast | Read-only SSH |
| `ssh.exec` | agent | Medium | Write SSH commands |
| `digest.daily` | flow | Slow | Generate summaries |

## Response Status Codes

| Status | Meaning | Next Step |
|--------|---------|-----------|
| `success` | Completed synchronously | Use result immediately |
| `accepted` | Running async | Poll /jobs/{id} |
| `error` | Failed | Check error message |

## Safety Checklist

- [ ] Always use `dry_run: true` first for destructive operations
- [ ] Verify API key is secure (not default)
- [ ] Check allowlists before SSH commands
- [ ] Confirm operations with user before executing
- [ ] Monitor logs for suspicious activity
- [ ] Backup database regularly
- [ ] Use HTTPS in production
- [ ] Rotate API keys periodically

## Quick Links

- **API Docs**: http://localhost:8000/docs
- **n8n UI**: http://localhost:5678
- **Health Check**: http://localhost:8000/health
- **Orchestrator Guide**: [ORCHESTRATOR.md](backend/ORCHESTRATOR.md)
- **Integration Guide**: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- **ChatGPT Actions**: [chatgpt_actions.json](chatgpt_actions.json)
