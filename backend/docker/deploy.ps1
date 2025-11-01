# Production Deployment Script for Windows
# Usage: .\deploy.ps1 [core1|core3|all]

param(
    [string]$Target = "all"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  OpenAI Personal Assistant - Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path "..\..\\.env")) {
    Write-Host "❌ Error: .env file not found" -ForegroundColor Red
    Write-Host "   Please copy .env.example to .env and configure it"
    exit 1
}

# Load environment variables
Get-Content "..\..\\.env" | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

# Validate required environment variables
$requiredVars = @(
    "API_KEY",
    "POSTGRES_PASSWORD",
    "N8N_BASIC_AUTH_USER",
    "N8N_BASIC_AUTH_PASSWORD",
    "N8N_ENCRYPTION_KEY"
)

Write-Host "🔍 Validating environment variables..." -ForegroundColor Yellow
$missingVars = @()
foreach ($var in $requiredVars) {
    $value = [Environment]::GetEnvironmentVariable($var, "Process")
    if ([string]::IsNullOrEmpty($value) -or $value -like "*change-me*") {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "❌ Missing or default values for required variables:" -ForegroundColor Red
    foreach ($var in $missingVars) {
        Write-Host "   - $var"
    }
    Write-Host ""
    Write-Host "Please update .env file with proper values"
    exit 1
}

Write-Host "✅ Environment variables validated" -ForegroundColor Green
Write-Host ""

# Check Docker
try {
    docker --version | Out-Null
    docker-compose --version | Out-Null
    Write-Host "✅ Docker and Docker Compose found" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker or Docker Compose not found" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Create networks
Write-Host "🔧 Creating Docker networks..." -ForegroundColor Yellow
docker network create core1_core 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "   Network core1_core already exists"
}
Write-Host ""

function Deploy-Core1 {
    Write-Host "🚀 Deploying Core1 (Application Stack)..." -ForegroundColor Cyan
    docker-compose -f compose.core1.yml up -d
    Write-Host "✅ Core1 deployed" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    docker-compose -f compose.core1.yml ps
}

function Deploy-Core3 {
    Write-Host "🚀 Deploying Core3 (Edge Stack)..." -ForegroundColor Cyan
    
    # Check SSL certificates
    if (-not (Test-Path ".\nginx\ssl\origin-cert.pem") -or -not (Test-Path ".\nginx\ssl\origin-key.pem")) {
        Write-Host "⚠️  Warning: SSL certificates not found in nginx/ssl/" -ForegroundColor Yellow
        Write-Host "   Please add Cloudflare Origin Certificate:"
        Write-Host "   - nginx/ssl/origin-cert.pem"
        Write-Host "   - nginx/ssl/origin-key.pem"
        $continue = Read-Host "   Continue anyway? (y/N)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            exit 1
        }
    }
    
    # Check Cloudflare tunnel token
    $tunnelToken = [Environment]::GetEnvironmentVariable("CLOUDFLARE_TUNNEL_TOKEN", "Process")
    if ([string]::IsNullOrEmpty($tunnelToken) -or $tunnelToken -like "*change-me*") {
        Write-Host "⚠️  Warning: CLOUDFLARE_TUNNEL_TOKEN not configured" -ForegroundColor Yellow
        $continue = Read-Host "   Continue anyway? (y/N)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            exit 1
        }
    }
    
    docker-compose -f compose.core3.yml up -d
    Write-Host "✅ Core3 deployed" -ForegroundColor Green
    Write-Host ""
    
    docker-compose -f compose.core3.yml ps
}

switch ($Target) {
    "core1" {
        Deploy-Core1
    }
    "core3" {
        Deploy-Core3
    }
    "all" {
        Deploy-Core1
        Write-Host ""
        Deploy-Core3
    }
    default {
        Write-Host "❌ Unknown deployment target: $Target" -ForegroundColor Red
        Write-Host "Usage: .\deploy.ps1 [core1|core3|all]"
        exit 1
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Check status:"
Write-Host "   docker ps"
Write-Host ""
Write-Host "📋 View logs:"
Write-Host "   docker-compose -f compose.core1.yml logs -f"
Write-Host "   docker-compose -f compose.core3.yml logs -f"
Write-Host ""
Write-Host "🧪 Test API:"
Write-Host "   curl -H `"Authorization: Bearer `$env:API_KEY`" http://localhost:8080/healthz"
Write-Host ""
Write-Host "📖 Full documentation: ..\..\DEPLOYMENT.md"
Write-Host ""
