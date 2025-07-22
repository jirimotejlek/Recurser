import streamlit as st
import os
import requests

# Import page functions from separate files
from main_app import run_main_app
from test_chromadb import run_chromadb_test
from analytics import run_analytics
from test_ollama import run_ollama_test

def main():
    """Main application entry point with routing"""
    st.set_page_config(
        page_title="RAG Application",
        page_icon="🤖",
        #layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Get query parameters for routing
    query_params = st.query_params
    page = query_params.get("page", "main")
    
    # Define available pages
    pages = {
        "main": {
            "title": "Main App",
            "function": run_main_app,
            "description": "RAG Application"
        },
        "test_chromadb": {
            "title": "Test DB",
            "function": run_chromadb_test,
            "description": "ChromaDB Connection Test"
        },
        "test_ollama": {
            "title": "Test LLM",
            "function": run_ollama_test,
            "description": "Ollama LLM Test"
        },
        "analytics": {
            "title": "Analytics",
            "function": run_analytics,
            "description": "Analytics Dashboard"
        }        
        # Add more pages here as needed
    }
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        
        # Navigation buttons
        for page_key, page_info in pages.items():
            if st.button(
                page_info["title"],
                key=f"nav_{page_key}",
                use_container_width=True,
                type="primary" if page == page_key else "secondary"
            ):
                st.query_params = {"page": page_key}
                st.rerun()
        
        st.divider()
        
        # Current page info
        current_page = pages.get(page, pages["main"])
        st.info(f"📍 {current_page['description']}")
        
        # Show direct link for current page
        if page != "main":
            st.caption("Direct link to this page:")
            st.code(f"http://localhost:8501/?page={page}", language=None)
        
        # Quick ChromaDB status check
        st.divider()
        st.caption("🔄 System Status")
        
        try:
            host = os.getenv('CHROMA_HOST', 'chromadb')
            port = int(os.getenv('CHROMA_PORT', '8000'))
            response = requests.get(
                f"http://{host}:{port}/api/v2/heartbeat",
                timeout=2
            )
            if response.status_code == 200:
                st.success("✅ ChromaDB: Online")
            else:
                st.error("❌ ChromaDB: Error")
        except requests.exceptions.ConnectionError:
            st.error("❌ ChromaDB: Offline")
        except Exception as e:
            st.error("❌ ChromaDB: Unknown")
        
        # Footer
        st.divider()
        st.caption("Built with Streamlit & ChromaDB")
    
    # Route to the appropriate page
    if page in pages:
        pages[page]["function"]()
    else:
        # Default to main page if route not found
        pages["main"]["function"]()

if __name__ == "__main__":
    main()