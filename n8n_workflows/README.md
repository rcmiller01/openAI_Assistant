# n8n Workflow Recipes

This directory contains ready-to-import n8n workflows that integrate with the orchestrator.

## Quick Start

### 1. Import Workflows

In n8n UI:
1. Go to **Workflows** → **Import from File**
2. Upload `gmail-triage.json`
3. Activate the workflow

### 2. Configure Webhooks

Each workflow creates a webhook endpoint. The URL format is:
```
http://n8n:5678/webhook/gmail-triage
```

Set this in your environment:
```bash
N8N_WEBHOOK_BASE=http://n8n:5678/webhook
```

### 3. Test from Orchestrator

```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "intent": "gmail.triage",
    "inputs": {
      "query": "is:unread in:inbox",
      "label": "INBOX/Processed",
      "dry_run": true,
      "max_results": 20
    },
    "mode": "flow"
  }'
```

## Available Workflows

### 1. gmail.triage

**File**: `gmail-triage.json`

**Intent**: `gmail.triage`

**Inputs**:
- `query` (string): Gmail search query (default: "is:unread")
- `label` (string, optional): Label ID to apply
- `dry_run` (boolean): Preview without changes (default: false)
- `max_results` (number): Max emails to process (default: 20)

**Flow**:
1. Parse inputs from webhook
2. Search Gmail with query
3. If dry_run → return preview
4. If label provided → apply label to emails
5. Return counts and email IDs

**Example Response**:
```json
{
  "status": "success",
  "result": {
    "query": "is:unread in:inbox",
    "found": 15,
    "labeled": 15,
    "label_id": "INBOX/Processed",
    "email_ids": ["abc123", "def456", ...]
  },
  "trace": {...}
}
```

**Dry Run Response**:
```json
{
  "status": "success",
  "result": {
    "dry_run": true,
    "found": 15,
    "would_apply_label": "INBOX/Processed",
    "preview": [
      {
        "id": "abc123",
        "from": "sender@example.com",
        "subject": "Important Email",
        "date": "Mon, 1 Nov 2025 10:00:00 -0800"
      }
    ],
    "note": "No changes made. Set dry_run=false to apply label."
  }
}
```

### 2. memory.digest (Coming Soon)

**Intent**: `memory.digest`

**Inputs**:
- `since` (string): Time range (e.g., "24h", "1 week")
- `tags` (array): Filter by tags
- `format` (string): Output format (markdown, json)

**Flow**:
1. Query memory service for recent items
2. Group by tags/categories
3. Format as markdown digest
4. Optionally post to Slack/Email

### 3. slack.summarize (Coming Soon)

**Intent**: `slack.summarize`

**Inputs**:
- `channels` (array): Channel IDs to summarize
- `since` (string): Time range
- `destination` (string): Where to post summary

**Flow**:
1. Fetch messages from channels
2. Use AI to summarize key points
3. Post summary to destination channel

## Creating New Workflows

### Workflow Template

Every workflow should follow this contract:

**Input** (from webhook):
```json
{
  "intent": "your.intent",
  "inputs": { ... },
  "trace": {
    "request_id": "...",
    "job_id": "...",
    "timestamp": "..."
  }
}
```

**Output** (synchronous):
```json
{
  "status": "success|error",
  "result": { ... },
  "trace": { ... }
}
```

**Output** (async with callback):
```json
{
  "status": "accepted",
  "job_id": "...",
  "callback_url": "https://your-api.com/callbacks/ingest"
}
```

### Best Practices

1. **Parse Inputs First**: Use Function node to validate and extract inputs
2. **Include Trace**: Pass trace object through all nodes for observability
3. **Handle Dry Run**: Add IF node to preview changes without executing
4. **Error Handling**: Add error handler node to catch and format errors
5. **Return Consistent Schema**: Always return status + result + trace
6. **Timeout Awareness**: Keep sync flows under 8 seconds

### Essential Nodes

- **Webhook**: Trigger (set path to match intent name)
- **Function**: Parse inputs, transform data
- **IF/Switch**: Branch on dry_run, conditions
- **HTTP Request**: Call FastAPI tools if needed
- **Gmail/Slack/etc**: Native integrations
- **Respond to Webhook**: Return result synchronously

### Async Patterns

For long-running workflows (>8s):

1. Immediately respond with job_id:
```javascript
// Early response node
return {
  json: {
    status: 'accepted',
    job_id: $node['Parse Inputs'].json.job_id,
    message: 'Processing in background'
  }
};
```

2. Continue processing in background
3. POST result to callback URL when complete:
```javascript
// Callback node - HTTP Request
URL: {{ $node['Parse Inputs'].json.callback_url }}
Method: POST
Body: {
  job_id: "...",
  status: "success",
  result: { ... },
  trace: { ... }
}
```

## Testing Workflows

### Manual Test in n8n

1. Open workflow in n8n editor
2. Click **Execute Workflow** button
3. Manually provide test webhook data
4. Inspect node outputs

### Test via Orchestrator

Use the test script:

```bash
cd backend
python test_orchestrator.py
```

Or curl:

```bash
# Test gmail.triage
curl -X POST http://localhost:8000/orchestrate \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d @test_payloads/gmail_triage.json
```

### Dry Run Testing

Always test with `dry_run: true` first:

```json
{
  "intent": "gmail.triage",
  "inputs": {
    "query": "is:unread",
    "dry_run": true
  },
  "mode": "flow"
}
```

## Gmail Setup

### 1. Get OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://n8n:5678/rest/oauth2-credential/callback`

### 2. Configure in n8n

1. Go to **Credentials** → **Add Credential**
2. Select **Gmail OAuth2 API**
3. Enter Client ID and Client Secret
4. Click **Connect my account**
5. Authorize with Google

### 3. Find Label IDs

Labels in Gmail have IDs. To find them:

```javascript
// Add this Function node to test workflow
const gmail = $node['Gmail Search'].json;
console.log('Available Labels:', gmail.labelIds);
```

Common labels:
- `INBOX` - Inbox
- `UNREAD` - Unread
- `STARRED` - Starred
- `IMPORTANT` - Important
- Custom labels: `Label_123456789`

## Monitoring

### View Execution History

In n8n:
1. Go to **Executions**
2. Filter by workflow name
3. Click execution to see node outputs

### Check Logs

```bash
docker logs n8n -f
```

### Trace Jobs

All workflows include trace object:

```json
{
  "trace": {
    "request_id": "req_abc123",
    "job_id": "job_xyz789",
    "intent": "gmail.triage",
    "timestamp": "2025-11-01T10:00:00Z"
  }
}
```

Use these IDs to correlate across systems:
- FastAPI logs: Search for `request_id`
- n8n executions: Check workflow inputs
- Job status: `GET /jobs/{job_id}`

## Troubleshooting

### Workflow Returns Error

Check n8n execution logs for details. Common issues:
- Missing credentials
- Invalid label ID
- Gmail API quota exceeded
- Timeout (workflow too slow)

### Webhook Not Triggering

Verify:
- Workflow is **activated** (toggle in top-right)
- Webhook path matches intent name
- n8n is accessible from FastAPI container
- `N8N_WEBHOOK_BASE` is set correctly

### No Results from Gmail

Check:
- OAuth credentials are valid
- Query syntax is correct
- Account has matching emails
- Gmail API is enabled in Google Cloud

## Next Steps

1. Create more workflows (memory.digest, slack.summarize)
2. Add scheduled triggers for daily digests
3. Integrate with Google Sheets for reporting
4. Add Postgres nodes for direct DB access
5. Build approval flows with Slack buttons
