import json
import os
import uuid
from typing import Dict, List, Optional

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


def scrape_content_from_urls(urls: List[str]) -> Dict[str, str]:
    """
    Scrape content from URLs using the scraper service.
    Returns a dict mapping URL to scraped content.
    """
    scraped_content = {}
    
    for url in urls:
        try:
            st.info(f"📄 Scraping content from: {url[:50]}...")
            response = requests.post(
                f"http://{SCRAPER}:{SCRAPER_PORT}/scrape",
                json={"url": url},
                timeout=30,
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'content' in data and data['content'].strip():
                    scraped_content[url] = data['content']
                    st.success(f"✅ Successfully scraped: {url[:50]}...")
                else:
                    st.warning(f"⚠️ No content found for: {url[:50]}...")
            else:
                st.warning(f"⚠️ Failed to scrape: {url[:50]}... (Status: {response.status_code})")
                
        except Exception as e:
            st.warning(f"⚠️ Error scraping {url[:50]}...: {str(e)}")
            continue
    
    return scraped_content


def store_documents_in_rag(scraped_content: Dict[str, str], session_id: str) -> bool:
    """
    Store scraped documents in ChromaDB via RAG builder service.
    Returns True if successful, False otherwise.
    """
    success_count = 0
    total_count = len(scraped_content)
    
    for url, content in scraped_content.items():
        try:
            # Prepare document for RAG storage
            document_data = {
                "content": content,
                "session_id": session_id,
                "source_url": url,
                "title": f"Scraped content from {url}"
            }
            
            st.info(f"💾 Storing document in RAG: {url[:50]}...")
            response = requests.post(
                f"http://{RAG_BUILDER}:{RAG_BUILDER_PORT}/embed",
                json=document_data,
                timeout=60,
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    chunks_stored = data.get('processing_summary', {}).get('total_chunks', 0)
                    st.success(f"✅ Stored {chunks_stored} chunks from: {url[:50]}...")
                    success_count += 1
                else:
                    st.warning(f"⚠️ Failed to store: {url[:50]}...")
            else:
                st.warning(f"⚠️ RAG storage failed for: {url[:50]}... (Status: {response.status_code})")
                
        except Exception as e:
            st.warning(f"⚠️ Error storing {url[:50]}...: {str(e)}")
            continue
    
    st.info(f"📊 RAG Storage Summary: {success_count}/{total_count} documents stored successfully")
    return success_count > 0


def retrieve_rag_chunks(query: str, session_id: str, max_results: int = 5) -> List[Dict]:
    """
    Retrieve relevant chunks from ChromaDB via RAG builder service.
    Returns a list of relevant chunks with metadata.
    """
    try:
        st.info("🔍 Retrieving relevant chunks from RAG...")
        
        retrieval_data = {
            "query": query,
            "session_id": session_id,
            "max_results": max_results,
            "similarity_threshold": 0.1  # Adjust threshold as needed, higher values = more relevant chunks
        }
        
        response = requests.post(
            f"http://{RAG_BUILDER}:{RAG_BUILDER_PORT}/retrieve",
            json=retrieval_data,
            timeout=30,
        )
        
        if response.status_code == 200:
            data = response.json()
            chunks = data.get('chunks', [])
            
            if chunks:
                st.success(f"✅ Retrieved {len(chunks)} relevant chunks from RAG")
                return chunks
            else:
                st.info("ℹ️ No relevant chunks found in RAG database")
                return []
        else:
            st.warning(f"⚠️ RAG retrieval failed (Status: {response.status_code})")
            return []
            
    except Exception as e:
        st.warning(f"⚠️ Error retrieving from RAG: {str(e)}")
        return []


def run_query_pipeline(user_query: str) -> dict:
    """
    Run the complete RAG pipeline with proper error handling and status updates.
    """
    # Generate unique session ID for this query
    session_id = f"query_{uuid.uuid4().hex[:8]}"
    
    try:
        # Step 1: Call optimiser (using the query endpoint)
        st.info("🔄 Optimizing your query...")
        response = requests.post(
            f"http://{OPTIMIZER}:{OPTIMIZER_PORT}/query",
            json={"query": user_query},
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
            f"http://{SEARCH_ENGINE}:{SEARCH_ENGINE_PORT}/query",
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
        st.info(f"🧠 Search results: {search_results}")

        # Step 3: RAG Processing - Scrape, Store, and Retrieve
        st.info("🧠 Processing documents with RAG...")
        
        # Extract URLs from search results for scraping
        urls_to_scrape = []
        for result in search_results[:3]:  # Limit to top 3 for performance
            if isinstance(result, dict) and 'href' in result:
                url = result['href']
                if url and url.startswith('http'):
                    urls_to_scrape.append(url)

        #st.info(f"🧠 URLs to scrape: {urls_to_scrape}")

        rag_chunks = []
        if urls_to_scrape:
            # Scrape content from URLs
            scraped_content = scrape_content_from_urls(urls_to_scrape)

            if scraped_content:
                # Store documents in ChromaDB
                if store_documents_in_rag(scraped_content, session_id):
                    # Retrieve relevant chunks using the optimized query
                    rag_chunks = retrieve_rag_chunks(optimal_query, session_id, max_results=5)

        #st.info(f"🧠 RAG chunks: {rag_chunks}")
        # Step 4: Prepare enhanced context from both search results and RAG chunks
        st.info("🤖 Generating enhanced response with LLM...")


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

        # Prepare context from RAG chunks
        rag_context = ""
        if rag_chunks:
            rag_context = "\n\nRelevant document chunks from web scraping:\n"
            for i, chunk in enumerate(rag_chunks, 1):
                content = chunk.get('content', 'No content')
                similarity = chunk.get('similarity_score', 0)
                source_url = chunk.get('metadata', {}).get('source_url', 'Unknown source')
                rag_context += (
                    f"{i}. (Similarity: {similarity:.3f}) Source: {source_url}\n"
                    f"   Content: {content[:400]}...\n\n"
                )

        # Step 5: Send query + enhanced context to LLM dispatcher
        llm_prompt = f"""Based on the following search results and relevant document content, provide a comprehensive answer to the user's question.

User Question: {user_query}

Search Results:
{search_context}{rag_context}

Please provide a detailed, accurate answer based on the information above. If the provided information doesn't contain enough details to answer the question completely, please say so."""
        st.info(f"🧠 LLM prompt: {llm_prompt}")
        llm_response = requests.post(
            f"http://{LLM_DISPATCHER}:{LLM_DISPATCHER_PORT}/query", json={"prompt": llm_prompt}, timeout=120
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
        
        # Add processing summary
        processing_summary = {
            "search_results": len(search_results),
            "urls_scraped": len(urls_to_scrape) if urls_to_scrape else 0,
            "rag_chunks_retrieved": len(rag_chunks),
            "session_id": session_id
        }
        
        st.success("✅ Enhanced response generated successfully!")
        st.info(f"📊 Processing Summary: {processing_summary['search_results']} search results, "
                f"{processing_summary['urls_scraped']} pages scraped, "
                f"{processing_summary['rag_chunks_retrieved']} RAG chunks retrieved")
        
        return {
            "answer": final_answer, 
            "error": False,
            "processing_summary": processing_summary
        }

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
