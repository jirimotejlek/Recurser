from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from functools import wraps
from typing import Dict, List, Any, Optional
from ddgs import DDGS
import logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/query', methods=['POST'])
def search_engine_request():
    """Direct query to search engine endpoint"""
    data = request.json
    
    if not data or 'search_query' not in data:
        return jsonify({'error': 'Missing search_query in request body'}), 400
    
    search_query = data['search_query']

    logger.info(f"Querying DuckDuckGo with search_query: {search_query[:100]}...")
    
    result = DDGS().text(search_query, max_results=5)
    print(result)

    # Standardize response format
    response_data = {
        'response': result,
        'provider': 'duckduckgo',
        'model': 'unknown'
    }

    return jsonify(response_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5150, debug=True)