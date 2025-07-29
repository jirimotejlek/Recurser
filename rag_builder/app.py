"""
RAG Builder - Production-Ready Retrieval-Augmented Generation Service
====================================================================

A containerized RAG system that processes documents, creates semantic embeddings,
and provides intelligent chunk retrieval for enhanced LLM responses.

Core Features:
- Intelligent text chunking with sentence boundary preservation
- Semantic embeddings using sentence-transformers 
- ChromaDB vector storage with session isolation
- Automatic cleanup and health monitoring
- Production-ready API with comprehensive error handling

Author: Recurser Team
Version: 2.0 (Production)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from typing import Dict, List, Any, Optional
import logging
import re
import uuid
from datetime import datetime, timedelta

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RAG-specific imports
try:
    import tiktoken
    import numpy as np
    from sentence_transformers import SentenceTransformer
    import chromadb
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    logger.error(f"Missing RAG dependencies: {e}")
    DEPENDENCIES_AVAILABLE = False

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Environment variables
CHROMA_HOST = os.getenv('CHROMA_HOST', 'localhost')
CHROMA_PORT = int(os.getenv('CHROMA_PORT', '8000'))

# RAG Configuration
CHUNK_TARGET_TOKENS = int(os.getenv('CHUNK_TARGET_TOKENS', '512'))
CHUNK_MIN_TOKENS = int(os.getenv('CHUNK_MIN_TOKENS', '100'))
CHUNK_MAX_TOKENS = int(os.getenv('CHUNK_MAX_TOKENS', '800'))
CHUNK_OVERLAP_TOKENS = int(os.getenv('CHUNK_OVERLAP_TOKENS', '50'))
EMBEDDING_MODEL_NAME = os.getenv('EMBEDDING_MODEL_NAME', 'all-MiniLM-L6-v2')
SESSION_CLEANUP_HOURS = int(os.getenv('SESSION_CLEANUP_HOURS', '24'))

# Initialize global components
embedding_model = None
tokenizer = None
chroma_client = None

if DEPENDENCIES_AVAILABLE:
    try:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-3.5/4 tokenizer
        
        # Initialize ChromaDB client
        logger.info(f"Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}")
        chroma_client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT
        )
        
        # Test connection
        chroma_client.heartbeat()
        logger.info("RAG components initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG components: {e}")
        embedding_model = None
        tokenizer = None
        chroma_client = None

# ================================
# CHUNKING AND EMBEDDING FUNCTIONS
# ================================

def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken"""
    if not tokenizer:
        # Fallback: approximate token count (1 token ≈ 4 characters)
        return len(text) // 4
    
    try:
        return len(tokenizer.encode(text))
    except Exception as e:
        logger.warning(f"Token counting failed, using approximation: {e}")
        return len(text) // 4

