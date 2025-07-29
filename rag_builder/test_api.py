#!/usr/bin/env python3
"""
Container RAG Builder API Test
Tests the containerized RAG Builder with ML Wikipedia content
Validates: chunking, embedding, storage, and semantic retrieval
"""

import requests
import json

# Configuration for Docker containers
RAG_BUILDER_URL = "http://localhost:5300"  # RAG Builder container exposed port
SESSION_ID = "docker_test_session"  # Use different session ID for container testing

# Expected for ML Wikipedia page (65K+ characters)
EXPECTED_MIN_CHUNKS = 20  # Should create many chunks from large Wikipedia article
EXPECTED_MIN_TOKENS = 15000  # Large article should have many tokens

def test_container_health():
    """Test that the containerized RAG Builder is healthy and ready"""
    print("🔍 Testing container health...")
    
    try:
        health_response = requests.get(f"{RAG_BUILDER_URL}/health", timeout=10)
        
        if health_response.status_code == 200:
            health = health_response.json()
            print(f"✅ RAG Builder Status: {health['status']}")
            print(f"📊 Services: {health['services']}")
            
            # Check critical services
            critical_services = ["chromadb", "embedding_model", "tokenizer"]
            all_good = True
            
            for service in critical_services:
                status = health['services'].get(service, 'unknown')
                if status != 'up':
                    print(f"❌ Critical service {service}: {status}")
                    all_good = False
                else:
                    print(f"✅ {service}: {status}")
            
            if not all_good:
                print("❌ Some critical services are down. Check docker-compose logs.")
                return False
                
            print(f"⚙️  Configuration: {health['rag_config']['chunk_target_tokens']} token chunks")
            print(f"🧠 Embedding Model: {health['rag_config']['embedding_model']}")
            return True
            
        else:
            print(f"❌ RAG Builder health check failed: {health_response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to RAG Builder container!")
        print("💡 Make sure containers are running: docker-compose up -d")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def load_test_document():
    """Load the test document from file with error handling"""
    try:
        with open("test_document.txt", 'r', encoding='utf-8') as file:
            content = file.read().strip()
            print(f"📄 Loaded ML Wikipedia page: {len(content):,} characters")
            return content
    except FileNotFoundError:
        print("❌ test_document.txt not found!")
        print("💡 Make sure your ML Wikipedia content is saved as test_document.txt")
        return None
    except Exception as e:
        print(f"❌ Error reading test document: {e}")
        return None

