# Recurser Application Architecture

## Overview

This document outlines the architecture for the Recurser application, a containerised system that optimises user queries, performs web searches, scrapes content, and provides intelligent responses using RAG (Retrieval-Augmented Generation) techniques.

## Application Flow

The application follows this sequence:
1. User submits query → UI
2. UI → Optimiser → LLM Dispatcher (query optimisation)
3. UI → Search Engine (search with optimised query)
4. UI → Crawler (scrape search results)
5. UI → RAG Builder (create embeddings & find relevant chunks)
6. UI → LLM Dispatcher (final response generation)
7. UI displays final result to user

---

## Container Specifications

### 1. `recurser_ui`

**Purpose:** Frontend interface and orchestration hub for the entire application flow.

**Responsibilities:**
- Accept user queries through web interface
- Orchestrate API calls to other containers in the correct sequence
- Display final results to users
- Handle error states and user feedback

**Inputs:**
- User queries (from web interface)
- Optimised queries (from `optimiser`)
- Search results (from `search_engine`)
- Scraped content (from `crawler`)
- Relevant text chunks (from `rag_builder`)
- Final LLM responses (from `llm_dispatcher`)

**Outputs:**
- Original queries (to `optimiser`)
- Optimised queries (to `search_engine`)
- Search results (to `crawler`)
- Scraped content (to `rag_builder`)
- Query + relevant chunks (to `llm_dispatcher`)
- Final responses (to user interface)

**APIs Exposed:**
- Web interface for user interaction
- Health check endpoint

---

### 2. `optimiser`

**Purpose:** Enhance and optimise user queries before search and retrieval operations.

**Responsibilities:**
- Receive raw user queries
- Add appropriate context and optimisation instructions
- Coordinate with LLM dispatcher for query enhancement
- Return optimised queries suitable for search engines

**Inputs:**
- Raw user queries (from `recurser_ui`)
- Optimised query responses (from `llm_dispatcher`)

**Outputs:**
- Query + optimisation context (to `llm_dispatcher`)
- Optimised queries (to `recurser_ui`)

**APIs Exposed:**
- `POST /optimise` - accepts raw query, returns optimised query

**API Calls Made:**
- `POST` to `llm_dispatcher` for query optimisation

---

### 3. `llm_dispatcher`

**Purpose:** Central LLM service that handles both query optimisation and final response generation.

**Responsibilities:**
- Route LLM requests to appropriate providers (local LLM or OpenAI API)
- Handle query optimisation requests from optimiser
- Generate final responses using optimised queries and relevant context
- Manage LLM provider failover and load balancing

**Inputs:**
- Query + optimisation instructions (from `optimiser`)
- Final query + relevant chunks (from `recurser_ui`)

**Outputs:**
- Optimised queries (to `optimiser`)
- Final generated responses (to `recurser_ui`)

**APIs Exposed:**
- `POST /optimise` - optimise queries for search
- `POST /generate` - generate final responses with context

**External Dependencies:**
- Local LLM container (if using local models)
- OpenAI API (if using OpenAI models)

---

### 4. `search_engine`

**Purpose:** Perform web searches using optimised queries and return structured results.

**Responsibilities:**
- Accept optimised search queries
- Interface with external search APIs (Google, Bing, etc.)
- Format and structure search results
- Handle rate limiting and error responses from search providers

**Inputs:**
- Optimised queries (from `recurser_ui`)

**Outputs:**
- Structured search results with URLs and metadata (to `recurser_ui`)

**APIs Exposed:**
- `POST /search` - performs search and returns results

**External Dependencies:**
- Search engine APIs (Google Search API, Bing Search API, etc.)

---

### 5. `crawler`

**Purpose:** Scrape and sanitise content from search result URLs.

**Responsibilities:**
- Accept list of URLs from search results
- Scrape web content from each URL
- Extract and sanitise text content (remove HTML, ads, navigation, etc.)
- Handle different content types and encoding
- Implement respectful crawling (rate limiting, robots.txt compliance)

**Inputs:**
- Search results with URLs (from `recurser_ui`)

**Outputs:**
- Sanitised text content from scraped websites (to `recurser_ui`)

**APIs Exposed:**
- `POST /crawl` - accepts URLs, returns sanitised text content

**Considerations:**
- Implement timeout handling for slow websites
- Handle JavaScript-rendered content if necessary
- Respect robots.txt and rate limits

---

### 6. `rag_builder`

**Purpose:** Manage embeddings, vector database operations, and chunk retrieval for RAG.

**Responsibilities:**
- Create and store embeddings from scraped content
- Manage ChromaDB operations (insert, query, update)
- Chunk text content appropriately for embedding
- Find most relevant chunks based on query similarity
- Maintain embedding consistency and quality

**Inputs:**
- Scraped text content (from `recurser_ui` via `crawler`)
- Optimised queries for similarity search (from `recurser_ui`)

**Outputs:**
- Confirmation of successful embedding storage (to `recurser_ui`)
- Most relevant text chunks for query (to `recurser_ui`)

**APIs Exposed:**
- `POST /embed` - create and store embeddings from content
- `POST /retrieve` - find relevant chunks for a given query

**External Dependencies:**
- ChromaDB database
- Embedding model (local or API-based)

---

## API Communication Patterns

### Query Optimisation Flow
```
recurser_ui → optimiser → llm_dispatcher → optimiser → recurser_ui
```

### Content Processing Flow
```
recurser_ui → search_engine → recurser_ui → crawler → recurser_ui → rag_builder
```

### Final Response Generation Flow
```
recurser_ui (query + chunks) → llm_dispatcher → recurser_ui
```

---

## Error Handling Strategy

Each container should implement:
- Graceful degradation when dependencies are unavailable
- Appropriate timeout handling
- Structured error responses with actionable information
- Health check endpoints for monitoring
- Retry logic with exponential backoff where appropriate

---

## Development Guidelines

### For Team Members

1. **Container Independence:** Each container should be independently deployable and testable
2. **API Contracts:** Maintain backward compatibility in API contracts
3. **Documentation:** Each container should include API documentation and usage examples
4. **Testing:** Implement unit tests and integration tests for your container
5. **Monitoring:** Include logging and metrics collection
6. **Configuration:** Use environment variables for external service configuration

### Shared Standards

- All APIs should use JSON for request/response bodies
- HTTP status codes should follow REST conventions
- Authentication/authorisation strategy (to be defined)
- Logging format and levels (to be standardised)
- Error response format (to be standardised)

---

## Deployment Considerations

- Each container should include a Dockerfile
- Consider using Docker Compose for local development
- Plan for horizontal scaling of stateless containers
- ChromaDB persistence and backup strategy
- Environment-specific configuration management
