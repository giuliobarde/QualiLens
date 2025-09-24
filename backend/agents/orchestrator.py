"""
Agent Orchestrator for QualiLens.

This module contains the agent orchestrator for the QualiLens project.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from .tool_registry import ToolRegistry
from .agent_registry import AgentRegistry
from .question_classifier import QuestionClassifier, ClassificationResult, QueryType
from .tools.base_tool import BaseTool
from .agents.base_agent import BaseAgent, AgentResponse

# Add the project root to the Python path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LLM.openai_client import OpenAIClient

logger = logging.getLogger(__name__)

@dataclass
class OrchestratorResponse:
    """Response from the agent orchestrator."""
    success: bool
    result: Optional[Dict[str, Any]]
    agent_used: Optional[str]
    tools_used: Optional[List[str]]
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
        self.agent_registry = AgentRegistry()
        self.question_classifier = QuestionClassifier()
        self.openai_client = OpenAIClient()

        # Initialize agents
        self._initialize_agents()

        # Performance tracking
        self._execution_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "average_execution_time": 0.0
        }

    def _initialize_agents(self):
        """Initialize and register all available agents."""
        from .agents.chat_agent import ChatAgent
        from .agents.paper_analysis_agent import PaperAnalysisAgent
        
        # Create and register agents
        chat_agent = ChatAgent(self.tool_registry)
        paper_analysis_agent = PaperAnalysisAgent(self.tool_registry)
        
        self.agent_registry.register_agent(chat_agent)
        self.agent_registry.register_agent(paper_analysis_agent)
        
        logger.info("Initialized agents: chat_agent, paper_analysis_agent")

    def process_query(self, query: str) -> OrchestratorResponse:
        """
        Process a user query through the agent system.
        
        Args:
            query (str): User query to process
            
        Returns:
            OrchestratorResponse: Response from the agent system
        """
        start_time = datetime.now()
        
        try:
            # Get available tools for classification
            available_tools = self.tool_registry.get_tool_names()
            
            # Classify the query
            classification = self.question_classifier.classify_query(query, available_tools)
            
            # Find the best agent to handle this query
            selected_agent = self._select_agent(query, classification)
            
            if not selected_agent:
                return OrchestratorResponse(
                    success=False,
                    result=None,
                    agent_used=None,
                    tools_used=None,
                    classification=classification,
                    error_message="No suitable agent found to handle this query",
                    execution_time_ms=0,
                    timestamp=start_time
                )
            
            # Process the query with the selected agent
            try:
                agent_response = selected_agent.process_query(query, classification)
                
                # Update execution stats
                self._update_execution_stats(agent_response.success, start_time)
                
                return OrchestratorResponse(
                    success=agent_response.success,
                    result=agent_response.result,
                    agent_used=agent_response.agent_name,
                    tools_used=agent_response.tools_used,
                    classification=classification,
                    error_message=agent_response.error_message,
                    execution_time_ms=agent_response.execution_time_ms,
                    timestamp=start_time
                )
                
            except Exception as agent_error:
                logger.error(f"Agent execution error: {str(agent_error)}")
                self._update_execution_stats(False, start_time)
                
                return OrchestratorResponse(
                    success=False,
                    result=None,
                    agent_used=selected_agent.name,
                    tools_used=[],
                    classification=classification,
                    error_message=f"Agent execution failed: {str(agent_error)}",
                    execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    timestamp=start_time
                )
                
        except Exception as e:
            logger.error(f"Query processing error: {str(e)}")
            self._update_execution_stats(False, start_time)
            
            return OrchestratorResponse(
                success=False,
                result=None,
                agent_used=None,
                tools_used=None,
                classification=None,
                error_message=f"Query processing failed: {str(e)}",
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                timestamp=start_time
            )

    def _select_agent(self, query: str, classification: ClassificationResult) -> Optional[BaseAgent]:
        """
        Select the best agent to handle the given query.
        
        Args:
            query (str): The user query
            classification (ClassificationResult): The classification result
            
        Returns:
            Optional[BaseAgent]: The selected agent or None if no suitable agent found
        """
        # Get all available agents
        agents = self.agent_registry.get_all_agents()
        
        # Find agents that can handle this query
        suitable_agents = []
        for agent in agents.values():
            if agent.can_handle(query, classification):
                suitable_agents.append(agent)
        
        if not suitable_agents:
            logger.warning(f"No suitable agent found for query: {query}")
            return None
        
        # For now, return the first suitable agent
        # In the future, this could be enhanced with more sophisticated selection logic
        selected_agent = suitable_agents[0]
        logger.info(f"Selected agent: {selected_agent.name} for query: {query}")
        return selected_agent

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

    def get_available_agents(self) -> List[str]:
        """Get list of available agent names."""
        return self.agent_registry.get_agent_names()

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

    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator."""
        self.agent_registry.register_agent(agent)

    def run(self, query: str) -> OrchestratorResponse:
        """Run the agent (legacy method)."""
        return self.process_query(query)