# analytics.py
import streamlit as st
import os
import requests

SEARCH_ENGINE = os.getenv('SEARCH_ENGINE', 'search-engine')
SEARCH_ENGINE_PORT = os.getenv('SEARCH_ENGINE_PORT', '5150')

def streamlit_page():
    st.title("📊 Analytics Dashboard")
    # Your analytics code here
    if st.button("Test web search"):
        with st.spinner("Searching..."):
            response = requests.post(f"http://{SEARCH_ENGINE}:{SEARCH_ENGINE_PORT}/query", timeout=60, json={"search_query": "What is the capital of France?"})
            st.write(response)
            data = response.json()
            if 'response' in data:
                st.write(data['response'])
            else:
                st.error(f"❌ Error: {'Unknown error'}")