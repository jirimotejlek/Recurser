# RAG Builder

The RAG Builder is a production-ready Retrieval-Augmented Generation system that forms the knowledge processing core of the Recurser application. It intelligently processes web content scraped from search results, creates semantic embeddings, and provides contextually relevant chunks to enhance LLM responses.

## System Overview

The RAG Builder operates as part of a larger containerised ecosystem:

```
User Query → Optimiser → Search Engine → Crawler → RAG Builder → LLM Dispatcher → Response
                                              ↓
                                        ChromaDB Storage
```

## Core Features

✅ **Intelligent Text Processing** - Advanced chunking with sentence boundary preservation  
✅ **Semantic Embeddings** - Local `all-MiniLM-L6-v2` model for contextual understanding  
✅ **Vector Database** - ChromaDB integration with session-based isolation  
✅ **Auto-cleanup** - Automatic removal of old sessions (configurable)  
✅ **Production Ready** - Comprehensive API with error handling and monitoring  
✅ **Container Native** - Designed for Docker deployment with health checks  

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start ChromaDB (Required)

Make sure ChromaDB is running on `localhost:8000` (configured in docker-compose).

### 3. Run RAG Builder

```bash
python app.py
```

The API will be available at `http://localhost:5300`

### 4. Test the API

```bash
python test_api.py
```

## API Endpoints

### Core RAG Operations

#### Store Document Chunks
```http
POST /embed
Content-Type: application/json

{
  "content": "Your document text...",
  "session_id": "unique_session_id", 
  "source_url": "https://example.com/source",
  "title": "Optional document title"
}
```

#### Retrieve Relevant Chunks
```http
POST /retrieve
Content-Type: application/json

{
  "query": "optimized search query",
  "session_id": "unique_session_id",
  "max_results": 5,
  "similarity_threshold": 0.0
}
```

### Collection Management

#### List All Collections
```http
GET /collections
```

#### Get Session Info
```http
GET /collections/{session_id}
```

#### Delete Session
```http
DELETE /collections/{session_id}
```

#### Manual Cleanup
```http
POST /cleanup
```

### Monitoring

#### Health Check
```http
GET /health
```

Returns status of all components including ChromaDB, embedding model, and tokenizer.

## Configuration

Environment variables:

```bash
# Chunking Configuration
CHUNK_TARGET_TOKENS=512      # Target chunk size
CHUNK_MIN_TOKENS=100         # Minimum chunk size
CHUNK_MAX_TOKENS=800         # Maximum chunk size  
CHUNK_OVERLAP_TOKENS=50      # Overlap between chunks

# Embedding Configuration
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2

# ChromaDB Configuration  
CHROMA_HOST=chromadb
CHROMA_PORT=8000

# Cleanup Configuration
SESSION_CLEANUP_HOURS=24     # Auto-delete after 24 hours
```

## Module Architecture & Workflow

### 1. **Frontend/UI Module** (External)
**Purpose**: Orchestrates the entire RAG pipeline  
**Integration**: Sends scraped content and optimised queries to RAG Builder  
**Data Flow**: 
- Receives scraped content from crawler
- Sends documents to `/embed` endpoint
- Sends optimised queries to `/retrieve` endpoint  
- Forwards retrieved chunks to LLM Dispatcher

### 2. **Document Processing Pipeline** (Internal)
**Components**: 
- **Text Chunker**: Intelligently splits documents into 512-token segments
- **Sentence Preprocessor**: Ensures chunks don't break mid-sentence
- **Overlap Manager**: Maintains 50-token overlap for context preservation

**How It Works**:
```python
Raw Text → Sentence Detection → Smart Chunking → Token Validation → Clean Chunks
```
- Respects paragraph and sentence boundaries
- Handles edge cases (very long sentences, short content)
- Validates minimum chunk size (100 tokens) and maximum (800 tokens)

### 3. **Embedding Generation System** (Internal)
**Model**: `all-MiniLM-L6-v2` (384-dimensional vectors)  
**Process**:
- Loads model once at startup (90MB download)
- Batch processes chunks for efficiency
- Generates semantic embeddings for both storage and retrieval
- Uses CPU inference (GPU support available)

**How It Works**:
```python
Text Chunks → SentenceTransformer → 384D Vectors → Normalised Embeddings
```

