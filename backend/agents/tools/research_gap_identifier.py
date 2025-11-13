"""
Research Gap Identifier Tool for QualiLens.

This tool identifies research gaps and future directions in research papers.
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
                future_focus: str = "general") -> Dict[str, Any]:
        """
        Identify research gaps and future directions.
        
        Args:
            text_content: The text content to analyze
            gap_types: Types of gaps to identify
            future_focus: Focus area for future directions
            
        Returns:
            Dict containing research gaps and future directions
        """
        try:
            logger.info(f"Identifying research gaps with focus: {future_focus}")
            
            # Generate gap identification analysis
            gap_analysis = self._identify_research_gaps(text_content, gap_types, future_focus)
            
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
    
    def _identify_research_gaps(self, text_content: str, gap_types: Optional[List[str]], future_focus: str) -> Dict[str, Any]:
        """
        Identify research gaps and future directions using two-step chain-of-thought reasoning.

        Step 1: Brainstorm potential research gaps (creative, temperature > 0)
        Step 2: Verify and evaluate each potential gap (deterministic, temperature = 0)
        """
        try:
            # STEP 1: Brainstorm potential research gaps (more creative)
            logger.info("Step 1: Brainstorming potential research gaps...")
            brainstorm_prompt = f"""
You are an expert research analyst with deep knowledge across multiple domains. Your task is to BRAINSTORM potential research gaps in this paper.

PAPER CONTENT:
{text_content[:6000]}

{f"SPECIFIC GAP TYPES TO CONSIDER: {', '.join(gap_types)}" if gap_types else ""}
FUTURE FOCUS AREA: {future_focus}

BRAINSTORMING INSTRUCTIONS:
- Be thorough and creative in identifying POTENTIAL gaps
- This is a brainstorming phase - include anything that MIGHT be a gap or limitation
- Think about what's missing, unexplored, or inadequately addressed
- Consider methodological, theoretical, practical, and empirical gaps
- Don't worry about false positives at this stage

For each potential gap, think through:
1. What is missing or inadequately addressed?
2. Why might this be important?
3. What evidence suggests this is a gap?

Provide your brainstorming in JSON format:
{{
  "potential_gaps": [
    {{
      "gap_type": "methodological | theoretical | empirical | practical | conceptual",
      "initial_assessment": "What MIGHT be missing or inadequately addressed",
      "evidence": "Why you think this might be a gap",
      "potential_significance": "Why this could be important if it's a real gap",
      "reasoning": "Your chain-of-thought reasoning"
    }}
  ],
  "potential_future_directions": [
    {{
      "direction": "Potential research direction",
      "rationale": "Why this might be worth pursuing",
      "reasoning": "Your chain-of-thought"
    }}
  ]
}}

