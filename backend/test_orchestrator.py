"""
Test script for orchestrator.

Run this to verify the /orchestrate endpoint works.
"""

import requests
import json


BASE_URL = "http://localhost:8000"


def test_memory_write():
    """Test memory.write intent."""
    print("\n=== Testing memory.write ===")
    
    response = requests.post(
        f"{BASE_URL}/orchestrate",
        json={
            "intent": "memory.write",
            "inputs": {
                "text": "The capital of France is Paris",
                "tags": ["geography", "facts"]
            },
            "mode": "agent"
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()


def test_memory_search():
    """Test memory.search intent."""
    print("\n=== Testing memory.search ===")
    
    response = requests.post(
        f"{BASE_URL}/orchestrate",
        json={
            "intent": "memory.search",
            "inputs": {
                "query": "France",
                "k": 3
            },
            "mode": "agent"
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()


def test_ssh_peek():
    """Test ssh.exec.peek intent."""
    print("\n=== Testing ssh.exec.peek ===")
    
    response = requests.post(
        f"{BASE_URL}/orchestrate",
        json={
            "intent": "ssh.exec.peek",
            "inputs": {
                "host": "example.com",
                "command": "ls -la"
            },
            "mode": "agent"
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()


def test_ssh_dangerous():
    """Test ssh.exec with safety check."""
    print("\n=== Testing ssh.exec (should block) ===")
    
    response = requests.post(
        f"{BASE_URL}/orchestrate",
        json={
            "intent": "ssh.exec",
            "inputs": {
                "host": "example.com",
                "command": "rm -rf /"
            },
            "mode": "agent"
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()


def test_auto_mode():
    """Test auto mode selection."""
    print("\n=== Testing auto mode ===")
    
    response = requests.post(
        f"{BASE_URL}/orchestrate",
        json={
            "intent": "memory.write",
            "inputs": {
                "text": "Test auto mode"
            },
            "mode": "auto"
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()


def test_job_status(job_id: str):
    """Test job status retrieval."""
    print(f"\n=== Testing job status: {job_id} ===")
    
    response = requests.get(f"{BASE_URL}/jobs/{job_id}")
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()


def test_idempotency():
    """Test idempotency key."""
    print("\n=== Testing idempotency ===")
    
    payload = {
        "intent": "memory.write",
        "inputs": {
            "text": "Idempotency test"
        },
        "mode": "agent"
    }
    
    # First request
    r1 = requests.post(f"{BASE_URL}/orchestrate", json=payload)
    print(f"Request 1 - Status: {r1.status_code}")
    print(f"Response 1: {json.dumps(r1.json(), indent=2)}")
    
    # Second request (should get cached result)
    r2 = requests.post(f"{BASE_URL}/orchestrate", json=payload)
    print(f"Request 2 - Status: {r2.status_code}")
    print(f"Response 2: {json.dumps(r2.json(), indent=2)}")
    
    return r1.json(), r2.json()


if __name__ == "__main__":
    print("Starting orchestrator tests...")
    print(f"Connecting to: {BASE_URL}")
    
    try:
        # Run tests
        test_memory_write()
        test_memory_search()
        test_ssh_peek()
        test_ssh_dangerous()
        test_auto_mode()
        test_idempotency()
        
        print("\n=== All tests completed ===")
        
    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to server")
        print("Make sure FastAPI is running: uvicorn app.main:app --reload")
        
    except Exception as e:
        print(f"\nERROR: {e}")
