from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from functools import wraps
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables

LLM_DISPATCHER = os.getenv('LLM_DISPATCHER', 'api')
LLM_DISPATCHER_PORT = int(os.getenv('LLM_DISPATCHER_PORT', '5100'))

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "services": {
            "llm_dispatcher": "up"
        }
    }
    # Check llm dispatcher
    try:
        response = requests.get(f"http://{LLM_DISPATCHER}:{LLM_DISPATCHER_PORT}/health", timeout=2)
        result = response.json()
        if result["status"] != "healthy":
            health_status["status"] = "degraded"
            health_status["services"]["llm_dispatcher"] = "down"

    except:
        health_status["status"] = "degraded"
        health_status["services"]["llm_dispatcher"] = "down"
    return jsonify(health_status)


@app.route('/query', methods=['POST'])
def optimize_query():
    """Requesting to llm dispatcher"""
    data = request.json
    
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing prompt in request body'}), 400
    
    query = data['query']
    
    logger.info(f"Querying LLM with prompt: {query[:100]}...")
    current_date = datetime.now().strftime("%Y-%m-%d")
    optimized_query = f"Rewrite the following question into a concise and optimized search engine query for Google or Bing. Question: {query}, current date, use this if needed: {current_date}"
    logger.info(f"Optimized prompt: {optimized_query}")
    print("querying llm dispatcher", f"http://{LLM_DISPATCHER}:{LLM_DISPATCHER_PORT}/query")
    result = requests.post(f"http://{LLM_DISPATCHER}:{LLM_DISPATCHER_PORT}/query", json={"prompt": optimized_query})
    result = result.json()
    print("result is ", result)
    if 'error' in result:
        return jsonify(result), 500
    
    return jsonify({
        'response': result.get('response', '')
    })



@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    return jsonify({
        "message": "Optimizer API is running"
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)