def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences for boundary preservation"""
    # Simple sentence splitting - could be enhanced with NLTK/spaCy
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]

def chunk_text_with_overlap(
    text: str, 
    target_tokens: int = CHUNK_TARGET_TOKENS,
    overlap_tokens: int = CHUNK_OVERLAP_TOKENS,
    min_tokens: int = CHUNK_MIN_TOKENS,
    max_tokens: int = CHUNK_MAX_TOKENS
) -> List[str]:
    """
    Chunk text into overlapping segments with sentence boundary preservation
    
    Args:
        text: Input text to chunk
        target_tokens: Target chunk size in tokens
        overlap_tokens: Overlap between chunks in tokens
        min_tokens: Minimum chunk size (skip smaller chunks)
        max_tokens: Maximum chunk size (hard limit)
    
    Returns:
        List of text chunks
    """
    if not text.strip():
        return []
    
    # Split into sentences for boundary preservation
    sentences = split_into_sentences(text)
    if not sentences:
        return []
    
    chunks = []
    current_chunk = ""
    current_tokens = 0
    
    i = 0
    while i < len(sentences):
        sentence = sentences[i]
        sentence_tokens = count_tokens(sentence)
        
        # If single sentence exceeds max_tokens, split it by words
        if sentence_tokens > max_tokens:
            words = sentence.split()
            word_chunk = ""
            
            for word in words:
                word_tokens = count_tokens(word_chunk + " " + word)
                if word_tokens > target_tokens and word_chunk:
                    if count_tokens(word_chunk) >= min_tokens:
                        chunks.append(word_chunk.strip())
                    word_chunk = word
                else:
                    word_chunk += " " + word if word_chunk else word
            
            if word_chunk and count_tokens(word_chunk) >= min_tokens:
                chunks.append(word_chunk.strip())
            
            i += 1
            continue
        
        # Check if adding this sentence would exceed target
        potential_tokens = current_tokens + sentence_tokens
        
        if potential_tokens > target_tokens and current_chunk:
            # Save current chunk if it meets minimum size
            if current_tokens >= min_tokens:
                chunks.append(current_chunk.strip())
            
            # Start new chunk with overlap
            if overlap_tokens > 0 and chunks:
                # Create overlap by taking last part of previous chunk
                overlap_text = current_chunk
                overlap_token_count = count_tokens(overlap_text)
                
                # Trim overlap to desired size
                if overlap_token_count > overlap_tokens:
                    words = overlap_text.split()
                    overlap_text = ""
                    for word in reversed(words):
                        test_text = word + " " + overlap_text if overlap_text else word
                        if count_tokens(test_text) <= overlap_tokens:
                            overlap_text = test_text
                        else:
                            break
                
                current_chunk = overlap_text + " " + sentence if overlap_text else sentence
                current_tokens = count_tokens(current_chunk)
            else:
                current_chunk = sentence
                current_tokens = sentence_tokens
        else:
            # Add sentence to current chunk
            current_chunk += " " + sentence if current_chunk else sentence
            current_tokens = potential_tokens
        
        i += 1
    
    # Add final chunk if it meets minimum size
    if current_chunk and current_tokens >= min_tokens:
        chunks.append(current_chunk.strip())
    
    logger.info(f"Chunked text into {len(chunks)} chunks (avg {sum(count_tokens(c) for c in chunks) // len(chunks) if chunks else 0} tokens)")
    return chunks

def generate_embeddings(texts: List[str]) -> Optional[List[List[float]]]:
    """
    Generate embeddings for a list of texts
    
    Args:
        texts: List of text strings to embed
    
    Returns:
        List of embedding vectors or None if failed
    """
    if not embedding_model:
        logger.error("Embedding model not available")
        return None
    
    if not texts:
        return []
    
    try:
        logger.info(f"Generating embeddings for {len(texts)} texts")
        embeddings = embedding_model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        return None

def process_document_for_rag(
    content: str,
    session_id: str,
    source_url: str,
    document_title: str = ""
) -> Dict[str, Any]:
    """
    Process a single document: chunk and embed
    
    Args:
        content: Document text content
        session_id: Session identifier
        source_url: Source URL of the document
        document_title: Optional document title
    
    Returns:
        Processed chunks with embeddings and metadata
    """
    if not content.strip():
        return {"error": "Empty content provided", "chunks": []}
    
    try:
        # Step 1: Chunk the content
        chunks = chunk_text_with_overlap(content)
        
        if not chunks:
            return {"error": "No valid chunks created", "chunks": []}
        
        # Step 2: Generate embeddings
        embeddings = generate_embeddings(chunks)
        
        if embeddings is None:
            return {"error": "Failed to generate embeddings", "chunks": []}
        
        # Step 3: Create chunk objects with metadata
        processed_chunks = []
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{source_url}_{i}_{uuid.uuid4().hex[:8]}"
            
            chunk_obj = {
                "chunk_id": chunk_id,
                "content": chunk_text,
                "embedding": embedding,
                "metadata": {
                    "session_id": session_id,
                    "source_url": source_url,
                    "chunk_index": i,
                    "chunk_id": chunk_id,
                    "document_title": document_title,
                    "token_count": count_tokens(chunk_text),
                    "created_at": datetime.utcnow().isoformat()
                }
            }
            processed_chunks.append(chunk_obj)
        
        result = {
            "chunks": processed_chunks,
            "summary": {
                "total_chunks": len(processed_chunks),
                "total_tokens": sum(count_tokens(chunk) for chunk in chunks),
                "average_chunk_size": sum(count_tokens(chunk) for chunk in chunks) // len(chunks),
                "embedding_dimensions": len(embeddings[0]) if embeddings else 0
            }
        }
        
        logger.info(f"Successfully processed document: {len(chunks)} chunks, {result['summary']['total_tokens']} tokens")
        return result
        
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        return {"error": f"Document processing failed: {str(e)}", "chunks": []}

def generate_query_embedding(query: str) -> Optional[List[float]]:
    """
    Generate embedding for a search query
    
    Args:
        query: Search query text
    
    Returns:
        Query embedding vector or None if failed
    """
    if not embedding_model:
        logger.error("Embedding model not available")
        return None
    
    if not query.strip():
        logger.error("Empty query provided")
        return None
    
    try:
        embedding = embedding_model.encode([query.strip()], convert_to_numpy=True)
        return embedding[0].tolist()
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        return None

# ================================
# CHROMADB INTEGRATION FUNCTIONS
# ================================

def get_collection_name(session_id: str) -> str:
    """Generate collection name for session"""
    # Sanitize session_id for ChromaDB collection naming
    sanitized_id = re.sub(r'[^a-zA-Z0-9_-]', '_', session_id)
    return f"session_{sanitized_id}"

def create_or_get_collection(session_id: str):
    """Create or get existing collection for session"""
    if not chroma_client:
        raise Exception("ChromaDB client not available")
    
    collection_name = get_collection_name(session_id)
    
    try:
        # Try to get existing collection
        collection = chroma_client.get_collection(name=collection_name)
        logger.info(f"Retrieved existing collection: {collection_name}")
        return collection
    except Exception:
        # Collection doesn't exist, create it
        try:
            collection = chroma_client.create_collection(
                name=collection_name,
                metadata={
                    "session_id": session_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "cleanup_after": (datetime.utcnow() + timedelta(hours=SESSION_CLEANUP_HOURS)).isoformat()
                }
            )
            logger.info(f"Created new collection: {collection_name}")
            return collection
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise

def store_chunks_in_chromadb(chunks: List[Dict[str, Any]], session_id: str) -> Dict[str, Any]:
    """
    Store processed chunks in ChromaDB
    
    Args:
        chunks: List of chunk objects with embeddings and metadata
        session_id: Session identifier
    
    Returns:
        Storage result summary
    """
    if not chroma_client:
        return {"error": "ChromaDB client not available"}
    
    if not chunks:
        return {"error": "No chunks to store"}
    
    try:
        # Get or create collection
        collection = create_or_get_collection(session_id)
        
        # Prepare data for ChromaDB
        ids = [chunk["chunk_id"] for chunk in chunks]
        documents = [chunk["content"] for chunk in chunks]
        embeddings = [chunk["embedding"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        # Store in ChromaDB
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        logger.info(f"Stored {len(chunks)} chunks in collection {get_collection_name(session_id)}")
        
        return {
            "success": True,
            "chunks_stored": len(chunks),
            "collection_name": get_collection_name(session_id),
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Failed to store chunks in ChromaDB: {e}")
        return {"error": f"Failed to store chunks: {str(e)}"}

def retrieve_relevant_chunks(
    query: str,
    session_id: str,
    max_results: int = 5,
    similarity_threshold: float = 0.0
) -> Dict[str, Any]:
    """
    Retrieve relevant chunks for a query from ChromaDB
    
    Args:
        query: Search query
        session_id: Session identifier
        max_results: Maximum number of chunks to return
        similarity_threshold: Minimum similarity score (0-1)
    
    Returns:
        Retrieved chunks with metadata and scores
    """
    if not chroma_client:
        return {"error": "ChromaDB client not available"}
    
    if not query.strip():
        return {"error": "Empty query provided"}
    
    try:
        # Generate query embedding
        query_embedding = generate_query_embedding(query)
        if query_embedding is None:
            return {"error": "Failed to generate query embedding"}
        
        # Get collection
        collection_name = get_collection_name(session_id)
        try:
            collection = chroma_client.get_collection(name=collection_name)
        except Exception:
            logger.warning(f"Collection {collection_name} not found")
            return {
                "query": query,
                "chunks": [],
                "total_chunks_searched": 0,
                "message": "No documents found for this session"
            }
        
        # Perform similarity search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=max_results,
            include=["documents", "metadatas", "distances"]
        )
        
        if not results["documents"] or not results["documents"][0]:
            return {
                "query": query,
                "chunks": [],
                "total_chunks_searched": 0,
                "message": "No relevant chunks found"
            }
        
        # Process results
        retrieved_chunks = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )):
            # Convert distance to similarity score (ChromaDB uses cosine distance)
            similarity_score = 1.0 - distance
            
            # Apply similarity threshold
            if similarity_score < similarity_threshold:
                continue
            
            chunk_result = {
                "content": doc,
                "similarity_score": round(similarity_score, 4),
                "metadata": metadata,
                "rank": i + 1
            }
            retrieved_chunks.append(chunk_result)
        
        logger.info(f"Retrieved {len(retrieved_chunks)} relevant chunks for query in session {session_id}")
        
        return {
            "query": query,
            "chunks": retrieved_chunks,
            "total_chunks_searched": collection.count(),
            "retrieval_summary": {
                "results_returned": len(retrieved_chunks),
                "similarity_threshold": similarity_threshold,
                "session_id": session_id
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve chunks: {e}")
        return {"error": f"Retrieval failed: {str(e)}"}

def cleanup_old_collections() -> Dict[str, Any]:
    """
    Clean up collections older than SESSION_CLEANUP_HOURS
    
    Returns:
        Cleanup summary
    """
    if not chroma_client:
        return {"error": "ChromaDB client not available"}
    
    try:
        all_collections = chroma_client.list_collections()
        cleanup_summary = {
            "collections_checked": 0,
            "collections_deleted": 0,
            "deleted_collections": [],
            "errors": []
        }
        
        cutoff_time = datetime.utcnow() - timedelta(hours=SESSION_CLEANUP_HOURS)
        
        for collection_info in all_collections:
            cleanup_summary["collections_checked"] += 1
            collection_name = collection_info.name
            
            # Only process session collections
            if not collection_name.startswith("session_"):
                continue
            
            try:
                collection = chroma_client.get_collection(name=collection_name)
                metadata = collection.metadata
                
                if metadata and "created_at" in metadata:
                    created_at = datetime.fromisoformat(metadata["created_at"].replace('Z', '+00:00'))
                    
                    if created_at < cutoff_time:
                        chroma_client.delete_collection(name=collection_name)
                        cleanup_summary["collections_deleted"] += 1
                        cleanup_summary["deleted_collections"].append({
                            "name": collection_name,
                            "created_at": metadata["created_at"],
                            "session_id": metadata.get("session_id", "unknown")
                        })
                        logger.info(f"Deleted old collection: {collection_name}")
                
            except Exception as e:
                error_msg = f"Error processing collection {collection_name}: {str(e)}"
                cleanup_summary["errors"].append(error_msg)
                logger.error(error_msg)
        
        logger.info(f"Cleanup complete: {cleanup_summary['collections_deleted']} collections deleted")
        return cleanup_summary
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {"error": f"Cleanup failed: {str(e)}"}

def get_session_info(session_id: str) -> Dict[str, Any]:
    """Get information about a session's collection"""
    if not chroma_client:
        return {"error": "ChromaDB client not available"}
    
    collection_name = get_collection_name(session_id)
    
    try:
        collection = chroma_client.get_collection(name=collection_name)
        
        return {
            "session_id": session_id,
            "collection_name": collection_name,
            "chunk_count": collection.count(),
            "metadata": collection.metadata,
            "exists": True
        }
    except Exception:
        return {
            "session_id": session_id,
            "collection_name": collection_name,
            "exists": False,
            "message": "Collection not found"
        }

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "services": {
            "api": "up",
            "chromadb": "unknown",
            "embedding_model": "unknown",
            "tokenizer": "unknown"
        },
        "rag_config": {
            "chunk_target_tokens": CHUNK_TARGET_TOKENS,
            "chunk_overlap_tokens": CHUNK_OVERLAP_TOKENS,
            "embedding_model": EMBEDDING_MODEL_NAME,
            "dependencies_available": DEPENDENCIES_AVAILABLE
        }
    }
    
    # Check ChromaDB
    try:
        if chroma_client:
            chroma_client.heartbeat()
            health_status["services"]["chromadb"] = "up"
        else:
            health_status["services"]["chromadb"] = "down"
    except Exception as e:
        logger.warning(f"ChromaDB health check failed: {e}")
        health_status["services"]["chromadb"] = "down"
    
    # Check RAG Components
    health_status["services"]["embedding_model"] = "up" if embedding_model is not None else "down"
    health_status["services"]["tokenizer"] = "up" if tokenizer is not None else "down"
    
    # Overall status
    core_services = ["chromadb", "embedding_model", "tokenizer"]
    if any(health_status["services"][service] == "down" for service in core_services):
        health_status["status"] = "degraded"
    elif not DEPENDENCIES_AVAILABLE:
        health_status["status"] = "degraded"
    
    return jsonify(health_status)


