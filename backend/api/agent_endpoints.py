#!/usr/bin/env python3
"""
Agent API Endpoints for Medical-Hub.

This module contains all the Flask route handlers for the agent API.
"""

import logging
from datetime import datetime
from flask import request, jsonify, current_app
from typing import Dict, Any, Optional

# Add the project root to the Python path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import AgentOrchestrator, AgentResponse
from agents.tools.parse_pdf import ParsePDFTool

logger = logging.getLogger(__name__)


def create_agent_orchestrator() -> AgentOrchestrator:
    """
    Create and configure the agent orchestrator with all available tools.
    
    Returns:
        AgentOrchestrator: Configured agent orchestrator
    """
    try:
        orchestrator = AgentOrchestrator()
        
        # Register the search tool
        parse_pdf_tool = ParsePDFTool()
        orchestrator.register_tool(parse_pdf_tool)
        
        logger.info("Agent orchestrator created and configured successfully")
        return orchestrator
        
    except Exception as e:
        logger.error(f"Failed to create agent orchestrator: {str(e)}")
        raise


def agent_query():
    """
    Process a query through the agent system.
    
    POST /api/agent/query
    Expected JSON payload:
    {
        "query": "user query string",
        "user_context": {
            "filters": {},
            "preferences": {}
        }
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        query = data.get('query', '').strip()
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
                
        logger.info(f"Processing agent query: '{query[:100]}...'")
        
        # Get or create agent orchestrator
        if not hasattr(current_app, 'agent_orchestrator'):
            current_app.agent_orchestrator = create_agent_orchestrator()
        
        orchestrator = current_app.agent_orchestrator
        
        # Process the query
        response = orchestrator.process_query(query)
        
        # Format response for frontend
        result = {
            'success': response.success,
            'result': response.result,
            'tool_used': response.tool_used,
            'classification': {
                'query_type': response.classification.query_type.value if response.classification else None,
                'confidence': response.classification.confidence if response.classification else None,
                'suggested_tool': response.classification.suggested_tool if response.classification else None,
                'extracted_parameters': response.classification.extracted_parameters if response.classification else None,
                'reasoning': response.classification.reasoning if response.classification else None
            } if response.classification else None,
            'error_message': response.error_message,
            'execution_time_ms': response.execution_time_ms,
            'timestamp': response.timestamp.isoformat()
        }
        
        if response.success:
            logger.info(f"Agent query successful - Tool: {response.tool_used}, Time: {response.execution_time_ms}ms")
            return jsonify(result)
        else:
            logger.warning(f"Agent query failed: {response.error_message}")
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Agent query error: {str(e)}")
        return jsonify({'error': str(e)}), 500


def get_agent_status():
    """
    Get the status of the agent system.
    
    GET /api/agent/status
    """
    try:
        # Get or create agent orchestrator
        if not hasattr(current_app, 'agent_orchestrator'):
            current_app.agent_orchestrator = create_agent_orchestrator()
        
        orchestrator = current_app.agent_orchestrator
        
        # Get status information
        available_tools = orchestrator.get_available_tools()
        execution_stats = orchestrator.get_execution_stats()
        
        # Get search tool status if available
        search_tool_status = None
        search_tool = orchestrator.tool_registry.get_tool('search_tool')
        if search_tool:
            search_tool_status = search_tool.get_search_engines_status()
        
        status = {
            'agent_initialized': True,
            'available_tools': available_tools,
            'execution_stats': execution_stats,
            'search_tool_status': search_tool_status,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Agent status error: {str(e)}")
        return jsonify({'error': str(e)}), 500


def get_agent_tools():
    """
    Get information about available agent tools.
    
    GET /api/agent/tools
    """
    try:
        # Get or create agent orchestrator
        if not hasattr(current_app, 'agent_orchestrator'):
            current_app.agent_orchestrator = create_agent_orchestrator()
        
        orchestrator = current_app.agent_orchestrator
        
        # Get tool information
        tools_info = []
        for tool_name in orchestrator.get_available_tools():
            tool = orchestrator.tool_registry.get_tool(tool_name)
            if tool:
                tools_info.append({
                    'name': tool.get_name(),
                    'description': tool.get_description(),
                    'category': tool.metadata.category,
                    'examples': tool.get_examples(),
                    'parameters': tool.metadata.parameters
                })
        
        return jsonify({
            'tools': tools_info,
            'total_tools': len(tools_info),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Agent tools error: {str(e)}")
        return jsonify({'error': str(e)}), 500


def clear_agent_cache():
    """
    Clear the agent system caches.
    
    POST /api/agent/clear-cache
    """
    try:
        # Get or create agent orchestrator
        if not hasattr(current_app, 'agent_orchestrator'):
            current_app.agent_orchestrator = create_agent_orchestrator()
        
        orchestrator = current_app.agent_orchestrator
        
        # Clear caches
        orchestrator.clear_caches()
        
        logger.info(f"Agent caches cleared")
        
        return jsonify({
            'success': True,
            'message': 'Agent caches cleared successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Clear agent cache error: {str(e)}")
        return jsonify({'error': str(e)}), 500
