"""
Shared ChromaDB utilities used across the application
"""
import chromadb
import os
import streamlit as st
from typing import Optional, List, Dict, Any

@st.cache_resource
def get_chromadb_client() -> chromadb.HttpClient:
    """
    Get or create a cached ChromaDB client.
    Uses Streamlit's cache to avoid creating multiple connections.
    """
    return chromadb.HttpClient(
        host=os.getenv('CHROMA_HOST', 'chromadb'),
        port=int(os.getenv('CHROMA_PORT', '8000'))
    )

def list_collections() -> List[str]:
    """Get list of all collection names"""
    client = get_chromadb_client()
    return [col.name for col in client.list_collections()]

def create_collection_safe(name: str, **kwargs) -> Optional[Any]:
    """
    Safely create a collection, handling errors gracefully
    """
    try:
        client = get_chromadb_client()
        return client.create_collection(name, **kwargs)
    except Exception as e:
        st.error(f"Error creating collection '{name}': {e}")
        return None

def get_or_create_collection(name: str, **kwargs) -> Optional[Any]:
    """
    Get existing collection or create if it doesn't exist
    """
    try:
        client = get_chromadb_client()
        return client.get_or_create_collection(name, **kwargs)
    except Exception as e:
        st.error(f"Error accessing collection '{name}': {e}")
        return None

def delete_collection_safe(name: str) -> bool:
    """
    Safely delete a collection
    """
    try:
        client = get_chromadb_client()
        client.delete_collection(name)
        return True
    except Exception as e:
        st.error(f"Error deleting collection '{name}': {e}")
        return False

def get_collection_stats(collection_name: str) -> Dict[str, Any]:
    """
    Get statistics for a collection
    """
    try:
        client = get_chromadb_client()
        collection = client.get_collection(collection_name)
        
        return {
            "name": collection_name,
            "count": collection.count(),
            # Add more stats as needed
        }
    except Exception as e:
        return {"error": str(e)}

def check_chromadb_health() -> Dict[str, Any]:
    """
    Check ChromaDB connection health
    """
    import requests
    
    host = os.getenv('CHROMA_HOST', 'chromadb')
    port = int(os.getenv('CHROMA_PORT', '8000'))
    
    try:
        response = requests.get(
            f"http://{host}:{port}/api/v2/heartbeat",
            timeout=2
        )
        return {
            "status": "online" if response.status_code == 200 else "error",
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else None
        }
    except Exception as e:
        return {
            "status": "offline",
            "error": str(e)
        }