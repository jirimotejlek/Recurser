import streamlit as st
import chromadb
import os
from datetime import datetime
import hashlib

# You can add other imports for your RAG functionality
# from langchain.embeddings import OpenAIEmbeddings
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# import PyPDF2

def init_chromadb():
    """Initialize ChromaDB connection"""
    return chromadb.HttpClient(
        host=os.getenv('CHROMA_HOST', 'chromadb'),
        port=int(os.getenv('CHROMA_PORT', '8000'))
    )

def process_document(uploaded_file, collection):
    """Process and add document to ChromaDB"""
    # This is a placeholder - add your actual document processing logic
    content = uploaded_file.read().decode('utf-8')
    
    # Generate a unique ID for the document
    doc_id = hashlib.md5(content.encode()).hexdigest()[:12]
    
    # Add metadata
    metadata = {
        "filename": uploaded_file.name,
        "upload_time": datetime.now().isoformat(),
        "size": len(content)
    }
    
    # In a real implementation, you would:
    # 1. Split the document into chunks
    # 2. Generate embeddings
    # 3. Add to ChromaDB
    
    # Simple example: add as single document
    collection.add(
        documents=[content],
        ids=[doc_id],
        metadatas=[metadata]
    )
    
    return doc_id

def search_documents(query, collection, n_results=5):
    """Search documents in ChromaDB"""
    # Perform the search
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    return results

def run_main_app():
    """Main RAG application"""
    st.title("RAG Application!")
    st.write("Build your knowledge base and ask questions!")
    
    # Initialize ChromaDB
    try:
        client = st.session_state.get('chromadb_client')
        if not client:
            client = init_chromadb()
            st.session_state.chromadb_client = client
        
        # Connection status in sidebar
        with st.sidebar:
            st.success("✅ Connected to ChromaDB")
            
            # Collection selector
            st.header("Settings")
            collections = client.list_collections()
            collection_names = [col.name for col in collections] + ["+ Create New"]
            
            selected_collection = st.selectbox(
                "Select Collection",
                collection_names,
                index=0 if collection_names else None
            )
            
            if selected_collection == "+ Create New":
                new_collection_name = st.text_input("Collection Name")
                if st.button("Create Collection") and new_collection_name:
                    try:
                        client.create_collection(new_collection_name)
                        st.success(f"Created collection: {new_collection_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating collection: {e}")
            
            # Settings
            st.divider()
            n_results = st.slider("Number of results", 1, 20, 5)
            
            # Stats
            if selected_collection and selected_collection != "+ Create New":
                collection = client.get_collection(selected_collection)
                st.metric("Documents", collection.count())
        
        # Main interface
        tab1, tab2, tab3 = st.tabs(["📄 Upload Documents", "🔍 Search", "📊 Analytics"])
        
        with tab1:
            st.header("Upload Documents")
            
            if not selected_collection or selected_collection == "+ Create New":
                st.warning("Please select or create a collection first.")
            else:
                collection = client.get_collection(selected_collection)
                
                uploaded_files = st.file_uploader(
                    "Choose files",
                    type=['txt', 'pdf', 'docx', 'md'],
                    accept_multiple_files=True
                )
                
                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        with st.spinner(f"Processing {uploaded_file.name}..."):
                            try:
                                doc_id = process_document(uploaded_file, collection)
                                st.success(f"✅ Uploaded: {uploaded_file.name} (ID: {doc_id})")
                            except Exception as e:
                                st.error(f"❌ Error processing {uploaded_file.name}: {e}")
                    
                    st.balloons()
                    st.info(f"Total documents in collection: {collection.count()}")
        
        with tab2:
            st.header("Search Documents")
            
            if not selected_collection or selected_collection == "+ Create New":
                st.warning("Please select a collection first.")
            else:
                collection = client.get_collection(selected_collection)
                
                # Search interface
                query = st.text_area("Enter your question:", height=100)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    search_button = st.button("🔍 Search", type="primary", use_container_width=True)
                with col2:
                    clear_button = st.button("🗑️ Clear", use_container_width=True)
                
                if clear_button:
                    st.session_state.pop('search_results', None)
                    st.rerun()
                
                if search_button and query:
                    with st.spinner("Searching..."):
                        try:
                            results = search_documents(query, collection, n_results)
                            st.session_state.search_results = results
                        except Exception as e:
                            st.error(f"Search error: {e}")
                
                # Display results
                if 'search_results' in st.session_state:
                    results = st.session_state.search_results
                    
                    st.divider()
                    st.subheader("Search Results")
                    
                    if results['documents'] and results['documents'][0]:
                        for i, (doc, distance, metadata) in enumerate(zip(
                            results['documents'][0],
                            results['distances'][0],
                            results['metadatas'][0]
                        )):
                            with st.expander(f"Result {i+1} - Score: {1-distance:.3f}"):
                                st.write("**Content:**")
                                st.write(doc[:500] + "..." if len(doc) > 500 else doc)
                                
                                st.write("**Metadata:**")
                                st.json(metadata)
                                
                                st.write(f"**Distance:** {distance:.4f}")
                    else:
                        st.info("No results found. Try a different query.")
        
        with tab3:
            st.header("Collection Analytics")
            
            if not selected_collection or selected_collection == "+ Create New":
                st.warning("Please select a collection first.")
            else:
                collection = client.get_collection(selected_collection)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Documents", collection.count())
                
                with col2:
                    st.metric("Collection Name", selected_collection)
                
                with col3:
                    st.metric("Active Collections", len(collections))
                
                # You can add more analytics here
                st.divider()
                
                if st.button("🗑️ Delete This Collection", type="secondary"):
                    if st.checkbox("I understand this will delete all documents"):
                        try:
                            client.delete_collection(selected_collection)
                            st.success(f"Deleted collection: {selected_collection}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting collection: {e}")
                
    except Exception as e:
        st.error(f"Failed to connect to ChromaDB: {e}")
        st.info("💡 Try running the ChromaDB test to diagnose the issue.")
        if st.button("Go to ChromaDB Test"):
            st.query_params = {"page": "test_chromadb"}
            st.rerun()

# This allows the file to be imported and run independently
if __name__ == "__main__":
    run_main_app()