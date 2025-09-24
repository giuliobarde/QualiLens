#!/usr/bin/env python3
"""
Main Flask application for QualiLens backend.

This module contains the Flask app configuration and startup.
"""

import logging
from flask import Flask
from flask_cors import CORS
from api.agent_endpoints import (
    agent_query, 
    get_agent_status, 
    get_agent_tools, 
    clear_agent_cache,
    upload_file
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Enable CORS for frontend communication
    CORS(app, origins=['http://localhost:3000', 'http://localhost:3001'], supports_credentials=True)
    
    # Register API routes
    app.add_url_rule('/api/agent/query', 'agent_query', agent_query, methods=['POST'])
    app.add_url_rule('/api/agent/status', 'get_agent_status', get_agent_status, methods=['GET'])
    app.add_url_rule('/api/agent/tools', 'get_agent_tools', get_agent_tools, methods=['GET'])
    app.add_url_rule('/api/agent/clear-cache', 'clear_agent_cache', clear_agent_cache, methods=['POST'])
    app.add_url_rule('/api/agent/upload', 'upload_file', upload_file, methods=['POST'])
    
    logger.info("Flask application created successfully")
    return app

if __name__ == '__main__':
    app = create_app()
    logger.info("Starting QualiLens backend server on port 5002")
    app.run(host='0.0.0.0', port=5002, debug=True)
