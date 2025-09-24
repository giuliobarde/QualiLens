#!/usr/bin/env python3
"""
Agent API Endpoints for Medical-Hub.

This module contains all the Flask route handlers for the agent API.
"""

import logging
from datetime import datetime
from flask import request, jsonify, current_app
from typing import Dict, Any, Optional
import base64

# Add the project root to the Python path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import AgentOrchestrator, OrchestratorResponse
from agents.tools.parse_pdf import ParsePDFTool
from agents.tools.text_section_analyzer import TextSectionAnalyzerTool
from agents.tools.link_analyzer import LinkAnalyzerTool
from agents.tools.general_chat import GeneralChatTool

logger = logging.getLogger(__name__)


def create_agent_orchestrator() -> AgentOrchestrator:
    """
    Create and configure the agent orchestrator with all available tools.
    
    Returns:
        AgentOrchestrator: Configured agent orchestrator
    """
    try:
        orchestrator = AgentOrchestrator()
        
        # Register all tools
        parse_pdf_tool = ParsePDFTool()
        orchestrator.register_tool(parse_pdf_tool)
        
        text_section_tool = TextSectionAnalyzerTool()
        orchestrator.register_tool(text_section_tool)
        
        link_analyzer_tool = LinkAnalyzerTool()
        orchestrator.register_tool(link_analyzer_tool)
        
        general_chat_tool = GeneralChatTool()
        orchestrator.register_tool(general_chat_tool)
        
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
            'agent_used': response.agent_used,
            'tools_used': response.tools_used,
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
            logger.info(f"Agent query successful - Agent: {response.agent_used}, Tools: {response.tools_used}, Time: {response.execution_time_ms}ms")
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
        available_agents = orchestrator.get_available_agents()
        execution_stats = orchestrator.get_execution_stats()
        
        # Get search tool status if available
        search_tool_status = None
        search_tool = orchestrator.tool_registry.get_tool('search_tool')
        if search_tool:
            search_tool_status = search_tool.get_search_engines_status()
        
        status = {
            'agent_initialized': True,
            'available_agents': available_agents,
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


def upload_file():
    """
    Handle file uploads for analysis.
    
    POST /api/agent/upload
    Expected multipart form data with file
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file type
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are supported'}), 400
        
        # Read file content
        file_content = file.read()
        
        # Get or create agent orchestrator
        if not hasattr(current_app, 'agent_orchestrator'):
            current_app.agent_orchestrator = create_agent_orchestrator()
        
        orchestrator = current_app.agent_orchestrator
        
        # Process the file upload through the agent system
        # Create a query that will trigger PDF analysis
        query = f"Analyze this PDF file: {file.filename}"
        
        # Process the query through the orchestrator
        response = orchestrator.process_query(query)
        
        # If the agent system didn't handle it, fall back to direct tool usage
        if not response.success or not response.result:
            # Get the PDF tool directly as fallback
            pdf_tool = orchestrator.tool_registry.get_tool('parse_pdf')
            if not pdf_tool:
                return jsonify({'error': 'PDF tool not available'}), 500
            
            # Execute PDF analysis directly
            try:
                # Save file temporarily for processing
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(file_content)
                    temp_file_path = temp_file.name
                
                try:
                    result = pdf_tool.execute(file_path=temp_file_path)
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                
                # Format response
                response_data = {
                    'success': True,
                    'result': result,
                    'agent_used': 'paper_analysis_agent',
                    'tools_used': ['parse_pdf'],
                    'classification': {
                        'query_type': 'pdf_analysis',
                        'confidence': 1.0,
                        'suggested_tool': 'parse_pdf',
                        'extracted_parameters': {},
                        'reasoning': 'PDF file uploaded for analysis'
                    },
                    'error_message': None,
                    'execution_time_ms': 0,
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.info(f"PDF analysis successful for file: {file.filename}")
                return jsonify(response_data)
                
            except Exception as tool_error:
                logger.error(f"PDF analysis error: {str(tool_error)}")
                return jsonify({
                    'success': False,
                    'result': None,
                    'agent_used': 'paper_analysis_agent',
                    'tools_used': ['parse_pdf'],
                    'error_message': f"PDF analysis failed: {str(tool_error)}",
                    'timestamp': datetime.now().isoformat()
                }), 500
        else:
            # Use the agent response
            response_data = {
                'success': response.success,
                'result': response.result,
                'agent_used': response.agent_used,
                'tools_used': response.tools_used,
                'classification': {
                    'query_type': response.classification.query_type.value if response.classification else 'pdf_analysis',
                    'confidence': response.classification.confidence if response.classification else 1.0,
                    'suggested_tool': response.classification.suggested_tool if response.classification else 'parse_pdf',
                    'extracted_parameters': response.classification.extracted_parameters if response.classification else {},
                    'reasoning': response.classification.reasoning if response.classification else 'PDF file uploaded for analysis'
                },
                'error_message': response.error_message,
                'execution_time_ms': response.execution_time_ms,
                'timestamp': response.timestamp.isoformat()
            }
            
            logger.info(f"PDF analysis successful for file: {file.filename} using agent: {response.agent_used}")
            return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500
