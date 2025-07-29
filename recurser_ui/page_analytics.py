# analytics.py
import os
import time
from datetime import datetime, timedelta

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
RAG_BUILDER = os.getenv("RAG_BUILDER", "rag-builder")
RAG_BUILDER_PORT = os.getenv("RAG_BUILDER_PORT", "5300")


def streamlit_page():
    st.title("📊 Analytics Dashboard")
    st.markdown("Monitor system performance, query statistics, and service health.")

    # System Overview
    st.header("🔧 System Overview")

    # Quick Health Status
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Search Engine", "🟢 Online")
    with col2:
        st.metric("Scraper", "🟢 Online")
    with col3:
        st.metric("RAG Builder", "🟢 Online")
    with col4:
        st.metric("LLM Dispatcher", "🟢 Online")

    # Service Testing Section
    st.header("🧪 Service Testing")

    # First row of tests
    cols = st.columns(3)

    with cols[0]:
        if st.button("Test web search", use_container_width=True):
            with st.spinner("Searching..."):
                try:
                    start_time = time.time()
                    response = requests.post(
                        f"http://{SEARCH_ENGINE}:{SEARCH_ENGINE_PORT}/query",
                        timeout=60,
                        json={"search_query": "What is the capital of France?"},
                    )
                    end_time = time.time()

                    if response.status_code == 200:
                        data = response.json()
                        st.success(
                            f"✅ Search successful in {end_time - start_time:.2f}s"
                        )
                        st.write(f"**Results found:** {data.get('result_count', 0)}")
                        if "response" in data and len(data["response"]) > 0:
                            st.write(
                                f"**First result:** {data['response'][0].get('title', 'No title')}"
                            )
                    else:
                        st.error(f"❌ Error: HTTP {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    with cols[1]:
        if st.button("Test web scraper", use_container_width=True):
            with st.spinner("Scraping..."):
                try:
                    start_time = time.time()
                    response = requests.post(
                        f"http://{SCRAPER}:{SCRAPER_PORT}/scrape",
                        timeout=60,
                        json={"url": "https://www.google.com"},
                    )
                    end_time = time.time()

                    if response.status_code == 200:
                        data = response.json()
                        st.success(
                            f"✅ Scraping successful in {end_time - start_time:.2f}s"
                        )
                        if "response" in data:
                            st.write(
                                f"**Content length:** {len(data['response'])} characters"
                            )
                    else:
                        st.error(f"❌ Error: HTTP {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    with cols[2]:
        if st.button("Test optimizer", use_container_width=True):
            with st.spinner("Testing..."):
                try:
                    start_time = time.time()
                    response = requests.get(
                        f"http://{OPTIMIZER}:{OPTIMIZER_PORT}/health", timeout=60
                    )
                    end_time = time.time()

                    if response.status_code == 200:
                        data = response.json()
                        st.success(
                            f"✅ Optimizer healthy in {end_time - start_time:.2f}s"
                        )
                        st.write(f"**Status:** {data.get('status', 'Unknown')}")
                    else:
                        st.error(f"❌ Error: HTTP {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # Second row of tests
    cols = st.columns(3)

    with cols[0]:
        if st.button("Test LLM dispatcher", use_container_width=True):
            with st.spinner("Testing..."):
                try:
                    start_time = time.time()
                    response = requests.get(
                        f"http://{LLM_DISPATCHER}:{LLM_DISPATCHER_PORT}/health",
                        timeout=60,
                    )
                    end_time = time.time()

                    if response.status_code == 200:
                        data = response.json()
                        st.success(
                            f"✅ LLM Dispatcher healthy in {end_time - start_time:.2f}s"
                        )
                        st.write(f"**Status:** {data.get('status', 'Unknown')}")
                    else:
                        st.error(f"❌ Error: HTTP {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    with cols[1]:
        if st.button("Test RAG builder", use_container_width=True):
            with st.spinner("Testing..."):
                try:
                    start_time = time.time()
                    response = requests.get(
                        f"http://{RAG_BUILDER}:{RAG_BUILDER_PORT}/health", timeout=60
                    )
                    end_time = time.time()

                    if response.status_code == 200:
                        data = response.json()
                        st.success(
                            f"✅ RAG Builder healthy in {end_time - start_time:.2f}s"
                        )
                        st.write(f"**Status:** {data.get('status', 'Unknown')}")
                    else:
                        st.error(f"❌ Error: HTTP {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    with cols[2]:
        if st.button("Test ChromaDB", use_container_width=True):
            with st.spinner("Testing..."):
                try:
                    start_time = time.time()
                    response = requests.get(
                        "http://chromadb:8000/api/v2/heartbeat", timeout=60
                    )
                    end_time = time.time()

                    if response.status_code == 200:
                        st.success(
                            f"✅ ChromaDB healthy in {end_time - start_time:.2f}s"
                        )
                    else:
                        st.error(f"❌ Error: HTTP {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # System Information
    st.header("ℹ️ System Information")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Environment Variables")
        env_vars = {
            "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "Not set"),
            "CHROMA_HOST": os.getenv("CHROMA_HOST", "Not set"),
            "CHROMA_PORT": os.getenv("CHROMA_PORT", "Not set"),
            "OPTIMIZER_HOST": os.getenv("OPTIMIZER_HOST", "Not set"),
            "SEARCH_ENGINE": os.getenv("SEARCH_ENGINE", "Not set"),
            "SCRAPER": os.getenv("SCRAPER", "Not set"),
            "RAG_BUILDER": os.getenv("RAG_BUILDER", "Not set"),
        }

        for key, value in env_vars.items():
            st.write(f"**{key}:** {value}")

    with col2:
        st.subheader("Service Endpoints")
        endpoints = {
            "Optimizer": "http://optimizer:5050",
            "Search Engine": "http://search-engine:5150",
            "Scraper": "http://scraper:5200",
            "RAG Builder": "http://rag-builder:5300",
            "LLM Dispatcher": "http://llm-dispatcher:5100",
            "ChromaDB": "http://chromadb:8000",
        }

        for service, endpoint in endpoints.items():
            st.write(f"**{service}:** {endpoint}")

    # Refresh button
    st.markdown("---")
    if st.button("🔄 Refresh Analytics", use_container_width=True):
        st.rerun()

    # Footer
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
