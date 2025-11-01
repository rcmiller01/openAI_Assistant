# Integration Guide: ChatGPT Actions + n8n + Orchestrator

This guide shows how to integrate ChatGPT with your orchestrator and n8n workflows.

## Architecture Overview

```
┌─────────────┐
│   ChatGPT   │ Single Action: /orchestrate
│   Custom    │
│    GPT      │
└──────┬──────┘
       │
       │ POST /orchestrate {"intent": "...", "inputs": {...}}
       │
┌──────▼─────────────────────────────────────┐
│      FastAPI Orchestrator                  │
│      (Single Unified Endpoint)             │
└──────┬────────────┬──────────────┬─────────┘
       │            │              │
   ┌───▼───┐    ┌───▼───┐     ┌───▼────┐
   │ Agent │    │  n8n  │     │  MCP   │
   │ Tools │    │ Flows │     │Adapter │
   └───────┘    └───┬───┘     └────────┘
                    │
       ┌────────────┼────────────┐
       │            │            │
   ┌───▼───┐    ┌───▼───┐   ┌───▼──────┐
   │ Gmail │    │ Slack │   │  Sheets  │
   └───────┘    └───────┘   └──────────┘
```

## Step 1: Set Up n8n Workflows

### Import gmail.triage Workflow

1. Open n8n: `http://localhost:5678`
2. Go to **Workflows** → **Add workflow** → **Import from File**
3. Upload `n8n_workflows/gmail-triage.json`
4. **Activate** the workflow (toggle in top-right)

### Configure Gmail Credentials

1. Go to **Credentials** → **Add Credential**
2. Select **Gmail OAuth2 API**
3. Fill in your Google OAuth2 credentials:
   - Client ID: `your-client-id.apps.googleusercontent.com`
   - Client Secret: `your-client-secret`
4. Click **Connect my account** and authorize
5. Save credential

### Test the Workflow

In n8n editor:

1. Click the workflow
2. Click **Execute Workflow** button
3. In test panel, provide webhook data:

```json
{
  "body": {
    "intent": "gmail.triage",
    "inputs": {
      "query": "is:unread in:inbox",
      "dry_run": true,
      "max_results": 5
    },
    "trace": {
      "request_id": "req_test123",
      "job_id": "job_test456"
    }
  }
}
```

4. Verify nodes execute successfully
5. Check **Respond to Webhook** node output

## Step 2: Configure Orchestrator

### Update Environment Variables

Edit `.env`:

```bash
# n8n Integration
N8N_WEBHOOK_BASE=http://n8n:5678/webhook

# API Authentication
API_KEY=your-long-random-api-key-here

# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/assistant
```

### Verify Intent Mapping

The orchestrator automatically maps intents to webhook URLs:

```python
# In app/core/orchestrator.py
INTENT_FLOW_MAP = {
    "gmail.triage": "http://n8n:5678/webhook/gmail-triage",
    "slack.summarize": "http://n8n:5678/webhook/slack-summarize",
    # Add more mappings as you create workflows
}
```

To add new intents, update this mapping.

### Start Services

```bash
# Start Docker Compose
cd backend/docker
docker-compose -f compose.core1.yml up -d

# Check logs
docker logs backend -f
docker logs n8n -f
```

## Step 3: Test Integration

### Test Local Agent Mode

```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d @backend/test_payloads/memory_write.json
```

Expected response:
```json
{
  "job_id": "job_abc123",
  "status": "success",
  "result": {
    "item_id": "mem_12345",
    "status": "stored",
    "text_length": 108,
    "tags": ["preferences", "user-profile", "python"]
  },
  "mode": "agent",
  "duration_ms": 45
}
```

### Test Flow Mode (n8n)

```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d @backend/test_payloads/gmail_triage.json
```

Expected response (dry run):
```json
{
  "job_id": "job_def456",
  "status": "success",
  "result": {
    "dry_run": true,
    "found": 15,
    "would_apply_label": "INBOX/Processed",
    "preview": [
      {
        "id": "abc123",
        "from": "sender@example.com",
        "subject": "Important Email"
      }
    ],
    "note": "No changes made. Set dry_run=false to apply label."
  },
  "mode": "flow",
  "duration_ms": 2500
}
```

