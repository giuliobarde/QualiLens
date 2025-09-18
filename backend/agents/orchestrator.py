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

    def run(self, query: str) -> AgentResponse:
        """Run the agent."""
        return AgentResponse(success=True, result=None, tool_used=None, classification=None, error_message=None, execution_time_ms=0, timestamp=datetime.now())