"""
Base Agent Interface for QualiLens.

This module defines the base interface that all agents must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from ..tools.base_tool import BaseTool
from ..tool_registry import ToolRegistry


@dataclass
class AgentResponse:
    """Response from an agent."""
    success: bool
    result: Optional[Dict[str, Any]]
    agent_name: str
    tools_used: List[str]
    error_message: Optional[str]
    execution_time_ms: int
    timestamp: datetime


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    All agents must inherit from this class and implement the required methods.
    """
    
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        self.name = self._get_name()
        self.description = self._get_description()
        self.capabilities = self._get_capabilities()
    
    @abstractmethod
    def _get_name(self) -> str:
        """Return the name of this agent."""
        pass
    
    @abstractmethod
    def _get_description(self) -> str:
        """Return the description of this agent."""
        pass
    
    @abstractmethod
    def _get_capabilities(self) -> List[str]:
        """Return the capabilities of this agent."""
        pass
    
    @abstractmethod
    def can_handle(self, query: str, classification: Any) -> bool:
        """
        Determine if this agent can handle the given query.
        
        Args:
            query (str): The user query
            classification: The classification result from question classifier
            
        Returns:
            bool: True if this agent can handle the query
        """
        pass
    
    @abstractmethod
    def process_query(self, query: str, classification: Any) -> AgentResponse:
        """
        Process a user query.
        
        Args:
            query (str): The user query
            classification: The classification result from question classifier
            
        Returns:
            AgentResponse: Response from the agent
        """
        pass
    
    def get_available_tools(self) -> List[str]:
        """Get list of tools available to this agent."""
        return self.tool_registry.get_tool_names()
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a specific tool by name."""
        return self.tool_registry.get_tool(tool_name)
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool with the given parameters."""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        return tool.execute(**kwargs)
