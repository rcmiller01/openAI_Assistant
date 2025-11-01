# Production Deployment Guide

## Prerequisites

1. **Docker & Docker Compose**: Version 20.10+ recommended
2. **Domain**: Cloudflare-managed domain (e.g., yourdomain.com)
3. **Cloudflare Tunnel**: Created and configured in Cloudflare dashboard
4. **SSL Certificates**: Cloudflare Origin Certificate downloaded

## Initial Setup

### 1. Clone Repository
```bash
git clone https://github.com/rcmiller01/openAI_Assistant.git
cd openAI_Assistant
```

### 2. Generate Secrets
```bash
# API Key (32+ characters)
openssl rand -base64 32

# Database Password
openssl rand -base64 24

# n8n Encryption Key
openssl rand -base64 32

# n8n Admin Password
openssl rand -base64 16
```

### 3. Configure Environment
```bash
# Copy and edit .env file
cp .env.example .env
nano .env
```

Update all `change-me-*` values with:
- Strong passwords (20+ characters)
- Real API keys and tokens
- Your domain names
- Cloudflare tunnel token

### 4. SSL Certificates (Cloudflare Origin Certificate)

1. Go to Cloudflare Dashboard → SSL/TLS → Origin Server
2. Create Certificate (15 year validity)
3. Download certificate and private key
4. Save to `backend/docker/nginx/ssl/`:
   ```bash
   mkdir -p backend/docker/nginx/ssl
   # Save certificate as origin-cert.pem
   # Save private key as origin-key.pem
   chmod 600 backend/docker/nginx/ssl/*
   ```

### 5. Create Docker Networks
```bash
# Create Core1 network first
cd backend/docker
docker network create core1_core

# Core3 will create its own edge network
```

## Deployment

### Start Core1 (API + Database + n8n)
```bash
cd backend/docker
docker-compose -f compose.core1.yml up -d

# Check logs
docker-compose -f compose.core1.yml logs -f

# Verify health
docker ps
```

### Start Core3 (Nginx + Cloudflare)
```bash
cd backend/docker
docker-compose -f compose.core3.yml up -d

# Check logs
docker-compose -f compose.core3.yml logs -f
```

## Post-Deployment

### 1. Initialize Database
```bash
# Database tables are auto-created on first startup
# Check logs for "Database tables created"
docker-compose -f compose.core1.yml logs api | grep "Database tables created"
```

### 2. Test API
```bash
# From local machine
curl -H "Authorization: Bearer YOUR_API_KEY" https://yourdomain.com/healthz

# Expected response: {"status":"ok",...}
```

### 3. Configure Cloudflare Tunnel

In Cloudflare Dashboard:
1. Go to Zero Trust → Access → Tunnels
2. Select your tunnel
3. Configure Public Hostname:
   - Subdomain: `api` (or `*` for wildcard)
   - Domain: `yourdomain.com`
   - Service: `https://core3-nginx:443`

### 4. Test n8n Access
```bash
# n8n is internal only, accessible via API or port-forward for admin
docker-compose -f compose.core1.yml exec n8n wget -O- http://localhost:5678/healthz
```

## Monitoring

### Health Checks
```bash
# Check all container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# API health
curl https://yourdomain.com/healthz

# Nginx health (from Core3 container)
docker exec core3-nginx wget -O- http://localhost/healthz
```

### Logs
```bash
# Follow API logs
docker-compose -f compose.core1.yml logs -f api

# Check Cloudflare tunnel logs
docker-compose -f compose.core3.yml logs -f cloudflared

# Check nginx access logs
docker exec core3-nginx tail -f /var/log/nginx/access.log
```

### Database Backups
```bash
# Backups run automatically at 2 AM daily
# Check backup status
docker-compose -f compose.core1.yml logs postgres-backup

# List backups
docker exec core1-postgres ls -lh /backups/

# Manual backup
docker-compose -f compose.core1.yml exec postgres-backup /backup.sh
```

### Restore from Backup
```bash
# Stop API
docker-compose -f compose.core1.yml stop api

# Restore database
docker exec core1-postgres sh -c "gunzip < /backups/backup_opa_YYYYMMDD_HHMMSS.sql.gz | psql -U opa -d opa"

# Restart API
docker-compose -f compose.core1.yml start api
```

## Updates

### Update API Code
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
cd backend/docker
docker-compose -f compose.core1.yml build api
docker-compose -f compose.core1.yml up -d api
```

### Update Dependencies
```bash
# Update pyproject.toml
cd backend
poetry update

# Export requirements
poetry export -f requirements.txt --output requirements.txt --without-hashes

# Rebuild
cd docker
docker-compose -f compose.core1.yml build api
docker-compose -f compose.core1.yml up -d api
```

## Maintenance

### Rotate Secrets
1. Generate new secret
2. Update .env file
3. Restart affected services:
   ```bash
   docker-compose -f compose.core1.yml up -d api
   ```

### Clean Up Old Images
```bash
docker image prune -a --filter "until=168h"  # Remove images older than 7 days
```

### Database Maintenance
```bash
# Vacuum database
docker exec core1-postgres psql -U opa -d opa -c "VACUUM ANALYZE;"
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose -f compose.core1.yml logs <service-name>

# Check resource usage
docker stats

# Restart service
docker-compose -f compose.core1.yml restart <service-name>
```

### Database connection issues
```bash
# Check if postgres is healthy
docker exec core1-postgres pg_isready -U opa

# Check network
docker network inspect core1_core
```

### Cloudflare tunnel issues
```bash
# Check tunnel status
docker-compose -f compose.core3.yml logs cloudflared

# Verify tunnel token
echo $CLOUDFLARE_TUNNEL_TOKEN

# Restart tunnel
docker-compose -f compose.core3.yml restart cloudflared
```

## Security Checklist

- [ ] Changed all default passwords in .env
- [ ] API_KEY is 32+ random characters
- [ ] Database password is strong (20+ characters)
- [ ] n8n authentication enabled with strong password
- [ ] Cloudflare SSL/TLS mode set to "Full (strict)"
- [ ] Cloudflare WAF rules configured
- [ ] Only port 80/443 exposed on Core3
- [ ] No database ports exposed to internet
- [ ] File system mounted read-only
- [ ] Container user is non-root
- [ ] Backups are working and tested
- [ ] Monitoring/alerting configured
- [ ] Log rotation enabled
- [ ] Resource limits set on all containers

## Production Environment Variables

Verify these are set correctly in `.env`:
- `APP_ENV=prod` (NOT dev)
- `LOG_LEVEL=INFO` (NOT DEBUG)
- Strong passwords for all services
- Real domain names (not localhost)
- Production Cloudflare tunnel token
