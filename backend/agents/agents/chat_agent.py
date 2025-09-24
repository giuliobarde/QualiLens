"""
Chat Agent for QualiLens.

This agent handles general conversation and chat queries.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from .base_agent import BaseAgent, AgentResponse
from ..question_classifier import ClassificationResult, QueryType

logger = logging.getLogger(__name__)


class ChatAgent(BaseAgent):
    """
    Agent responsible for handling general chat and conversation queries.
    """
    
    def _get_name(self) -> str:
        """Return the name of this agent."""
        return "chat_agent"
    
    def _get_description(self) -> str:
        """Return the description of this agent."""
        return "Handles general conversation, questions, and chat interactions"
    
    def _get_capabilities(self) -> List[str]:
        """Return the capabilities of this agent."""
        return [
            "general_chat",
            "conversation",
            "question_answering",
            "small_talk"
        ]
    
    def can_handle(self, query: str, classification: ClassificationResult) -> bool:
        """
        Determine if this agent can handle the given query.
        
        Args:
            query (str): The user query
            classification (ClassificationResult): The classification result
            
        Returns:
            bool: True if this agent can handle the query
        """
        # Handle general chat queries
        if classification.query_type == QueryType.GENERAL_CHAT:
            return True
        
        # Handle queries that don't require specific tools
        if classification.suggested_tool == "general_chat_tool":
            return True
        
        # Handle queries with no specific tool suggestion
        if not classification.suggested_tool:
            return True
        
        return False
    
    def process_query(self, query: str, classification: ClassificationResult) -> AgentResponse:
        """
        Process a user query using the general chat tool.
        
        Args:
            query (str): The user query
            classification (ClassificationResult): The classification result
            
        Returns:
            AgentResponse: Response from the agent
        """
        start_time = datetime.now()
        
        try:
            # Use the general chat tool
            result = self.execute_tool("general_chat_tool", query=query)
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return AgentResponse(
                success=True,
                result=result,
                agent_name=self.name,
                tools_used=["general_chat_tool"],
                error_message=None,
                execution_time_ms=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            logger.error(f"Chat agent error: {str(e)}")
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return AgentResponse(
                success=False,
                result=None,
                agent_name=self.name,
                tools_used=[],
                error_message=f"Chat agent failed: {str(e)}",
                execution_time_ms=execution_time,
                timestamp=start_time
            )
