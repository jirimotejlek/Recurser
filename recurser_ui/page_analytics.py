# analytics.py
import os
import time
from datetime import datetime, timedelta

import requests
import streamlit as st


def streamlit_page():
    st.title("📊 Analytics Dashboard")
    st.markdown("Monitor system performance, query statistics, and service health.")

    # Temporarily simplified system status
    st.header("🔧 System Overview")
    st.info("System status monitoring temporarily disabled for debugging")

    # Performance Testing
    st.header("🧪 Performance Testing")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Search Engine Test")
        if st.button("Test Web Search"):
            with st.spinner("Testing search engine..."):
                try:
                    start_time = time.time()
                    response = requests.post(
                        "http://search-engine:5150/query",
                        timeout=30,
                        json={"search_query": "What is the capital of France?"},
                    )
                    end_time = time.time()

                    if response.status_code == 200:
                        data = response.json()
                        st.success(
                            f"✅ Search successful in {end_time - start_time:.2f}s"
                        )
                        st.write(f"**Results found:** {data.get('result_count', 0)}")
                        st.write(f"**Provider:** {data.get('provider', 'Unknown')}")

                        # Show first result
                        results = data.get("response", [])
                        if results:
                            st.write("**First result:**")
                            first_result = results[0]
                            if isinstance(first_result, dict):
                                st.write(
                                    f"Title: {first_result.get('title', 'No title')}"
                                )
                                st.write(f"URL: {first_result.get('link', 'No URL')}")
                            else:
                                st.write(str(first_result))
                    else:
                        st.error(f"❌ Search failed: {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Test failed: {str(e)}")

    with col2:
        st.subheader("LLM Dispatcher Test")
        if st.button("Test LLM"):
            with st.spinner("Testing LLM dispatcher..."):
                try:
                    start_time = time.time()
                    response = requests.post(
                        "http://llm-dispatcher:5100/query",
                        timeout=60,
                        json={"prompt": "Say 'Hello, I'm working!' and nothing else."},
                    )
                    end_time = time.time()

                    if response.status_code == 200:
                        data = response.json()
                        st.success(
                            f"✅ LLM test successful in {end_time - start_time:.2f}s"
                        )
                        st.write(f"**Response:** {data.get('response', 'No response')}")
                        st.write(f"**Model:** {data.get('model', 'Unknown')}")
                    else:
                        st.error(f"❌ LLM test failed: {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Test failed: {str(e)}")

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
        }

        for key, value in env_vars.items():
            st.write(f"**{key}:** {value}")

    with col2:
        st.subheader("Service Endpoints")
        endpoints = {
            "Optimizer": "http://optimizer:5050",
            "Search Engine": "http://search-engine:5150",
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
