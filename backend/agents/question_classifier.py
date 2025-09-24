import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

# Add the project root to the Python path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LLM.openai_client import OpenAIClient

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Type of query."""
    PDF_ANALYSIS = "pdf_analysis"
    TEXT_SECTION = "text_section"
    LINK_ANALYSIS = "link_analysis"
    GENERAL_CHAT = "general_chat"

@dataclass
class ClassificationResult:
    """Result of the question classifier."""
    query_type: QueryType
    confidence: float
    suggested_tool: str
    extracted_parameters: Dict[str, Any]
    reasoning: str

class QuestionClassifier:
    """
    Classifies user queries to determine the appropriate tool and parameters.
    
    Uses LLM to understand user intent and route to the correct tool.
    """

    def __init__(self):
        self.openai_client = OpenAIClient()
        self._classification_cache: Dict[str, ClassificationResult] = {}

    def classify_query(self, query: str, available_tools: List[str]) -> ClassificationResult:
        """
        Classify a user query and determine the appropriate tool.
        
        Args:
            query (str): User query to classify
            available_tools (List[str]): List of available tool names
            
        Returns:
            ClassificationResult: Classification result with suggested tool and parameters
        """
        cached_key = f"{query}|{','.join(sorted(available_tools))}"
        if cached_key in self._classification_cache:
            logger.debug(f"Classification cache hit for query: {query}")
            return self._classification_cache[cached_key]
        
        prompt = _create_classification_prompt(query, available_tools)
        
        response = self.openai_client.generate_completion(
            prompt=prompt,
            model="gpt-3.5-turbo",
            max_tokens=500,
        )
        
        result = _parse_classification_response(response, query)

        return result


def _create_classification_prompt(query: str, available_tools: List[str]) -> str:
    """
        Create the classification prompt for the LLM.
        
        Args:
            query (str): User query
            available_tools (List[str]): Available tool names
            
        Returns:
            str: Formatted prompt for LLM
        """
    prompt = f"""
You are a helpful assistant that classifies user queries to determine the appropriate tool.
The user query is: {query}
The available tools are: {available_tools}

Query types:
- pdf_analysis: For PDF file analysis
- text_section: For analyzing text sections of papers
- link_analysis: For analyzing links to academic papers
- general_chat: For general conversational queries

You should return the appropriate tool and parameters for the user query.

Respond with a JSON object containing:
{{
    "query_type": "one of the query types above",
    "confidence": 0.0-1.0,
    "suggested_tool": "tool name or null",
    "extracted_parameters": {{
        "query": "extracted search query if applicable",
        "filters": {{
            "statuses": ["list of status filters if mentioned"],
            "phases": ["list of phase filters if mentioned"],
            "studyTypes": ["list of study type filters if mentioned"],
            "providers": ["list of provider/sponsor filters if mentioned"]
        }},
        "other_params": {{}}
    }},
    "reasoning": "brief explanation of classification"
}}
    """
    return prompt

def _parse_classification_response(response: str, original_query: str) -> ClassificationResult:
        """
        Parse the LLM response into a ClassificationResult.
        
        Args:
            response (str): LLM response
            original_query (str): Original user query
            
        Returns:
            ClassificationResult: Parsed classification result
        """
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            # Parse query type
            query_type_str = data.get('query_type', 'general_chat')
            try:
                query_type = QueryType(query_type_str)
            except ValueError:
                query_type = QueryType.GENERAL_CHAT
            
            # Parse confidence
            confidence = float(data.get('confidence', 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
            
            # Parse suggested tool
            suggested_tool = data.get('suggested_tool')
            if suggested_tool == "null" or suggested_tool is None:
                suggested_tool = None
            
            # Parse extracted parameters
            extracted_parameters = data.get('extracted_parameters', {})
            
            # Ensure query is in parameters if not provided
            if 'query' not in extracted_parameters and query_type in [QueryType.SEARCH_QUERY, QueryType.QUESTION]:
                extracted_parameters['query'] = original_query
            
            # Parse reasoning
            reasoning = data.get('reasoning', 'No reasoning provided')
            
            return ClassificationResult(
                query_type=query_type,
                confidence=confidence,
                suggested_tool=suggested_tool,
                extracted_parameters=extracted_parameters,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Error parsing classification response: {str(e)}")
            return _create_fallback_result(original_query)


def _create_fallback_result(original_query: str) -> ClassificationResult:
    """Create a fallback classification result."""
    return ClassificationResult(
        query_type=QueryType.GENERAL_CHAT,
        confidence=0.5,
        suggested_tool="general_chat_tool",
        extracted_parameters={"query": original_query},
        reasoning="Fallback classification due to parsing error"
    )