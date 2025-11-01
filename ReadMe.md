# OpenAI Personal Assistant Environment

## Overview
A production-ready private extensible personal assistant environment designed to run entirely through **ChatGPT Actions** or an external **Agent Builder (n8n)**.  
FastAPI provides a secure REST API interface exposing memory, filesystem, SSH, fetch services, and workflow automation.

**Status:** ✅ Production-Ready (See [DEPLOYMENT.md](DEPLOYMENT.md))

---

## Quick Start

### Development
```bash
cp .env.example .env
cd backend/docker
docker-compose -f compose.core1.yml -f compose.dev.yml up -d
# API: http://localhost:8080/docs
```

### Production
```bash
# See DEPLOYMENT.md for complete setup guide
docker-compose -f compose.core1.yml up -d  # Application stack
docker-compose -f compose.core3.yml up -d  # Edge/Cloudflare
```

---

## Architecture