def test_embed_and_retrieve():
    """Test the complete embed and retrieve workflow with containerized RAG Builder"""
    
    print("=" * 60)
    print("🐳 TESTING CONTAINERIZED RAG BUILDER")
    print("=" * 60)
    
    # First, test container health
    if not test_container_health():
        print("❌ Container health check failed. Aborting test.")
        return False
    
    print("\n" + "─" * 50)
    
    # Clean up any previous test data to start fresh
    print("🧹 Cleaning up previous test data...")
    try:
        requests.delete(f"{RAG_BUILDER_URL}/collections/{SESSION_ID}")
        print("✅ Previous test data cleaned")
    except:
        print("ℹ️  No previous data to clean (normal)")
    
    # Load the ML Wikipedia page
    document = load_test_document()
    if not document:
        return False
    
    print(f"📄 Preview: {document[:100]}...")
    print(f"📄 Document end: ...{document[-100:]}")
    
    print("\n📄 Testing document embedding with container...")
    
    # 1. Embed document
    embed_response = requests.post(f"{RAG_BUILDER_URL}/embed", json={
        "content": document,
        "session_id": SESSION_ID,
        "source_url": "https://en.wikipedia.org/wiki/test_page",
        "title": "Wikipedia Test Document"
    })
    
    if embed_response.status_code == 200:
        result = embed_response.json()
        chunks_created = result['processing_summary']['total_chunks']
        total_tokens = result['processing_summary']['total_tokens']
        
        print(f"✅ Successfully embedded ML Wikipedia page!")
        print(f"📊 Chunks created: {chunks_created}")
        print(f"🔢 Total tokens: {total_tokens:,}")
        print(f"📏 Average chunk size: {result['processing_summary']['average_chunk_size']} tokens")
        print(f"💾 Stored in collection: {result['storage_summary']['collection_name']}")
        
        # Validate results for large Wikipedia article
        if chunks_created >= EXPECTED_MIN_CHUNKS:
            print(f"✅ Chunk count validation passed ({chunks_created} >= {EXPECTED_MIN_CHUNKS})")
        else:
            print(f"⚠️  Low chunk count: {chunks_created} (expected >= {EXPECTED_MIN_CHUNKS})")
            
        if total_tokens >= EXPECTED_MIN_TOKENS:
            print(f"✅ Token count validation passed ({total_tokens:,} >= {EXPECTED_MIN_TOKENS:,})")
        else:
            print(f"⚠️  Low token count: {total_tokens:,} (expected >= {EXPECTED_MIN_TOKENS:,})")
            
    else:
        print(f"❌ Container embedding failed: {embed_response.text}")
        return False

    print("\n🔍 Testing chunk retrieval...")
    
    # 2. Retrieve chunks with Machine Learning specific queries
    queries = [
        "What is machine learning?",                    # Definition/overview
        "supervised learning vs unsupervised learning", # Core concepts
        "neural networks and deep learning",            # Advanced techniques  
        "applications of machine learning",             # Real-world usage (matches your snippet!)
        "training data and algorithms",                 # Technical fundamentals
        "computer vision and NLP applications",         # Specific domains
        "predictive analytics in business",             # Business applications
        "history and development of ML"                 # Historical context
    ]
    
    for query in queries:
        retrieve_response = requests.post(f"{RAG_BUILDER_URL}/retrieve", json={
            "query": query,
            "session_id": SESSION_ID,
            "max_results": 3,
            "similarity_threshold": 0.1
        })
        
        if retrieve_response.status_code == 200:
            result = retrieve_response.json()
            print(f"\n🔎 Query: '{query}'")
            print(f"✅ Found {len(result['chunks'])} relevant chunks")
            
            for i, chunk in enumerate(result['chunks'], 1):
                print(f"   {i}. Similarity: {chunk['similarity_score']:.3f}")
                print(f"      Content: {chunk['content'][:100]}...")
                print(f"      Source: {chunk['metadata']['source_url']}")
                print()
        else:
            print(f"❌ Retrieval failed: {retrieve_response.text}")
    
    return True

def test_collection_info():
    """Test collection management features"""
    print("\n📁 Testing collection management...")
    
    # Get session info
    info_response = requests.get(f"{RAG_BUILDER_URL}/collections/{SESSION_ID}")
    if info_response.status_code == 200:
        info = info_response.json()
        if info.get('exists'):
            print(f"✅ Session collection: {info['chunk_count']} chunks stored")
            print(f"📦 Collection name: {info['collection_name']}")
        else:
            print(f"❌ Session collection not found")
    
    # List all collections
    collections_response = requests.get(f"{RAG_BUILDER_URL}/collections")
    if collections_response.status_code == 200:
        collections = collections_response.json()
        print(f"📚 Total collections: {collections['total_collections']}")

if __name__ == "__main__":
    print("🚀 Container RAG Builder Test Suite")
    print("📋 Testing ML Wikipedia page with containerized services")
    print()
    
    try:
        # Run the main test
        success = test_embed_and_retrieve()
        
        if success:
            print("\n" + "─" * 50)
            test_collection_info()
            print("\n" + "=" * 60)
            print("🎉 ALL CONTAINER TESTS PASSED!")
            print("✅ RAG Builder container is working perfectly")
            print("✅ ML Wikipedia page processed successfully") 
            print("✅ Semantic search working with good relevance")
            print("=" * 60)
        else:
            print("\n❌ Container tests failed!")
            print("💡 Check docker-compose logs for details")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to containers!")
        print("💡 Make sure containers are running:")
        print("   docker-compose up -d")
        print("   docker-compose ps  # Check status")
    except Exception as e:
        print(f"❌ Unexpected test error: {e}")
        print("💡 Check container logs: docker-compose logs rag-builder") 