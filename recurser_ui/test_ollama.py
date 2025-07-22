import streamlit as st
import requests
import json
import os
from typing import Dict, Any, Optional

def test_ollama_connection():
    """Test connection to Ollama service"""
    host = os.getenv('OLLAMA_HOST', 'llm')
    port = int(os.getenv('OLLAMA_PORT', '11434'))
    
    try:
        response = requests.get(f"http://{host}:{port}/api/tags", timeout=5)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except Exception as e:
        return False, str(e)

def query_ollama(prompt: str, model: str = None, stream: bool = False) -> Dict[str, Any]:
    """Send a query to Ollama"""
    host = os.getenv('OLLAMA_HOST', 'llm')
    port = int(os.getenv('OLLAMA_PORT', '11434'))
    model = model or os.getenv('OLLAMA_MODEL', 'gemma:3b')
    
    url = f"http://{host}:{port}/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}

def run_ollama_test():
    """Ollama LLM Test Page"""
    st.title("Ollama LLM Test")
    
    # Get connection parameters
    host = os.getenv('OLLAMA_HOST', 'llm')
    port = int(os.getenv('OLLAMA_PORT', '11434'))
    default_model = os.getenv('OLLAMA_MODEL', 'gemma:3b')
    
    st.write("**Connection Parameters:**")
    st.code(f"Host: {host}\nPort: {port}\nDefault Model: {default_model}")
    
    # Test 1: Basic connectivity
    st.header("1. Connectivity Test")
    is_connected, data = test_ollama_connection()
    
    if is_connected:
        st.success("✅ Ollama is reachable!")
        if data and 'models' in data:
            st.write("**Available Models:**")
            for model in data['models']:
                st.write(f"- {model['name']} ({model['size']})")
        else:
            st.warning("No models found. The model might still be downloading.")
    else:
        st.error(f"❌ Connection failed: {data}")
        st.stop()
    
    # Test 2: Model inference
    st.header("2. Model Inference Test")
    
    # Model selector
    available_models = []
    if is_connected and data and 'models' in data:
        available_models = [model['name'] for model in data['models']]
    
    if available_models:
        selected_model = st.selectbox(
            "Select Model",
            available_models,
            index=available_models.index(default_model) if default_model in available_models else 0
        )
    else:
        selected_model = st.text_input("Model Name", value=default_model)
    
    # Test prompts
    st.subheader("Quick Tests")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Test Basic"):
            with st.spinner("Generating..."):
                result = query_ollama("Say 'Hello, I'm working!' and nothing else.", selected_model)
                if 'response' in result:
                    st.success("✅ Basic test passed!")
                    st.write(result['response'])
                else:
                    st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
    
    with col2:
        if st.button("Test Math"):
            with st.spinner("Calculating..."):
                result = query_ollama("What is 25 + 17? Just give the number.", selected_model)
                if 'response' in result:
                    st.write(result['response'])
                else:
                    st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
    
    with col3:
        if st.button("Test Completion"):
            with st.spinner("Completing..."):
                result = query_ollama("Complete this: The capital of France is", selected_model)
                if 'response' in result:
                    st.write(result['response'])
                else:
                    st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
    
    # Custom prompt
    st.divider()
    st.subheader("Custom Prompt")
    
    prompt = st.text_area("Enter your prompt:", height=100)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        generate_button = st.button("🚀 Generate", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)
    
    if clear_button:
        st.session_state.pop('ollama_result', None)
        st.rerun()
    
    if generate_button and prompt:
        with st.spinner("Generating response..."):
            import time
            start_time = time.time()
            
            result = query_ollama(prompt, selected_model)
            
            end_time = time.time()
            generation_time = end_time - start_time
            
            st.session_state.ollama_result = {
                'result': result,
                'time': generation_time,
                'prompt': prompt,
                'model': selected_model
            }
    
    # Display result
    if 'ollama_result' in st.session_state:
        result_data = st.session_state.ollama_result
        
        st.divider()
        st.subheader("Response")
        
        if 'response' in result_data['result']:
            st.write(result_data['result']['response'])
            
            # Show metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Generation Time", f"{result_data['time']:.2f}s")
            with col2:
                st.metric("Model", result_data['model'])
            with col3:
                if 'total_duration' in result_data['result']:
                    total_ms = result_data['result']['total_duration'] / 1_000_000
                    st.metric("Total Duration", f"{total_ms:.0f}ms")
            
            # Show additional details in expander
            with st.expander("📊 Detailed Response"):
                st.json(result_data['result'])
        else:
            st.error(f"Error: {result_data['result'].get('error', 'Unknown error')}")
    
    # RAG Integration Example
    st.divider()
    st.header("3. RAG Integration Example")
    
    with st.expander("💡 How to integrate with ChromaDB"):
        st.code('''
# Example RAG integration
import chromadb
from typing import List

def rag_query(question: str, collection_name: str) -> str:
    # 1. Get relevant documents from ChromaDB
    client = chromadb.HttpClient(host='chromadb', port=8000)
    collection = client.get_collection(collection_name)
    
    # Search for relevant documents
    results = collection.query(
        query_texts=[question],
        n_results=3
    )
    
    # 2. Build context from results
    context = "\\n\\n".join(results['documents'][0])
    
    # 3. Create RAG prompt
    rag_prompt = f"""Use the following context to answer the question.
    
Context:
{context}

Question: {question}

Answer:"""
    
    # 4. Query Ollama
    response = query_ollama(rag_prompt, model='gemma:3b')
    
    return response.get('response', 'No response generated')
        ''', language='python')

# Allow direct execution for testing
if __name__ == "__main__":
    run_ollama_test()