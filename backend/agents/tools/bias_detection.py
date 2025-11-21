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
                logger.info(f"📊 Collecting evidence for {len(detected_biases)} detected biases")

                for idx, bias in enumerate(detected_biases):
                    # PRIORITY 1: Use the full_section_text (which contains the complete biased section)
                    evidence_text = bias.get("full_section_text", "")

                    # PRIORITY 2: Use the evidence field or text_excerpt
                    if not evidence_text or len(evidence_text) < 50:
                        evidence_text = bias.get("evidence", "")

                    if not evidence_text or len(evidence_text) < 50:
                        evidence_text = bias.get("text_excerpt", "")

                    # PRIORITY 3: Use description as fallback
                    if not evidence_text or len(evidence_text) < 50:
                        evidence_text = bias.get("description", "")

                    # PRIORITY 4 (Last resort): Search for relevant text in the paper
                    if not evidence_text or len(evidence_text) < 50:
                        bias_type = bias.get("bias_type", "").lower()
                        section_name = bias.get("section_name", "")

                        # Search for section name or bias type keywords in content
                        if text_content:
                            # Try to find the section in the text
                            search_terms = []
                            if section_name:
                                # Try to find a section header or the section name in the text
                                search_terms.append(section_name.lower())

                            # Add bias type keywords
                            keywords = bias_type.split("_") if "_" in bias_type else [bias_type]
                            search_terms.extend(keywords)

                            for term in search_terms:
                                if term in text_content.lower():
                                    # Find context around the term - extract a larger section
                                    idx_pos = text_content.lower().find(term)
                                    start = max(0, idx_pos - 300)
                                    end = min(len(text_content), idx_pos + 700)
                                    evidence_text = text_content[start:end].strip()
                                    logger.info(f"   Found evidence for bias {idx+1} using search term '{term}' (extracted {len(evidence_text)} chars)")
                                    break

                    # Log the source and length of evidence text
                    if bias.get("full_section_text"):
                        logger.info(f"   Using full_section_text for bias {idx+1} ({len(evidence_text)} characters)")
                    elif bias.get("evidence"):
                        logger.info(f"   Using evidence field for bias {idx+1} ({len(evidence_text)} characters)")
                    else:
                        logger.info(f"   Using fallback text for bias {idx+1} ({len(evidence_text)} characters)")

                    # Calculate score impact based on severity
                    severity = bias.get("severity", "medium")
                    if severity == "high":
                        score_impact = -25.0
                        confidence = 0.85
                    elif severity == "medium":
                        score_impact = -12.0
                        confidence = 0.70
                    else:
                        score_impact = -6.0
                        confidence = 0.60

                    # Additional penalty for critical bias types
                    bias_type = bias.get("bias_type", "").lower()
                    if any(bt in bias_type for bt in ["selection", "confounding", "publication"]):
                        score_impact -= 5.0
                        logger.info(f"   Applied additional penalty for critical bias type: {bias_type}")

                    # Build comprehensive rationale using chain-of-thought reasoning
                    section_name = bias.get("section_name", "Unknown section")
                    verification_reasoning = bias.get("verification_reasoning", "")
                    why_bias = bias.get("why_bias_not_limitation", "")
                    impact = bias.get("impact", "")

                    # Construct detailed rationale
                    rationale_parts = [f"Bias detected in section: {section_name}"]

                    if verification_reasoning:
                        rationale_parts.append(f"Reasoning: {verification_reasoning}")

                    if why_bias:
                        rationale_parts.append(f"Why this is bias (not limitation): {why_bias}")

                    if impact:
                        rationale_parts.append(f"Impact: {impact}")

                    full_rationale = " | ".join(rationale_parts)

                    # Add evidence to collector
                    # Don't truncate if we have full_section_text - preserve the complete context
                    max_snippet_length = 1500 if bias.get("full_section_text") else 400
                    text_to_add = evidence_text[:max_snippet_length] if evidence_text else bias.get("description", "")[:400]

                    # Add ellipsis if truncated
                    if evidence_text and len(evidence_text) > max_snippet_length:
                        text_to_add = text_to_add + "... [truncated for display]"
                        logger.info(f"   ⚠️  Evidence text truncated from {len(evidence_text)} to {max_snippet_length} chars for bias {idx+1}")

                    evidence_id = evidence_collector.add_evidence(
                        category="bias",
                        text_snippet=text_to_add,
                        rationale=full_rationale[:1200],  # Increased length for chain-of-thought
                        severity=severity,
                        confidence=confidence,
                        score_impact=score_impact
                    )

                    logger.info(f"✅ Added evidence {evidence_id} for bias: {section_name} ({bias_type}, {severity} severity, impact: {score_impact:.1f}, text_length: {len(text_to_add)} chars)")
                
                # Also collect evidence from limitations (these are important for peer reviewers)
                limitations = bias_analysis.get("limitations", [])
                logger.info(f"📊 Collecting evidence for {len(limitations)} study limitations")
                
                for idx, limitation in enumerate(limitations):
                    if isinstance(limitation, str) and len(limitation) > 30:
                        # Try to find this limitation in the paper
                        limitation_snippet = self._find_limitation_text(text_content, limitation)
                        evidence_collector.add_evidence(
                            category="bias",
                            text_snippet=limitation_snippet[:500] if limitation_snippet else limitation[:500],
                            rationale=f"Study Limitation: {limitation}. This represents a constraint or weakness in the study design that may affect the interpretation or generalizability of the findings, but is not necessarily a systematic bias.",
                            confidence=0.7,
                            severity="low",
                            score_impact=-2.0
                        )
                        logger.info(f"✅ Added limitation evidence {idx+1}/{len(limitations)}")
                
                # Collect evidence from confounding factors
                confounding_factors = bias_analysis.get("confounding_factors", [])
                logger.info(f"📊 Collecting evidence for {len(confounding_factors)} confounding factors")
                
                for idx, confounder in enumerate(confounding_factors):
                    if isinstance(confounder, str) and len(confounder) > 30:
                        # Try to find this confounder in the paper
                        confounder_snippet = self._find_limitation_text(text_content, confounder)
                        evidence_collector.add_evidence(
                            category="bias",
                            text_snippet=confounder_snippet[:500] if confounder_snippet else confounder[:500],
                            rationale=f"Confounding Factor: {confounder}. This represents a variable that may be associated with both the exposure and outcome, potentially distorting the true relationship. This is important for peer reviewers to verify whether confounding was adequately controlled.",
                            confidence=0.75,
                            severity="medium",
                            score_impact=-8.0
                        )
                        logger.info(f"✅ Added confounding factor evidence {idx+1}/{len(confounding_factors)}")
                
                logger.info(f"✅ Bias evidence collection complete. Total biases: {len(detected_biases)}, Limitations: {len(limitations)}, Confounders: {len(confounding_factors)}")
            
            return {
                "success": True,
                "detected_biases": bias_analysis.get("detected_biases", []),
                "rejected_sections": bias_analysis.get("rejected_sections", bias_analysis.get("rejected_biases", [])),
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
        Detect various types of biases in the research paper using a comprehensive two-phase approach.

        PHASE 1: Section-Level Analysis
        - Analyze the entire paper to identify sections that could potentially contain biases
        - Break down the paper into meaningful sections (methodology, results, discussion, etc.)
        - Flag sections that show indicators of potential bias

        PHASE 2: Detailed Verification with Chain-of-Thought
        - For each flagged section, perform detailed verification
        - Determine whether the section actually contains bias
        - Provide explicit reasoning for why it is or isn't biased
        - Include specific evidence and impact assessment
        """
        try:
            # PHASE 1: Identify potentially biased sections across the paper
            logger.info("🔍 PHASE 1: Identifying potentially biased sections across the paper...")

            section_analysis_prompt = f"""
You are an expert research methodologist. Your task is to analyze this research paper and identify SECTIONS that potentially contain biases.

PAPER CONTENT:
{text_content[:8000]}

BIAS TYPES TO DETECT: {', '.join(bias_types)}

PHASE 1 INSTRUCTIONS - SECTION-LEVEL ANALYSIS:
Your goal is to scan through the ENTIRE paper and identify specific sections or passages that may contain biases.

CRITICAL: For each potentially biased section, you must extract the COMPLETE text of that section so readers can see the full context.

For each potentially biased section, provide:
1. The section name/location (e.g., "Methods - Sampling", "Results - Statistical Analysis", "Discussion - Interpretation")
2. The FULL TEXT of the entire section or paragraph that contains the bias (100-500 words minimum - include complete context)
3. The type of bias you suspect (selection, measurement, confounding, publication, reporting)
4. Initial red flags that suggest this section might be biased
5. Preliminary severity estimate

Think systematically through these areas:
- **Abstract & Introduction**: Claims, framing, literature review completeness
- **Methods**:
  - Sampling methods and participant selection
  - Measurement instruments and procedures
  - Randomization and control procedures
  - Statistical analysis choices
- **Results**:
  - Selective reporting of outcomes
  - Statistical presentation and interpretation
  - Missing data handling
- **Discussion**:
  - Interpretation of findings
  - Acknowledgment of limitations
  - Generalization claims
- **Overall**: Conflicts of interest, funding influence, missing information

Provide your analysis in JSON format:
{{
  "potentially_biased_sections": [
    {{
      "section_name": "Name/location of the section (e.g., 'Methods - Participant Selection')",
      "full_section_text": "COMPLETE TEXT of the entire section/paragraph containing the bias (100-500 words). Include full context so readers can understand the complete picture.",
      "suspected_bias_type": "selection_bias | measurement_bias | confounding_bias | publication_bias | reporting_bias",
      "red_flags": ["List of specific indicators that suggest bias"],
      "preliminary_severity": "low | medium | high",
      "page_hint": "Rough location in paper (beginning, middle, end, or specific keyword)",
      "initial_reasoning": "Brief explanation of why this section is flagged"
    }}
  ]
}}

BIAS DETECTION GUIDELINES:
1. **Selection Bias**: Non-random sampling, unclear inclusion/exclusion criteria, convenience sampling, volunteer bias, survival bias
2. **Measurement Bias**: Self-reported data without validation, leading questions, observer bias, instrument calibration issues, recall bias
3. **Confounding Bias**: Lack of control group, uncontrolled confounding variables, missing covariates, inadequate matching
4. **Publication Bias**: Selective outcome reporting, post-hoc analysis, p-hacking indicators, missing negative results
5. **Reporting Bias**: Incomplete methods, missing data, selective emphasis, data dredging, HARKing (Hypothesizing After Results Known)

IMPORTANT: Extract the FULL SECTION TEXT for each potential bias. Users need to see the complete context, not just a snippet.

Be thorough - scan the entire paper systematically. Look for what's MISSING as well as what's present.
"""

            # Phase 1: Section identification with moderate temperature for thoroughness
            section_response = self._get_openai_client().generate_completion(
                prompt=section_analysis_prompt,
                model="gpt-3.5-turbo",
                max_tokens=3000,
                temperature=0.2  # Low temperature for systematic analysis
            )

            if not section_response:
                logger.error("❌ PHASE 1 failed: No response from LLM")
                return {"error": "No response from Phase 1 (section analysis)"}

            try:
                phase1_result = json.loads(section_response)
                potentially_biased_sections = phase1_result.get("potentially_biased_sections", [])
                logger.info(f"✅ PHASE 1 complete: {len(potentially_biased_sections)} potentially biased sections identified")

                # Log details of flagged sections
                for idx, section in enumerate(potentially_biased_sections):
                    logger.info(f"   Section {idx+1}: {section.get('section_name')} - {section.get('suspected_bias_type')} ({section.get('preliminary_severity')} severity)")

            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse Phase 1 response: {str(e)}")
                logger.error(f"Response was: {section_response[:500]}")
                return {"error": "Failed to parse section analysis results"}

            if not potentially_biased_sections:
                logger.info("✅ No potentially biased sections identified - paper appears clean")
                return {
                    "detected_biases": [],
                    "rejected_biases": [],
                    "bias_summary": "No significant biases detected in the paper.",
                    "limitations": [],
                    "confounding_factors": [],
                    "severity_scores": {bt: "none" for bt in bias_types},
                    "recommendations": []
                }

            # PHASE 2: Detailed verification with chain-of-thought reasoning
            logger.info(f"🔍 PHASE 2: Verifying {len(potentially_biased_sections)} potentially biased sections...")

            verification_prompt = f"""
You are a rigorous research quality assessor. You will now VERIFY each potentially biased section identified in Phase 1.

PAPER CONTENT:
{text_content[:8000]}

POTENTIALLY BIASED SECTIONS TO VERIFY:
{json.dumps(potentially_biased_sections, indent=2)}

SEVERITY THRESHOLD: {severity_threshold}

PHASE 2 INSTRUCTIONS - DETAILED VERIFICATION WITH CHAIN-OF-THOUGHT:

For EACH potentially biased section, you must:

1. **RE-EXAMINE THE EVIDENCE**: Look at the full section text and context
2. **APPLY CHAIN-OF-THOUGHT REASONING**:
   - ANALYZE: What does the evidence actually show? What are the facts?
   - CONTEXT: What is the research context? What are acceptable practices in this field?
   - EVALUATE: Is this a genuine methodological bias, or is it a reasonable limitation/trade-off?
   - SEVERITY: If it IS a bias, how severely does it compromise the study's validity?
   - IMPACT: What specific effects does this bias have on the results and conclusions?
3. **MAKE A DECISION**: Is this section ACTUALLY biased or not?
4. **PROVIDE EXPLICIT REASONING**: Explain your decision step-by-step

CRITICAL REJECTION THRESHOLD:
- Only REJECT a potential bias if you are >90% CONFIDENT it is NOT a bias
- When in doubt, keep the bias and explain the uncertainty in your reasoning
- It's better to flag something for human review than to miss a real bias
- If confidence is 50-90% that it's a bias, KEEP IT as detected bias with appropriate severity

IMPORTANT DISTINCTIONS:
- **Bias** = Systematic error that skews results in a particular direction
- **Limitation** = Constraint or weakness that doesn't necessarily create directional error
- **Trade-off** = Methodological choice with pros and cons

Provide your verification in JSON format:
{{
  "detected_biases": [
    {{
      "section_name": "Name of the section (from Phase 1)",
      "bias_type": "selection_bias | measurement_bias | confounding_bias | publication_bias | reporting_bias",
      "description": "Clear, specific description of the confirmed bias",
      "full_section_text": "The COMPLETE text from Phase 1's full_section_text field - preserve this exactly",
      "evidence": "Specific quotes highlighting the bias within the full text",
      "severity": "low | medium | high",
      "impact": "Specific explanation of how this bias affects the study's validity and results",
      "verification_reasoning": "DETAILED chain-of-thought explanation of WHY this IS a genuine bias (not just a limitation)",
      "why_bias_not_limitation": "Explicit explanation of why this is a bias and not merely a study limitation",
      "confidence_percentage": 50-100 (your confidence level that this IS a bias)
    }}
  ],
  "rejected_sections": [
    {{
      "section_name": "Name of the section (from Phase 1)",
      "suspected_bias_type": "Type that was suspected",
      "rejection_reasoning": "DETAILED chain-of-thought explanation of WHY you are >90% confident this is NOT a genuine bias",
      "alternative_classification": "What this actually is (e.g., 'acceptable limitation', 'methodological trade-off', 'false positive')",
      "confidence_percentage": 90-100 (must be >90 to reject)
    }}
  ],
  "bias_summary": "Overall summary of confirmed biases and their collective impact",
  "limitations": ["Study limitations that are NOT biases (important for transparency)"],
  "confounding_factors": ["Specific uncontrolled variables that could affect results"],
  "severity_scores": {{
    "selection_bias": "none | low | medium | high",
    "measurement_bias": "none | low | medium | high",
    "confounding_bias": "none | low | medium | high",
    "publication_bias": "none | low | medium | high",
    "reporting_bias": "none | low | medium | high"
  }},
  "recommendations": ["Specific, actionable recommendations to address each confirmed bias"]
}}

VERIFICATION STANDARDS:
- Only confirm biases that meet or exceed the severity threshold: {severity_threshold}
- ONLY REJECT if >90% confident it's NOT a bias - when in doubt, keep it
- Distinguish clearly between biases, limitations, and methodological choices
- PRESERVE the full_section_text from Phase 1 in detected_biases so users can see complete context
- Provide specific evidence with quotes when possible
- Consider field-specific norms and constraints
- Think about practical research constraints vs. actual bias

CHAIN-OF-THOUGHT TEMPLATE for each section:
1. "The evidence shows..."
2. "In the context of this research..."
3. "This is/is not a bias because..."
4. "My confidence level is X% because..."
5. "The severity is X because..."
6. "The impact on results is..."
7. "Therefore, my conclusion is..."

REMEMBER: Be conservative in rejecting - only reject if >90% certain it's not a bias!
"""

            # Phase 2: Rigorous verification with deterministic reasoning
            verification_response = self._get_openai_client().generate_completion(
                prompt=verification_prompt,
                model="gpt-3.5-turbo",
                max_tokens=4000,
                temperature=0.0  # Deterministic for consistent, rigorous verification
            )

            if not verification_response:
                logger.error("❌ PHASE 2 failed: No response from LLM")
                return {"error": "No response from Phase 2 (verification)"}

            try:
                result = json.loads(verification_response)
                confirmed_biases = result.get("detected_biases", [])
                rejected_sections = result.get("rejected_biases", []) or result.get("rejected_sections", [])

                logger.info(f"✅ PHASE 2 complete:")
                logger.info(f"   - {len(confirmed_biases)} biases CONFIRMED")
                logger.info(f"   - {len(rejected_sections)} sections REJECTED (not biases)")

                # Log details of confirmed biases
                for idx, bias in enumerate(confirmed_biases):
                    logger.info(f"   Confirmed Bias {idx+1}: {bias.get('section_name')} - {bias.get('bias_type')} ({bias.get('severity')} severity)")

                # Log details of rejected sections
                for idx, rejected in enumerate(rejected_sections):
                    logger.info(f"   Rejected {idx+1}: {rejected.get('section_name')} - {rejected.get('alternative_classification', 'not a bias')}")

                return result

            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse Phase 2 response: {str(e)}")
                logger.error(f"Response was: {verification_response[:500]}")
                # Fallback if JSON parsing fails
                return {
                    "detected_biases": [],
                    "rejected_biases": [],
                    "bias_summary": verification_response[:1000],  # Include partial response
                    "limitations": [],
                    "confounding_factors": [],
                    "severity_scores": {},
                    "recommendations": [],
                    "error": "Failed to parse verification response"
                }

        except Exception as e:
            logger.error(f"❌ Bias detection analysis failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e)}
    
    def _find_limitation_text(self, text_content: str, search_text: str) -> Optional[str]:
        """Find limitation or confounding factor text in the paper content."""
        if not text_content or not search_text:
            return None
        
        # Normalize text for searching
        text_lower = text_content.lower()
        search_lower = search_text.lower().strip()
        
        # Try to find exact or partial match
        idx = text_lower.find(search_lower)
        if idx == -1:
            # Try finding key words (first 3-4 meaningful words)
            words = [w for w in search_lower.split() if len(w) > 3][:4]
            for word in words:
                idx = text_lower.find(word)
                if idx != -1:
                    break
        
        if idx != -1:
            # Extract context around the match
            start = max(0, idx - 200)
            end = min(len(text_content), idx + len(search_text) + 300)
            return text_content[start:end].strip()
        
        return None
