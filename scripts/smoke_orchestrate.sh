#!/bin/bash
# Smoke test for orchestrator endpoints
# Tests basic functionality without requiring full setup

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-test-api-key}"

echo "🔥 Smoke Testing Orchestrator"
echo "API URL: $API_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

test_passed=0
test_failed=0

# Helper function to test endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local path="$3"
    local data="$4"
    
    echo -n "Testing $name... "
    
    if [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" \
            -X POST "$API_URL$path" \
            -H "Authorization: Bearer $API_KEY" \
            -H "Content-Type: application/json" \
            -d "$data")
    else
        response=$(curl -s -w "\n%{http_code}" \
            -X GET "$API_URL$path" \
            -H "Authorization: Bearer $API_KEY")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        test_passed=$((test_passed + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $http_code)"
        echo "Response: $body"
        test_failed=$((test_failed + 1))
        return 1
    fi
}

# Test 1: Health endpoint
test_endpoint \
    "Health Check" \
    "GET" \
    "/health" \
    ""

# Test 2: Memory write
test_endpoint \
    "Memory Write" \
    "POST" \
    "/orchestrate" \
    '{"intent":"memory.write","inputs":{"text":"Smoke test memory item","tags":["test","smoke"]},"mode":"agent"}'

# Test 3: Memory search
test_endpoint \
    "Memory Search" \
    "POST" \
    "/orchestrate" \
    '{"intent":"memory.search","inputs":{"query":"smoke test","k":5},"mode":"agent"}'

# Test 4: Gmail triage (dry run)
test_endpoint \
    "Gmail Triage (Dry Run)" \
    "POST" \
    "/orchestrate" \
    '{"intent":"gmail.triage","inputs":{"query":"is:unread","dry_run":true},"mode":"agent"}'

# Test 5: SSH peek (safe command)
test_endpoint \
    "SSH Peek (Safe)" \
    "POST" \
    "/orchestrate" \
    '{"intent":"ssh.exec.peek","inputs":{"host":"localhost","command":"ls"},"mode":"agent"}'

# Test 6: SSH exec (should block without confirm)
test_endpoint \
    "SSH Exec (Should Block)" \
    "POST" \
    "/orchestrate" \
    '{"intent":"ssh.exec","inputs":{"host":"localhost","command":"rm -rf /"},"mode":"agent"}'

# Test 7: Filesystem list
test_endpoint \
    "Filesystem List" \
    "POST" \
    "/orchestrate" \
    '{"intent":"fs.list","inputs":{"path":"/tmp"},"mode":"agent"}'

# Test 8: Idempotency check
echo -n "Testing Idempotency... "
response1=$(curl -s -X POST "$API_URL/orchestrate" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"intent":"memory.write","inputs":{"text":"Idempotency test"},"mode":"agent"}')
    
response2=$(curl -s -X POST "$API_URL/orchestrate" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"intent":"memory.write","inputs":{"text":"Idempotency test"},"mode":"agent"}')

if [ "$response1" = "$response2" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Responses match)"
    test_passed=$((test_passed + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Responses differ)"
    test_failed=$((test_failed + 1))
fi

# Summary
echo ""
echo "========================================="
echo "Test Results:"
echo "  Passed: $test_passed"
echo "  Failed: $test_failed"
echo "========================================="

if [ $test_failed -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed! ✗${NC}"
    exit 1
fi
