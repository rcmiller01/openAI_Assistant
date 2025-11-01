#!/bin/bash
# Production deployment startup script

set -e

echo "=========================================="
echo "  OpenAI Personal Assistant - Deployment"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f "../../.env" ]; then
    echo "❌ Error: .env file not found"
    echo "   Please copy .env.example to .env and configure it"
    exit 1
fi

# Source environment
set -a
source ../../.env
set +a

# Validate required environment variables
REQUIRED_VARS=(
    "API_KEY"
    "POSTGRES_PASSWORD"
    "N8N_BASIC_AUTH_USER"
    "N8N_BASIC_AUTH_PASSWORD"
    "N8N_ENCRYPTION_KEY"
)

echo "🔍 Validating environment variables..."
MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    elif [[ "${!var}" == *"change-me"* ]]; then
        MISSING_VARS+=("$var (still has default value)")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo "❌ Missing or default values for required variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please update .env file with proper values"
    exit 1
fi

echo "✅ Environment variables validated"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    exit 1
fi

echo "✅ Docker and Docker Compose found"
echo ""

# Create networks if they don't exist
echo "🔧 Creating Docker networks..."
docker network create core1_core 2>/dev/null || echo "   Network core1_core already exists"
echo ""

# Deploy based on argument
DEPLOY_TARGET="${1:-all}"

deploy_core1() {
    echo "🚀 Deploying Core1 (Application Stack)..."
    docker-compose -f compose.core1.yml up -d
    echo "✅ Core1 deployed"
    echo ""
    
    echo "⏳ Waiting for services to be healthy..."
    sleep 10
    
    # Check health
    docker-compose -f compose.core1.yml ps
}

deploy_core3() {
    echo "🚀 Deploying Core3 (Edge Stack)..."
    
    # Check SSL certificates
    if [ ! -f "./nginx/ssl/origin-cert.pem" ] || [ ! -f "./nginx/ssl/origin-key.pem" ]; then
        echo "⚠️  Warning: SSL certificates not found in nginx/ssl/"
        echo "   Please add Cloudflare Origin Certificate:"
        echo "   - nginx/ssl/origin-cert.pem"
        echo "   - nginx/ssl/origin-key.pem"
        read -p "   Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check Cloudflare tunnel token
    if [ -z "$CLOUDFLARE_TUNNEL_TOKEN" ] || [[ "$CLOUDFLARE_TUNNEL_TOKEN" == *"change-me"* ]]; then
        echo "⚠️  Warning: CLOUDFLARE_TUNNEL_TOKEN not configured"
        read -p "   Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    docker-compose -f compose.core3.yml up -d
    echo "✅ Core3 deployed"
    echo ""
    
    docker-compose -f compose.core3.yml ps
}

case $DEPLOY_TARGET in
    core1)
        deploy_core1
        ;;
    core3)
        deploy_core3
        ;;
    all)
        deploy_core1
        echo ""
        deploy_core3
        ;;
    *)
        echo "❌ Unknown deployment target: $DEPLOY_TARGET"
        echo "Usage: $0 [core1|core3|all]"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "📊 Check status:"
echo "   docker ps"
echo ""
echo "📋 View logs:"
echo "   docker-compose -f compose.core1.yml logs -f"
echo "   docker-compose -f compose.core3.yml logs -f"
echo ""
echo "🧪 Test API:"
echo "   curl -H \"Authorization: Bearer \$API_KEY\" http://localhost:8080/healthz"
echo ""
echo "📖 Full documentation: ../../DEPLOYMENT.md"
echo ""
