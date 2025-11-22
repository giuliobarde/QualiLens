"""
Research Gap Identifier Tool for QualiLens.

This tool identifies research gaps and future directions in research papers.
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
                future_focus: str = "general", evidence_collector=None) -> Dict[str, Any]:
        """
        Identify research gaps and future directions.
        
        Args:
            text_content: The text content to analyze
            gap_types: Types of gaps to identify
            future_focus: Focus area for future directions
            evidence_collector: Optional evidence collector for evidence traces
            
        Returns:
            Dict containing research gaps and future directions
        """
        try:
            logger.info(f"Identifying research gaps with focus: {future_focus}")
            
            # Generate gap identification analysis
            gap_analysis = self._identify_research_gaps(text_content, gap_types, future_focus)
            
            # Collect evidence if evidence_collector is provided
            if evidence_collector:
                # Collect evidence from research gaps
                research_gaps = gap_analysis.get("research_gaps", [])
                logger.info(f"📊 Collecting evidence for {len(research_gaps)} research gaps")
                
                for idx, gap in enumerate(research_gaps):
                    if isinstance(gap, dict):
                        gap_description = gap.get("description", "")
                        gap_type = gap.get("gap_type", "unknown")
                        significance = gap.get("significance", "")
                        evidence_text = gap.get("evidence", "")
                        
                        # Use evidence text if available, otherwise use description
                        text_snippet = evidence_text if evidence_text else gap_description
                        
                        # Build rationale
                        rationale_parts = [f"🔍 RESEARCH GAP: {gap_type.replace('_', ' ').title()}"]
                        if gap_description:
                            rationale_parts.append(f"\n📋 GAP DESCRIPTION:\n{gap_description}")
                        if significance:
                            rationale_parts.append(f"\n💡 SIGNIFICANCE:\n{significance}")
                        if evidence_text:
                            rationale_parts.append(f"\n📄 EVIDENCE:\n{evidence_text}")
                        
                        full_rationale = "\n".join(rationale_parts)
                        
                        # Add evidence
                        evidence_id = evidence_collector.add_evidence(
                            category="research_gap",
                            text_snippet=text_snippet[:500] if text_snippet else gap_description[:500],
                            rationale=full_rationale[:2000],
                            confidence=0.7,
                            severity="medium",
                            score_impact=-5.0  # Research gaps have moderate negative impact
                        )
                        
                        logger.info(f"✅ Added evidence {evidence_id} for research gap: {gap_type} ({len(text_snippet)} chars)")
                
                # Collect evidence from methodological gaps
                methodological_gaps = gap_analysis.get("methodological_gaps", [])
                logger.info(f"📊 Collecting evidence for {len(methodological_gaps)} methodological gaps")
                
                for idx, gap in enumerate(methodological_gaps):
                    if isinstance(gap, dict):
                        gap_desc = gap.get("gap", "") or gap.get("description", "")
                        if gap_desc:
                            evidence_collector.add_evidence(
                                category="research_gap",
                                text_snippet=gap_desc[:500],
                                rationale=f"Methodological Gap: {gap_desc}. {gap.get('improvement', '')}",
                                confidence=0.7,
                                severity="medium",
                                score_impact=-5.0
                            )
                            logger.info(f"✅ Added methodological gap evidence {idx+1}/{len(methodological_gaps)}")
                
                # Collect evidence from unaddressed questions
                unaddressed_questions = gap_analysis.get("unaddressed_questions", [])
                logger.info(f"📊 Collecting evidence for {len(unaddressed_questions)} unaddressed questions")
                
                for idx, question in enumerate(unaddressed_questions):
                    if isinstance(question, dict):
                        question_text = question.get("question", "")
                        if question_text:
                            evidence_collector.add_evidence(
                                category="research_gap",
                                text_snippet=question_text[:500],
                                rationale=f"Unaddressed Question: {question_text}. {question.get('importance', '')}",
                                confidence=0.65,
                                severity="low",
                                score_impact=-3.0
                            )
                            logger.info(f"✅ Added unaddressed question evidence {idx+1}/{len(unaddressed_questions)}")
                
                logger.info(f"✅ Research gap evidence collection complete. Total gaps: {len(research_gaps)}, Methodological: {len(methodological_gaps)}, Questions: {len(unaddressed_questions)}")
            
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
    
    def _pattern_match_gaps(self, text_content: str) -> List[Dict[str, Any]]:
        """Pattern matching to find obvious research gap indicators."""
        patterns = []
        text_lower = text_content.lower()
        
        # Short follow-up
        if re.search(r"\b(?:12|8|6|4)[- ]week|short[- ]term|brief follow[- ]up", text_lower):
            patterns.append({
                "type": "methodological",
                "gap": "Lack of long-term follow-up data",
                "description": "Short follow-up duration limits assessment of long-term effects",
                "significance": "Unknown durability of effects, potential late adverse events"
            })
        
        # Proprietary measures
        if re.search(r"proprietary|developed by (?:the )?authors?|custom instrument|unvalidated", text_lower):
            patterns.append({
                "type": "methodological",
                "gap": "Lack of independent validation of proprietary measures",
                "description": "Proprietary instruments prevent replication and independent validation",
                "significance": "Cannot verify measurement validity, prevents replication"
            })
        
        # Restricted data access
        if re.search(r"data available (?:upon|on) request|proprietary data|data not publicly available|restricted access", text_lower):
            patterns.append({
                "type": "empirical",
                "gap": "Restricted data access prevents independent verification",
                "description": "Data not publicly available limits reproducibility",
                "significance": "Cannot independently verify results or conduct re-analyses"
            })
        
        # Single-center
        if re.search(r"single[- ]center|single[- ]centre|single[- ]site|single[- ]institution", text_lower):
            patterns.append({
                "type": "empirical",
                "gap": "Limited generalizability due to single-center design",
                "description": "Single-center study limits generalizability to other populations/contexts",
                "significance": "Results may not apply to different settings or populations"
            })
        
        # Self-citation patterns (excessive)
        self_citation_count = len(re.findall(r"previous (?:studies|work|research) (?:by|from) (?:our|the) (?:group|authors|team)", text_lower))
        if self_citation_count >= 3:
            patterns.append({
                "type": "empirical",
                "gap": "Lack of independent validation due to excessive self-citation",
                "description": "High proportion of self-citations suggests lack of external validation",
                "significance": "No independent replication or validation by other research groups"
            })
        
        # LOCF
        if re.search(r"\blocf\b|last observation carried forward", text_lower):
            patterns.append({
                "type": "methodological",
                "gap": "Alternative missing data methods not explored",
                "description": "LOCF imputation may introduce bias; other methods not considered",
                "significance": "Potential bias in handling missing data"
            })
        
        # Per-protocol analysis
        if re.search(r"per[- ]protocol|per protocol|pp analysis", text_lower):
            patterns.append({
                "type": "methodological",
                "gap": "Intention-to-treat analysis not performed",
                "description": "Per-protocol analysis may introduce selection bias",
                "significance": "Results may be biased toward positive outcomes"
            })
        
        return patterns
    
    def _identify_research_gaps(self, text_content: str, gap_types: Optional[List[str]], future_focus: str) -> Dict[str, Any]:
        """
        Identify research gaps using pattern matching + single-pass LLM approach.
        NEW SIMPLIFIED APPROACH: Direct detection without overly conservative verification.
        """
        try:
            # Use full text content
            text_length = len(text_content)
            if text_length > 100000:
                text_for_analysis = text_content[:40000] + "\n\n[... middle sections omitted ...]\n\n" + text_content[-30000:]
                logger.info(f"Text content is {text_length} chars, using first 40000 + last 30000 for gap analysis")
            else:
                text_for_analysis = text_content
                logger.info(f"Using full text content ({text_length} chars) for gap analysis")
            
            # STEP 1: Pattern matching
            logger.info("🔍 STEP 1: Pattern matching for obvious research gaps...")
            pattern_matches = self._pattern_match_gaps(text_for_analysis)
            logger.info(f"✅ Pattern matching found {len(pattern_matches)} potential gaps")
            
            # STEP 2: Single-pass LLM detection
            logger.info("🔍 STEP 2: LLM-based gap detection...")
            
            # Build pattern context
            pattern_context = ""
            if pattern_matches:
                pattern_context = "\n\nPATTERN MATCHING FOUND THESE POTENTIAL GAPS (YOU MUST VERIFY AND EXPAND ON THESE):\n"
                for i, match in enumerate(pattern_matches, 1):
                    pattern_context += f"{i}. {match['gap']} ({match['type']} gap) - {match['description']}\n"
            
            detection_prompt = f"""You are an expert research analyst identifying research gaps. Your task is to find ALL gaps, especially implicit ones.

