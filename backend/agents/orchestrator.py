"""
Agent Orchestrator for QualiLens.

This module contains the agent orchestrator for the QualiLens project.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from .tool_registry import ToolRegistry
from .question_classifier import QuestionClassifier, ClassificationResult, QueryType
from .tools.base_tool import BaseTool

# Add the project root to the Python path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LLM.openai_client import OpenAIClient

logger = logging.getLogger(__name__)

@dataclass
class AgentResponse:
    """Response from the agent orchestrator."""
    success: bool
    result: Optional[Dict[str, Any]]
    tool_used: Optional[str]
    classification: Optional[ClassificationResult]
    error_message: Optional[str]
    execution_time_ms: int
    timestamp: datetime

class AgentOrchestrator:
    """
    Initialize the agent orchestrator.
    """
    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.question_classifier = QuestionClassifier()
        self.openai_client = OpenAIClient()

        # Performance tracking
        self._execution_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "average_execution_time": 0.0
        }

    def process_query(self, query: str) -> AgentResponse:
        """
        Process a user query through the agent system.
        
        Args:
            query (str): User query to process
            
        Returns:
            AgentResponse: Response from the agent system
        """
        start_time = datetime.now()
        
        try:
            # Get available tools
            available_tools = self.tool_registry.get_tool_names()
            
            # Classify the query
            classification = self.question_classifier.classify_query(query, available_tools)
            
            # Determine which tool to use
            tool_name = classification.suggested_tool
            if not tool_name or tool_name not in available_tools:
                # Default to general chat if no specific tool suggested
                tool_name = "general_chat_tool"
            
            # Get the tool
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                return AgentResponse(
                    success=False,
                    result=None,
                    tool_used=None,
                    classification=classification,
                    error_message=f"Tool '{tool_name}' not found",
                    execution_time_ms=0,
                    timestamp=start_time
                )
            
            # Execute the tool
            try:
                # Merge query with extracted parameters, avoiding duplicates
                params = classification.extracted_parameters.copy()
                if 'query' not in params:
                    params['query'] = query
                result = tool.execute(**params)
                
                # Update execution stats
                self._update_execution_stats(True, start_time)
                
                return AgentResponse(
                    success=True,
                    result=result,
                    tool_used=tool_name,
                    classification=classification,
                    error_message=None,
                    execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    timestamp=start_time
                )
                
            except Exception as tool_error:
                logger.error(f"Tool execution error: {str(tool_error)}")
                self._update_execution_stats(False, start_time)
                
                return AgentResponse(
                    success=False,
                    result=None,
                    tool_used=tool_name,
                    classification=classification,
                    error_message=f"Tool execution failed: {str(tool_error)}",
                    execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    timestamp=start_time
                )
                
        except Exception as e:
            logger.error(f"Query processing error: {str(e)}")
            self._update_execution_stats(False, start_time)
            
            return AgentResponse(
                success=False,
                result=None,
                tool_used=None,
                classification=None,
                error_message=f"Query processing failed: {str(e)}",
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                timestamp=start_time
            )

    def _update_execution_stats(self, success: bool, start_time: datetime):
        """Update execution statistics."""
        self._execution_stats["total_queries"] += 1
        if success:
            self._execution_stats["successful_queries"] += 1
        else:
            self._execution_stats["failed_queries"] += 1
        
        # Update average execution time
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        current_avg = self._execution_stats["average_execution_time"]
        total_queries = self._execution_stats["total_queries"]
        self._execution_stats["average_execution_time"] = (
            (current_avg * (total_queries - 1) + execution_time) / total_queries
        )

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return self.tool_registry.get_tool_names()

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return self._execution_stats.copy()

    def clear_caches(self):
        """Clear all caches."""
        self.question_classifier._classification_cache.clear()
        logger.info("All caches cleared")

    def register_tool(self, tool: BaseTool):
        """Register a tool with the orchestrator."""
        self.tool_registry.register_tool(tool)

    def run(self, query: str) -> AgentResponse:
        """Run the agent (legacy method)."""
        return self.process_query(query)