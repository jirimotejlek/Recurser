#!/usr/bin/env python3
"""
Test script to check Ollama service and model availability
"""

import json

import requests


def test_ollama():
    """Test Ollama service"""
    print("🔍 Testing Ollama Service...")

    # Test 1: Check if Ollama is running
    print("\n1. Checking if Ollama is running...")
    try:
        response = requests.get("http://llm:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
            data = response.json()
            models = data.get("models", [])
            print(f"📦 Available models: {[model['name'] for model in models]}")

            # Check if the required model is available
            required_model = "gemma3n:e2b"
            model_names = [model["name"] for model in models]
            if required_model in model_names:
                print(f"✅ Required model '{required_model}' is available")
            else:
                print(f"❌ Required model '{required_model}' is NOT available")
                print(f"Available models: {model_names}")
                return False
        else:
            print(f"❌ Ollama returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        return False

    # Test 2: Try a simple generation
    print("\n2. Testing simple generation...")
    try:
        payload = {
            "model": "gemma3n:e2b",
            "prompt": "Say 'Hello, I'm working!' and nothing else.",
            "stream": False,
        }

        response = requests.post(
            "http://llm:11434/api/generate", json=payload, timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ Generation successful")
            print(f"Response: {data.get('response', 'No response')}")
            return True
        else:
            print(f"❌ Generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Generation error: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Ollama Service Test")
    print("=" * 40)

    success = test_ollama()

    print("\n" + "=" * 40)
    if success:
        print("✅ Ollama is working correctly!")
    else:
        print("❌ Ollama has issues that need to be fixed.")
        print("\n🔧 Troubleshooting steps:")
        print("1. Make sure Ollama container is running: docker ps | grep ollama")
        print("2. Check Ollama logs: docker logs ollama-llm")
        print(
            "3. Pull the required model: docker exec -it ollama-llm ollama pull gemma3n:e2b"
        )
        print("4. Restart the Ollama container if needed")


if __name__ == "__main__":
    main()