PAPER CONTENT:
{text_for_analysis[:50000]}{pattern_context}

CRITICAL INSTRUCTIONS:
1. You MUST find at least 2-5 research gaps. If you find 0 gaps, you are NOT being thorough enough.
2. Look for IMPLICIT gaps - things that are missing or inadequately addressed
3. Use the pattern matches above as starting points - verify them and find additional gaps
4. Be AGGRESSIVE in detection - err on the side of finding gaps rather than missing them

EXPLICIT PATTERNS TO LOOK FOR (these are ALWAYS gaps):
- "12-week" or short follow-up → Gap: Lack of long-term data
- "proprietary" or "developed by authors" instrument → Gap: Lack of independent validation
- "data available upon request" → Gap: Restricted data access
- "single-center" → Gap: Limited generalizability
- Excessive self-citation → Gap: Lack of independent validation
- "LOCF" → Gap: Alternative missing data methods not explored
- "per-protocol" analysis → Gap: Intention-to-treat analysis not performed

For EACH gap you find, provide:
1. gap_type: methodological | theoretical | empirical | practical
2. description: Clear description of the gap
3. significance: Why this gap is important
4. evidence: Text from paper showing this is missing
5. verification_reasoning: Why this is a real gap

Return ONLY valid JSON in this exact format:
{{
  "research_gaps": [
    {{
      "gap_type": "methodological",
      "description": "Lack of long-term follow-up data",
      "significance": "Unknown durability of effects, potential late adverse events",
      "evidence": "[Text from paper showing short follow-up]",
      "verification_reasoning": "The study reports 12-week follow-up, which is insufficient for assessing long-term outcomes"
    }}
  ],
  "methodological_gaps": [
    {{
      "gap": "Specific methodological gap",
      "description": "What's missing methodologically",
      "improvement": "How methodology could be improved"
    }}
  ],
  "unaddressed_questions": [
    {{
      "question": "Specific unaddressed question",
      "importance": "Why this matters",
      "research_approach": "How to investigate"
    }}
  ],
  "future_directions": [
    {{
      "direction": "Future research direction",
      "rationale": "Why this is important",
      "priority": "High | Medium | Low"
    }}
  ],
  "limitations": [
    {{
      "limitation": "Study limitation",
      "impact": "How this affects findings"
    }}
  ]
}}

