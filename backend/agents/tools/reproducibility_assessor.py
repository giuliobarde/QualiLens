"""
Reproducibility Assessor Tool for QualiLens.

This tool evaluates the reproducibility of research studies.
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


class ReproducibilityAssessorTool(BaseTool):
    """
    Reproducibility Assessor tool for evaluating study reproducibility.
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
            name="reproducibility_assessor_tool",
            description="Evaluate the reproducibility of research studies",
            parameters={
                "required": ["text_content"],
                "optional": ["assessment_criteria", "reproducibility_level"],
                "properties": {
                    "text_content": {
                        "type": "string",
                        "description": "The text content to assess for reproducibility"
                    },
                    "assessment_criteria": {
                        "type": "array",
                        "description": "Specific reproducibility criteria to assess",
                        "default": []
                    },
                    "reproducibility_level": {
                        "type": "string",
                        "description": "Level of reproducibility assessment: 'basic', 'detailed'",
                        "default": "detailed"
                    }
                }
            },
            examples=[
                "Assess the reproducibility of this research study",
                "Evaluate if the study can be replicated",
                "Check for sufficient methodological detail"
            ],
            category="reproducibility_analysis"
        )
    
    def execute(self, text_content: str, assessment_criteria: Optional[List[str]] = None,
                reproducibility_level: str = "detailed") -> Dict[str, Any]:
        """
        Assess study reproducibility.
        
        Args:
            text_content: The text content to assess
            assessment_criteria: Specific criteria to assess
            reproducibility_level: Level of assessment
            
        Returns:
            Dict containing reproducibility assessment
        """
        try:
            logger.info(f"Assessing reproducibility with level: {reproducibility_level}")
            
            # Generate reproducibility assessment based on level
            if reproducibility_level == "basic":
                assessment_result = self._assess_basic_reproducibility(text_content, assessment_criteria)
            else:  # detailed
                assessment_result = self._assess_detailed_reproducibility(text_content, assessment_criteria)
            
            return {
                "success": True,
                "reproducibility_score": assessment_result.get("reproducibility_score", 0.0),
                "methodological_detail": assessment_result.get("methodological_detail", ""),
                "data_availability": assessment_result.get("data_availability", ""),
                "code_availability": assessment_result.get("code_availability", ""),
                "reproducibility_barriers": assessment_result.get("reproducibility_barriers", []),
                "recommendations": assessment_result.get("recommendations", []),
                "assessment_criteria": assessment_criteria or [],
                "reproducibility_level": reproducibility_level,
                "tool_used": "reproducibility_assessor_tool"
            }
            
        except Exception as e:
            logger.error(f"Reproducibility assessment failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_used": "reproducibility_assessor_tool"
            }
    
    def _assess_basic_reproducibility(self, text_content: str, assessment_criteria: Optional[List[str]]) -> Dict[str, Any]:
        """Assess basic reproducibility elements."""
        try:
            prompt = f"""
You are an expert research analyst. Provide a basic assessment of the reproducibility of this research study.

PAPER CONTENT:
{text_content[:6000]}

{f"SPECIFIC CRITERIA TO ASSESS: {', '.join(assessment_criteria)}" if assessment_criteria else ""}

Provide basic reproducibility assessment in JSON format:
{{
  "reproducibility_score": 0.0-1.0,  // Calculate actual score based on content analysis
  "methodological_detail": "Assessment of methodological detail provided",
  "data_availability": "Information about data availability",
  "code_availability": "Information about code availability",
  "reproducibility_barriers": [
    "Barrier 1",
    "Barrier 2"
  ],
  "recommendations": [
    "Recommendation 1",
    "Recommendation 2"
  ]
}}

IMPORTANT: Calculate the reproducibility_score based on actual content analysis. Consider:
- Methodological detail provided (0.0-0.3 points)
- Data availability mentioned (0.0-0.3 points) 
- Code availability mentioned (0.0-0.2 points)
- Reproducibility barriers identified (0.0-0.2 points)
- Provide a realistic score between 0.0 and 1.0 based on the actual content

Focus on the most essential reproducibility elements.
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-3.5-turbo",
                max_tokens=1000
            )
            
            if llm_response:
                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    return {"error": "Could not parse reproducibility assessment"}
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Basic reproducibility assessment failed: {str(e)}")
            return {"error": str(e)}
    
    def _assess_detailed_reproducibility(self, text_content: str, assessment_criteria: Optional[List[str]]) -> Dict[str, Any]:
        """Assess detailed reproducibility elements."""
        try:
            prompt = f"""
You are an expert research analyst. Provide a detailed assessment of the reproducibility of this research study.

PAPER CONTENT:
{text_content[:6000]}

{f"SPECIFIC CRITERIA TO ASSESS: {', '.join(assessment_criteria)}" if assessment_criteria else ""}

Provide detailed reproducibility assessment in JSON format:
{{
  "reproducibility_score": 0.0-1.0,  // Calculate actual score based on content analysis
  "methodological_detail": {{
    "sufficient": "Is methodological detail sufficient for replication?",
    "missing_elements": ["Missing methodological elements"],
    "clarity": "How clear are the methodological descriptions?",
    "step_by_step": "Are procedures described step-by-step?"
  }},
  "data_availability": {{
    "raw_data": "Is raw data available?",
    "processed_data": "Is processed data available?",
    "data_format": "What format is the data in?",
    "access_restrictions": "Any access restrictions?",
    "data_quality": "Assessment of data quality"
  }},
  "code_availability": {{
    "analysis_code": "Is analysis code available?",
    "software_used": "What software was used?",
    "version_control": "Is version control used?",
    "documentation": "Is code documented?",
    "dependencies": "Are dependencies specified?"
  }},
  "reproducibility_barriers": [
    {{
      "barrier": "Description of barrier",
      "severity": "low/medium/high",
      "impact": "How this affects reproducibility"
    }}
  ],
  "environmental_factors": {{
    "software_environment": "Software environment requirements",
    "hardware_requirements": "Hardware requirements",
    "external_dependencies": "External dependencies",
    "version_specificity": "Version specificity issues"
  }},
  "reproducibility_indicators": {{
    "open_science_practices": "Open science practices used",
    "pre_registration": "Was the study pre-registered?",
    "peer_review": "Was code/data peer reviewed?",
    "replication_attempts": "Any replication attempts mentioned?"
  }},
  "recommendations": [
    "Detailed recommendation 1",
    "Detailed recommendation 2"
  ],
  "overall_assessment": "Overall reproducibility assessment"
}}

Provide comprehensive analysis of all reproducibility aspects.
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
                    return {"error": "Could not parse detailed reproducibility assessment"}
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Detailed reproducibility assessment failed: {str(e)}")
            return {"error": str(e)}
