"""
General Chat tool for QualiLens.

This module contains the General Chat tool for handling general conversational queries.
"""

from typing import Any, Dict
from .base_tool import BaseTool, ToolMetadata


class GeneralChatTool(BaseTool):
    """
    General Chat tool for QualiLens.
    """
    
    def _get_metadata(self) -> ToolMetadata:
        """Return the metadata for this tool."""
        return ToolMetadata(
            name="general_chat_tool",
            description="Handle general conversational queries",
            parameters={
                "required": ["query"],
                "optional": [],
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The general chat query"
                    }
                }
            },
            examples=[
                "How are you?",
                "What can you help me with?",
                "Tell me about your capabilities"
            ],
            category="chat"
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the general chat tool.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            Dict[str, Any]: Tool execution result
        """
        print("General Chat Tool being called")
        
        return {
            "success": True,
            "message": "General chat response completed",
            "tool_used": "general_chat_tool"
        }
