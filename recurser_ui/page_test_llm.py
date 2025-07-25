import streamlit as st
import requests
#import anthropic
import json
import os
from typing import Dict, Any, Optional

LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'error')
LLM_DISPATCHER = os.getenv('LLM_DISPATCHER', 'error')
LLM_DISPATCHER_PORT = os.getenv('LLM_DISPATCHER_PORT', 'error')

def streamlit_page():
    if LLM_PROVIDER == 'local':
        local_llm_page()
    elif LLM_PROVIDER != 'error':
        external_llm_page()


def external_llm_page():
    st.title("External LLM Test")

    st.write(f"LLM_PROVIDER: **{LLM_PROVIDER}**")
    response = requests.get(f"http://{LLM_DISPATCHER}:{LLM_DISPATCHER_PORT}/models", timeout=5)
    if response.status_code == 200:
        st.success("✅ LLM Dispatcher is reachable")
    else:
        st.error(f"Failed to fetch models: {response.status_code}")

    if st.button("Test connection"):
        response = requests.post(f"http://{LLM_DISPATCHER}:{LLM_DISPATCHER_PORT}/query", timeout=60, json={"prompt": "What is the capital of France?"})
        st.write(response.json())
        data = response.json()
        if 'response' in data:
            st.write(data['response'])
        else:
            st.error(f"❌ Error: {'Unknown error'}")
            

def local_llm_page():
    """Ollama LLM Test Page"""
    st.title("Ollama LLM Test")


    # Test prompts
    st.subheader("Quick Tests")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Test Basic"):
            with st.spinner("Generating..."):
                response = requests.post(f"http://{LLM_DISPATCHER}:{LLM_DISPATCHER_PORT}/query", timeout=60, json={"prompt": "Say 'Hello, I'm working!' and nothing else."})
                data = response.json()
                if 'response' in data:
                    st.write(data['response'])
                else:
                    st.error(f"❌ Error: {'Unknown error'}")


    with col2:
        if st.button("Test Math"):
            with st.spinner("Calculating..."):
                response = requests.post(f"http://{LLM_DISPATCHER}:{LLM_DISPATCHER_PORT}/query", timeout=60, json={"prompt": "What is 25 + 17? Just give the number."})
                data = response.json()
                if 'response' in data:
                    st.write(data['response'])
                else:
                    st.error(f"❌ Error: {'Unknown error'}")

    with col3:
        if st.button("Test Completion"):
            with st.spinner("Completing..."):
                response = requests.post(f"http://{LLM_DISPATCHER}:{LLM_DISPATCHER_PORT}/query", timeout=60, json={"prompt": "Complete this: The capital of France is"})
                data = response.json()
                if 'response' in data:
                    st.write(data['response'])
                else:
                    st.error(f"❌ Error: {'Unknown error'}")

if __name__ == "__main__":
    streamlit_page()