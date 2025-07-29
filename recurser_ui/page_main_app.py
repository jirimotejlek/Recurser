import streamlit as st
import os

CHROMA_HOST = os.getenv('CHROMA_HOST', 'chromadb')
CHROMA_PORT = os.getenv('CHROMA_PORT', '8000')

def streamlit_page():
    """Main RAG application"""
    st.title("RAG Application!")
    st.write("Build your knowledge base and ask questions!")


def init_chromadb():
    """Initialize ChromaDB connection"""
    return chromadb.HttpClient(
        host=CHROMA_HOST,
        port=int(CHROMA_PORT)
    )


if __name__ == "__main__":
    streamlit_page()