REMEMBER: You MUST find gaps. If the paper has short follow-up, proprietary measures, restricted data, single-center design, or excessive self-citation, these ARE gaps."""

            # Single-pass detection
            detection_response = self._get_openai_client().generate_completion(
                prompt=detection_prompt,
                model="gpt-4o-mini",
                max_tokens=4000,
                temperature=0.3
            )

            if not detection_response:
                logger.error("❌ Detection failed: No response from LLM")
                # Fallback: use pattern matches
                if pattern_matches:
                    logger.warning("⚠️ Using pattern matches as fallback")
                    return {
                        "research_gaps": pattern_matches,
                        "methodological_gaps": [m for m in pattern_matches if m['type'] == 'methodological'],
                        "unaddressed_questions": [],
                        "future_directions": [],
                        "limitations": []
                    }
                return {"error": "No response from LLM and no pattern matches"}

            try:
                result = json.loads(detection_response)
                research_gaps = result.get("research_gaps", [])
                
                # Merge pattern matches if not already detected
                if pattern_matches:
                    for pattern in pattern_matches:
                        pattern_detected = any(
                            pattern['gap'].lower() in gap.get('description', '').lower()
                            for gap in research_gaps
                        )
                        if not pattern_detected:
                            research_gaps.append({
                                "gap_type": pattern['type'],
                                "description": pattern['gap'],
                                "significance": pattern['significance'],
                                "evidence": pattern['description'],
                                "verification_reasoning": f"Pattern matched: {pattern['description']}"
                            })
                
                logger.info(f"✅ Detection complete: {len(research_gaps)} gaps detected")
                for idx, gap in enumerate(research_gaps):
                    logger.info(f"   Gap {idx+1}: {gap.get('gap_type')} - {gap.get('description')[:60]}...")

                result["research_gaps"] = research_gaps
                result["success"] = True
                return result

            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse detection response: {str(e)}")
                logger.error(f"Response was: {detection_response[:500]}")
                # Fallback to pattern matches
                if pattern_matches:
                    logger.warning("⚠️ Using pattern matches as fallback due to JSON parse error")
                    return {
                        "research_gaps": pattern_matches,
                        "methodological_gaps": [m for m in pattern_matches if m['type'] == 'methodological'],
                        "unaddressed_questions": [],
                        "future_directions": [],
                        "limitations": [],
                        "success": True
                    }
                return {
                    "error": "Failed to parse detection response",
                    "research_gaps": [],
                    "methodological_gaps": [],
                    "unaddressed_questions": [],
                    "future_directions": [],
                    "limitations": []
                }

        except Exception as e:
            logger.error(f"❌ Research gap identification failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "error": str(e),
                "research_gaps": [],
                "methodological_gaps": [],
                "unaddressed_questions": [],
                "future_directions": [],
                "limitations": []
            }
