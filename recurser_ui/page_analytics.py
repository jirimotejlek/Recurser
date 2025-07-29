# analytics.py
import streamlit as st
import os
import requests

SEARCH_ENGINE = os.getenv('SEARCH_ENGINE', 'search-engine')
SEARCH_ENGINE_PORT = os.getenv('SEARCH_ENGINE_PORT', '5150')
SCRAPER = os.getenv('SCRAPER', 'scraper')
SCRAPER_PORT = os.getenv('SCRAPER_PORT', '5200')

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

    if st.button("Test web scraper"):
        with st.spinner("Searching..."):
            response = requests.post(f"http://{SCRAPER}:{SCRAPER_PORT}/scrape", timeout=60, json={"url": "https://www.google.com"})
            st.write(response)
            data = response.json()
            if 'response' in data:
                st.write(data['response'])
            else:
                st.error(f"❌ Error: {'Unknown error'}")