### Run Test Suite

```bash
cd backend
python test_orchestrator.py
```

This tests:
- Memory write/search
- SSH peek mode
- SSH dangerous command blocking
- Auto mode selection
- Idempotency

## Step 4: Create ChatGPT Custom GPT

### 1. Create New GPT

1. Go to [ChatGPT](https://chat.openai.com)
2. Click your profile → **My GPTs**
3. Click **Create a GPT**
4. Click **Configure**

### 2. Set GPT Details

**Name**: AI Assistant with Memory

**Description**:
```
Personal AI assistant with persistent memory, Gmail automation, 
and SSH capabilities. Can remember conversations, organize emails, 
and execute safe remote commands.
```

**Instructions**:
```
You are a helpful AI assistant with the following capabilities:

1. MEMORY: Store and recall information about the user
   - Use memory.write to save important facts, preferences, and context
   - Use memory.search to retrieve relevant information
   - Always check memory before answering questions about the user

2. GMAIL: Automate email organization
   - Use gmail.triage to find and label emails
   - Always use dry_run=true first to preview changes
   - Confirm with user before applying labels

3. SSH: Execute safe remote commands
   - Use ssh.exec.peek for read-only commands (ls, cat, ps, df, etc.)
   - Never use ssh.exec without explicit user confirmation
   - Always show dry run results first

IMPORTANT:
- When user shares personal information, automatically store it in memory
- Use tags to categorize memories: preferences, work, personal, projects
- For any destructive operation, show dry run first and ask for confirmation
- Be proactive about organizing information and suggesting automations

Example interactions:
- User: "I prefer dark mode" → Immediately call memory.write
- User: "Archive old emails" → Show gmail.triage with dry_run=true first
- User: "Check disk space" → Use ssh.exec.peek with df -h
```

### 3. Configure Actions

Click **Add actions** and paste the entire contents of `chatgpt_actions.json`:

```bash
# Copy the file contents
cat chatgpt_actions.json
```

Or manually configure:

**Authentication**: Bearer
**API Key**: Your API key from `.env`

**Schema**:
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "AI Assistant Orchestrator",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "https://your-domain.com"
    }
  ],
  "paths": {
    "/orchestrate": { ... }
  }
}
```

### 4. Test Actions

In the GPT chat:

**Test Memory**:
```
User: I love Python and use it for data analysis
GPT: [Calls memory.write with text and tags]
GPT: "I've stored that in memory! I'll remember your Python preference."
```

**Test Gmail**:
```
User: Can you organize my old unread emails?
GPT: [Calls gmail.triage with dry_run=true]
GPT: "I found 15 unread emails older than 2 days. Would you like me to 
     apply the 'Processed' label?"
User: Yes
GPT: [Calls gmail.triage with dry_run=false]
GPT: "Done! Labeled 15 emails."
```

**Test SSH**:
```
User: Check disk space on my server
GPT: [Calls ssh.exec.peek with df -h]
GPT: "Your server has 45% disk usage on /dev/sda1..."
```

## Step 5: Add More Workflows

### Create memory.digest Flow

```json
{
  "intent": "memory.digest",
  "inputs": {
    "since": "24h",
    "tags": ["work", "projects"],
    "format": "markdown"
  }
}
```

**Workflow**:
1. Call FastAPI `/api/v1/memory/search` with tags
2. Group results by tag
3. Format as markdown digest
4. Return formatted text

### Create slack.summarize Flow

```json
{
  "intent": "slack.summarize",
  "inputs": {
    "channels": ["general", "engineering"],
    "since": "24h"
  }
}
```

**Workflow**:
1. Fetch messages from Slack channels
2. Call OpenAI to summarize key points
3. Post summary to user's DM
4. Return summary

## Step 6: Production Deployment

### Expose via Cloudflare Tunnel

Update `compose.core3.yml`:

```yaml
cloudflared:
  image: cloudflare/cloudflared:latest
  command: tunnel --no-autoupdate run
  environment:
    - TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}
  networks:
    - edge
    - core
