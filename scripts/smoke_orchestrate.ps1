# PowerShell version of smoke test
# Tests basic orchestrator functionality

$API_URL = if ($env:API_URL) { $env:API_URL } else { "http://localhost:8000" }
$API_KEY = if ($env:API_KEY) { $env:API_KEY } else { "test-api-key" }

Write-Host "🔥 Smoke Testing Orchestrator" -ForegroundColor Cyan
Write-Host "API URL: $API_URL"
Write-Host ""

$test_passed = 0
$test_failed = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Path,
        [string]$Data = $null
    )
    
    Write-Host -NoNewline "Testing $Name... "
    
    try {
        $headers = @{
            "Authorization" = "Bearer $API_KEY"
            "Content-Type" = "application/json"
        }
        
        $params = @{
            Uri = "$API_URL$Path"
            Method = $Method
            Headers = $headers
        }
        
        if ($Data) {
            $params.Body = $Data
        }
        
        $response = Invoke-RestMethod @params -ErrorAction Stop
        
        Write-Host "✓ PASS" -ForegroundColor Green
        $script:test_passed++
        return $true
    }
    catch {
        Write-Host "✗ FAIL" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        $script:test_failed++
        return $false
    }
}

# Test 1: Health
Test-Endpoint -Name "Health Check" -Method GET -Path "/health"

# Test 2: Memory write
Test-Endpoint -Name "Memory Write" -Method POST -Path "/orchestrate" `
    -Data '{"intent":"memory.write","inputs":{"text":"Smoke test","tags":["test"]},"mode":"agent"}'

# Test 3: Memory search
Test-Endpoint -Name "Memory Search" -Method POST -Path "/orchestrate" `
    -Data '{"intent":"memory.search","inputs":{"query":"smoke test","k":5},"mode":"agent"}'

# Test 4: Gmail triage (dry run)
Test-Endpoint -Name "Gmail Triage" -Method POST -Path "/orchestrate" `
    -Data '{"intent":"gmail.triage","inputs":{"query":"is:unread","dry_run":true},"mode":"agent"}'

# Test 5: SSH peek
Test-Endpoint -Name "SSH Peek" -Method POST -Path "/orchestrate" `
    -Data '{"intent":"ssh.exec.peek","inputs":{"host":"localhost","command":"ls"},"mode":"agent"}'

# Test 6: Filesystem list
Test-Endpoint -Name "FS List" -Method POST -Path "/orchestrate" `
    -Data '{"intent":"fs.list","inputs":{"path":"/tmp"},"mode":"agent"}'

# Summary
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Test Results:"
Write-Host "  Passed: $test_passed" -ForegroundColor Green
Write-Host "  Failed: $test_failed" -ForegroundColor Red
Write-Host "=========================================" -ForegroundColor Cyan

if ($test_failed -eq 0) {
    Write-Host "All tests passed! ✓" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some tests failed! ✗" -ForegroundColor Red
    exit 1
}
