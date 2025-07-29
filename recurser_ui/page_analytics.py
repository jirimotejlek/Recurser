# analytics.py
import os

import requests
import streamlit as st

SEARCH_ENGINE = os.getenv("SEARCH_ENGINE", "search-engine")
SEARCH_ENGINE_PORT = os.getenv("SEARCH_ENGINE_PORT", "5150")
SCRAPER = os.getenv("SCRAPER", "scraper")
SCRAPER_PORT = os.getenv("SCRAPER_PORT", "5200")
OPTIMIZER = os.getenv("OPTIMIZER", "optimizer")
OPTIMIZER_PORT = os.getenv("OPTIMIZER_PORT", "5050")
LLM_DISPATCHER = os.getenv("LLM_DISPATCHER", "llm-dispatcher")
LLM_DISPATCHER_PORT = os.getenv("LLM_DISPATCHER_PORT", "5100")


def streamlit_page():
    st.title("📊 Analytics Dashboard")
    # Arrange buttons in a 3-column grid
    cols = st.columns(3)

    # First row
    with cols[0]:
        if st.button("Test web search", use_container_width=True):
            with st.spinner("Searching..."):
                response = requests.post(
                    f"http://{SEARCH_ENGINE}:{SEARCH_ENGINE_PORT}/query",
                    timeout=60,
                    json={"search_query": "What is the capital of France?"},
                )
                data = response.json()
                if "response" in data:
                    if len(data["response"]) > 0 and data["response"][0]["title"]:
                        st.success("Web search is healthy")
                    else:
                        st.error(f"❌ Error: {'Web search is not healthy'}")
                else:
                    st.error(f"❌ Error: {'Unknown error'}")
    with cols[1]:
        if st.button("Test web scraper", use_container_width=True):
            with st.spinner("Searching..."):
                response = requests.post(
                    f"http://{SCRAPER}:{SCRAPER_PORT}/scrape",
                    timeout=60,
                    json={"url": "https://www.google.com"},
                )
                st.write(response)
                data = response.json()
                if "response" in data:
                    st.write(data["response"])
                else:
                    st.error(f"❌ Error: {'Unknown error'}")
    with cols[2]:
        if st.button("Test optimizer", use_container_width=True):
            with st.spinner("Optimizing..."):
                response = requests.get(
                    f"http://{OPTIMIZER}:{OPTIMIZER_PORT}/health", timeout=60
                )
                response = response.json()
                if response["status"] == "healthy":
                    st.success("Optimizer is healthy")
                else:
                    st.error(f"❌ Error: {'Optimizer is not healthy'}")

    cols = st.columns(3)
    # Second row
    with cols[0]:
        if st.button("Test llm dispatcher", use_container_width=True):
            with st.spinner("Testing..."):
                response = requests.get(
                    f"http://{LLM_DISPATCHER}:{LLM_DISPATCHER_PORT}/health", timeout=60
                )
                response = response.json()
                if response["status"] == "healthy":
                    st.success("LLM Dispatcher is healthy")
                else:
                    st.error(f"❌ Error: {'LLM Dispatcher is not healthy'}")
    with cols[1]:
        if st.button("Test chromadb", use_container_width=True):
            with st.spinner("Testing..."):
                response = requests.get(
                    f"http://{LLM_DISPATCHER}:{LLM_DISPATCHER_PORT}/health", timeout=60
                )
                response = response.json()
                if response["services"]["chromadb"] == "up":
                    st.success("Chromadb is healthy")
                else:
                    st.error(f"❌ Error: {'Chromadb is not healthy'}")
    with cols[2]:
        if st.button("Test LLM", use_container_width=True):
            with st.spinner("Testing..."):
                response = requests.get(
                    f"http://{LLM_DISPATCHER}:{LLM_DISPATCHER_PORT}/health", timeout=60
                )
                response = response.json()
                if response["services"]["llm"] == "up":
                    st.success("Ollama is healthy")
                else:
                    st.error(f"❌ Error: {'LLM is not healthy'}")
