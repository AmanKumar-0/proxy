#!/usr/bin/env python3
"""
Test client for AI Proxy Gateway
"""

import jwt
import requests
from datetime import datetime, timedelta
import json


def generate_token(secret="your-secret-key-change-in-production"):
    """Generate a JWT token for testing"""
    payload = {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token


def test_health_check():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get("http://localhost:8000/v1/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def test_list_models(token):
    """Test list models endpoint"""
    print("\n=== Testing List Models ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("http://localhost:8000/v1/models", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_non_streaming(token, provider="openai", model="gpt-3.5-turbo"):
    """Test non-streaming chat completion"""
    print(f"\n=== Testing Non-Streaming ({provider}/{model}) ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "model": f"{provider}/{model}",
        "messages": [
            {"role": "user", "content": "Say hello in one sentence"}
        ],
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")


def test_streaming(token, provider="openai", model="gpt-3.5-turbo"):
    """Test streaming chat completion"""
    print(f"\n=== Testing Streaming ({provider}/{model}) ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "model": f"{provider}/{model}",
        "messages": [
            {"role": "user", "content": "Count from 1 to 5"}
        ],
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/v1/chat/completions",
            headers=headers,
            json=data,
            stream=True,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print("Streaming response:")
        
        for line in response.iter_lines():
            if line:
                print(line.decode())
                
    except Exception as e:
        print(f"Error: {e}")


def test_metrics():
    """Test metrics endpoint"""
    print("\n=== Testing Metrics ===")
    response = requests.get("http://localhost:8000/metrics")
    print(f"Status: {response.status_code}")
    
    # Show first 20 lines of metrics
    lines = response.text.split('\n')
    for line in lines[:20]:
        if line and not line.startswith('#'):
            print(line)


def test_authentication_failure():
    """Test authentication failure"""
    print("\n=== Testing Authentication Failure ===")
    
    # Test without token
    response = requests.post(
        "http://localhost:8000/v1/chat/completions",
        json={
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello"}]
        }
    )
    print(f"Without token - Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test with invalid token
    headers = {"Authorization": "Bearer invalid-token"}
    response = requests.post(
        "http://localhost:8000/v1/chat/completions",
        headers=headers,
        json={
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello"}]
        }
    )
    print(f"\nInvalid token - Status: {response.status_code}")
    print(f"Response: {response.json()}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("AI Proxy Gateway Test Client")
    print("=" * 60)
    
    # Generate token
    token = generate_token()
    print(f"\nGenerated JWT Token: {token[:50]}...")
    
    # Run tests
    test_health_check()
    test_authentication_failure()
    test_list_models(token)
    test_metrics()
    
    # Note: Uncomment these when you have valid API keys configured
    # test_non_streaming(token, "openai", "gpt-3.5-turbo")
    # test_streaming(token, "openai", "gpt-3.5-turbo")
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