@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    return jsonify({
        'name': 'RAG Builder API',
        'version': '2.0',
        'description': 'Retrieval-Augmented Generation with chunking and embeddings',
        'capabilities': {
            'chunking': f'{CHUNK_TARGET_TOKENS} token chunks with {CHUNK_OVERLAP_TOKENS} token overlap',
            'embeddings': f'{EMBEDDING_MODEL_NAME} model',
            'storage': 'ChromaDB vector database with session isolation',
            'cleanup': f'Auto-cleanup sessions after {SESSION_CLEANUP_HOURS} hours'
        },
        'endpoints': {
            '/health': 'GET - Health check with RAG component status',
            '/embed': 'POST - Process and store document chunks',
            '/retrieve': 'POST - Retrieve relevant chunks for query',
            '/collections': 'GET - List all session collections',
            '/collections/<session_id>': 'GET/DELETE - Manage specific session collection',
            '/cleanup': 'POST - Manually trigger cleanup of old collections'
        },
        'rag_pipeline': {
            'embed_workflow': '1. Chunk document → 2. Generate embeddings → 3. Store in ChromaDB',
            'retrieve_workflow': '1. Embed query → 2. Similarity search → 3. Return relevant chunks'
        },
        'status': {
            'chunking': 'PRODUCTION READY',
            'embeddings': 'PRODUCTION READY', 
            'chromadb_integration': 'PRODUCTION READY',
            'api_endpoints': 'PRODUCTION READY',
            'auto_cleanup': 'PRODUCTION READY'
        }
    })


