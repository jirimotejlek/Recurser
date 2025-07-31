import logging
import os
from functools import wraps
from typing import Any, Dict, List, Optional

import requests
from ddgs import DDGS
from flask import Flask, jsonify, request
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        # Test a simple search to verify the service is working
        test_result = DDGS().text("test", max_results=1)
        return jsonify(
            {
                "status": "healthy",
                "service": "search_engine",
                "provider": "duckduckgo",
                "test_result_count": len(list(test_result)) if test_result else 0,
            }
        )
    except Exception as e:
        return (
            jsonify(
                {"status": "unhealthy", "service": "search_engine", "error": str(e)}
            ),
            500,
        )


@app.route("/query", methods=["POST"])
def search_engine_request():
    """Direct query to search engine endpoint"""
    data = request.json

    if not data or "search_query" not in data:
        return jsonify({"error": "Missing search_query in request body"}), 400

    search_query = data["search_query"]

    logger.info(f"Querying DuckDuckGo with search_query: {search_query[:100]}...")

    try:
        result = DDGS().text(search_query, max_results=5)
        result_list = list(result)  # Convert generator to list

        # Standardize response format
        response_data = {
            "response": result_list,
            "provider": "duckduckgo",
            "query": search_query,
            "result_count": len(result_list),
        }

        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        return (
            jsonify(
                {
                    "error": f"Search failed: {str(e)}",
                    "provider": "duckduckgo",
                    "query": search_query,
                }
            ),
            500,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5150, debug=True)
