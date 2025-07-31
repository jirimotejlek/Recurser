#!/usr/bin/env python3
"""
Debug script to test individual services and identify issues
"""

import json
import time

import requests


def test_service(name, url, method="GET", data=None, timeout=10):
    """Test a service endpoint"""
    print(f"\n🔍 Testing {name} at {url}")
    print(f"Method: {method}")

    try:
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        else:
            print(f"❌ Unknown method: {method}")
            return False

        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text[:500]}...")

        if response.status_code == 200:
            try:
                json_data = response.json()
                print(f"✅ JSON Response: {json.dumps(json_data, indent=2)[:500]}...")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ JSON Parse Error: {e}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Cannot connect to {name}")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Timeout Error: {name} took too long to respond")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False


def main():
    """Test all services"""
    print("🚀 Starting service debug tests...")

    # Test health endpoints
    services = [
        ("Optimizer Health", "http://optimizer:5050/health", "GET"),
        ("Search Engine Health", "http://search-engine:5150/health", "GET"),
        ("LLM Dispatcher Health", "http://llm-dispatcher:5100/health", "GET"),
        ("ChromaDB Health", "http://chromadb:8000/api/v2/heartbeat", "GET"),
    ]

    health_results = {}
    for name, url, method in services:
        health_results[name] = test_service(name, url, method)

    print("\n" + "=" * 50)
    print("📊 Health Check Results:")
    for name, result in health_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")

    # Test functional endpoints
    print("\n" + "=" * 50)
    print("🧪 Testing Functional Endpoints:")

    # Test Optimizer
    print("\n1. Testing Optimizer Query:")
    test_service(
        "Optimizer Query",
        "http://optimizer:5050/query",
        "POST",
        {"prompt": "Optimize this search query: 'where is brazil'"},
    )

    # Test Search Engine
    print("\n2. Testing Search Engine:")
    test_service(
        "Search Engine Query",
        "http://search-engine:5150/query",
        "POST",
        {"search_query": "where is brazil"},
    )

    # Test LLM Dispatcher
    print("\n3. Testing LLM Dispatcher:")
    test_service(
        "LLM Dispatcher Query",
        "http://llm-dispatcher:5100/query",
        "POST",
        {"prompt": "Say 'Hello, I'm working!' and nothing else."},
    )

    print("\n" + "=" * 50)
    print("🎯 Debug Summary:")
    print("If you see JSON Parse Errors above, that service needs attention.")
    print("If you see Connection Errors, the service container might not be running.")
    print(
        "If you see Timeout Errors, the service might be overloaded or misconfigured."
    )


if __name__ == "__main__":
    main()
