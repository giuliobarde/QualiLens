"""
Bias Detection Tool for QualiLens.

This tool identifies potential biases, limitations, and confounding factors
in research papers to provide critical quality assessment.
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


class BiasDetectionTool(BaseTool):
    """
    Bias Detection tool for identifying potential biases and limitations in research papers.
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
            name="bias_detection_tool",
            description="Detect potential biases, limitations, and confounding factors in research papers",
            parameters={
                "required": ["text_content"],
                "optional": ["bias_types", "severity_threshold"],
                "properties": {
                    "text_content": {
                        "type": "string",
                        "description": "The text content to analyze for biases"
                    },
                    "bias_types": {
                        "type": "array",
                        "description": "Types of biases to detect: 'selection', 'measurement', 'confounding', 'publication', 'reporting'",
                        "default": ["selection", "measurement", "confounding", "publication", "reporting"]
                    },
                    "severity_threshold": {
                        "type": "string",
                        "description": "Minimum severity to report: 'low', 'medium', 'high'",
                        "default": "low"
                    }
                }
            },
            examples=[
                "Detect potential biases in this research paper",
                "Identify selection bias and confounding factors",
                "Analyze for publication bias and reporting bias"
            ],
            category="quality_assessment"
        )
    
    def execute(self, text_content: str, bias_types: Optional[List[str]] = None, 
                severity_threshold: str = "low") -> Dict[str, Any]:
        """
        Detect potential biases and limitations in research papers.
        
        Args:
            text_content: The text content to analyze
            bias_types: Types of biases to detect
            severity_threshold: Minimum severity to report
            
        Returns:
            Dict containing detected biases and their analysis
        """
        try:
            logger.info(f"Detecting biases with types: {bias_types}, threshold: {severity_threshold}")
            
            # Default bias types if not specified
            if bias_types is None:
                bias_types = ["selection", "measurement", "confounding", "publication", "reporting"]
            
            # Generate bias detection analysis
            bias_analysis = self._detect_biases(text_content, bias_types, severity_threshold)
            
            return {
                "success": True,
                "detected_biases": bias_analysis.get("detected_biases", []),
                "bias_summary": bias_analysis.get("bias_summary", ""),
                "limitations": bias_analysis.get("limitations", []),
                "confounding_factors": bias_analysis.get("confounding_factors", []),
                "severity_scores": bias_analysis.get("severity_scores", {}),
                "recommendations": bias_analysis.get("recommendations", []),
                "bias_types_analyzed": bias_types,
                "severity_threshold": severity_threshold,
                "tool_used": "bias_detection_tool"
            }
            
        except Exception as e:
            logger.error(f"Bias detection failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_used": "bias_detection_tool"
            }
    
    def _detect_biases(self, text_content: str, bias_types: List[str], severity_threshold: str) -> Dict[str, Any]:
        """Detect various types of biases in the research paper."""
        try:
            prompt = f"""
You are an expert research analyst specializing in bias detection and quality assessment. 
Analyze this research paper for potential biases and limitations.

PAPER CONTENT:
{text_content[:6000]}

BIAS TYPES TO ANALYZE: {', '.join(bias_types)}
SEVERITY THRESHOLD: {severity_threshold}

Please analyze the paper for potential biases and provide a comprehensive assessment in JSON format:
{{
  "detected_biases": [
    {{
      "bias_type": "selection_bias",
      "description": "Description of the bias found",
      "evidence": "Specific evidence from the paper",
      "severity": "low/medium/high",
      "impact": "How this bias affects the results"
    }}
  ],
  "bias_summary": "Overall summary of bias assessment",
  "limitations": [
    "Limitation 1",
    "Limitation 2"
  ],
  "confounding_factors": [
    "Confounding factor 1",
    "Confounding factor 2"
  ],
  "severity_scores": {{
    "selection_bias": "low/medium/high",
    "measurement_bias": "low/medium/high",
    "confounding_bias": "low/medium/high",
    "publication_bias": "low/medium/high",
    "reporting_bias": "low/medium/high"
  }},
  "recommendations": [
    "Recommendation 1",
    "Recommendation 2"
  ]
}}

BIAS DETECTION GUIDELINES:
1. Selection Bias: Look for non-random sampling, exclusion criteria, recruitment methods
2. Measurement Bias: Check for measurement errors, instrument bias, observer bias
3. Confounding Bias: Identify uncontrolled variables that could affect results
4. Publication Bias: Look for selective reporting, missing negative results
5. Reporting Bias: Check for incomplete reporting, selective outcome reporting

Focus on identifying specific evidence of biases and their potential impact on the study's validity.
Only report biases that meet or exceed the severity threshold.
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-3.5-turbo",
                max_tokens=2000
            )
            
            if llm_response:
                try:
                    result = json.loads(llm_response)
                    return result
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return {
                        "detected_biases": [],
                        "bias_summary": llm_response,
                        "limitations": [],
                        "confounding_factors": [],
                        "severity_scores": {},
                        "recommendations": []
                    }
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Bias detection analysis failed: {str(e)}")
            return {"error": str(e)}
