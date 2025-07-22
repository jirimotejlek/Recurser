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

def query_ollama(prompt: str, model: str = None, stream: bool = False) -> Dict[str, Any]:
    """Send a query to Ollama"""
    url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/generate"
    
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
    
    # Check Ollama
    try:
        response = requests.get(f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/tags", timeout=2)
        health_status["services"]["ollama"] = "up" if response.status_code == 200 else "down"
    except:
        health_status["services"]["ollama"] = "down"
    
    # Overall status
    if any(status == "down" for status in health_status["services"].values()):
        health_status["status"] = "degraded"
    
    return jsonify(health_status)


@app.route('/query', methods=['POST'])
def query_llm():
    """Direct query to LLM endpoint"""
    data = request.json
    
    if not data or 'prompt' not in data:
        return jsonify({'error': 'Missing prompt in request body'}), 400
    
    prompt = data['prompt']
    model = data.get('model', OLLAMA_MODEL)
    
    logger.info(f"Querying LLM with prompt: {prompt[:100]}...")
    
    result = query_ollama(prompt, model)
    
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

@app.route('/models', methods=['GET'])
def list_models():
    """List available Ollama models"""
    try:
        response = requests.get(f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'models': [
                    {
                        'name': model['name'],
                        'size': model['size'],
                        'modified': model['modified_at']
                    }
                    for model in data.get('models', [])
                ],
                'default_model': OLLAMA_MODEL
            })
        else:
            return jsonify({'error': 'Failed to fetch models from Ollama'}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to list models: {str(e)}'}), 500


@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    return jsonify({
        'name': 'LLM Dispatcher',
        'version': '1.0',
        'endpoints': {
            '/health': 'GET - Health check',
            '/query': 'POST - Direct LLM query',
            '/models': 'GET - List available LLM models'
        },
        'documentation': {
            'query': {
                'method': 'POST',
                'body': {
                    'prompt': 'Your question here',
                    'model': 'model name [openai|local_small]'
                }
            }
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=True)