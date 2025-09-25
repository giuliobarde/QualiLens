"""
Research Gap Identifier Tool for QualiLens.

This tool identifies research gaps and future directions in research papers.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from .base_tool import BaseTool, ToolMetadata

# Add the project root to the Python path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from LLM.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class ResearchGapIdentifierTool(BaseTool):
    """
    Research Gap Identifier tool for identifying gaps and future directions.
    """
    
    def __init__(self):
        super().__init__()
        self.openai_client = None
    
    def _get_openai_client(self):
        """Get OpenAI client, initializing it lazily if needed."""
        if self.openai_client is None:
            self.openai_client = OpenAIClient()
        return self.openai_client
    
    def _get_metadata(self) -> ToolMetadata:
        """Return the metadata for this tool."""
        return ToolMetadata(
            name="research_gap_identifier_tool",
            description="Identify research gaps and future research directions",
            parameters={
                "required": ["text_content"],
                "optional": ["gap_types", "future_focus"],
                "properties": {
                    "text_content": {
                        "type": "string",
                        "description": "The text content to analyze for research gaps"
                    },
                    "gap_types": {
                        "type": "array",
                        "description": "Types of gaps to identify",
                        "default": []
                    },
                    "future_focus": {
                        "type": "string",
                        "description": "Focus area for future directions",
                        "default": "general"
                    }
                }
            },
            examples=[
                "Identify research gaps in this paper",
                "Find future research directions",
                "Analyze limitations and gaps"
            ],
            category="gap_analysis"
        )
    
    def execute(self, text_content: str, gap_types: Optional[List[str]] = None,
                future_focus: str = "general") -> Dict[str, Any]:
        """
        Identify research gaps and future directions.
        
        Args:
            text_content: The text content to analyze
            gap_types: Types of gaps to identify
            future_focus: Focus area for future directions
            
        Returns:
            Dict containing research gaps and future directions
        """
        try:
            logger.info(f"Identifying research gaps with focus: {future_focus}")
            
            # Generate gap identification analysis
            gap_analysis = self._identify_research_gaps(text_content, gap_types, future_focus)
            
            return {
                "success": True,
                "research_gaps": gap_analysis.get("research_gaps", []),
                "future_directions": gap_analysis.get("future_directions", []),
                "limitations": gap_analysis.get("limitations", []),
                "unaddressed_questions": gap_analysis.get("unaddressed_questions", []),
                "methodological_gaps": gap_analysis.get("methodological_gaps", []),
                "theoretical_gaps": gap_analysis.get("theoretical_gaps", []),
                "gap_types_analyzed": gap_types or [],
                "future_focus": future_focus,
                "tool_used": "research_gap_identifier_tool"
            }
            
        except Exception as e:
            logger.error(f"Research gap identification failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_used": "research_gap_identifier_tool"
            }
    
    def _identify_research_gaps(self, text_content: str, gap_types: Optional[List[str]], future_focus: str) -> Dict[str, Any]:
        """Identify research gaps and future directions."""
        try:
            prompt = f"""
You are an expert research analyst. Identify research gaps and future directions in this research paper.

PAPER CONTENT:
{text_content[:6000]}

{f"SPECIFIC GAP TYPES TO IDENTIFY: {', '.join(gap_types)}" if gap_types else ""}
FUTURE FOCUS AREA: {future_focus}

Provide comprehensive gap analysis in JSON format:
{{
  "research_gaps": [
    {{
      "gap_type": "Type of gap",
      "description": "Description of the gap",
      "significance": "Why this gap is important",
      "evidence": "Evidence supporting this gap"
    }}
  ],
  "future_directions": [
    {{
      "direction": "Future research direction",
      "rationale": "Why this direction is important",
      "feasibility": "How feasible is this direction?",
      "priority": "High/Medium/Low priority"
    }}
  ],
  "limitations": [
    {{
      "limitation": "Study limitation",
      "impact": "How this affects the findings",
      "addressed": "How this could be addressed in future research"
    }}
  ],
  "unaddressed_questions": [
    {{
      "question": "Unaddressed research question",
      "importance": "Why this question is important",
      "research_approach": "How this could be addressed"
    }}
  ],
  "methodological_gaps": [
    {{
      "gap": "Methodological gap",
      "description": "Description of the methodological limitation",
      "improvement": "How methodology could be improved"
    }}
  ],
  "theoretical_gaps": [
    {{
      "gap": "Theoretical gap",
      "description": "Description of the theoretical limitation",
      "development": "How theory could be developed"
    }}
  ],
  "research_priorities": [
    "Priority 1",
    "Priority 2"
  ],
  "collaboration_opportunities": [
    "Collaboration opportunity 1",
    "Collaboration opportunity 2"
  ],
  "funding_considerations": [
    "Funding consideration 1",
    "Funding consideration 2"
  ]
}}

Focus on identifying specific, actionable gaps and future directions that could advance the field.
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-3.5-turbo",
                max_tokens=2000
            )
            
            if llm_response:
                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return {
                        "research_gaps": [],
                        "future_directions": [],
                        "limitations": [],
                        "unaddressed_questions": [],
                        "methodological_gaps": [],
                        "theoretical_gaps": []
                    }
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Research gap identification analysis failed: {str(e)}")
            return {"error": str(e)}
