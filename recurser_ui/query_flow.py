import json
from typing import Dict, List, Optional

import requests
import streamlit as st


def run_query_pipeline(user_query: str) -> dict:
    """
    Run the complete RAG pipeline with proper error handling and status updates.
    """
    try:
        # Step 1: Call optimiser (using the query endpoint)
        st.info("🔄 Optimizing your query...")
        optimization_prompt = f"Optimize this search query for better web search results: '{user_query}'. Return only the optimized query, nothing else."

        response = requests.post(
            "http://optimizer:5050/query",
            json={"prompt": optimization_prompt},
            timeout=30,
        )

        if response.status_code != 200:
            st.error(f"❌ Optimizer failed: {response.status_code}")
            st.error(f"Response text: {response.text}")
            return {"answer": "Error: Query optimization failed", "error": True}

        # Check if response is valid JSON
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            st.error(f"❌ Optimizer returned invalid JSON: {response.text}")
            return {"answer": "Error: Invalid response from optimizer", "error": True}

        optimal_query = response_data.get("response", user_query).strip()
        st.success(f"✅ Query optimized: '{optimal_query}'")

        # Step 2: Call search engine
        st.info("🔍 Searching the web...")
        search_response = requests.post(
            "http://search-engine:5150/query",
            json={"search_query": optimal_query},
            timeout=60,
        )

        if search_response.status_code != 200:
            st.error(f"❌ Search engine failed: {search_response.status_code}")
            st.error(f"Response text: {search_response.text}")
            return {"answer": "Error: Web search failed", "error": True}

        # Check if search response is valid JSON
        try:
            search_data = search_response.json()
        except json.JSONDecodeError as e:
            st.error(f"❌ Search engine returned invalid JSON: {search_response.text}")
            return {
                "answer": "Error: Invalid response from search engine",
                "error": True,
            }

        search_results = search_data.get("response", [])

        if not search_results:
            st.warning("⚠️ No search results found")
            return {
                "answer": "No relevant information found on the web for your query.",
                "error": False,
            }

        st.success(f"✅ Found {len(search_results)} search results")

        # Step 3: Prepare context from search results and generate response
        st.info("🤖 Generating response with LLM...")

        # Prepare context from search results
        search_context = f"Search query: {optimal_query}\n\nSearch results:\n"
        for i, result in enumerate(search_results[:5], 1):  # Limit to top 5 results
            if isinstance(result, dict):
                title = result.get("title", "No title")
                body = result.get("body", "No content")
                url = result.get("link", "No URL")
                search_context += (
                    f"{i}. {title}\n   URL: {url}\n   Content: {body[:200]}...\n\n"
                )
            else:
                search_context += f"{i}. {str(result)}\n"

        # Step 4: Send query + search context to LLM dispatcher
        llm_prompt = f"""Based on the following search results, provide a comprehensive answer to the user's question.

User Question: {user_query}

Search Results:
{search_context}

Please provide a detailed, accurate answer based on the search results above. If the search results don't contain enough information to answer the question, please say so."""

        llm_response = requests.post(
            "http://llm-dispatcher:5100/query", json={"prompt": llm_prompt}, timeout=120
        )

        if llm_response.status_code != 200:
            st.error(f"❌ LLM dispatcher failed: {llm_response.status_code}")
            st.error(f"Response text: {llm_response.text}")
            return {"answer": "Error: Failed to generate response", "error": True}

        # Check if LLM response is valid JSON
        try:
            llm_data = llm_response.json()
        except json.JSONDecodeError as e:
            st.error(f"❌ LLM dispatcher returned invalid JSON: {llm_response.text}")
            return {
                "answer": "Error: Invalid response from LLM dispatcher",
                "error": True,
            }

        final_answer = llm_data.get("response", "No answer generated")
        st.success("✅ Response generated successfully!")
        return {"answer": final_answer, "error": False}

    except requests.exceptions.Timeout:
        st.error("⏰ Request timed out. Please try again.")
        return {"answer": "Error: Request timed out", "error": True}
    except requests.exceptions.ConnectionError:
        st.error(
            "🔌 Cannot connect to services. Please check if all containers are running."
        )
        return {"answer": "Error: Service connection failed", "error": True}
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return {"answer": f"Error: {str(e)}", "error": True}