```

### Update ChatGPT Actions URL

Change server URL in actions schema:
```json
{
  "servers": [
    {
      "url": "https://your-custom-domain.com"
    }
  ]
}
```

### Enable HTTPS

Update nginx configuration:
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cloudflare-origin.pem;
    ssl_certificate_key /etc/nginx/ssl/cloudflare-origin-key.pem;
    
    location /orchestrate {
        proxy_pass http://backend:8000;
        # ... proxy settings
    }
}
```

### Secure API Keys

Use Docker secrets or environment variables:

```bash
# Generate secure API key
openssl rand -hex 32 > .api_key

# Reference in compose
docker-compose -f compose.core1.yml \
  -e API_KEY=$(cat .api_key) \
  up -d
```

## Troubleshooting

### ChatGPT Can't Reach API

**Check**:
1. Server is running: `curl http://localhost:8000/health`
2. API key is correct
3. CORS is enabled (already configured in FastAPI)
4. Cloudflare tunnel is connected

**Fix**:
```bash
# Check backend logs
docker logs backend -f

# Verify API key
curl -X POST http://localhost:8000/orchestrate \
  -H "Authorization: Bearer YOUR_KEY" \
  -d '{"intent":"memory.write","inputs":{"text":"test"}}'
```

### n8n Workflow Times Out

**Check**:
1. Workflow is activated
2. Credentials are valid
3. Gmail API quota not exceeded

**Fix**:
- Reduce `max_results` in gmail.triage
- Add error handling nodes
- Increase timeout in orchestrator (default 120s)

### ChatGPT Doesn't Use Actions

**Check**:
1. Actions are properly configured in GPT settings
2. Schema is valid OpenAPI 3.0
3. Examples are clear in operation descriptions

**Fix**:
- Update GPT instructions to be more explicit about when to use actions
- Add more examples in action descriptions
- Test actions manually in GPT interface

### Memory Not Persisting

**Check**:
1. PostgreSQL is running: `docker ps | grep postgres`
2. Database schema is initialized
3. Embeddings are being generated

**Fix**:
```bash
# Check database
docker exec -it postgres psql -U user -d assistant
\dt  # List tables
SELECT COUNT(*) FROM memory_items;

# Check backend logs
docker logs backend -f | grep memory
```

## Best Practices

### 1. Always Use Dry Run First

For any destructive operation:
```json
{
  "intent": "gmail.triage",
  "inputs": {
    "dry_run": true  // Always preview first!
  }
}
```

### 2. Tag Memories Consistently

Use clear, hierarchical tags:
```json
{
  "tags": ["preferences", "work", "python"]  // Good
  "tags": ["stuff", "things"]  // Bad
}
```

### 3. Implement Rate Limiting

Already configured in `app/deps/auth.py`:
- 100 requests per hour per API key
- Configurable via `RATE_LIMIT_*` env vars

### 4. Monitor Usage

Check job status:
```bash
curl http://localhost:8000/jobs/job_abc123 \
  -H "Authorization: Bearer YOUR_KEY"
```

View logs:
```bash
# Orchestrator logs
docker logs backend -f | grep orchestrate

# n8n execution logs
docker logs n8n -f
```

### 5. Backup Everything

- PostgreSQL: Automated backups via cron (see `compose.core1.yml`)
- n8n workflows: Export regularly via UI
- Redis: AOF persistence enabled

## Next Steps

1. **Add More Intents**:
   - `calendar.schedule` - Smart meeting scheduling
   - `notes.sync` - Sync with Notion/Obsidian
   - `tasks.create` - Create tasks in project management tools

2. **Enhance Workflows**:
   - Add approval steps (Slack buttons)
   - Implement retry logic
   - Add scheduling (daily digests)

3. **Improve Observability**:
   - Set up Grafana dashboards
   - Add Prometheus metrics
   - Configure alerts

4. **Scale**:
   - Replace in-memory job store with Redis
   - Add load balancer for multiple backend instances
   - Implement circuit breakers

## Resources

- [n8n Documentation](https://docs.n8n.io)
- [ChatGPT Actions Guide](https://platform.openai.com/docs/actions)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Orchestrator README](backend/ORCHESTRATOR.md)
