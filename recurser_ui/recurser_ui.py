import streamlit as st

# Import page functions from separate files
from page_main_app import streamlit_page as streamlit_page_main_app
from page_test_chromadb import streamlit_page as streamlit_page_test_chromadb
from page_analytics import streamlit_page as streamlit_page_analytics
from page_test_llm import streamlit_page as streamlit_page_test_llm

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
            "function": streamlit_page_main_app,
            "description": "RAG Application"
        },
        "test_chromadb": {
            "title": "Test DB",
            "function": streamlit_page_test_chromadb,
            "description": "ChromaDB Connection Test"
        },
        "test_ollama": {
            "title": "Test LLM",
            "function": streamlit_page_test_llm,
            "description": "Ollama LLM Test"
        },
        "analytics": {
            "title": "Analytics",
            "function": streamlit_page_analytics,
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

        # Show direct link for current page
        if page != "main":
            st.divider()
            st.caption("Direct link to this page:")
            st.code(f"http://localhost:8501/?page={page}", language=None)


    # Route to the appropriate page
    if page in pages:
        pages[page]["function"]()
    else:
        # Default to main page if route not found
        pages["main"]["function"]()

if __name__ == "__main__":
    main()