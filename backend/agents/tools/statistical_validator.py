"""
Statistical Validator Tool for QualiLens.

This tool validates statistical methods, tests, and results in research papers.
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


class StatisticalValidatorTool(BaseTool):
    """
    Statistical Validator tool for validating statistical methods and results.
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
            name="statistical_validator_tool",
            description="Validate statistical methods, tests, and results in research papers",
            parameters={
                "required": ["text_content"],
                "optional": ["validation_level", "statistical_tests"],
                "properties": {
                    "text_content": {
                        "type": "string",
                        "description": "The text content to validate statistically"
                    },
                    "validation_level": {
                        "type": "string",
                        "description": "Level of validation: 'basic', 'detailed', 'comprehensive'",
                        "default": "detailed"
                    },
                    "statistical_tests": {
                        "type": "array",
                        "description": "Specific statistical tests to validate",
                        "default": []
                    }
                }
            },
            examples=[
                "Validate the statistical methods used in this study",
                "Check if the statistical tests are appropriate",
                "Verify statistical assumptions and power analysis"
            ],
            category="statistical_analysis"
        )
    
    def execute(self, text_content: str, validation_level: str = "detailed",
                statistical_tests: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate statistical methods and results.
        
        Args:
            text_content: The text content to validate
            validation_level: Level of statistical validation
            statistical_tests: Specific tests to validate
            
        Returns:
            Dict containing statistical validation results
        """
        try:
            logger.info("Validating statistics with comprehensive level")
            
            # Always use comprehensive statistical validation
            validation_result = self._validate_comprehensive_statistics(text_content, statistical_tests)
            
            return {
                "success": True,
                "statistical_tests_used": validation_result.get("statistical_tests_used", []),
                "test_appropriateness": validation_result.get("test_appropriateness", {}),
                "assumptions_met": validation_result.get("assumptions_met", {}),
                "power_analysis": validation_result.get("power_analysis", {}),
                "effect_size_interpretation": validation_result.get("effect_size_interpretation", ""),
                "statistical_concerns": validation_result.get("statistical_concerns", []),
                "recommendations": validation_result.get("recommendations", []),
                "validation_level": "comprehensive",
                "statistical_tests_requested": statistical_tests or [],
                "tool_used": "statistical_validator_tool"
            }
            
        except Exception as e:
            logger.error(f"Statistical validation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_used": "statistical_validator_tool"
            }
    
    def _validate_comprehensive_statistics(self, text_content: str, statistical_tests: Optional[List[str]]) -> Dict[str, Any]:
        """Validate comprehensive statistical elements."""
        try:
            prompt = f"""
You are an expert statistician. Provide a comprehensive validation of the statistical methods used in this research.

PAPER CONTENT:
{text_content[:6000]}

{f"SPECIFIC TESTS TO VALIDATE: {', '.join(statistical_tests)}" if statistical_tests else ""}

Provide comprehensive statistical validation in JSON format:
{{
  "statistical_tests_used": [
    {{
      "test_name": "Test name",
      "purpose": "What this test was used for",
      "appropriateness": "How appropriate this test is",
      "assumptions": "Statistical assumptions for this test",
      "justification": "Why this test was chosen",
      "alternatives": "Alternative tests that could have been used"
    }}
  ],
  "test_appropriateness": {{
    "overall": "Overall assessment of test appropriateness",
    "specific_tests": {{
      "test1": "Detailed assessment of test 1",
      "test2": "Detailed assessment of test 2"
    }},
    "concerns": ["Specific concerns about test selection"],
    "alternatives": ["Alternative approaches that could have been used"],
    "missing_tests": ["Important tests that were not conducted"]
  }},
  "assumptions_met": {{
    "normality": {{
      "checked": "Were normality assumptions checked?",
      "method": "How were they checked?",
      "violations": "Any violations found?",
      "corrections": "Any corrections applied?"
    }},
    "independence": {{
      "assessed": "Were independence assumptions assessed?",
      "violations": "Any violations found?",
      "corrections": "Any corrections applied?"
    }},
    "homogeneity": {{
      "checked": "Were homogeneity assumptions checked?",
      "method": "How were they checked?",
      "violations": "Any violations found?",
      "corrections": "Any corrections applied?"
    }},
    "other_assumptions": "Other statistical assumptions checked",
    "overall_assessment": "Overall assessment of assumption checking"
  }},
  "power_analysis": {{
    "conducted": "Was power analysis conducted?",
    "method": "What method was used?",
    "effect_size": "What effect size was assumed?",
    "power_achieved": "What power was achieved?",
    "adequate": "Was the sample size adequate?",
    "post_hoc": "Was post-hoc power analysis conducted?",
    "limitations": "Any limitations in power analysis?"
  }},
  "effect_size_interpretation": {{
    "reported": "Were effect sizes reported?",
    "interpretation": "How were they interpreted?",
    "clinical_significance": "Clinical significance discussed?",
    "practical_significance": "Practical significance discussed?",
    "confidence_intervals": "Were confidence intervals reported?"
  }},
  "statistical_concerns": [
    {{
      "concern": "Description of concern",
      "severity": "low/medium/high",
      "impact": "How this affects the results",
      "recommendation": "How to address this concern"
    }}
  ],
  "recommendations": [
    "Comprehensive recommendation 1",
    "Comprehensive recommendation 2"
  ],
  "overall_quality": "Overall statistical quality assessment"
}}

Provide the most comprehensive statistical validation possible.
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-3.5-turbo",
                max_tokens=2500,
                temperature=0.0  # Deterministic for consistency
            )
            
            if llm_response:
                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    return {"error": "Could not parse comprehensive statistical validation"}
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Comprehensive statistical validation failed: {str(e)}")
            return {"error": str(e)}