### 4. **ChromaDB Vector Storage** (External Service)
**Purpose**: Persistent vector storage with metadata  
**Collections**: Session-based isolation (`session_{session_id}`)  
**Storage Schema**:
```json
{
  "chunk_id": "unique_identifier",
  "content": "actual_text_chunk", 
  "embedding": [0.1, -0.3, 0.7, ...],
  "metadata": {
    "session_id": "search_session_123",
    "source_url": "https://example.com",
    "chunk_index": 2,
    "token_count": 456
  }
}
```

### 5. **Semantic Retrieval Engine** (Internal)
**Method**: Cosine similarity search in vector space  
**Process**:
- Generates embedding for optimised query
- Searches ChromaDB collection for similar vectors
- Ranks results by similarity score
- Applies configurable similarity threshold
- Returns top-k most relevant chunks

**How It Works**:
```python
Query → Query Embedding → Vector Search → Similarity Ranking → Filtered Results
```

### 6. **Session Management System** (Internal)
**Features**:
- Automatic collection creation per search session
- Metadata tracking (creation time, session info)
- Auto-cleanup of collections older than 24 hours
- Manual cleanup endpoints for administration

## Complete System Workflow

### Document Storage Flow
```
1. Crawler scrapes web content
2. Frontend sends content to RAG Builder /embed
3. RAG Builder chunks text (512 tokens, 50 overlap)
4. Generates embeddings using all-MiniLM-L6-v2  
5. Stores vectors + metadata in ChromaDB
6. Returns processing summary to frontend
```

### Query Retrieval Flow  
```
1. User submits query to frontend
2. Optimiser enhances query
3. Frontend sends optimised query to RAG Builder /retrieve
4. RAG Builder generates query embedding
5. Performs similarity search in ChromaDB
6. Returns top relevant chunks to frontend
7. Frontend forwards query + chunks to LLM Dispatcher
8. LLM generates final response with context
```

## Development

### Run Tests
```bash
python test_api.py
```

### Debug Mode
The application runs in debug mode by default. Check logs for detailed processing information.

### Session Management
- Collections are named `session_{session_id}`
- Automatic cleanup removes collections older than 24 hours
- Manual cleanup available via `/cleanup` endpoint

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical documentation.

## Troubleshooting

### ChromaDB Connection Issues
- Ensure ChromaDB is running on correct host/port
- Check Docker container status
- Verify network connectivity

### Embedding Model Issues  
- First run downloads model (~90MB)
- Ensure sufficient memory for model loading
- Check dependencies are installed correctly

### Performance Optimization
- Increase `CHUNK_OVERLAP_TOKENS` for better context preservation
- Decrease `CHUNK_TARGET_TOKENS` for more precise retrieval
- Adjust `similarity_threshold` in queries for quality control

---

## Tuning & Optimization Parameters

The RAG Builder contains several configurable parameters that significantly impact performance, accuracy, and resource usage. These "arbitrary" decisions should be optimized based on your specific use case, content types, and performance requirements.

### 🎯 **Critical Parameters for Tuning**

#### **Text Chunking Configuration**
```bash
CHUNK_TARGET_TOKENS=512      # Target chunk size
CHUNK_MIN_TOKENS=100         # Minimum viable chunk size  
CHUNK_MAX_TOKENS=800         # Hard limit for chunk size
CHUNK_OVERLAP_TOKENS=50      # Overlap between adjacent chunks
```

**Impact & Tuning Guidance**:
- **Larger chunks (700+ tokens)**: Better context preservation, less precise retrieval
- **Smaller chunks (300-400 tokens)**: More precise retrieval, may lose context  
- **More overlap (80-100 tokens)**: Better context flow, increased storage cost
- **Less overlap (20-30 tokens)**: Reduced storage, potential context gaps

**Recommended Testing**:
- Technical documents: Try 400-600 tokens with 80 token overlap
- News articles: Try 300-500 tokens with 40 token overlap  
- Long-form content: Try 600-800 tokens with 100 token overlap

#### **Similarity Search Thresholds**
```python
# In API calls to /retrieve
similarity_threshold = 0.0-1.0    # Default: 0.0 (no filtering)
max_results = 1-20               # Default: 5
```

**Impact & Tuning Guidance**:
- **Higher threshold (0.3-0.5)**: Only very relevant chunks, may miss useful context
- **Lower threshold (0.05-0.15)**: More chunks but some may be tangentially related
- **More results (8-15)**: Better context for LLM, higher token usage
- **Fewer results (2-5)**: Focused context, may miss important information

