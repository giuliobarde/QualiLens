"""
Tool Registry for Medical-Hub.

This module manages the registration and discovery of available tools
that the agent can use to process user queries.
"""

import logging
from typing import Dict, List, Optional, Type
from .tools.base_tool import BaseTool, ToolMetadata

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for managing available agent tools.
    
    This class handles tool registration, discovery, and provides
    metadata for LLM-based tool selection.
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_metadata: Dict[str, ToolMetadata] = {}
    
    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool in the registry.
        
        Args:
            tool (BaseTool): The tool to register
        """
        tool_name = tool.get_name()
        if tool_name in self._tools:
            logger.warning(f"Tool '{tool_name}' is already registered. Overwriting.")
        
        self._tools[tool_name] = tool
        self._tool_metadata[tool_name] = tool.metadata
        logger.info(f"Registered tool: {tool_name}")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.
        
        Args:
            tool_name (str): Name of the tool to retrieve
            
        Returns:
            Optional[BaseTool]: The tool if found, None otherwise
        """
        return self._tools.get(tool_name)
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """
        Get all registered tools.
        
        Returns:
            Dict[str, BaseTool]: Dictionary of all registered tools
        """
        return self._tools.copy()
    
    def get_tool_names(self) -> List[str]:
        """
        Get list of all registered tool names.
        
        Returns:
            List[str]: List of tool names
        """
        return list(self._tools.keys())
    
    def get_tool_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """
        Get metadata for a specific tool.
        
        Args:
            tool_name (str): Name of the tool
            
        Returns:
            Optional[ToolMetadata]: Tool metadata if found, None otherwise
        """
        return self._tool_metadata.get(tool_name)
    
    def get_all_metadata(self) -> Dict[str, ToolMetadata]:
        """
        Get metadata for all registered tools.
        
        Returns:
            Dict[str, ToolMetadata]: Dictionary of all tool metadata
        """
        return self._tool_metadata.copy()
    
    def get_tools_by_category(self, category: str) -> Dict[str, BaseTool]:
        """
        Get all tools in a specific category.
        
        Args:
            category (str): Category to filter by
            
        Returns:
            Dict[str, BaseTool]: Dictionary of tools in the category
        """
        return {
            name: tool for name, tool in self._tools.items()
            if tool.metadata.category == category
        }
    
    def get_available_tools_description(self) -> str:
        """
        Get a formatted description of all available tools for LLM consumption.
        
        Returns:
            str: Formatted description of all tools
        """
        descriptions = []
        for name, metadata in self._tool_metadata.items():
            desc = f"Tool: {name}\n"
            desc += f"Description: {metadata.description}\n"
            desc += f"Category: {metadata.category}\n"
            
            if metadata.parameters:
                required = metadata.parameters.get('required', [])
                optional = metadata.parameters.get('optional', [])
                if required:
                    desc += f"Required parameters: {', '.join(required)}\n"
                if optional:
                    desc += f"Optional parameters: {', '.join(optional)}\n"
            
            if metadata.examples:
                desc += f"Examples: {'; '.join(metadata.examples)}\n"
            
            descriptions.append(desc)
        
        return "\n".join(descriptions)
    
    def unregister_tool(self, tool_name: str) -> bool:
        """
        Unregister a tool from the registry.
        
        Args:
            tool_name (str): Name of the tool to unregister
            
        Returns:
            bool: True if tool was unregistered, False if not found
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            del self._tool_metadata[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")
            return True
        return False
    
    def clear_registry(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._tool_metadata.clear()
        logger.info("Cleared all tools from registry")
    
    def is_tool_registered(self, tool_name: str) -> bool:
        """
        Check if a tool is registered.
        
        Args:
            tool_name (str): Name of the tool to check
            
        Returns:
            bool: True if tool is registered, False otherwise
        """
        return tool_name in self._tools
