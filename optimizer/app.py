from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from functools import wraps
from typing import Dict, List, Any, Optional
import logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
CHROMA_HOST = os.getenv('CHROMA_HOST', 'chromadb')
CHROMA_PORT = int(os.getenv('CHROMA_PORT', '8000'))
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'llm')
OLLAMA_PORT = int(os.getenv('OLLAMA_PORT', '11434'))
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'gemma3n:e2b')
LLM_DISPATCHER_HOST = os.getenv('LLM_DISPATCHER_HOST', 'api')
LLM_DISPATCHER_PORT = int(os.getenv('LLM_DISPATCHER_PORT', '5100'))

def query_ollama(prompt: str, model: str = None, stream: bool = False) -> Dict[str, Any]:
    """Send a query to Ollama"""
    url = f"http://{LLM_DISPATCHER_HOST}:{LLM_DISPATCHER_PORT}/query"
    
    payload = {
        "model": model or OLLAMA_MODEL,
        "prompt": prompt,
        "stream": stream
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Ollama returned status {response.status_code}: {response.text}"}
    except requests.exceptions.Timeout:
        return {"error": "Request to Ollama timed out"}
    except Exception as e:
        return {"error": f"Failed to query Ollama: {str(e)}"}


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "services": {
            "api": "up",
            "chromadb": "unknown",
            "ollama": "unknown"
        }
    }
    
    # Check ChromaDB
    try:
        response = requests.get(f"http://{CHROMA_HOST}:{CHROMA_PORT}/api/v2/heartbeat", timeout=2)
        health_status["services"]["chromadb"] = "up" if response.status_code == 200 else "down"
    except:
        health_status["services"]["chromadb"] = "down"
    
    # Check llm dispatcher
    try:
        response = requests.get(f"http://{LLM_DISPATCHER_HOST}:{LLM_DISPATCHER_PORT}/health", timeout=2)
        health_status["services"]["ollama"] = "up" if response.status_code == 200 else "down"
    except:
        health_status["services"]["ollama"] = "down"
    
    # Overall status
    if any(status == "down" for status in health_status["services"].values()):
        health_status["status"] = "degraded"
    
    return jsonify(health_status)


@app.route('/query', methods=['POST'])
def query_llm():
    """Requesting to llm dispatcher"""
    data = request.json
    
    if not data or 'prompt' not in data:
        return jsonify({'error': 'Missing prompt in request body'}), 400
    
    prompt = data['prompt']
    model = data.get('model', OLLAMA_MODEL)
    
    logger.info(f"Querying LLM with prompt: {prompt[:100]}...")
    
    optimized_prompt = f"Rewrite the following question into a concise and optimized search engine query for Google or Bing. Question: {prompt}"
    logger.info(f"Optimized prompt: {optimized_prompt}")
    result = requests.post(f"http://{LLM_DISPATCHER_HOST}:{LLM_DISPATCHER_PORT}/query", json={"prompt": optimized_prompt, "model": model})
    
    if 'error' in result:
        return jsonify(result), 500
    
    return jsonify({
        'response': result.get('response', ''),
        'model': model,
        'total_duration': result.get('total_duration', 0),
        'load_duration': result.get('load_duration', 0),
        'prompt_eval_duration': result.get('prompt_eval_duration', 0),
        'eval_duration': result.get('eval_duration', 0),
        'eval_count': result.get('eval_count', 0)
    })



@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    return jsonify({
        'name': 'RAG API',
        'version': '1.0',
        'endpoints': {
            '/health': 'GET - Health check',
            '/query': 'POST - Direct LLM query',
            '/rag_query': 'POST - RAG query (ChromaDB + LLM)',
            '/collections': 'GET - List ChromaDB collections',
            '/models': 'GET - List available LLM models'
        },
        'documentation': {
            'query': {
                'method': 'POST',
                'body': {
                    'prompt': 'Your question here',
                    'model': '(optional) model name'
                }
            }
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)