GAP CATEGORIES TO CONSIDER:
1. Methodological: Missing methods, inadequate controls, sample limitations, measurement issues
2. Theoretical: Unexplored frameworks, missing constructs, theoretical underdevelopment
3. Empirical: Untested hypotheses, unexplored populations, missing variables, generalizability limits
4. Practical: Real-world applications not explored, implementation challenges unaddressed
5. Conceptual: Undefined terms, ambiguous concepts, inconsistent definitions

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
                potential_gaps = brainstormed.get("potential_gaps", [])
                potential_directions = brainstormed.get("potential_future_directions", [])
                logger.info(f"Step 1 complete: {len(potential_gaps)} potential gaps, {len(potential_directions)} potential directions identified")
            except json.JSONDecodeError:
                logger.error("Failed to parse brainstorming response")
                return {"error": "Failed to parse brainstorming results"}

            # STEP 2: Verify and evaluate each potential gap (deterministic)
            logger.info("Step 2: Verifying and evaluating potential gaps...")
            verification_prompt = f"""
You are a rigorous research evaluator. You will now VERIFY and EVALUATE each potential research gap identified in the brainstorming phase.

PAPER CONTENT:
{text_content[:6000]}

POTENTIAL GAPS TO VERIFY:
{json.dumps(potential_gaps, indent=2)}

POTENTIAL FUTURE DIRECTIONS TO EVALUATE:
{json.dumps(potential_directions, indent=2)}

VERIFICATION INSTRUCTIONS:
For each potential gap, you must:
1. Carefully examine whether it's truly a gap or already addressed in the paper
2. Determine if it's a REAL gap or a false positive
3. If it's a real gap, assess its significance and impact
4. Provide clear justification for your decision

Use chain-of-thought reasoning:
- ANALYZE: Is this actually missing from the paper?
- EVALUATE: If missing, is it a significant gap or minor limitation?
- ASSESS: What's the potential impact of addressing this gap?
- PRIORITIZE: How important is this gap relative to others?
- CONCLUDE: Should this be included as a confirmed research gap?

Provide your verification in JSON format:
{{
  "research_gaps": [
    {{
      "gap_type": "methodological | theoretical | empirical | practical",
      "description": "Clear description of the confirmed gap",
      "significance": "Why this gap is important and impactful",
      "evidence": "Evidence from the paper showing this is missing",
      "verification_reasoning": "Your chain-of-thought for why this IS a real gap"
    }}
  ],
  "rejected_gaps": [
    {{
      "gap_type": "type from potential list",
      "rejection_reasoning": "Why this is NOT a real gap after verification"
    }}
  ],
  "future_directions": [
    {{
      "direction": "Confirmed future research direction",
      "rationale": "Why this direction is important and feasible",
      "priority": "High | Medium | Low",
      "feasibility": "Assessment of how feasible this is"
    }}
  ],
  "limitations": [
    {{
      "limitation": "Confirmed study limitation",
      "impact": "How this affects the findings",
      "addressed": "How this could be addressed in future research"
    }}
  ],
  "unaddressed_questions": [
    {{
      "question": "Specific unaddressed research question",
      "importance": "Why this question matters",
      "research_approach": "How this could be investigated"
    }}
  ],
  "methodological_gaps": [
    {{
      "gap": "Specific methodological gap",
      "description": "What's missing methodologically",
      "improvement": "How methodology could be improved"
    }}
  ],
  "theoretical_gaps": [
    {{
      "gap": "Specific theoretical gap",
      "description": "What's missing theoretically",
      "development": "How theory could be developed"
    }}
  ],
  "research_priorities": ["Top priority research needs based on verified gaps"],
  "collaboration_opportunities": ["Potential collaboration areas based on gaps"],
  "funding_considerations": ["Funding opportunities related to addressing gaps"]
}}

VERIFICATION STANDARDS:
- Only include gaps that are genuinely missing or inadequately addressed
- Be conservative - distinguish between minor limitations and significant gaps
- Provide specific evidence from the paper
- Assess the real-world significance of each gap
- Different papers should yield different numbers and types of gaps based on actual content

IMPORTANT: The number of gaps should vary based on the paper's actual completeness:
- Comprehensive papers may have 0-2 major gaps
- Average papers may have 3-5 gaps
- Papers with significant limitations may have 6+ gaps
- Base this on ACTUAL analysis, not arbitrary numbers
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
                    logger.info(f"Step 2 complete: {len(result.get('research_gaps', []))} gaps confirmed, {len(result.get('rejected_gaps', []))} rejected")
                    return result
                except json.JSONDecodeError:
                    logger.error("Failed to parse verification response")
                    # Fallback if JSON parsing fails
                    return {
                        "research_gaps": [],
                        "rejected_gaps": [],
                        "future_directions": [],
                        "limitations": [],
                        "unaddressed_questions": [],
                        "methodological_gaps": [],
                        "theoretical_gaps": [],
                        "research_priorities": [],
                        "collaboration_opportunities": [],
                        "funding_considerations": []
                    }
            else:
                return {"error": "No response from Step 2 (verification)"}

        except Exception as e:
            logger.error(f"Research gap identification analysis failed: {str(e)}")
            return {"error": str(e)}
