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
                statistical_tests: Optional[List[str]] = None, evidence_collector=None) -> Dict[str, Any]:
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
            
            # Collect evidence if evidence_collector is provided
            if evidence_collector:
                logger.info("📊 Starting comprehensive statistical evidence collection...")
                
                # Collect evidence from ALL statistical tests used (not just concerns)
                statistical_tests_used = validation_result.get("statistical_tests_used", [])
                logger.info(f"📊 Collecting evidence for {len(statistical_tests_used)} statistical tests")
                
                for test_info in statistical_tests_used:
                    if isinstance(test_info, dict):
                        test_name = test_info.get("test_name", "")
                        test_purpose = test_info.get("purpose", "")
                        test_appropriateness = test_info.get("appropriateness", "")
                        test_justification = test_info.get("justification", "")
                        test_assumptions = test_info.get("assumptions", "")
                        
                        if test_name:
                            # Find the actual text in the paper mentioning this test
                            test_snippet = self._find_text_snippet(text_content, test_name)
                            
                            # Build comprehensive rationale
                            rationale_parts = [f"Statistical Test: {test_name}"]
                            if test_purpose:
                                rationale_parts.append(f"Purpose: {test_purpose}")
                            if test_appropriateness:
                                rationale_parts.append(f"Appropriateness: {test_appropriateness}")
                            if test_justification:
                                rationale_parts.append(f"Justification: {test_justification}")
                            if test_assumptions:
                                rationale_parts.append(f"Assumptions: {test_assumptions}")
                            
                            rationale = " | ".join(rationale_parts)
                            
                            # Determine score impact based on appropriateness
                            if "appropriate" in test_appropriateness.lower() or "suitable" in test_appropriateness.lower():
                                score_impact = 5.0
                            elif "inappropriate" in test_appropriateness.lower() or "unsuitable" in test_appropriateness.lower():
                                score_impact = -8.0
                            else:
                                score_impact = 0.0
                            
                            evidence_collector.add_evidence(
                                category="statistics",
                                text_snippet=test_snippet[:500] if test_snippet else f"{test_name}: {test_purpose[:400]}",
                                rationale=rationale[:1000],
                                confidence=0.8,
                                score_impact=score_impact
                            )
                            logger.info(f"✅ Added evidence for statistical test: {test_name}")
                
                # Collect evidence from ALL concerns (not just top 5)
                concerns = validation_result.get("statistical_concerns", [])
                logger.info(f"📊 Collecting evidence for {len(concerns)} statistical concerns")
                
                for idx, concern in enumerate(concerns):
                    if isinstance(concern, dict):
                        concern_text = concern.get("concern", str(concern))
                        concern_impact = concern.get("impact", "")
                        concern_recommendation = concern.get("recommendation", "")
                        concern_severity = concern.get("severity", "medium")
                        
                        if concern_text and len(concern_text) > 20:
                            concern_snippet = self._find_text_snippet(text_content, concern_text)
                            
                            # Build comprehensive rationale
                            rationale_parts = [f"Statistical Concern: {concern_text}"]
                            if concern_impact:
                                rationale_parts.append(f"Impact: {concern_impact}")
                            if concern_recommendation:
                                rationale_parts.append(f"Recommendation: {concern_recommendation}")
                            
                            rationale = " | ".join(rationale_parts)
                            
                            evidence_collector.add_evidence(
                                category="statistics",
                                text_snippet=concern_snippet[:500] if concern_snippet else concern_text[:500],
                                rationale=rationale[:1000],
                                severity=concern_severity,
                                confidence=0.75,
                                score_impact=-12.0 if concern_severity == "high" else -6.0 if concern_severity == "medium" else -3.0
                            )
                            logger.info(f"✅ Added concern evidence {idx+1}/{len(concerns)}: {concern_severity} severity")
                    elif isinstance(concern, str) and len(concern) > 20:
                        concern_snippet = self._find_text_snippet(text_content, concern)
                        evidence_collector.add_evidence(
                            category="statistics",
                            text_snippet=concern_snippet[:500] if concern_snippet else concern[:500],
                            rationale=f"Statistical Concern: {concern}. This represents a potential issue with the statistical methods, assumptions, or interpretation that may affect the validity of the results.",
                            confidence=0.75,
                            score_impact=-4.0
                        )
                        logger.info(f"✅ Added concern evidence (string format)")
                
                # Collect evidence from test appropriateness assessment
                test_appropriateness = validation_result.get("test_appropriateness", {})
                if isinstance(test_appropriateness, dict):
                    overall_assessment = test_appropriateness.get("overall", "")
                    specific_tests = test_appropriateness.get("specific_tests", {})
                    concerns_list = test_appropriateness.get("concerns", [])
                    missing_tests = test_appropriateness.get("missing_tests", [])
                    
                    if overall_assessment and len(overall_assessment) > 30:
                        assessment_snippet = self._find_text_snippet(text_content, overall_assessment[:50])
                        evidence_collector.add_evidence(
                            category="statistics",
                            text_snippet=assessment_snippet[:500] if assessment_snippet else overall_assessment[:500],
                            rationale=f"Overall Test Appropriateness Assessment: {overall_assessment}. This provides an overall evaluation of whether the statistical tests used are appropriate for the research design and data.",
                            confidence=0.8,
                            score_impact=5.0 if "appropriate" in overall_assessment.lower() else -5.0
                        )
                        logger.info(f"✅ Added overall appropriateness assessment")
                    
                    # Add evidence for each specific test assessment
                    if isinstance(specific_tests, dict):
                        for test_name, test_assessment in specific_tests.items():
                            if isinstance(test_assessment, str) and len(test_assessment) > 30:
                                test_snippet = self._find_text_snippet(text_content, test_name)
                                evidence_collector.add_evidence(
                                    category="statistics",
                                    text_snippet=test_snippet[:500] if test_snippet else f"{test_name}: {test_assessment[:450]}",
                                    rationale=f"Test Appropriateness for {test_name}: {test_assessment}. This evaluates whether this specific statistical test is appropriate for the research question and data characteristics.",
                                    confidence=0.8,
                                    score_impact=3.0 if "appropriate" in test_assessment.lower() else -3.0
                                )
                                logger.info(f"✅ Added specific test assessment: {test_name}")
                    
                    # Add evidence for missing tests
                    for missing_test in missing_tests:
                        if isinstance(missing_test, str) and len(missing_test) > 10:
                            evidence_collector.add_evidence(
                                category="statistics",
                                text_snippet=f"Missing statistical test: {missing_test}",
                                rationale=f"Missing Statistical Test: {missing_test}. This test may have been appropriate for the research design but was not conducted, which could limit the comprehensiveness of the analysis.",
                                confidence=0.7,
                                score_impact=-2.0
                            )
                            logger.info(f"✅ Added missing test evidence: {missing_test}")
                
                # Collect evidence from assumptions checking
                assumptions_met = validation_result.get("assumptions_met", {})
                if isinstance(assumptions_met, dict):
                    normality = assumptions_met.get("normality", {})
                    independence = assumptions_met.get("independence", {})
                    homogeneity = assumptions_met.get("homogeneity", {})
                    overall_assessment = assumptions_met.get("overall_assessment", "")
                    
                    if isinstance(normality, dict):
                        normality_checked = normality.get("checked", "")
                        normality_violations = normality.get("violations", "")
                        if normality_checked and len(normality_checked) > 20:
                            norm_snippet = self._find_text_snippet(text_content, "normality")
                            evidence_collector.add_evidence(
                                category="statistics",
                                text_snippet=norm_snippet[:500] if norm_snippet else f"Normality: {normality_checked[:450]}",
                                rationale=f"Normality Assumption: {normality_checked}. Violations: {normality_violations if normality_violations else 'None reported'}. This describes whether the normality assumption for parametric tests was checked and any violations found.",
                                confidence=0.8,
                                score_impact=3.0 if "checked" in normality_checked.lower() and "violation" not in str(normality_violations).lower() else -3.0
                            )
                            logger.info(f"✅ Added normality assumption evidence")
                    
                    if isinstance(independence, dict):
                        independence_assessed = independence.get("assessed", "")
                        if independence_assessed and len(independence_assessed) > 20:
                            indep_snippet = self._find_text_snippet(text_content, "independence")
                            evidence_collector.add_evidence(
                                category="statistics",
                                text_snippet=indep_snippet[:500] if indep_snippet else f"Independence: {independence_assessed[:450]}",
                                rationale=f"Independence Assumption: {independence_assessed}. This describes whether the independence assumption for statistical tests was assessed.",
                                confidence=0.8,
                                score_impact=2.0 if "assessed" in independence_assessed.lower() else -2.0
                            )
                            logger.info(f"✅ Added independence assumption evidence")
                    
                    if overall_assessment and len(overall_assessment) > 30:
                        overall_snippet = self._find_text_snippet(text_content, overall_assessment[:50])
                        evidence_collector.add_evidence(
                            category="statistics",
                            text_snippet=overall_snippet[:500] if overall_snippet else overall_assessment[:500],
                            rationale=f"Overall Assumption Assessment: {overall_assessment}. This provides a comprehensive evaluation of whether statistical assumptions were properly checked and met.",
                            confidence=0.8,
                            score_impact=4.0 if "met" in overall_assessment.lower() or "satisfied" in overall_assessment.lower() else -4.0
                        )
                        logger.info(f"✅ Added overall assumption assessment")
                
                # Collect evidence from power analysis
                power_analysis = validation_result.get("power_analysis", {})
                if isinstance(power_analysis, dict):
                    power_conducted = power_analysis.get("conducted", "")
                    power_method = power_analysis.get("method", "")
                    power_adequate = power_analysis.get("adequate", "")
                    power_achieved = power_analysis.get("power_achieved", "")
                    
                    if power_conducted and len(power_conducted) > 20:
                        power_snippet = self._find_text_snippet(text_content, "power")
                        rationale_parts = [f"Power Analysis: {power_conducted}"]
                        if power_method:
                            rationale_parts.append(f"Method: {power_method}")
                        if power_adequate:
                            rationale_parts.append(f"Adequacy: {power_adequate}")
                        if power_achieved:
                            rationale_parts.append(f"Power Achieved: {power_achieved}")
                        
                        rationale = " | ".join(rationale_parts)
                        
                        evidence_collector.add_evidence(
                            category="statistics",
                            text_snippet=power_snippet[:500] if power_snippet else f"Power analysis: {power_conducted[:450]}",
                            rationale=f"{rationale}. Power analysis determines whether the study had sufficient sample size to detect meaningful effects.",
                            confidence=0.8,
                            score_impact=8.0 if "yes" in power_conducted.lower() or "conducted" in power_conducted.lower() else -5.0
                        )
                        logger.info(f"✅ Added power analysis evidence")
                
                # Collect evidence from effect size interpretation
                effect_size_interpretation = validation_result.get("effect_size_interpretation", {})
                if isinstance(effect_size_interpretation, dict):
                    effect_reported = effect_size_interpretation.get("reported", "")
                    effect_interpretation = effect_size_interpretation.get("interpretation", "")
                    confidence_intervals = effect_size_interpretation.get("confidence_intervals", "")
                    
                    if effect_reported and len(effect_reported) > 20:
                        effect_snippet = self._find_text_snippet(text_content, "effect size")
                        rationale_parts = [f"Effect Size Reporting: {effect_reported}"]
                        if effect_interpretation:
                            rationale_parts.append(f"Interpretation: {effect_interpretation}")
                        if confidence_intervals:
                            rationale_parts.append(f"Confidence Intervals: {confidence_intervals}")
                        
                        rationale = " | ".join(rationale_parts)
                        
                        evidence_collector.add_evidence(
                            category="statistics",
                            text_snippet=effect_snippet[:500] if effect_snippet else f"Effect size: {effect_reported[:450]}",
                            rationale=f"{rationale}. Effect sizes provide information about the magnitude of effects beyond statistical significance.",
                            confidence=0.8,
                            score_impact=6.0 if "yes" in effect_reported.lower() or "reported" in effect_reported.lower() else -3.0
                        )
                        logger.info(f"✅ Added effect size evidence")
                
                logger.info(f"✅ Statistical evidence collection complete.")
            
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
    
    def _find_text_snippet(self, text_content: str, search_text: str) -> Optional[str]:
        """Find a text snippet in content around search text."""
        if not text_content or not search_text:
            return None
        
        text_lower = text_content.lower()
        search_lower = search_text.lower()
        
        # Try to find search text
        idx = text_lower.find(search_lower)
        if idx == -1:
            # Try finding key words
            words = search_lower.split()[:3]  # First 3 words
            for word in words:
                if len(word) > 4:  # Only meaningful words
                    idx = text_lower.find(word)
                    if idx != -1:
                        break
        
        if idx != -1:
            start = max(0, idx - 100)
            end = min(len(text_content), idx + 200)
            return text_content[start:end].strip()
        
        return None
    
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