**Recommended Testing**:
- Start with threshold 0.1 and max_results 5
- Monitor retrieval quality and adjust based on your content domain
- A/B test different thresholds with your typical queries

#### **Session & Cleanup Management**
```bash
SESSION_CLEANUP_HOURS=24     # Auto-delete collections after X hours
```

**Impact & Tuning Guidance**:
- **Longer retention (48-72 hours)**: Better for iterative searches, higher storage cost
- **Shorter retention (6-12 hours)**: Lower storage cost, users may lose context
- **Consider usage patterns**: Business hours vs 24/7 applications

#### **Embedding Model Selection**
```bash
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2    # Current model
```

**Alternative Models to Test**:
- `all-mpnet-base-v2`: Higher quality, slower inference, 768 dimensions
- `all-MiniLM-L12-v2`: Balanced quality/speed, 384 dimensions  
- `paraphrase-multilingual-MiniLM-L12-v2`: For multilingual content

**Trade-offs**:
- **Larger models**: Better semantic understanding, higher memory usage, slower inference
- **Smaller models**: Faster inference, lower memory, may miss nuanced similarities

### 🔬 **Advanced Tuning Parameters**

#### **Performance vs Quality Trade-offs**
```python
# Internal configuration (would need code changes)
BATCH_SIZE = 32              # Embedding generation batch size
MAX_CONCURRENT_REQUESTS = 4  # Parallel processing limit
CACHE_TTL_SECONDS = 3600     # Response caching duration
```

#### **Vector Search Optimization**
```python
# ChromaDB configuration
n_results = 20               # Retrieve more, then re-rank
include = ["documents", "metadatas", "distances"]  # What to return
```

### 🧪 **Experimental Parameters Worth Testing**

#### **Context Window Strategies**
- **Variable chunk sizes**: Adjust based on content type detection
- **Adaptive overlap**: More overlap for technical content, less for narrative
- **Hierarchical chunking**: Large chunks for context + small chunks for precision

#### **Retrieval Enhancement**
- **Hybrid search**: Combine semantic similarity with keyword matching
- **Query expansion**: Automatically expand queries with synonyms/related terms
- **Re-ranking**: Use additional scoring based on metadata (source quality, recency)

#### **Multi-stage Retrieval**
- **First pass**: Broad similarity search (threshold 0.05, n_results=20)
- **Second pass**: Re-rank with business logic (domain trust, content type)
- **Final selection**: Return top 5 after re-ranking

### 📊 **Monitoring Metrics for Optimization**

Track these metrics to guide parameter tuning:

#### **Chunking Quality**
- Average chunk size distribution
- Percentage of chunks below minimum threshold
- Sentence boundary preservation rate

#### **Retrieval Performance**  
- Average similarity scores of returned chunks
- Percentage of queries returning 0 results
- User feedback on result relevance (if available)

#### **System Performance**
- Embedding generation latency
- ChromaDB query response times  
- Memory usage patterns
- Storage growth rates

### 🎯 **Quick Optimization Checklist**

1. **Baseline Test**: Record current performance with default parameters
2. **Content Analysis**: Analyze your typical document lengths and query types
3. **Chunk Size Tuning**: Test 400, 512, 600 token chunks with your content
4. **Threshold Testing**: Try similarity thresholds of 0.05, 0.1, 0.2, 0.3
5. **Overlap Optimization**: Test 30, 50, 80 token overlaps
6. **Model Comparison**: Benchmark different embedding models with sample queries
7. **Load Testing**: Verify performance under realistic usage patterns
8. **Iterative Refinement**: Adjust based on user feedback and usage analytics

### ⚡ **Performance vs Accuracy Matrix**

| Configuration | Speed | Accuracy | Storage | Use Case |
|---------------|-------|----------|---------|----------|
| 300 tokens, 30 overlap, threshold 0.2 | ⚡⚡⚡ | ⭐⭐ | 💾 | Fast search, limited context |
| 512 tokens, 50 overlap, threshold 0.1 | ⚡⚡ | ⭐⭐⭐ | 💾💾 | **Recommended default** |
| 700 tokens, 80 overlap, threshold 0.05 | ⚡ | ⭐⭐⭐⭐ | 💾💾💾 | High-quality search, rich context |

**Remember**: These parameters are highly dependent on your specific content domain, user query patterns, and quality requirements. Start with defaults and iterate based on empirical testing with your actual data. 