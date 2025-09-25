"""
Methodology Analyzer Tool for QualiLens.

This tool provides deep analysis of research methodology, study design,
sample characteristics, and methodological quality assessment.
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


class MethodologyAnalyzerTool(BaseTool):
    """
    Methodology Analyzer tool for comprehensive analysis of research methodology.
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
            name="methodology_analyzer_tool",
            description="Analyze research methodology, study design, sample characteristics, and methodological quality",
            parameters={
                "required": ["text_content"],
                "optional": ["analysis_depth", "focus_areas"],
                "properties": {
                    "text_content": {
                        "type": "string",
                        "description": "The text content to analyze for methodology"
                    },
                    "analysis_depth": {
                        "type": "string",
                        "description": "Depth of analysis: 'basic', 'detailed', 'comprehensive'",
                        "default": "detailed"
                    },
                    "focus_areas": {
                        "type": "array",
                        "description": "Specific methodology areas to focus on",
                        "default": []
                    }
                }
            },
            examples=[
                "Analyze the methodology of this research study",
                "Evaluate the study design and sample characteristics",
                "Assess the methodological quality and validity"
            ],
            category="methodology_analysis"
        )
    
    def execute(self, text_content: str, analysis_depth: str = "detailed", 
                focus_areas: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze research methodology comprehensively.
        
        Args:
            text_content: The text content to analyze
            analysis_depth: Depth of methodology analysis
            focus_areas: Specific areas to focus on
            
        Returns:
            Dict containing methodology analysis results
        """
        try:
            logger.info(f"Analyzing methodology with depth: {analysis_depth}")
            
            # Generate methodology analysis based on depth
            if analysis_depth == "basic":
                methodology_result = self._analyze_basic_methodology(text_content, focus_areas)
            elif analysis_depth == "comprehensive":
                methodology_result = self._analyze_comprehensive_methodology(text_content, focus_areas)
            else:  # detailed
                methodology_result = self._analyze_detailed_methodology(text_content, focus_areas)
            
            return {
                "success": True,
                "study_design": methodology_result.get("study_design", ""),
                "sample_characteristics": methodology_result.get("sample_characteristics", {}),
                "data_collection": methodology_result.get("data_collection", {}),
                "analysis_methods": methodology_result.get("analysis_methods", {}),
                "validity_measures": methodology_result.get("validity_measures", {}),
                "ethical_considerations": methodology_result.get("ethical_considerations", {}),
                "methodological_strengths": methodology_result.get("methodological_strengths", []),
                "methodological_weaknesses": methodology_result.get("methodological_weaknesses", []),
                "quality_rating": methodology_result.get("quality_rating", ""),
                "analysis_depth": analysis_depth,
                "focus_areas": focus_areas or [],
                "tool_used": "methodology_analyzer_tool"
            }
            
        except Exception as e:
            logger.error(f"Methodology analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_used": "methodology_analyzer_tool"
            }
    
    def _analyze_basic_methodology(self, text_content: str, focus_areas: Optional[List[str]]) -> Dict[str, Any]:
        """Analyze basic methodology elements."""
        try:
            prompt = f"""
You are an expert research analyst. Provide a basic analysis of the research methodology.

PAPER CONTENT:
{text_content[:6000]}

{f"SPECIFIC FOCUS AREAS: {', '.join(focus_areas)}" if focus_areas else ""}

Provide basic methodology analysis in JSON format:
{{
  "study_design": "Type of study design (e.g., randomized controlled trial, cohort study, case-control)",
  "sample_characteristics": {{
    "sample_size": "Number of participants",
    "demographics": "Basic participant demographics",
    "inclusion_criteria": "Who was included",
    "exclusion_criteria": "Who was excluded"
  }},
  "data_collection": {{
    "methods": "How data was collected",
    "instruments": "What tools were used"
  }},
  "analysis_methods": "Basic statistical or analytical methods used",
  "quality_rating": "Overall methodology quality (High/Medium/Low)"
}}

Focus on the most essential methodological elements.
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
                    return {"error": "Could not parse methodology analysis"}
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Basic methodology analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_detailed_methodology(self, text_content: str, focus_areas: Optional[List[str]]) -> Dict[str, Any]:
        """Analyze detailed methodology elements."""
        try:
            prompt = f"""
You are an expert research analyst. Provide a detailed analysis of the research methodology.

PAPER CONTENT:
{text_content[:6000]}

{f"SPECIFIC FOCUS AREAS: {', '.join(focus_areas)}" if focus_areas else ""}

Provide detailed methodology analysis in JSON format:
{{
  "study_design": "Detailed description of study design and rationale",
  "sample_characteristics": {{
    "sample_size": "Number of participants with justification",
    "demographics": "Detailed participant demographics",
    "inclusion_criteria": "Specific inclusion criteria",
    "exclusion_criteria": "Specific exclusion criteria",
    "recruitment_method": "How participants were recruited",
    "power_analysis": "Sample size justification if provided"
  }},
  "data_collection": {{
    "methods": "Detailed data collection methods",
    "instruments": "Specific instruments and tools used",
    "procedures": "Data collection procedures",
    "timeline": "Data collection timeline"
  }},
  "analysis_methods": {{
    "statistical_tests": "Statistical tests used",
    "software": "Software used for analysis",
    "assumptions": "Statistical assumptions checked"
  }},
  "validity_measures": {{
    "internal_validity": "Measures to ensure internal validity",
    "external_validity": "Measures to ensure external validity",
    "reliability": "Reliability measures"
  }},
  "ethical_considerations": {{
    "approval": "Ethical approval details",
    "consent": "Informed consent procedures",
    "privacy": "Privacy and confidentiality measures"
  }},
  "methodological_strengths": [
    "Strength 1",
    "Strength 2"
  ],
  "methodological_weaknesses": [
    "Weakness 1",
    "Weakness 2"
  ],
  "quality_rating": "Overall methodology quality (High/Medium/Low) with justification"
}}

Provide comprehensive analysis of all methodological aspects.
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
                    return {"error": "Could not parse detailed methodology analysis"}
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Detailed methodology analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_comprehensive_methodology(self, text_content: str, focus_areas: Optional[List[str]]) -> Dict[str, Any]:
        """Analyze comprehensive methodology elements."""
        try:
            prompt = f"""
You are an expert research analyst. Provide a comprehensive analysis of the research methodology.

PAPER CONTENT:
{text_content[:6000]}

{f"SPECIFIC FOCUS AREAS: {', '.join(focus_areas)}" if focus_areas else ""}

Provide comprehensive methodology analysis in JSON format:
{{
  "study_design": {{
    "type": "Type of study design",
    "rationale": "Why this design was chosen",
    "appropriateness": "How appropriate this design is for the research question",
    "alternatives": "Alternative designs that could have been used"
  }},
  "sample_characteristics": {{
    "sample_size": "Number of participants with power analysis",
    "demographics": "Detailed participant demographics",
    "inclusion_criteria": "Specific inclusion criteria",
    "exclusion_criteria": "Specific exclusion criteria",
    "recruitment_method": "Detailed recruitment process",
    "retention_rate": "Participant retention if applicable",
    "representativeness": "How representative the sample is"
  }},
  "data_collection": {{
    "methods": "Comprehensive data collection methods",
    "instruments": "All instruments and tools used with validation",
    "procedures": "Detailed data collection procedures",
    "timeline": "Data collection timeline",
    "quality_control": "Quality control measures"
  }},
  "analysis_methods": {{
    "statistical_tests": "All statistical tests used with justification",
    "software": "Software and tools used",
    "assumptions": "Statistical assumptions checked",
    "effect_sizes": "Effect size calculations if applicable",
    "confidence_intervals": "Confidence interval reporting"
  }},
  "validity_measures": {{
    "internal_validity": "Comprehensive internal validity measures",
    "external_validity": "External validity considerations",
    "reliability": "Reliability measures and coefficients",
    "bias_control": "Measures to control for bias"
  }},
  "ethical_considerations": {{
    "approval": "Ethical approval details and oversight",
    "consent": "Informed consent procedures",
    "privacy": "Privacy and confidentiality measures",
    "data_protection": "Data protection measures"
  }},
  "methodological_strengths": [
    "Comprehensive strength 1",
    "Comprehensive strength 2"
  ],
  "methodological_weaknesses": [
    "Comprehensive weakness 1",
    "Comprehensive weakness 2"
  ],
  "quality_rating": "Detailed quality assessment with specific criteria",
  "recommendations": [
    "Recommendation for improvement 1",
    "Recommendation for improvement 2"
  ]
}}

Provide the most comprehensive analysis possible of all methodological aspects.
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-3.5-turbo",
                max_tokens=2500
            )
            
            if llm_response:
                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    return {"error": "Could not parse comprehensive methodology analysis"}
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Comprehensive methodology analysis failed: {str(e)}")
            return {"error": str(e)}
