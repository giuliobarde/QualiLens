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
                # Collect evidence from research gaps (all gaps are now standardized)
                research_gaps = gap_analysis.get("research_gaps", [])
                logger.info(f"📊 Collecting evidence for {len(research_gaps)} research gaps")
                
                for idx, gap in enumerate(research_gaps):
                    # Ensure gap is standardized
                    standardized_gap = self._standardize_gap_format(gap) if isinstance(gap, dict) else {}
                    
                    gap_description = standardized_gap.get("description", "")
                    gap_type = standardized_gap.get("gap_type", "unknown")
                    significance = standardized_gap.get("significance", "")
                    evidence_text = standardized_gap.get("evidence", "")
                    verification_reasoning = standardized_gap.get("verification_reasoning", "")
                    
                    # Use evidence text if available, otherwise use description
                    text_snippet = evidence_text if evidence_text else gap_description
                    
                    # Build rationale from standardized fields
                    rationale_parts = [f"🔍 RESEARCH GAP: {gap_type.replace('_', ' ').title()}"]
                    if gap_description:
                        rationale_parts.append(f"\n📋 GAP DESCRIPTION:\n{gap_description}")
                    if significance:
                        rationale_parts.append(f"\n💡 SIGNIFICANCE:\n{significance}")
                    if evidence_text:
                        rationale_parts.append(f"\n📄 EVIDENCE:\n{evidence_text}")
                    if verification_reasoning:
                        rationale_parts.append(f"\n🔬 VERIFICATION:\n{verification_reasoning}")
                    
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
    
    def _standardize_gap_format(self, gap: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize a gap dictionary to a clean, consistent format.
        
        All gaps will have:
        - gap_type: str (methodological, theoretical, empirical, practical)
        - description: str (clear description of the gap)
        - significance: str (why this gap is important)
        - evidence: str (text from paper showing this is missing)
        - verification_reasoning: str (why this is a real gap)
        
        Args:
            gap: Gap dictionary in any format (pattern or LLM)
            
        Returns:
            Standardized gap dictionary with all required fields
        """
        standardized = {
            "gap_type": "",
            "description": "",
            "significance": "",
            "evidence": "",
            "verification_reasoning": ""
        }
        
        # Extract gap_type (handle both 'type' and 'gap_type' fields)
        gap_type = gap.get('gap_type', '') or gap.get('type', '')
        if gap_type:
            # Normalize gap type
            gap_type_lower = gap_type.lower()
            if 'method' in gap_type_lower:
                standardized["gap_type"] = "methodological"
            elif 'theor' in gap_type_lower:
                standardized["gap_type"] = "theoretical"
            elif 'empir' in gap_type_lower:
                standardized["gap_type"] = "empirical"
            elif 'pract' in gap_type_lower:
                standardized["gap_type"] = "practical"
            else:
                standardized["gap_type"] = gap_type  # Keep original if not recognized
        else:
            standardized["gap_type"] = "methodological"  # Default
        
        # Extract description (handle 'gap', 'description', 'text' fields)
        standardized["description"] = (
            gap.get('description', '') or 
            gap.get('gap', '') or 
            gap.get('text', '') or 
            ''
        ).strip()
        
        # Extract significance
        standardized["significance"] = (
            gap.get('significance', '') or 
            gap.get('importance', '') or 
            ''
        ).strip()
        
        # Extract evidence
        standardized["evidence"] = (
            gap.get('evidence', '') or 
            gap.get('evidence_text', '') or 
            ''
        ).strip()
        
        # Extract verification_reasoning
        standardized["verification_reasoning"] = (
            gap.get('verification_reasoning', '') or 
            gap.get('reasoning', '') or 
            gap.get('rationale', '') or 
            ''
        ).strip()
        
        # If evidence is missing but description exists, use description as evidence
        if not standardized["evidence"] and standardized["description"]:
            standardized["evidence"] = standardized["description"]
        
        # If verification_reasoning is missing, create a default one
        if not standardized["verification_reasoning"]:
            if standardized["evidence"]:
                standardized["verification_reasoning"] = f"Identified based on: {standardized['evidence'][:100]}"
            else:
                standardized["verification_reasoning"] = f"Identified as {standardized['gap_type']} gap: {standardized['description'][:100]}"
        
        # Clean up any empty strings and ensure all fields are strings
        for key in standardized:
            if not standardized[key]:
                standardized[key] = ""
            else:
                standardized[key] = str(standardized[key]).strip()
        
        return standardized
    
    def _normalize_text_for_comparison(self, text: str) -> str:
        """
        Normalize text for comparison by removing punctuation, extra spaces, and converting to lowercase.
        """
        if not text:
            return ""
        # Convert to lowercase, remove punctuation, normalize whitespace
        normalized = re.sub(r'[^\w\s]', '', text.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
    def _extract_key_phrases(self, text: str) -> set:
        """
        Extract key phrases from text for similarity comparison.
        Removes common stop words and returns meaningful words.
        """
        if not text:
            return set()
        
        # Common stop words to ignore
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                     'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                     'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them'}
        
        normalized = self._normalize_text_for_comparison(text)
        words = normalized.split()
        # Filter out stop words and short words (< 3 chars)
        key_phrases = {w for w in words if len(w) >= 3 and w not in stop_words}
        return key_phrases
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts using word overlap.
        Returns a score between 0.0 and 1.0.
        """
        if not text1 or not text2:
            return 0.0
        
        phrases1 = self._extract_key_phrases(text1)
        phrases2 = self._extract_key_phrases(text2)
        
        if not phrases1 or not phrases2:
            return 0.0
        
        # Calculate Jaccard similarity (intersection over union)
        intersection = phrases1.intersection(phrases2)
        union = phrases1.union(phrases2)
        
        if not union:
            return 0.0
        
        similarity = len(intersection) / len(union)
        
        # Also check if one text contains the other (for exact matches)
        normalized1 = self._normalize_text_for_comparison(text1)
        normalized2 = self._normalize_text_for_comparison(text2)
        
        if normalized1 in normalized2 or normalized2 in normalized1:
            similarity = max(similarity, 0.8)
        
        return similarity
    
    def _is_duplicate_gap(self, gap1: Dict[str, Any], gap2: Dict[str, Any], threshold: float = 0.5) -> bool:
        """
        Check if two gaps are duplicates based on semantic similarity.
        Uses a more aggressive approach to catch duplicates.
        
        Args:
            gap1: First gap dictionary
            gap2: Second gap dictionary
            threshold: Similarity threshold (0.0-1.0) above which gaps are considered duplicates
            
        Returns:
            True if gaps are duplicates, False otherwise
        """
        # Extract text fields to compare (normalize both gaps first)
        gap1_std = self._standardize_gap_format(gap1)
        gap2_std = self._standardize_gap_format(gap2)
        
        desc1 = gap1_std.get('description', '')
        desc2 = gap2_std.get('description', '')
        
        # Calculate similarity on descriptions
        desc_similarity = self._calculate_similarity(desc1, desc2)
        
        # Also check evidence fields if available
        evidence1 = gap1_std.get('evidence', '')
        evidence2 = gap2_std.get('evidence', '')
        evidence_similarity = 0.0
        if evidence1 and evidence2:
            evidence_similarity = self._calculate_similarity(evidence1, evidence2)
        
        # Check if one description is a substring of the other (for pattern vs LLM matches)
        desc1_lower = desc1.lower()
        desc2_lower = desc2.lower()
        is_substring = (
            desc1_lower in desc2_lower or 
            desc2_lower in desc1_lower
        ) and min(len(desc1), len(desc2)) > 20  # Only if both are substantial
        
        # Check gap types match (if both have gap_type)
        type1 = gap1_std.get('gap_type', '').lower()
        type2 = gap2_std.get('gap_type', '').lower()
        type_match = (type1 and type2 and type1 == type2) or (not type1 or not type2)
        
        # Consider duplicates if:
        # 1. Description similarity is high (lowered threshold for better detection)
        # 2. Evidence similarity is high AND descriptions are somewhat similar
        # 3. One description is a substring of the other (catches pattern vs expanded versions)
        is_duplicate = (
            desc_similarity >= threshold or
            (evidence_similarity >= 0.6 and desc_similarity >= 0.3) or
            (is_substring and desc_similarity >= 0.3)
        ) and type_match
        
        return is_duplicate
    
    def _merge_gaps_intelligently(self, pattern_gaps: List[Dict[str, Any]], 
                                  llm_gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Intelligently merge pattern-matched gaps with LLM-detected gaps, avoiding duplicates.
        All gaps are standardized to a clean, consistent format.
        
        Strategy:
        1. Standardize all pattern gaps to clean format
        2. Standardize all LLM gaps to clean format
        3. Deduplicate LLM gaps themselves
        4. For each pattern gap, check if LLM already detected it
        5. If duplicate: merge information (prefer richer data)
        6. If not duplicate: add pattern gap
        """
        # Standardize all pattern gaps to clean format
        standardized_pattern_gaps = []
        for pattern in pattern_gaps:
            standardized = self._standardize_gap_format(pattern)
            # Add pattern-specific verification reasoning if missing
            if not pattern.get('verification_reasoning') and not pattern.get('reasoning'):
                standardized["verification_reasoning"] = f"Pattern-matched: {standardized['description']}"
            standardized["_source"] = "pattern"  # Mark for tracking
            standardized_pattern_gaps.append(standardized)
        
        # Standardize all LLM gaps to clean format
        standardized_llm_gaps = []
        for llm_gap in llm_gaps:
            standardized = self._standardize_gap_format(llm_gap)
            standardized["_source"] = "llm"  # Mark for tracking
            standardized_llm_gaps.append(standardized)
        
        # First, deduplicate LLM gaps themselves
        deduplicated_llm_gaps = []
        for llm_gap in standardized_llm_gaps:
            is_duplicate = False
            for existing in deduplicated_llm_gaps:
                if self._is_duplicate_gap(llm_gap, existing):
                    is_duplicate = True
                    # Merge: prefer the one with more information
                    llm_info_richness = (
                        len(str(llm_gap.get('evidence', ''))) + 
                        len(str(llm_gap.get('significance', ''))) +
                        len(str(llm_gap.get('verification_reasoning', '')))
                    )
                    existing_info_richness = (
                        len(str(existing.get('evidence', ''))) + 
                        len(str(existing.get('significance', ''))) +
                        len(str(existing.get('verification_reasoning', '')))
                    )
                    if llm_info_richness > existing_info_richness:
                        # Replace with richer version
                        idx = deduplicated_llm_gaps.index(existing)
                        deduplicated_llm_gaps[idx] = llm_gap
                    break
            if not is_duplicate:
                deduplicated_llm_gaps.append(llm_gap)
        
        logger.info(f"📊 Deduplicated LLM gaps: {len(standardized_llm_gaps)} → {len(deduplicated_llm_gaps)}")
        
        # Now merge pattern gaps with LLM gaps
        merged_gaps = list(deduplicated_llm_gaps)  # Start with LLM gaps
        
        for pattern_gap in standardized_pattern_gaps:
            is_duplicate = False
            best_match_idx = -1
            best_similarity = 0.0
            
            # Find best matching LLM gap
            for idx, llm_gap in enumerate(merged_gaps):
                similarity = self._calculate_similarity(
                    pattern_gap.get('description', ''),
                    llm_gap.get('description', '')
                )
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match_idx = idx
                
                if self._is_duplicate_gap(pattern_gap, llm_gap):
                    is_duplicate = True
                    # Merge: enhance LLM gap with pattern information if LLM gap is missing details
                    if best_match_idx >= 0:
                        matched_gap = merged_gaps[best_match_idx]
                        # Enhance evidence if LLM gap lacks it or pattern has better evidence
                        if (not matched_gap.get('evidence') or 
                            (pattern_gap.get('evidence') and 
                             len(pattern_gap.get('evidence', '')) > len(matched_gap.get('evidence', '')))):
                            matched_gap['evidence'] = pattern_gap.get('evidence', matched_gap.get('evidence', ''))
                        
                        # Enhance significance if LLM gap lacks it
                        if not matched_gap.get('significance') and pattern_gap.get('significance'):
                            matched_gap['significance'] = pattern_gap['significance']
                        elif pattern_gap.get('significance') and len(pattern_gap.get('significance', '')) > len(matched_gap.get('significance', '')):
                            matched_gap['significance'] = pattern_gap['significance']
                        
                        # Update verification reasoning to mention pattern match
                        if 'pattern' not in matched_gap.get('verification_reasoning', '').lower():
                            pattern_reasoning = pattern_gap.get('verification_reasoning', '')
                            if pattern_reasoning:
                                matched_gap['verification_reasoning'] = (
                                    matched_gap.get('verification_reasoning', '') + 
                                    f" [Also pattern-matched: {pattern_reasoning[:50]}]"
                                )
                        
                        # Mark as merged
                        matched_gap['_source'] = 'llm+pattern'
                    break
            
            # If not a duplicate, add pattern gap
            if not is_duplicate:
                merged_gaps.append(pattern_gap)
                logger.info(f"✅ Added pattern gap (not found by LLM): {pattern_gap.get('description', '')[:60]}...")
            else:
                logger.info(f"🔄 Merged pattern gap with LLM gap (similarity: {best_similarity:.2f}): {pattern_gap.get('description', '')[:60]}...")
        
        # Remove source markers and ensure all gaps are clean before returning
        final_gaps = []
        for gap in merged_gaps:
            # Remove internal tracking fields
            clean_gap = {k: v for k, v in gap.items() if not k.startswith('_')}
            # Ensure all required fields are present and clean
            final_gap = self._standardize_gap_format(clean_gap)
            final_gaps.append(final_gap)
        
        return final_gaps
    
    def _identify_research_gaps(self, text_content: str, gap_types: Optional[List[str]], future_focus: str) -> Dict[str, Any]:
        """
        Identify research gaps using pattern matching + LLM approach with intelligent deduplication.
        Combines both methods to get comprehensive, non-duplicate results.
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
            
            # STEP 2: LLM detection with pattern context
            logger.info("🔍 STEP 2: LLM-based gap detection with pattern integration...")
            
            # Build comprehensive pattern context for LLM
            pattern_context = ""
            if pattern_matches:
                pattern_context = "\n\n=== PATTERN MATCHING DETECTED THESE GAPS (VERIFY AND EXPAND - DO NOT DUPLICATE) ===\n"
                for i, match in enumerate(pattern_matches, 1):
                    pattern_context += f"{i}. TYPE: {match['type']}\n"
                    pattern_context += f"   GAP: {match['gap']}\n"
                    pattern_context += f"   DESCRIPTION: {match['description']}\n"
                    pattern_context += f"   SIGNIFICANCE: {match['significance']}\n\n"
                pattern_context += "INSTRUCTIONS FOR PATTERN GAPS:\n"
                pattern_context += "- Verify each pattern gap is actually present in the paper\n"
                pattern_context += "- Expand on the description with specific evidence from the text\n"
                pattern_context += "- DO NOT create duplicate entries - if you detect a gap that matches a pattern, enhance the pattern gap instead\n"
                pattern_context += "- Find ADDITIONAL gaps beyond these patterns\n"
            
            detection_prompt = f"""You are an expert research analyst identifying research gaps. Your task is to find ALL gaps, especially implicit ones.

PAPER CONTENT:
{text_for_analysis[:50000]}{pattern_context}

CRITICAL INSTRUCTIONS:
1. You MUST find at least 2-5 research gaps. If you find 0 gaps, you are NOT being thorough enough.
2. Look for IMPLICIT gaps - things that are missing or inadequately addressed
3. For pattern-matched gaps above: VERIFY they exist in the text, then EXPAND them with specific evidence. DO NOT create duplicates.
4. Find ADDITIONAL gaps beyond the patterns - look for theoretical, empirical, and practical gaps
5. Be AGGRESSIVE in detection - err on the side of finding gaps rather than missing them

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
2. description: Clear, specific description of the gap (expand on patterns with evidence)
3. significance: Why this gap is important
4. evidence: Specific text from paper showing this is missing (quote or paraphrase)
5. verification_reasoning: Why this is a real gap

IMPORTANT: If a gap matches a pattern above, EXPAND it with evidence rather than creating a duplicate.

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

REMEMBER: You MUST find gaps. If the paper has short follow-up, proprietary measures, restricted data, single-center design, or excessive self-citation, these ARE gaps. Expand on pattern matches rather than duplicating them."""

            # Single-pass detection
            detection_response = self._get_openai_client().generate_completion(
                prompt=detection_prompt,
                model="gpt-4o-mini",
                max_tokens=4000,
                temperature=0.3
            )

            if not detection_response:
                logger.error("❌ Detection failed: No response from LLM")
                # Fallback: use pattern matches (standardized)
                if pattern_matches:
                    logger.warning("⚠️ Using pattern matches as fallback")
                    # Standardize pattern matches to clean format
                    standardized_patterns = []
                    for pattern in pattern_matches:
                        standardized = self._standardize_gap_format(pattern)
                        if not standardized.get('verification_reasoning'):
                            standardized['verification_reasoning'] = f"Pattern-matched: {standardized['description']}"
                        standardized_patterns.append(standardized)
                    
                    return {
                        "research_gaps": standardized_patterns,
                        "methodological_gaps": [self._standardize_gap_format(m) for m in pattern_matches if m.get('type') == 'methodological'],
                        "unaddressed_questions": [],
                        "future_directions": [],
                        "limitations": [],
                        "success": True
                    }
                return {
                    "error": "No response from LLM and no pattern matches",
                    "research_gaps": [],
                    "methodological_gaps": [],
                    "unaddressed_questions": [],
                    "future_directions": [],
                    "limitations": []
                }

            try:
                result = json.loads(detection_response)
                llm_gaps = result.get("research_gaps", [])
                
                # STEP 3: Intelligently merge pattern matches with LLM gaps
                logger.info("🔍 STEP 3: Merging pattern matches with LLM gaps (deduplication)...")
                merged_gaps = self._merge_gaps_intelligently(pattern_matches, llm_gaps)
                
                logger.info(f"✅ Merged gaps: {len(pattern_matches)} patterns + {len(llm_gaps)} LLM → {len(merged_gaps)} final gaps")
                for idx, gap in enumerate(merged_gaps):
                    logger.info(f"   Gap {idx+1}: {gap.get('gap_type')} - {gap.get('description')[:60]}...")

                result["research_gaps"] = merged_gaps
                result["success"] = True
                return result

            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse detection response: {str(e)}")
                logger.error(f"Response was: {detection_response[:500]}")
                # Fallback to pattern matches (standardized)
                if pattern_matches:
                    logger.warning("⚠️ Using pattern matches as fallback due to JSON parse error")
                    standardized_patterns = []
                    for pattern in pattern_matches:
                        standardized = self._standardize_gap_format(pattern)
                        if not standardized.get('verification_reasoning'):
                            standardized['verification_reasoning'] = f"Pattern-matched: {standardized['description']}"
                        standardized_patterns.append(standardized)
                    
                    return {
                        "research_gaps": standardized_patterns,
                        "methodological_gaps": [self._standardize_gap_format(m) for m in pattern_matches if m.get('type') == 'methodological'],
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