# ================================
# MAIN RAG API ENDPOINTS
# ================================

@app.route('/embed', methods=['POST'])
def embed_document():
    """
    Process and store document chunks in ChromaDB
    
    Expected JSON payload:
    {
        "content": "Document text content...",
        "session_id": "unique_session_id", 
        "source_url": "https://example.com/article",
        "title": "Optional document title"
    }
    """
    if not DEPENDENCIES_AVAILABLE:
        return jsonify({'error': 'RAG dependencies not available'}), 500
    
    if not chroma_client:
        return jsonify({'error': 'ChromaDB not available'}), 500
    
    # Validate request
    data = request.json
    if not data:
        return jsonify({'error': 'JSON payload required'}), 400
    
    required_fields = ['content', 'session_id', 'source_url']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    content = data['content']
    session_id = data['session_id']
    source_url = data['source_url']
    title = data.get('title', '')
    
    # Validate inputs
    if not content.strip():
        return jsonify({'error': 'Content cannot be empty'}), 400
    
    if not session_id.strip():
        return jsonify({'error': 'Session ID cannot be empty'}), 400
    
    logger.info(f"Processing document for session {session_id}: {len(content)} chars")
    
    try:
        # Step 1: Process document (chunk + embed)
        processing_result = process_document_for_rag(
            content=content,
            session_id=session_id,
            source_url=source_url,
            document_title=title
        )
        
        if 'error' in processing_result:
            return jsonify(processing_result), 500
        
        # Step 2: Store in ChromaDB
        storage_result = store_chunks_in_chromadb(
            chunks=processing_result['chunks'],
            session_id=session_id
        )
        
        if 'error' in storage_result:
            return jsonify(storage_result), 500
        
        # Step 3: Return success response
        response = {
            'success': True,
            'session_id': session_id,
            'processing_summary': processing_result['summary'],
            'storage_summary': storage_result,
            'message': f"Successfully processed and stored {len(processing_result['chunks'])} chunks"
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in embed endpoint: {e}")
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/retrieve', methods=['POST'])
def retrieve_chunks():
    """
    Retrieve relevant chunks for a query
    
    Expected JSON payload:
    {
        "query": "optimized search query",
        "session_id": "unique_session_id",
        "max_results": 5,  // optional, default 5
        "similarity_threshold": 0.7  // optional, default 0.0
    }
    """
    if not DEPENDENCIES_AVAILABLE:
        return jsonify({'error': 'RAG dependencies not available'}), 500
    
    if not chroma_client:
        return jsonify({'error': 'ChromaDB not available'}), 500
    
    # Validate request
    data = request.json
    if not data:
        return jsonify({'error': 'JSON payload required'}), 400
    
    required_fields = ['query', 'session_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    query = data['query']
    session_id = data['session_id']
    max_results = data.get('max_results', 5)
    similarity_threshold = data.get('similarity_threshold', 0.0)
    
    # Validate inputs
    if not query.strip():
        return jsonify({'error': 'Query cannot be empty'}), 400
    
    if not session_id.strip():
        return jsonify({'error': 'Session ID cannot be empty'}), 400
    
    # Validate parameters
    try:
        max_results = int(max_results)
        if max_results < 1 or max_results > 20:
            return jsonify({'error': 'max_results must be between 1 and 20'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'max_results must be a valid integer'}), 400
    
    try:
        similarity_threshold = float(similarity_threshold)
        if similarity_threshold < 0.0 or similarity_threshold > 1.0:
            return jsonify({'error': 'similarity_threshold must be between 0.0 and 1.0'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'similarity_threshold must be a valid number'}), 400
    
    logger.info(f"Retrieving chunks for query in session {session_id}: '{query[:100]}...'")
    
    try:
        # Retrieve relevant chunks
        result = retrieve_relevant_chunks(
            query=query,
            session_id=session_id,
            max_results=max_results,
            similarity_threshold=similarity_threshold
        )
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in retrieve endpoint: {e}")
        return jsonify({'error': f'Retrieval failed: {str(e)}'}), 500

@app.route('/collections', methods=['GET'])
def list_collections():
    """List all session collections with metadata"""
    if not chroma_client:
        return jsonify({'error': 'ChromaDB not available'}), 500
    
    try:
        all_collections = chroma_client.list_collections()
        
        session_collections = []
        for collection_info in all_collections:
            if collection_info.name.startswith("session_"):
                try:
                    collection = chroma_client.get_collection(name=collection_info.name)
                    session_collections.append({
                        "name": collection_info.name,
                        "chunk_count": collection.count(),
                        "metadata": collection.metadata
                    })
                except Exception as e:
                    logger.warning(f"Could not get details for collection {collection_info.name}: {e}")
        
        return jsonify({
            "collections": session_collections,
            "total_collections": len(session_collections)
        })
        
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        return jsonify({'error': f'Failed to list collections: {str(e)}'}), 500

@app.route('/collections/<session_id>', methods=['GET'])
def get_collection_info(session_id: str):
    """Get information about a specific session's collection"""
    if not chroma_client:
        return jsonify({'error': 'ChromaDB not available'}), 500
    
    try:
        info = get_session_info(session_id)
        return jsonify(info)
    except Exception as e:
        logger.error(f"Error getting collection info: {e}")
        return jsonify({'error': f'Failed to get collection info: {str(e)}'}), 500

@app.route('/collections/<session_id>', methods=['DELETE'])
def delete_collection(session_id: str):
    """Delete a specific session's collection"""
    if not chroma_client:
        return jsonify({'error': 'ChromaDB not available'}), 500
    
    try:
        collection_name = get_collection_name(session_id)
        chroma_client.delete_collection(name=collection_name)
        
        logger.info(f"Deleted collection: {collection_name}")
        return jsonify({
            "success": True,
            "message": f"Collection for session {session_id} deleted successfully",
            "collection_name": collection_name
        })
        
    except Exception as e:
        logger.error(f"Error deleting collection: {e}")
        return jsonify({'error': f'Failed to delete collection: {str(e)}'}), 500

@app.route('/cleanup', methods=['POST'])
def manual_cleanup():
    """Manually trigger cleanup of old collections"""
    if not chroma_client:
        return jsonify({'error': 'ChromaDB not available'}), 500
    
    try:
        result = cleanup_old_collections()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in manual cleanup: {e}")
        return jsonify({'error': f'Cleanup failed: {str(e)}'}), 500

# ================================
# STARTUP ROUTINES
# ================================

def startup_cleanup():
    """Perform cleanup on application startup"""
    if chroma_client:
        try:
            logger.info("Performing startup cleanup of old collections...")
            result = cleanup_old_collections()
            if 'error' not in result:
                logger.info(f"Startup cleanup complete: {result.get('collections_deleted', 0)} collections removed")
            else:
                logger.warning(f"Startup cleanup failed: {result['error']}")
        except Exception as e:
            logger.warning(f"Startup cleanup error: {e}")
    else:
        logger.warning("ChromaDB not available, skipping startup cleanup")

# Perform startup cleanup when module is loaded
startup_cleanup()

if __name__ == '__main__':
    logger.info("Starting RAG Builder API server...")
    logger.info(f"Configuration: {CHUNK_TARGET_TOKENS} token chunks, {EMBEDDING_MODEL_NAME} embeddings")
    logger.info(f"ChromaDB: {CHROMA_HOST}:{CHROMA_PORT}")
    logger.info(f"Session cleanup: {SESSION_CLEANUP_HOURS} hours")
    
    # Use debug mode from environment variable, default to False for production
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    app.run(host='0.0.0.0', port=5300, debug=debug_mode)