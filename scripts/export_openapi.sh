#!/bin/bash
# Export OpenAPI schema for ChatGPT Actions

set -e

API_URL="http://localhost:8080"
OUTPUT_FILE="../backend/openapi/actions.json"

echo "🔄 Exporting OpenAPI schema..."

# Check if API is running
if ! curl -f "$API_URL/healthz" > /dev/null 2>&1; then
    echo "❌ API is not running at $API_URL"
    echo "   Please start the API first:"
    echo "   docker compose -f backend/docker/compose.core1.yml up -d"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Fetch OpenAPI schema
echo "📡 Fetching OpenAPI schema from $API_URL/openapi.json..."
curl -s "$API_URL/openapi.json" > "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "✅ OpenAPI schema exported to $OUTPUT_FILE"
    echo "📊 Schema size: $(wc -l < "$OUTPUT_FILE") lines"
    
    # Pretty print summary
    echo "📋 API Summary:"
    jq -r '.info.title + " v" + .info.version' "$OUTPUT_FILE" 2>/dev/null || echo "   Failed to parse JSON"
    echo "🔗 Paths:"
    jq -r '.paths | keys[]' "$OUTPUT_FILE" 2>/dev/null | sed 's/^/   /' || echo "   Failed to parse paths"
else
    echo "❌ Failed to export OpenAPI schema"
    exit 1
fi