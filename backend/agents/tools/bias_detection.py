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
                severity_threshold: str = "low", evidence_collector=None) -> Dict[str, Any]:
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
            
            # Collect evidence if evidence_collector is provided
            if evidence_collector:
                detected_biases = bias_analysis.get("detected_biases", [])
                for bias in detected_biases:
                    evidence_collector.add_evidence(
                        category="bias",
                        text_snippet=bias.get("evidence", bias.get("description", "")),
                        rationale=bias.get("verification_reasoning", bias.get("description", "")),
                        severity=bias.get("severity", "medium"),
                        confidence=0.8 if bias.get("severity") == "high" else 0.6,
                        score_impact=-20.0 if bias.get("severity") == "high" else -10.0
                    )
            
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
        """
        Detect various types of biases in the research paper using two-step chain-of-thought reasoning.

        Step 1: Brainstorm potential biases (creative, temperature > 0)
        Step 2: Verify and analyze each potential bias (deterministic, temperature = 0)
        """
        try:
            # STEP 1: Brainstorm potential biases (more creative)
            logger.info("Step 1: Brainstorming potential biases...")
            brainstorm_prompt = f"""
You are an expert research methodologist specializing in bias detection. Your task is to BRAINSTORM potential biases in this research paper.

PAPER CONTENT:
{text_content[:6000]}

BIAS TYPES TO CONSIDER: {', '.join(bias_types)}

BRAINSTORMING INSTRUCTIONS:
- Be thorough and creative in identifying POTENTIAL biases
- This is a brainstorming phase - include anything that MIGHT be a bias
- Provide your reasoning for why each item might be a bias
- Include edge cases and subtle biases
- Don't worry about false positives at this stage

For each potential bias, think through:
1. What aspect of the study suggests this bias?
2. What is the specific evidence?
3. How would this bias affect the results if it exists?

Provide your brainstorming in JSON format:
{{
  "potential_biases": [
    {{
      "bias_type": "selection_bias | measurement_bias | confounding_bias | publication_bias | reporting_bias",
      "initial_assessment": "Why you think this MIGHT be a bias",
      "evidence_snippet": "Specific quote or aspect from the paper",
      "potential_severity": "low | medium | high",
      "reasoning": "Your chain-of-thought reasoning"
    }}
  ]
}}

BIAS DETECTION GUIDELINES:
1. Selection Bias: Non-random sampling, exclusion criteria, recruitment methods, sample representativeness
2. Measurement Bias: Measurement errors, instrument bias, observer bias, recall bias, social desirability
3. Confounding Bias: Uncontrolled variables, lack of randomization, missing covariates
4. Publication Bias: Selective reporting, missing negative results, outcome switching
5. Reporting Bias: Incomplete reporting, selective outcome reporting, data dredging

Be comprehensive - we'll verify these in the next step.
"""

            # Step 1: Creative brainstorming with temperature=0.3
            brainstorm_response = self._get_openai_client().generate_completion(
                prompt=brainstorm_prompt,
                model="gpt-3.5-turbo",
                max_tokens=2000,
                temperature=0.3  # Some creativity for brainstorming
            )

            if not brainstorm_response:
                return {"error": "No response from Step 1 (brainstorming)"}

            try:
                brainstormed = json.loads(brainstorm_response)
                potential_biases = brainstormed.get("potential_biases", [])
                logger.info(f"Step 1 complete: {len(potential_biases)} potential biases identified")
            except json.JSONDecodeError:
                logger.error("Failed to parse brainstorming response")
                return {"error": "Failed to parse brainstorming results"}

            # STEP 2: Verify and analyze each potential bias (deterministic)
            logger.info("Step 2: Verifying and analyzing potential biases...")
            verification_prompt = f"""
You are a rigorous research quality assessor. You will now VERIFY each potential bias identified in the brainstorming phase.

PAPER CONTENT:
{text_content[:6000]}

POTENTIAL BIASES TO VERIFY:
{json.dumps(potential_biases, indent=2)}

SEVERITY THRESHOLD: {severity_threshold}

VERIFICATION INSTRUCTIONS:
For each potential bias, you must:
1. Carefully examine the evidence
2. Determine if it is a TRUE bias or a false positive
3. If it's a true bias, assess its severity and impact
4. Provide clear justification for your decision

Use chain-of-thought reasoning:
- ANALYZE: What does the evidence actually show?
- EVALUATE: Is this a genuine bias or a limitation?
- ASSESS: If it's a bias, how severe is it?
- CONCLUDE: Should this be included in the final list?

Provide your verification in JSON format:
{{
  "detected_biases": [
    {{
      "bias_type": "type from potential list",
      "description": "Clear description of the confirmed bias",
      "evidence": "Specific evidence from the paper",
      "severity": "low | medium | high",
      "impact": "How this bias affects the study's validity and results",
      "verification_reasoning": "Your chain-of-thought for why this IS a genuine bias"
    }}
  ],
  "rejected_biases": [
    {{
      "bias_type": "type from potential list",
      "rejection_reasoning": "Why this is NOT a genuine bias after verification"
    }}
  ],
  "bias_summary": "Overall summary of confirmed biases",
  "limitations": ["Study limitations that are not biases"],
  "confounding_factors": ["Uncontrolled variables that could affect results"],
  "severity_scores": {{
    "selection_bias": "none | low | medium | high",
    "measurement_bias": "none | low | medium | high",
    "confounding_bias": "none | low | medium | high",
    "publication_bias": "none | low | medium | high",
    "reporting_bias": "none | low | medium | high"
  }},
  "recommendations": ["Recommendations to address the confirmed biases"]
}}

VERIFICATION STANDARDS:
- Only include biases that meet or exceed the severity threshold: {severity_threshold}
- Be conservative - when in doubt, explain why in rejected_biases
- Provide specific evidence, not speculation
- Distinguish between biases and general limitations
"""

            # Step 2: Deterministic verification with temperature=0.0
            verification_response = self._get_openai_client().generate_completion(
                prompt=verification_prompt,
                model="gpt-3.5-turbo",
                max_tokens=2500,
                temperature=0.0  # Deterministic for consistency
            )

            if verification_response:
                try:
                    result = json.loads(verification_response)
                    logger.info(f"Step 2 complete: {len(result.get('detected_biases', []))} biases confirmed, {len(result.get('rejected_biases', []))} rejected")
                    return result
                except json.JSONDecodeError:
                    logger.error("Failed to parse verification response")
                    # Fallback if JSON parsing fails
                    return {
                        "detected_biases": [],
                        "rejected_biases": [],
                        "bias_summary": verification_response,
                        "limitations": [],
                        "confounding_factors": [],
                        "severity_scores": {},
                        "recommendations": []
                    }
            else:
                return {"error": "No response from Step 2 (verification)"}

        except Exception as e:
            logger.error(f"Bias detection analysis failed: {str(e)}")
            return {"error": str(e)}
