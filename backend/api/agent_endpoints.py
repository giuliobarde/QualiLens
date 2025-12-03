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
from agents.question_classifier import ClassificationResult, QueryType
from agents.tools.parse_pdf import ParsePDFTool
from agents.tools.text_section_analyzer import TextSectionAnalyzerTool
from agents.tools.link_analyzer import LinkAnalyzerTool
from agents.tools.general_chat import GeneralChatTool
from agents.tools.paper_analyzer import PaperAnalyzerTool
from agents.progress_tracker import get_progress_tracker, ProcessingStage
from agents.time_estimator import get_time_estimator

# Import new Phase 1 and Phase 2 tools
from agents.tools.content_summarizer import ContentSummarizerTool
from agents.tools.bias_detection import BiasDetectionTool
from agents.tools.methodology_analyzer import MethodologyAnalyzerTool
from agents.tools.statistical_validator import StatisticalValidatorTool
from agents.tools.reproducibility_assessor import ReproducibilityAssessorTool
from agents.tools.research_gap_identifier import ResearchGapIdentifierTool
from agents.tools.citation_analyzer import CitationAnalyzerTool
from agents.tools.quality_assessor import QualityAssessorTool

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
        
        paper_analyzer_tool = PaperAnalyzerTool()
        orchestrator.register_tool(paper_analyzer_tool)
        
        # Register new Phase 1 and Phase 2 tools
        content_summarizer_tool = ContentSummarizerTool()
        orchestrator.register_tool(content_summarizer_tool)
        
        bias_detection_tool = BiasDetectionTool()
        orchestrator.register_tool(bias_detection_tool)
        
        methodology_analyzer_tool = MethodologyAnalyzerTool()
        orchestrator.register_tool(methodology_analyzer_tool)
        
        statistical_validator_tool = StatisticalValidatorTool()
        orchestrator.register_tool(statistical_validator_tool)
        
        reproducibility_assessor_tool = ReproducibilityAssessorTool()
        orchestrator.register_tool(reproducibility_assessor_tool)
        
        research_gap_identifier_tool = ResearchGapIdentifierTool()
        orchestrator.register_tool(research_gap_identifier_tool)
        
        citation_analyzer_tool = CitationAnalyzerTool()
        orchestrator.register_tool(citation_analyzer_tool)
        
        quality_assessor_tool = QualityAssessorTool()
        orchestrator.register_tool(quality_assessor_tool)
        
        logger.info("Agent orchestrator created and configured successfully with all Phase 1, Phase 2, and Quality Assessor tools")
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
        },
        "request_id": "optional-request-id-for-progress-tracking"
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
        
        # Get or create request ID for progress tracking
        request_id = data.get('request_id')
        progress_tracker = get_progress_tracker()
        if not request_id:
            request_id = progress_tracker.create_tracker()
        else:
            # Ensure tracker exists
            if not progress_tracker.get_progress(request_id):
                request_id = progress_tracker.create_tracker(request_id)
        
        # Estimate time
        time_estimator = get_time_estimator()
        estimated_time = time_estimator.estimate_total_time(
            file_size_mb=0.0,
            has_pdf=False,
            num_tools=8,
            analysis_level="comprehensive",
            parallel_execution=True
        )
        progress_tracker.update_stage(
            request_id,
            ProcessingStage.CLASSIFYING,
            message="Classifying query and determining analysis approach",
            progress=5.0,
            estimated_time_remaining=estimated_time
        )
                
        logger.info(f"Processing agent query: '{query[:100]}...' (request_id: {request_id})")
        
        # Get or create agent orchestrator
        if not hasattr(current_app, 'agent_orchestrator'):
            current_app.agent_orchestrator = create_agent_orchestrator()
        
        orchestrator = current_app.agent_orchestrator
        
        # Set progress tracker in orchestrator context (if supported)
        # For now, we'll pass request_id through the query context
        if hasattr(orchestrator, 'set_progress_tracker'):
            orchestrator.set_progress_tracker(progress_tracker, request_id)
        
        # Process the query
        logger.info(f"Processing query with orchestrator...")
        response = orchestrator.process_query(query, request_id=request_id)
        logger.info(f"Orchestrator response - Success: {response.success}")
        logger.info(f"Orchestrator response - Agent used: {response.agent_used}")
        logger.info(f"Orchestrator response - Tools used: {response.tools_used}")
        logger.info(f"Orchestrator response - Result keys: {list(response.result.keys()) if response.result else 'None'}")
        
        # Mark progress as complete
        progress_tracker.complete(request_id, response.success, 
                                 "Analysis complete" if response.success else response.error_message)
        
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
            'timestamp': response.timestamp.isoformat(),
            'request_id': request_id  # Include request_id for progress tracking
        }
        
        if response.success:
            logger.info(f"Agent query successful - Agent: {response.agent_used}, Tools: {response.tools_used}, Time: {response.execution_time_ms}ms")
            logger.info(f"Final result being sent to frontend - Success: {result['success']}")
            logger.info(f"Final result being sent to frontend - Tools used: {result['tools_used']}")
            logger.info(f"Final result being sent to frontend - Result keys: {list(result['result'].keys()) if result['result'] else 'None'}")
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
        
        # Check file size (50MB limit)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > 50 * 1024 * 1024:  # 50MB
            return jsonify({'error': 'File too large. Maximum size is 50MB'}), 400
        
        if file_size == 0:
            return jsonify({'error': 'Empty file provided'}), 400
        
        # Get or create request ID for progress tracking
        request_id = request.form.get('request_id')
        
        # Get rubric weights if provided
        rubric_weights = None
        if 'rubric_weights' in request.form:
            try:
                import json
                rubric_weights = json.loads(request.form.get('rubric_weights'))
                logger.info(f"Received custom rubric weights: {rubric_weights}")
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse rubric weights: {e}")
                rubric_weights = None
        
        progress_tracker = get_progress_tracker()
        time_estimator = get_time_estimator()
        
        file_size_mb = file_size / (1024 * 1024)
        
        # Estimate time based on file size
        estimated_time = time_estimator.estimate_total_time(
            file_size_mb=file_size_mb,
            has_pdf=True,
            num_tools=8,
            analysis_level="comprehensive",
            parallel_execution=True
        )
        
        if not request_id:
            request_id = progress_tracker.create_tracker()
        else:
            if not progress_tracker.get_progress(request_id):
                request_id = progress_tracker.create_tracker(request_id)
        
        progress_tracker.update_stage(
            request_id,
            ProcessingStage.INITIALIZING,
            message=f"Preparing to analyze {file.filename} ({file_size_mb:.2f} MB)",
            progress=2.0,
            estimated_time_remaining=estimated_time,
            metadata={"file_name": file.filename, "file_size_mb": file_size_mb}
        )
        
        # Read file content
        file_content = file.read()
        
        # Get or create agent orchestrator
        if not hasattr(current_app, 'agent_orchestrator'):
            current_app.agent_orchestrator = create_agent_orchestrator()
        
        orchestrator = current_app.agent_orchestrator
        
        # Save file temporarily for processing
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Process the file upload through the agent system
            # Create a query that will trigger comprehensive PDF analysis
            query = f"Analyze this PDF file: {file.filename} (Analysis level: comprehensive)"
            
            logger.info(f"Processing PDF upload with query: {query}")
            logger.info(f"Temporary file path: {temp_file_path}")
            
            # Update progress to classifying stage
            progress_tracker.update_stage(
                request_id,
                ProcessingStage.CLASSIFYING,
                message="Classifying PDF analysis request",
                progress=5.0,
                estimated_time_remaining=estimated_time * 0.95
            )
            
            # Manually create classification with file path to ensure PDF parsing
            from agents.question_classifier import ClassificationResult, QueryType
            classification = ClassificationResult(
                query_type=QueryType.PAPER_ANALYSIS,
                confidence=1.0,
                suggested_tool="parse_pdf",
                extracted_parameters={
                    "file_path": temp_file_path,
                    "query": query
                },
                reasoning="PDF file uploaded for analysis"
            )
            
            # Get the paper analysis agent directly
            paper_agent = orchestrator.agent_registry.get_agent("paper_analysis_agent")
            if paper_agent:
                # Set request_id for progress tracking
                if request_id:
                    paper_agent.set_request_id(request_id)
                # Set rubric weights if provided
                if rubric_weights:
                    paper_agent.set_rubric_weights(rubric_weights)
                agent_response = paper_agent.process_query(query, classification)
                response = OrchestratorResponse(
                    success=agent_response.success,
                    result=agent_response.result,
                    agent_used=agent_response.agent_name,
                    tools_used=agent_response.tools_used,
                    classification=classification,
                    error_message=agent_response.error_message,
                    execution_time_ms=agent_response.execution_time_ms,
                    timestamp=agent_response.timestamp
                )
            else:
                # Fallback to orchestrator
                response = orchestrator.process_query(query, request_id=request_id)
            
            # Mark progress as complete
            progress_tracker.complete(request_id, response.success,
                                     "Analysis complete" if response.success else response.error_message)
            
            # If the agent system handled it successfully, return the response
            if response.success and response.result:
                logger.info(f"PDF upload successful with new multi-tool system")
                return jsonify({
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
                    },
                    'error_message': response.error_message,
                    'execution_time_ms': response.execution_time_ms,
                    'timestamp': response.timestamp.isoformat(),
                    'request_id': request_id
                })
            
            # If the agent system didn't handle it, fall back to direct tool usage
            if not response.success or not response.result:
                # Get the PDF tool directly as fallback
                pdf_tool = orchestrator.tool_registry.get_tool('parse_pdf')
                if not pdf_tool:
                    return jsonify({'error': 'PDF tool not available'}), 500
                
                # Execute PDF analysis directly
                try:
                    result = pdf_tool.execute(file_path=temp_file_path)
                    
                    # If PDF parsing was successful, enhance with paper analysis
                    if result.get("success") and result.get("text"):
                        # Get the paper analyzer tool
                        paper_analyzer = orchestrator.tool_registry.get_tool('paper_analyzer_tool')
                        if paper_analyzer:
                            try:
                                # Extract research data using LLM
                                paper_analysis_result = paper_analyzer.execute(
                                    text_content=result.get("text", ""),
                                    query=f"Analyze this research paper: {file.filename}",
                                    extract_level="comprehensive"
                                )
                                
                                if paper_analysis_result.get("success"):
                                    # Merge the results
                                    result["extracted_research_data"] = paper_analysis_result.get("extracted_data", {})
                                    result["research_analysis"] = paper_analysis_result
                                    
                                    # Also analyze sections if available
                                    if result.get("sections"):
                                        section_analysis = paper_analyzer.analyze_paper_sections(result.get("sections"))
                                        if section_analysis.get("success"):
                                            result["section_analyses"] = section_analysis.get("section_analyses", {})
                                    
                                    logger.info("Enhanced PDF analysis with research data extraction")
                                    
                            except Exception as analysis_error:
                                logger.warning(f"Paper analysis failed, continuing with basic PDF parsing: {str(analysis_error)}")
                    
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
                
                # Mark progress as complete
                progress_tracker.complete(request_id, True, "Analysis complete")
                
                # Format response
                response_data = {
                    'success': True,
                    'result': result,
                    'agent_used': 'paper_analysis_agent',
                    'tools_used': ['parse_pdf', 'paper_analyzer_tool'] if result.get('extracted_research_data') else ['parse_pdf'],
                    'classification': {
                        'query_type': 'pdf_analysis',
                        'confidence': 1.0,
                        'suggested_tool': 'parse_pdf',
                        'extracted_parameters': {},
                        'reasoning': 'PDF file uploaded for analysis'
                    },
                    'error_message': None,
                    'execution_time_ms': 0,
                    'timestamp': datetime.now().isoformat(),
                    'request_id': request_id
                }
                
                logger.info(f"PDF analysis successful for file: {file.filename}")
                return jsonify(response_data)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500


def get_progress():
    """
    Get progress for a request.
    
    GET /api/agent/progress?request_id=<request_id>
    """
    try:
        request_id = request.args.get('request_id')
        if not request_id:
            return jsonify({'error': 'request_id parameter is required'}), 400
        
        progress_tracker = get_progress_tracker()
        progress = progress_tracker.get_progress(request_id)
        
        if not progress:
            return jsonify({'error': 'Progress not found for request_id'}), 404
        
        return jsonify(progress)
        
    except Exception as e:
        logger.error(f"Get progress error: {str(e)}")
        return jsonify({'error': str(e)}), 500
