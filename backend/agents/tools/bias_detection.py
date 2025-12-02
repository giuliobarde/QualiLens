"""
Bias Detection Tool for QualiLens.

This tool identifies potential biases, limitations, and confounding factors
in research papers to provide critical quality assessment.
"""

import logging
import json
import re
from typing import Dict, Any, Optional, List
from .base_tool import BaseTool, ToolMetadata

# Add the project root to the Python path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from LLM.openai_client import OpenAIClient

# Import tool result cache
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tool_result_cache import ToolResultCache

logger = logging.getLogger(__name__)


class BiasDetectionTool(BaseTool):
    """
    Bias Detection tool for identifying potential biases and limitations in research papers.
    """
    
    def __init__(self):
        super().__init__()
        self.openai_client = None
        self.result_cache = ToolResultCache()
    
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
            
            # Check cache first (evidence_collector is not part of cache key as it's for output only)
            cache_key_params = {
                "bias_types": bias_types,
                "severity_threshold": severity_threshold
            }
            cached_result = self.result_cache.get_cached_result(
                "bias_detection_tool",
                text_content,
                **cache_key_params
            )
            
            if cached_result:
                logger.info("✅ Using cached bias detection result")
                bias_analysis = cached_result
            else:
                # Generate bias detection analysis
                bias_analysis = self._detect_biases(text_content, bias_types, severity_threshold)
                
                # Cache the result (before evidence collection)
                if bias_analysis.get("success") and not bias_analysis.get("error"):
                    self.result_cache.cache_result(
                        "bias_detection_tool",
                        text_content,
                        bias_analysis,
                        **cache_key_params
                    )
            
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
                        default_confidence = 0.85
                    elif severity == "medium":
                        score_impact = -12.0
                        default_confidence = 0.70
                    else:
                        score_impact = -6.0
                        default_confidence = 0.60

                    # Additional penalty for critical bias types
                    bias_type = bias.get("bias_type", "").lower()
                    if any(bt in bias_type for bt in ["selection", "confounding", "publication"]):
                        score_impact -= 5.0
                        logger.info(f"   Applied additional penalty for critical bias type: {bias_type}")

                    # Build comprehensive rationale using chain-of-thought reasoning
                    section_name = bias.get("section_name", "Unknown section")
                    bias_type = bias.get("bias_type", "unknown")
                    verification_reasoning = bias.get("verification_reasoning", "")
                    why_bias = bias.get("why_bias_not_limitation", "")
                    impact = bias.get("impact", "")
                    
                    # CRITICAL FIX: Use consistent confidence value
                    # Get confidence from LLM response (as percentage 0-100) or use default
                    confidence_val_percentage = bias.get("confidence_percentage", 0)
                    
                    # Convert percentage to decimal (0-1) if available, otherwise use default
                    if confidence_val_percentage and confidence_val_percentage > 0:
                        # Convert from percentage (0-100) to decimal (0-1)
                        confidence = confidence_val_percentage / 100.0
                        # Ensure it's within valid range
                        confidence = max(0.0, min(1.0, confidence))
                    else:
                        # Use severity-based default
                        confidence = default_confidence
                        confidence_val_percentage = int(confidence * 100)

                    # Construct detailed rationale that explains why/why not this is a bias
                    rationale_parts = [f"🔍 BIAS DETECTED: {bias_type.replace('_', ' ').title()} in section: {section_name}"]

                    if verification_reasoning:
                        rationale_parts.append(f"\n📋 VERIFICATION REASONING:\n{verification_reasoning}")

                    if why_bias:
                        rationale_parts.append(f"\n⚖️ WHY THIS IS A BIAS (NOT JUST A LIMITATION):\n{why_bias}")

                    if impact:
                        rationale_parts.append(f"\n💥 IMPACT ON STUDY VALIDITY:\n{impact}")

                    # Use the same confidence value in rationale (as percentage for display)
                    # Only include if confidence is meaningful (> 0)
                    if confidence_val_percentage > 0:
                        rationale_parts.append(f"\n📊 Confidence Level: {confidence_val_percentage}%")

                    full_rationale = "\n".join(rationale_parts)

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
                        rationale=full_rationale[:2000],  # Increased length for detailed chain-of-thought reasoning
                        severity=severity,
                        confidence=confidence,
                        score_impact=score_impact
                    )

                    logger.info(f"✅ Added evidence {evidence_id} for bias: {section_name} ({bias_type}, {severity} severity, impact: {score_impact:.1f}, text_length: {len(text_to_add)} chars)")
                
                # Also collect evidence from limitations (these are important for peer reviewers)
                limitations = bias_analysis.get("limitations", [])
                logger.info(f"📊 Collecting evidence for {len(limitations)} study limitations")
                
                for idx, limitation in enumerate(limitations):
                    # Handle both string format (backward compatibility) and object format
                    if isinstance(limitation, str) and len(limitation) > 30:
                        limitation_text = limitation
                        limitation_impact = "This represents a constraint or weakness in the study design that may affect the interpretation or generalizability of the findings, but is not necessarily a systematic bias."
                        # Default confidence for string format
                        confidence_percentage = 70
                    elif isinstance(limitation, dict):
                        limitation_text = limitation.get("description", "")
                        limitation_impact = limitation.get("impact", "This represents a constraint or weakness in the study design that may affect the interpretation or generalizability of the findings, but is not necessarily a systematic bias.")
                        # Use AI-generated confidence, fallback to 70% if not provided
                        confidence_percentage = limitation.get("confidence_percentage", 70)
                    else:
                        continue
                    
                    if not limitation_text or len(limitation_text) < 30:
                        continue
                    
                    # Try to find this limitation in the paper
                    limitation_snippet = self._find_limitation_text(text_content, limitation_text)
                    
                    # Convert percentage to decimal (0-1)
                    confidence = max(0.0, min(1.0, confidence_percentage / 100.0))
                    
                    # Build structured rationale consistent with bias format
                    rationale_parts = [f"🔍 STUDY LIMITATION DETECTED"]
                    rationale_parts.append(f"\n📋 LIMITATION DESCRIPTION:\n{limitation_text}")
                    rationale_parts.append(f"\n💡 IMPACT ON STUDY VALIDITY:\n{limitation_impact}")
                    rationale_parts.append(f"\n📊 Confidence Level: {confidence_percentage}%")
                    full_rationale = "\n".join(rationale_parts)
                    
                    evidence_collector.add_evidence(
                        category="bias",
                        text_snippet=limitation_snippet[:500] if limitation_snippet else limitation_text[:500],
                        rationale=full_rationale[:2000],
                        confidence=confidence,
                        severity="low",
                        score_impact=-2.0
                    )
                    logger.info(f"✅ Added limitation evidence {idx+1}/{len(limitations)} (confidence: {confidence_percentage}%)")
                
                # Collect evidence from confounding factors
                confounding_factors = bias_analysis.get("confounding_factors", [])
                logger.info(f"📊 Collecting evidence for {len(confounding_factors)} confounding factors")
                
                for idx, confounder in enumerate(confounding_factors):
                    # Handle both string format (backward compatibility) and object format
                    if isinstance(confounder, str) and len(confounder) > 30:
                        confounder_text = confounder
                        confounder_impact = "This represents a variable that may be associated with both the exposure and outcome, potentially distorting the true relationship. This is important for peer reviewers to verify whether confounding was adequately controlled."
                        # Default confidence for string format
                        confidence_percentage = 75
                    elif isinstance(confounder, dict):
                        confounder_text = confounder.get("description", "")
                        confounder_impact = confounder.get("impact", "This represents a variable that may be associated with both the exposure and outcome, potentially distorting the true relationship. This is important for peer reviewers to verify whether confounding was adequately controlled.")
                        # Use AI-generated confidence, fallback to 75% if not provided
                        confidence_percentage = confounder.get("confidence_percentage", 75)
                    else:
                        continue
                    
                    if not confounder_text or len(confounder_text) < 30:
                        continue
                    
                    # Try to find this confounder in the paper
                    confounder_snippet = self._find_limitation_text(text_content, confounder_text)
                    
                    # Convert percentage to decimal (0-1)
                    confidence = max(0.0, min(1.0, confidence_percentage / 100.0))
                    
                    # Build structured rationale consistent with bias format
                    rationale_parts = [f"🔍 CONFOUNDING FACTOR DETECTED"]
                    rationale_parts.append(f"\n📋 CONFOUNDER DESCRIPTION:\n{confounder_text}")
                    rationale_parts.append(f"\n💥 IMPACT ON STUDY VALIDITY:\n{confounder_impact}")
                    rationale_parts.append(f"\n📊 Confidence Level: {confidence_percentage}%")
                    full_rationale = "\n".join(rationale_parts)
                    
                    evidence_collector.add_evidence(
                        category="bias",
                        text_snippet=confounder_snippet[:500] if confounder_snippet else confounder_text[:500],
                        rationale=full_rationale[:2000],
                        confidence=confidence,
                        severity="medium",
                        score_impact=-8.0
                    )
                    logger.info(f"✅ Added confounding factor evidence {idx+1}/{len(confounding_factors)} (confidence: {confidence_percentage}%)")
                
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
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "tool_used": "bias_detection_tool"
            }
    
    def _pattern_match_biases(self, text_content: str) -> List[Dict[str, Any]]:
        """
        Pattern matching to find obvious bias indicators before LLM analysis.
        This helps ensure we don't miss obvious biases.
        """
        patterns = []
        text_lower = text_content.lower()
        
        # Industry/Commercial Funding
        funding_patterns = [
            r"funded by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|Ltd|Corp|Pharma|Pharmaceuticals|Company))",
            r"supported by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|Ltd|Corp|Pharma|Pharmaceuticals|Company))",
            r"sponsored by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|Ltd|Corp|Pharma|Pharmaceuticals|Company))",
            r"grant from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|Ltd|Corp|Pharma|Pharmaceuticals|Company))"
        ]
        for pattern in funding_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                patterns.append({
                    "type": "publication_bias",
                    "indicator": "Industry/commercial funding",
                    "text": match.group(0),
                    "severity": "high"
                })
        
        # Single-center design
        if re.search(r"single[- ]center|single[- ]centre|single[- ]site|single[- ]institution", text_lower):
            patterns.append({
                "type": "selection_bias",
                "indicator": "Single-center design",
                "text": re.search(r"single[- ]center|single[- ]centre|single[- ]site|single[- ]institution", text_lower, re.IGNORECASE).group(0),
                "severity": "medium"
            })
        
        # Per-protocol analysis
        if re.search(r"per[- ]protocol|per protocol|pp analysis|primary analysis.*per", text_lower):
            patterns.append({
                "type": "selection_bias",
                "indicator": "Per-protocol primary analysis",
                "text": re.search(r"per[- ]protocol|per protocol|pp analysis|primary analysis.*per", text_lower, re.IGNORECASE).group(0),
                "severity": "high"
            })
        
        # LOCF
        if re.search(r"\blocf\b|last observation carried forward", text_lower):
            patterns.append({
                "type": "measurement_bias",
                "indicator": "LOCF imputation",
                "text": re.search(r"\blocf\b|last observation carried forward", text_lower, re.IGNORECASE).group(0),
                "severity": "medium"
            })
        
        # Proprietary measures
        if re.search(r"proprietary|developed by (?:the )?authors?|custom instrument|unvalidated", text_lower):
            patterns.append({
                "type": "measurement_bias",
                "indicator": "Proprietary or unvalidated measure",
                "text": re.search(r"proprietary|developed by (?:the )?authors?|custom instrument|unvalidated", text_lower, re.IGNORECASE).group(0),
                "severity": "high"
            })
        
        # Self-reported adherence
        if re.search(r"self[- ]reported.*adherence|self[- ]reported.*compliance|adherence.*self[- ]reported", text_lower):
            patterns.append({
                "type": "measurement_bias",
                "indicator": "Self-reported adherence without validation",
                "text": re.search(r"self[- ]reported.*adherence|self[- ]reported.*compliance|adherence.*self[- ]reported", text_lower, re.IGNORECASE).group(0),
                "severity": "medium"
            })
        
        # Short follow-up (12-week or less for long-term outcomes)
        if re.search(r"\b(?:12|8|6|4)[- ]week|short[- ]term|brief follow[- ]up", text_lower):
            patterns.append({
                "type": "temporal_bias",
                "indicator": "Short follow-up duration",
                "text": re.search(r"\b(?:12|8|6|4)[- ]week|short[- ]term|brief follow[- ]up", text_lower, re.IGNORECASE).group(0),
                "severity": "medium"
            })
        
        # Restricted data access
        if re.search(r"data available (?:upon|on) request|proprietary data|data not publicly available|restricted access", text_lower):
            patterns.append({
                "type": "reporting_bias",
                "indicator": "Restricted data access",
                "text": re.search(r"data available (?:upon|on) request|proprietary data|data not publicly available|restricted access", text_lower, re.IGNORECASE).group(0),
                "severity": "medium"
            })
        
        return patterns
    
    def _detect_biases(self, text_content: str, bias_types: List[str], severity_threshold: str) -> Dict[str, Any]:
        """
        Detect biases using pattern matching + single-pass LLM approach.
        NEW SIMPLIFIED APPROACH: Direct detection without overly conservative verification.
        """
        try:
            # Use full text content
            text_length = len(text_content)
            if text_length > 100000:
                # For very long papers, take strategic sections
                text_for_analysis = text_content[:40000] + "\n\n[... middle sections omitted ...]\n\n" + text_content[-30000:]
                logger.info(f"Text content is {text_length} chars, using first 40000 + last 30000 for analysis")
            else:
                text_for_analysis = text_content
                logger.info(f"Using full text content ({text_length} chars) for analysis")
            
            # STEP 1: Pattern matching to find obvious bias indicators
            logger.info("🔍 STEP 1: Pattern matching for obvious bias indicators...")
            pattern_matches = self._pattern_match_biases(text_for_analysis)
            logger.info(f"✅ Pattern matching found {len(pattern_matches)} potential bias indicators")
            
            # STEP 2: Single-pass LLM detection with explicit instructions
            logger.info("🔍 STEP 2: LLM-based bias detection...")
            
            # Build pattern match context for LLM
            pattern_context = ""
            if pattern_matches:
                pattern_context = "\n\nPATTERN MATCHING FOUND THESE POTENTIAL BIASES (YOU MUST VERIFY AND EXPAND ON THESE):\n"
                for i, match in enumerate(pattern_matches, 1):
                    pattern_context += f"{i}. {match['indicator']} ({match['type']}, {match['severity']} severity) - Found text: '{match['text'][:100]}'\n"
            
            detection_prompt = f"""You are an expert research methodologist detecting biases in research papers. Your task is to identify ALL biases, especially implicit ones.

PAPER CONTENT:
{text_for_analysis[:50000]}{pattern_context}

CRITICAL INSTRUCTIONS:
1. You MUST find at least 2-5 biases. If you find 0 biases, you are NOT being thorough enough.
2. Look for IMPLICIT biases - things that are stated but not explicitly called "bias"
3. Use the pattern matches above as starting points - verify them and find additional biases
4. Be AGGRESSIVE in detection - err on the side of finding biases rather than missing them
5. Extract the FULL TEXT where each bias appears (at least 100-300 words of context)

BIAS TYPES TO DETECT: {', '.join(bias_types)}

EXPLICIT PATTERNS TO LOOK FOR (these are ALWAYS biases):
- "single-center" or "single site" → Selection bias (limited generalizability)
- "per-protocol" as primary analysis → Selection bias (excludes non-adherent participants)
- "LOCF" or "last observation carried forward" → Measurement bias (assumes no change)
- "proprietary" or "developed by authors" instrument → Measurement bias (unvalidated)
- "self-reported adherence" without validation → Measurement bias
- Industry/commercial funding → Publication bias, conflict of interest
- "12-week" or short follow-up for long-term outcomes → Temporal bias
- "data available upon request" → Reporting bias (restricted access)
- Multiple subgroup analyses without correction → Publication bias (p-hacking)

For EACH bias you find, provide:
1. section_name: Where in the paper (e.g., "Methods - Analysis", "Acknowledgments")
2. bias_type: selection_bias | measurement_bias | confounding_bias | publication_bias | reporting_bias
3. description: Clear description of the bias
4. full_section_text: The COMPLETE text where this bias appears (100-500 words)
5. evidence: Specific quote showing the bias
6. severity: low | medium | high
7. impact: How this affects study validity
8. confidence_percentage: 70-100 (be confident if pattern matches or explicit)

For EACH limitation and confounding factor, provide:
- description: Clear description of the limitation/confounder
- impact: How this affects study validity
- confidence_percentage: 60-90 (provide appropriate confidence based on how clearly stated it is in the paper)

Return ONLY valid JSON in this exact format:
{{
  "detected_biases": [
    {{
      "section_name": "Methods - Statistical Analysis",
      "bias_type": "selection_bias",
      "description": "Primary analysis performed on per-protocol basis, excluding non-adherent participants",
      "full_section_text": "[COMPLETE TEXT FROM PAPER - 100-500 words]",
      "evidence": "[Specific quote]",
      "severity": "high",
      "impact": "Excludes participants who did not adhere, potentially biasing results toward positive outcomes",
      "confidence_percentage": 90
    }}
  ],
  "bias_summary": "Overall summary of all detected biases",
  "limitations": [
    {{
      "description": "Study limitation description",
      "impact": "How this affects study validity",
      "confidence_percentage": 70
    }}
  ],
  "confounding_factors": [
    {{
      "description": "Confounding factor description",
      "impact": "How this affects study validity",
      "confidence_percentage": 75
    }}
  ],
  "severity_scores": {{
    "selection_bias": "none | low | medium | high",
    "measurement_bias": "none | low | medium | high",
    "confounding_bias": "none | low | medium | high",
    "publication_bias": "none | low | medium | high",
    "reporting_bias": "none | low | medium | high"
  }},
  "recommendations": ["How to address each bias"]
}}

REMEMBER: You MUST find biases. If the paper has "single-center", "per-protocol", "LOCF", "proprietary", industry funding, or short follow-up, these ARE biases. Extract the full text where they appear."""

            # Single-pass detection with moderate temperature
            detection_response = self._get_openai_client().generate_completion(
                prompt=detection_prompt,
                model="gpt-4o-mini",
                max_tokens=6000,
                temperature=0.3  # Moderate temperature for balanced detection
            )

            if not detection_response:
                logger.error("❌ Detection failed: No response from LLM")
                # Fallback: use pattern matches
                if pattern_matches:
                    logger.warning("⚠️ Using pattern matches as fallback")
                    detected_biases = []
                    for match in pattern_matches:
                        # Try to find the text in the paper
                        match_text_lower = match['text'].lower()
                        idx = text_for_analysis.lower().find(match_text_lower)
                        if idx != -1:
                            start = max(0, idx - 200)
                            end = min(len(text_for_analysis), idx + len(match['text']) + 500)
                            full_text = text_for_analysis[start:end]
                        else:
                            full_text = match['text']
                        
                        detected_biases.append({
                            "section_name": "Pattern matched",
                            "bias_type": match['type'],
                            "description": match['indicator'],
                            "full_section_text": full_text,
                            "evidence": match['text'],
                            "severity": match['severity'],
                            "impact": f"This {match['indicator'].lower()} may introduce systematic error",
                            "confidence_percentage": 85
                        })
                    
                    return {
                        "detected_biases": detected_biases,
                        "bias_summary": f"Detected {len(detected_biases)} biases using pattern matching",
                        "limitations": [],
                        "confounding_factors": [],
                        "severity_scores": {bt: "medium" if any(m['type'] == bt for m in pattern_matches) else "none" for bt in bias_types},
                        "recommendations": ["Verify pattern-matched biases with full text analysis"]
                    }
                return {"error": "No response from LLM and no pattern matches"}

            try:
                result = json.loads(detection_response)
                detected_biases = result.get("detected_biases", [])
                
                # Merge pattern matches if they weren't already detected
                if pattern_matches:
                    for pattern in pattern_matches:
                        # Check if this pattern was already detected
                        pattern_detected = any(
                            pattern['indicator'].lower() in bias.get('description', '').lower() or
                            pattern['text'].lower() in bias.get('evidence', '').lower()
                            for bias in detected_biases
                        )
                        if not pattern_detected:
                            # Add pattern match as a detected bias
                            idx = text_for_analysis.lower().find(pattern['text'].lower())
                            if idx != -1:
                                start = max(0, idx - 200)
                                end = min(len(text_for_analysis), idx + len(pattern['text']) + 500)
                                full_text = text_for_analysis[start:end]
                            else:
                                full_text = pattern['text']
                            
                            detected_biases.append({
                                "section_name": "Pattern matched section",
                                "bias_type": pattern['type'],
                                "description": pattern['indicator'],
                                "full_section_text": full_text,
                                "evidence": pattern['text'],
                                "severity": pattern['severity'],
                                "impact": f"This {pattern['indicator'].lower()} introduces systematic error",
                                "confidence_percentage": 90
                            })
                
                logger.info(f"✅ Detection complete: {len(detected_biases)} biases detected")
                for idx, bias in enumerate(detected_biases):
                    logger.info(f"   Bias {idx+1}: {bias.get('bias_type')} - {bias.get('description')[:60]}... ({bias.get('severity')} severity)")

                # Ensure we have required fields
                result["detected_biases"] = detected_biases
                result["success"] = True
                
                return result

            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse detection response: {str(e)}")
                logger.error(f"Response was: {detection_response[:500]}")
                # Fallback to pattern matches
                if pattern_matches:
                    logger.warning("⚠️ Using pattern matches as fallback due to JSON parse error")
                    detected_biases = []
                    for match in pattern_matches:
                        idx = text_for_analysis.lower().find(match['text'].lower())
                        if idx != -1:
                            start = max(0, idx - 200)
                            end = min(len(text_for_analysis), idx + len(match['text']) + 500)
                            full_text = text_for_analysis[start:end]
                        else:
                            full_text = match['text']
                        
                        detected_biases.append({
                            "section_name": "Pattern matched",
                            "bias_type": match['type'],
                            "description": match['indicator'],
                            "full_section_text": full_text,
                            "evidence": match['text'],
                            "severity": match['severity'],
                            "impact": f"This {match['indicator'].lower()} may introduce systematic error",
                            "confidence_percentage": 85
                        })
                    
                    return {
                        "detected_biases": detected_biases,
                        "bias_summary": f"Detected {len(detected_biases)} biases using pattern matching (LLM parse failed)",
                        "limitations": [],
                        "confounding_factors": [],
                        "severity_scores": {bt: "medium" if any(m['type'] == bt for m in pattern_matches) else "none" for bt in bias_types},
                        "recommendations": ["Verify pattern-matched biases with full text analysis"],
                        "success": True
                    }
                return {
                    "error": "Failed to parse detection response",
                    "detected_biases": [],
                    "bias_summary": "Detection failed due to parsing error",
                    "limitations": [],
                    "confounding_factors": [],
                    "severity_scores": {bt: "none" for bt in bias_types},
                    "recommendations": []
                }

        except Exception as e:
            logger.error(f"❌ Bias detection analysis failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "error": str(e),
                "detected_biases": [],
                "bias_summary": f"Detection failed: {str(e)}",
                "limitations": [],
                "confounding_factors": [],
                "severity_scores": {bt: "none" for bt in bias_types},
                "recommendations": []
            }
    
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
