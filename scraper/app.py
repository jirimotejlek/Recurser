from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from functools import wraps
from typing import Dict, List, Any, Optional
import logging
import time
from urllib.parse import urljoin, urlparse

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import optional dependencies for better content extraction
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    logger.warning("BeautifulSoup not available, using basic text extraction")

try:
    from readability import Document
    HAS_READABILITY = True
except ImportError:
    HAS_READABILITY = False
    logger.warning("Readability not available, using basic content extraction")


def extract_content_with_bs4(html_content: str, url: str) -> str:
    """Extract clean content using BeautifulSoup"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Try to find main content areas
        content_areas = (
            soup.find('main') or 
            soup.find('article') or 
            soup.find('div', class_=lambda x: x and any(term in x.lower() for term in ['content', 'article', 'post', 'main'])) or
            soup.find('div', id=lambda x: x and any(term in x.lower() for term in ['content', 'article', 'post', 'main']))
        )
        
        if content_areas:
            text = content_areas.get_text()
        else:
            # Fallback to body content
            body = soup.find('body')
            text = body.get_text() if body else soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        logger.error(f"Error extracting content with BeautifulSoup: {e}")
        return html_content


def extract_content_basic(html_content: str) -> str:
    """Basic content extraction without external libraries"""
    import re
    
    # Remove script and style tags
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html_content)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def scrape_url(url: str) -> Dict[str, Any]:
    """
    Scrape content from a URL
    
    Args:
        url: URL to scrape
    
    Returns:
        Dict with content or error information
    """
    if not url or not url.strip():
        return {"error": "Empty URL provided"}
    
    # Validate URL format
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return {"error": "Invalid URL format"}
    
    try:
        # Set up headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        logger.info(f"Fetching content from: {url}")
        
        # Make request with timeout
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if 'text/html' not in content_type and 'text/plain' not in content_type:
            return {"error": f"Unsupported content type: {content_type}"}
        
        html_content = response.text
        
        # Extract content using best available method
        if HAS_BS4:
            content = extract_content_with_bs4(html_content, url)
        else:
            content = extract_content_basic(html_content)
        
        # Basic content validation
        if len(content.strip()) < 50:
            return {"error": "Extracted content too short, possibly blocked or empty page"}
        
        # Limit content length to prevent memory issues
        if len(content) > 50000:  # 50k characters limit
            content = content[:50000] + "... [Content truncated]"
        
        logger.info(f"Successfully scraped {len(content)} characters from {url}")
        
        return {
            "content": content,
            "url": url,
            "content_length": len(content),
            "status_code": response.status_code
        }
        
    except requests.exceptions.Timeout:
        return {"error": "Request timeout - website took too long to respond"}
    except requests.exceptions.ConnectionError:
        return {"error": "Connection error - could not connect to website"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error: {e.response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error scraping {url}: {e}")
        return {"error": f"Scraping failed: {str(e)}"}


@app.route('/scrape', methods=['GET'])
def scrape_website_get():
    """Scrape a website using GET request"""
    url = request.args.get('url')
    
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400

    logger.info(f"Scraping website (GET): {url}")
    
    result = scrape_url(url)
    
    if 'error' in result:
        return jsonify(result), 500
    
    return jsonify(result)


@app.route('/scrape', methods=['POST'])
def scrape_website_post():
    """Scrape a website using POST request"""
    data = request.json
    if not data:
        return jsonify({'error': 'JSON payload required'}), 400
    
    url = data.get('url')
    if not url:
        return jsonify({'error': 'Missing url in JSON payload'}), 400

    logger.info(f"Scraping website (POST): {url}")
    
    result = scrape_url(url)
    
    if 'error' in result:
        return jsonify(result), 500
    
    return jsonify(result)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'scraper',
        'capabilities': {
            'beautifulsoup': HAS_BS4,
            'readability': HAS_READABILITY,
            'basic_extraction': True
        }
    })


@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    return jsonify({
        'name': 'Scraper API',
        'version': '2.0',
        'description': 'Web content scraping service with intelligent content extraction',
        'endpoints': {
            '/health': 'GET - Health check',
            '/scrape': 'GET/POST - Scrape website content'
        },
        'documentation': {
            'scrape_get': {
                'method': 'GET',
                'parameters': {
                    'url': 'The URL of the website to scrape (query parameter)'
                },
                'example': '/scrape?url=https://example.com'
            },
            'scrape_post': {
                'method': 'POST',
                'content_type': 'application/json',
                'payload': {
                    'url': 'The URL of the website to scrape'
                },
                'example': '{"url": "https://example.com"}'
            }
        },
        'features': {
            'content_extraction': 'Intelligent content extraction using BeautifulSoup when available',
            'fallback_extraction': 'Basic regex-based extraction when BeautifulSoup unavailable',
            'content_filtering': 'Removes scripts, styles, navigation elements',
            'content_limits': 'Max 50,000 characters to prevent memory issues',
            'error_handling': 'Comprehensive error handling for various failure modes'
        },
        'capabilities': {
            'beautifulsoup': HAS_BS4,
            'readability': HAS_READABILITY,
            'basic_extraction': True
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5200, debug=True)