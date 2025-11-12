# OpenAI Personal Assistant Environment

## Overview
A production-ready AI assistant with **unified orchestration**, **persistent memory**, **Gmail automation**, and **SSH capabilities**. Built for ChatGPT Actions with n8n workflow integration.

**Key Features:**
- 🎯 **Single Endpoint**: `/orchestrate` handles all operations
- 🧠 **Persistent Memory**: Vector + keyword search with embeddings
- 📧 **Gmail Automation**: Triage, label, and organize emails
- 🔧 **SSH Tools**: Safe remote command execution
- 🔄 **n8n Workflows**: Complex automations and integrations
- ⚡ **Sync/Async**: Fast operations return immediately, slow ones use callbacks

**Status:** ✅ Production-Ready ([DEPLOYMENT.md](backend/docker/DEPLOYMENT.md))

---

## Quick Start

### 1. Development Setup

```bash
# Clone and configure
cp .env.example .env
# Edit .env with your API keys

# Start services
cd backend/docker
docker-compose -f compose.core1.yml -f compose.dev.yml up -d

# Access services
# - API Docs: http://localhost:8000/docs
# - n8n UI: http://localhost:5678
# - Health: http://localhost:8000/health
```

### 2. Import n8n Workflows

```bash
# In n8n UI (http://localhost:5678):
# 1. Workflows → Import from File
# 2. Select n8n_workflows/gmail-triage.json
# 3. Configure Gmail OAuth credentials
# 4. Activate workflow
```

### 3. Test the Orchestrator

```bash
# Set your API key
export API_KEY="your-api-key-here"

# Test memory
curl -X POST http://localhost:8000/orchestrate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"intent":"memory.write","inputs":{"text":"Test memory"}}'

# Run test suite
cd backend
python test_orchestrator.py
```

### 4. Preview the Admin Settings UI

The admin console is now a React application served with Vite. Use the helper script or Make target to install dependencies (if needed) and launch the dev server for hot-reload previews:

```bash
make serve-frontend
```

By default the site is available at `http://127.0.0.1:5173/`. Override the port with `PORT=9000 make serve-frontend` if needed. The Vite server binds to `0.0.0.0` so the IDE preview panel can connect.

### 5. Connect ChatGPT

1. Create Custom GPT at [chat.openai.com](https://chat.openai.com)
2. Import `chatgpt_actions.json` schema
3. Configure Bearer token with your API key
4. Test with: "Store this in memory: I prefer Python"

📚 **Complete Guide**: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)

---

## Architecture
