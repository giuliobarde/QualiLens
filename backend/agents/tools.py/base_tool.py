"""
Base Tool Interface for Medical-Hub.

This module defines the base interface that all agent tools must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ToolMetadata:
    """Metadata for a tool including description, parameters, and examples."""
    name: str
    description: str
    parameters: Dict[str, Any]
    examples: List[str]
    category: str = "general"


class BaseTool(ABC):
    """
    Abstract base class for all agent tools.
    
    All tools must inherit from this class and implement the required methods.
    """
    
    def __init__(self):
        self.metadata = self._get_metadata()
    
    @abstractmethod
    def _get_metadata(self) -> ToolMetadata:
        """
        Return the metadata for this tool.
        
        Returns:
            ToolMetadata: Tool metadata including name, description, parameters, and examples
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with the given parameters.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Dict[str, Any]: Tool execution result
        """
        pass
    
    def validate_parameters(self, **kwargs) -> bool:
        """
        Validate the parameters for this tool.
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            bool: True if parameters are valid, False otherwise
        """
        required_params = self.metadata.parameters.get('required', [])
        for param in required_params:
            if param not in kwargs:
                return False
        return True
    
    def get_description(self) -> str:
        """Get the tool description."""
        return self.metadata.description
    
    def get_name(self) -> str:
        """Get the tool name."""
        return self.metadata.name
    
    def get_examples(self) -> List[str]:
        """Get example queries for this tool."""
        return self.metadata.examples
