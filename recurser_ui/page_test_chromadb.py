import streamlit as st
import os
import sys
import requests
from datetime import datetime

# Try to import chromadb with better error handling
try:
    import chromadb
    CHROMADB_AVAILABLE = True
    CHROMADB_VERSION = chromadb.__version__
except ImportError as e:
    CHROMADB_AVAILABLE = False
    CHROMADB_VERSION = None
    st.error(f"ChromaDB module not installed: {e}")
except Exception as e:
    CHROMADB_AVAILABLE = False
    CHROMADB_VERSION = None
    st.error(f"Error loading ChromaDB: {e}")

def streamlit_page():
    """ChromaDB Connection Test Page"""
    st.title("ChromaDB Connection Test")
    
    # Check if ChromaDB is available
    if not CHROMADB_AVAILABLE:
        st.error("❌ ChromaDB module is not available. Please check your requirements.txt")
        st.code("pip install chromadb>=1.0.0")
        return
    
    # Get connection parameters
    host = os.getenv('CHROMA_HOST', 'chromadb')
    port = int(os.getenv('CHROMA_PORT', '8000'))
    
    st.write(f"**Connection Parameters:**")
    st.code(f"Host: {host}\nPort: {port}")
    
    # Test 1: Basic connectivity
    st.header("1. Basic Connectivity Test")
    try:
        response = requests.get(f"http://{host}:{port}/api/v2/heartbeat", timeout=5)
        if response.status_code == 200:
            st.success(f"✅ ChromaDB is reachable! Status: {response.status_code}")
            st.json(response.json())
        else:
            st.error(f"❌ ChromaDB returned status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to ChromaDB at {host}:{port}")
        st.info("Make sure the ChromaDB container is running: `docker ps`")
        return
    except Exception as e:
        st.error(f"❌ Connection failed: {type(e).__name__}: {e}")
        return
    
    # Test 2: ChromaDB Client
    st.header("2. ChromaDB Client Test")
    client = None
    try:
        # Create client with explicit error handling
        st.write("Creating ChromaDB client...")
        client = chromadb.HttpClient(host=host, port=port)
        st.success("✅ ChromaDB client initialized successfully!")
        
        # List collections
        st.write("Listing collections...")
        collections = client.list_collections()
        st.write(f"**Number of collections:** {len(collections)}")
        
        if collections:
            st.write("**Existing collections:**")
            for col in collections:
                st.write(f"- {col.name}")
        else:
            st.info("No collections found (this is normal for a fresh instance)")
            
    except AttributeError as e:
        st.error(f"❌ ChromaDB module issue: {e}")
        st.info("This might be a version compatibility issue. Check your ChromaDB version.")
        return
    except Exception as e:
        st.error(f"❌ Client initialization failed: {type(e).__name__}: {e}")
        st.info("Check the Docker logs: `docker logs chromadb`")
        return
    
    # Test 3: Create and test a collection
    st.header("3. Collection Operations Test")
    
    if st.button("Run Collection Test") and client:
        test_collection_name = f"test_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Create collection
            with st.spinner("Creating test collection..."):
                collection = client.create_collection(name=test_collection_name)
                st.success(f"✅ Created collection: {test_collection_name}")
            
            # Add documents
            with st.spinner("Adding test documents..."):
                collection.add(
                    documents=[
                        "The quick brown fox jumps over the lazy dog",
                        "ChromaDB is a vector database for AI applications",
                        "Streamlit makes it easy to build data apps"
                    ],
                    ids=["doc1", "doc2", "doc3"],
                    metadatas=[
                        {"source": "test", "category": "pangram"},
                        {"source": "test", "category": "tech"},
                        {"source": "test", "category": "tech"}
                    ]
                )
                st.success("✅ Added 3 test documents")
            
            # Query test
            with st.spinner("Testing query functionality..."):
                results = collection.query(
                    query_texts=["vector database"],
                    n_results=2
                )
                st.success("✅ Query executed successfully!")
                
                st.write("**Query Results:**")
                if results and 'documents' in results and results['documents']:
                    for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0])):
                        st.write(f"{i+1}. {doc[:100]}... (distance: {distance:.4f})")
                else:
                    st.warning("No results returned")
            
            # Cleanup
            with st.spinner("Cleaning up..."):
                client.delete_collection(test_collection_name)
                st.success(f"✅ Deleted test collection")
                
            st.balloons()
            st.success("🎉 All tests passed! ChromaDB is working perfectly!")
            
        except Exception as e:
            st.error(f"❌ Test failed: {type(e).__name__}: {e}")
            # Try to cleanup if collection was created
            try:
                client.delete_collection(test_collection_name)
                st.info("Cleaned up test collection")
            except:
                pass
    
    # Test 4: Performance test
    if client:
        st.header("4. Performance Test")
        
        if st.button("Run Performance Test"):
            try:
                import time
                
                # Create collection for performance test
                perf_collection = client.get_or_create_collection("performance_test")
                
                # Test insertion speed
                start_time = time.time()
                perf_collection.add(
                    documents=[f"Document {i}" for i in range(100)],
                    ids=[f"perf_doc_{i}" for i in range(100)]
                )
                insert_time = time.time() - start_time
                
                st.success(f"✅ Inserted 100 documents in {insert_time:.2f} seconds")
                
                # Test query speed
                start_time = time.time()
                results = perf_collection.query(
                    query_texts=["test query"],
                    n_results=10
                )
                query_time = time.time() - start_time
                
                st.success(f"✅ Query executed in {query_time:.3f} seconds")
                
                # Show collection stats
                st.write(f"**Collection count:** {perf_collection.count()}")
                
            except Exception as e:
                st.error(f"❌ Performance test failed: {type(e).__name__}: {e}")
    
    # Debug information
    with st.expander("🔧 Debug Information"):
        st.write("**Environment Variables:**")
        env_vars = {
            "CHROMA_HOST": os.getenv('CHROMA_HOST', 'not set'),
            "CHROMA_PORT": os.getenv('CHROMA_PORT', 'not set'),
            "PYTHONPATH": os.getenv('PYTHONPATH', 'not set'),
            "PATH": os.getenv('PATH', 'not set')[:100] + "..."  # Truncate long PATH
        }
        for key, value in env_vars.items():
            st.code(f"{key}: {value}")
        
        st.write("**Python Information:**")
        st.code(f"Python version: {sys.version}")
        st.code(f"Python executable: {sys.executable}")
        
        st.write("**ChromaDB Information:**")
        if CHROMADB_AVAILABLE:
            st.code(f"chromadb=={CHROMADB_VERSION}")
            st.code(f"Module location: {chromadb.__file__ if hasattr(chromadb, '__file__') else 'Unknown'}")
        else:
            st.error("ChromaDB module not available")
        
        st.write("**Installed Packages:**")
        if st.button("Show installed packages"):
            import subprocess
            result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                                  capture_output=True, text=True)
            st.code(result.stdout)