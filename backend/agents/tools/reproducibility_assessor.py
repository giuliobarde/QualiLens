"""
Reproducibility Assessor Tool for QualiLens.

This tool evaluates the reproducibility of research studies.
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


class ReproducibilityAssessorTool(BaseTool):
    """
    Reproducibility Assessor tool for evaluating study reproducibility.
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
            name="reproducibility_assessor_tool",
            description="Evaluate the reproducibility of research studies",
            parameters={
                "required": ["text_content"],
                "optional": ["assessment_criteria", "reproducibility_level"],
                "properties": {
                    "text_content": {
                        "type": "string",
                        "description": "The text content to assess for reproducibility"
                    },
                    "assessment_criteria": {
                        "type": "array",
                        "description": "Specific reproducibility criteria to assess",
                        "default": []
                    },
                    "reproducibility_level": {
                        "type": "string",
                        "description": "Level of reproducibility assessment: 'basic', 'detailed'",
                        "default": "detailed"
                    }
                }
            },
            examples=[
                "Assess the reproducibility of this research study",
                "Evaluate if the study can be replicated",
                "Check for sufficient methodological detail"
            ],
            category="reproducibility_analysis"
        )
    
    def execute(self, text_content: str, assessment_criteria: Optional[List[str]] = None,
                reproducibility_level: str = "detailed", evidence_collector=None, 
                methodology_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Assess study reproducibility.
        
        Args:
            text_content: The text content to assess
            assessment_criteria: Specific criteria to assess
            reproducibility_level: Level of assessment
            
        Returns:
            Dict containing reproducibility assessment
        """
        try:
            logger.info(f"Assessing reproducibility with level: {reproducibility_level}")
            
            # Generate reproducibility assessment based on level
            if reproducibility_level == "basic":
                assessment_result = self._assess_basic_reproducibility(text_content, assessment_criteria, methodology_data)
            else:  # detailed
                assessment_result = self._assess_detailed_reproducibility(text_content, assessment_criteria, methodology_data)
            
            # Collect evidence if evidence_collector is provided
            if evidence_collector:
                logger.info(f"📊 Collecting evidence for reproducibility practices")

                # Collect POSITIVE evidence (good practices)
                good_practices = assessment_result.get("good_practices", [])
                for idx, practice in enumerate(good_practices):
                    # Use full_section_text with priority
                    evidence_text = practice.get("full_section_text", "")

                    if not evidence_text or len(evidence_text) < 50:
                        evidence_text = practice.get("evidence", "")

                    if not evidence_text or len(evidence_text) < 50:
                        evidence_text = practice.get("description", "")

                    # Last resort: search in text
                    if not evidence_text or len(evidence_text) < 50:
                        section_name = practice.get("section_name", "")
                        if section_name:
                            evidence_text = self._find_text_snippet(text_content, section_name) or evidence_text

                    # Calculate score impact based on quality
                    quality_rating = practice.get("quality_rating", "adequate")
                    completeness = practice.get("completeness", 0.7)

                    if quality_rating == "excellent":
                        score_impact = +15.0 * completeness
                        confidence = 0.9
                    elif quality_rating == "good":
                        score_impact = +10.0 * completeness
                        confidence = 0.8
                    else:  # adequate
                        score_impact = +6.0 * completeness
                        confidence = 0.7

                    # Build rationale with chain-of-thought
                    section_name = practice.get("section_name", "Unknown section")
                    verification_reasoning = practice.get("verification_reasoning", "")
                    impact = practice.get("impact_on_reproducibility", "")

                    rationale_parts = [f"Good reproducibility practice in: {section_name}"]

                    if verification_reasoning:
                        rationale_parts.append(f"Reasoning: {verification_reasoning}")

                    if impact:
                        rationale_parts.append(f"Impact: {impact}")

                    full_rationale = " | ".join(rationale_parts)

                    # Determine snippet length
                    max_snippet_length = 1500 if practice.get("full_section_text") else 400
                    text_to_add = evidence_text[:max_snippet_length] if evidence_text else practice.get("description", "")[:400]

                    if evidence_text and len(evidence_text) > max_snippet_length:
                        text_to_add = text_to_add + "... [truncated for display]"
                        logger.info(f"   ⚠️  Evidence text truncated from {len(evidence_text)} to {max_snippet_length} chars for practice {idx+1}")

                    evidence_id = evidence_collector.add_evidence(
                        category="reproducibility",
                        text_snippet=text_to_add,
                        rationale=full_rationale[:1200],
                        confidence=confidence,
                        score_impact=score_impact
                    )

                    logger.info(f"✅ Added POSITIVE evidence {evidence_id}: {section_name} ({quality_rating}, impact: +{score_impact:.1f}, text_length: {len(text_to_add)} chars)")

                # Collect NEGATIVE evidence (bad practices / barriers)
                bad_practices = assessment_result.get("bad_practices", [])
                for idx, practice in enumerate(bad_practices):
                    # Use full_section_text with priority
                    evidence_text = practice.get("full_section_text", "")

                    if not evidence_text or len(evidence_text) < 50:
                        evidence_text = practice.get("evidence", "")

                    if not evidence_text or len(evidence_text) < 50:
                        evidence_text = practice.get("description", "")

                    # Last resort: search in text
                    if not evidence_text or len(evidence_text) < 50:
                        section_name = practice.get("section_name", "")
                        if section_name:
                            evidence_text = self._find_text_snippet(text_content, section_name) or evidence_text

                    # Calculate score impact based on severity
                    severity = practice.get("severity", "medium")

                    if severity == "high":
                        score_impact = -15.0
                        confidence = 0.85
                    elif severity == "medium":
                        score_impact = -8.0
                        confidence = 0.75
                    else:  # low
                        score_impact = -4.0
                        confidence = 0.65

                    # Build rationale with chain-of-thought
                    section_name = practice.get("section_name", "Unknown section")
                    verification_reasoning = practice.get("verification_reasoning", "")
                    impact = practice.get("impact_on_reproducibility", "")

                    rationale_parts = [f"Reproducibility barrier in: {section_name}"]

                    if verification_reasoning:
                        rationale_parts.append(f"Reasoning: {verification_reasoning}")

                    if impact:
                        rationale_parts.append(f"Impact: {impact}")

                    full_rationale = " | ".join(rationale_parts)

                    # Determine snippet length
                    max_snippet_length = 1500 if practice.get("full_section_text") else 400
                    text_to_add = evidence_text[:max_snippet_length] if evidence_text else practice.get("description", "")[:400]

                    if evidence_text and len(evidence_text) > max_snippet_length:
                        text_to_add = text_to_add + "... [truncated for display]"
                        logger.info(f"   ⚠️  Evidence text truncated from {len(evidence_text)} to {max_snippet_length} chars for barrier {idx+1}")

                    evidence_id = evidence_collector.add_evidence(
                        category="reproducibility",
                        text_snippet=text_to_add,
                        rationale=full_rationale[:1200],
                        severity=severity,
                        confidence=confidence,
                        score_impact=score_impact
                    )

                    logger.info(f"✅ Added NEGATIVE evidence {evidence_id}: {section_name} ({severity} severity, impact: {score_impact:.1f}, text_length: {len(text_to_add)} chars)")
            
            # Calculate base score with methodology adjustment
            raw_score = assessment_result.get("reproducibility_score", 0.0)
            
            # Calculate methodology-based baseline and adjustment
            methodology_baseline, methodology_adjustment = self._calculate_methodology_based_score(methodology_data)
            
            # Start with methodology baseline (higher default, typically 0.40-0.60)
            if raw_score < 0.10:
                # Use methodology baseline if score is too low
                adjusted_score = methodology_baseline
                logger.info(f"📊 Raw score {raw_score:.2f} too low, using methodology baseline: {methodology_baseline:.2f}")
            else:
                # Apply methodology adjustment to raw score
                adjusted_score = max(0.20, min(1.0, raw_score + methodology_adjustment))
                logger.info(f"📊 Raw score: {raw_score:.2f}, methodology adjustment: {methodology_adjustment:+.2f}, final: {adjusted_score:.2f}")
            
            final_score = adjusted_score

            logger.info(f"📊 Final reproducibility score: {final_score:.2f} (raw: {raw_score:.2f}, methodology baseline: {methodology_baseline:.2f}, adjustment: {methodology_adjustment:+.2f})")

            return {
                "success": True,
                "reproducibility_score": final_score,  # Use final_score, not raw
                "score_breakdown": assessment_result.get("score_breakdown", {}),
                "good_practices": assessment_result.get("good_practices", []),
                "bad_practices": assessment_result.get("bad_practices", []),
                "reclassified_sections": assessment_result.get("reclassified_sections", []),
                "methodological_detail": assessment_result.get("methodological_detail", ""),
                "data_availability": assessment_result.get("data_availability", ""),
                "code_availability": assessment_result.get("code_availability", ""),
                "reproducibility_barriers": assessment_result.get("reproducibility_barriers", []),
                "recommendations": assessment_result.get("recommendations", []),
                "overall_assessment": assessment_result.get("overall_assessment", ""),
                "assessment_criteria": assessment_criteria or [],
                "reproducibility_level": reproducibility_level,
                "tool_used": "reproducibility_assessor_tool"
            }
            
        except Exception as e:
            logger.error(f"Reproducibility assessment failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_used": "reproducibility_assessor_tool"
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
    
    def _calculate_methodology_based_score(self, methodology_data: Optional[Dict[str, Any]]) -> tuple:
        """
        Calculate baseline reproducibility score and adjustment based on methodology type.
        
        Returns:
            (baseline_score, adjustment): Baseline score (0.0-1.0) and adjustment (-0.2 to +0.2)
        """
        if not methodology_data:
            # Default baseline for unknown methodology
            return (0.45, 0.0)
        
        # Extract detected methodologies
        detected_methodologies = methodology_data.get("detected_methodologies", {})
        methodologies_list = detected_methodologies.get("methodologies", [])
        
        if not methodologies_list:
            # No methodologies detected, use moderate baseline
            return (0.45, 0.0)
        
        # First, try to use reproducibility_impact from methodology analysis if available
        best_baseline = 0.45  # Default moderate baseline
        best_adjustment = 0.0
        
        for methodology in methodologies_list:
            reproducibility_impact = methodology.get("reproducibility_impact", {})
            if reproducibility_impact:
                score_contribution = reproducibility_impact.get("reproducibility_score_contribution")
                if score_contribution:
                    try:
                        # Convert string to float if needed
                        if isinstance(score_contribution, str):
                            # Extract number from string like "0.65" or "0.6+"
                            import re
                            match = re.search(r'(\d+\.?\d*)', str(score_contribution))
                            if match:
                                score_contribution = float(match.group(1))
                            else:
                                score_contribution = None
                        
                        if score_contribution and isinstance(score_contribution, (int, float)):
                            # Use the methodology's own reproducibility assessment
                            baseline_from_methodology = float(score_contribution)
                            if baseline_from_methodology > best_baseline:
                                best_baseline = baseline_from_methodology
                                logger.info(f"📊 Using methodology-provided reproducibility baseline: {best_baseline:.2f}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Could not parse reproducibility_score_contribution: {score_contribution}")
        
        # If we got a good baseline from methodology, use it; otherwise fall back to lookup table
        if best_baseline > 0.50:  # If we got a high baseline from methodology analysis
            return (best_baseline, 0.0)
        
        # Fallback: Methodology-specific baselines and adjustments (if methodology didn't provide score)
        methodology_scores = {
            # High reproducibility potential
            "randomized controlled trial": (0.65, +0.10),  # RCTs typically well-documented
            "systematic review": (0.70, +0.15),  # Reviews often have detailed protocols
            "meta-analysis": (0.70, +0.15),  # Meta-analyses require detailed methods
            "laboratory experiment": (0.55, +0.05),  # Lab experiments often have detailed protocols
            "field experiment": (0.50, 0.0),  # Field experiments moderate
            "cohort study": (0.60, +0.08),  # Cohort studies often well-documented
            "case-control study": (0.55, +0.05),  # Case-control studies moderate-high
            "longitudinal study": (0.58, +0.08),  # Longitudinal studies need detailed tracking
            
            # Moderate reproducibility potential
            "cross-sectional study": (0.50, 0.0),  # Cross-sectional moderate
            "survey": (0.48, -0.02),  # Surveys can be vague
            "quasi-experimental": (0.52, +0.02),  # Quasi-experimental moderate
            "observational": (0.48, -0.02),  # Observational can be less detailed
            
            # Lower reproducibility potential (but still start higher)
            "qualitative": (0.42, -0.05),  # Qualitative methods can be less standardized
            "case study": (0.40, -0.08),  # Case studies often less reproducible
            "ethnography": (0.38, -0.10),  # Ethnography highly context-dependent
            "grounded theory": (0.40, -0.08),  # Grounded theory less standardized
            "narrative analysis": (0.38, -0.10),  # Narrative analysis less reproducible
        }
        
        # Find best matching methodology (only if we didn't get baseline from reproducibility_impact)
        lookup_baseline = 0.45  # Default for lookup
        lookup_adjustment = 0.0
        
        if best_baseline <= 0.50:  # Only use lookup if we don't have good methodology-based score
            for methodology in methodologies_list:
                methodology_type = methodology.get("type", "").lower()
                quality_rating = methodology.get("quality_assessment", {}).get("quality_rating", "fair").lower()
                
                # Check for exact or partial matches
                for key, (baseline, adjustment) in methodology_scores.items():
                    if key in methodology_type:
                        # Quality rating affects adjustment
                        quality_multiplier = {
                            "excellent": 1.2,
                            "good": 1.0,
                            "fair": 0.8,
                            "poor": 0.5,
                            "very_poor": 0.3
                        }.get(quality_rating, 1.0)
                        
                        adjusted_adjustment = adjustment * quality_multiplier
                        
                        # Use the methodology with highest baseline
                        if baseline > lookup_baseline:
                            lookup_baseline = baseline
                            lookup_adjustment = adjusted_adjustment
            
            # If no match found, use default with slight positive adjustment for having methodology
            if lookup_baseline == 0.45:
                lookup_adjustment = +0.05  # Small positive for having any methodology detected
            
            # Use lookup results
            best_baseline = lookup_baseline
            best_adjustment = lookup_adjustment
        
        logger.info(f"📊 Methodology-based scoring: baseline={best_baseline:.2f}, adjustment={best_adjustment:+.2f}")
        
        return (best_baseline, best_adjustment)
    
    def _assess_basic_reproducibility(self, text_content: str, assessment_criteria: Optional[List[str]], 
                                      methodology_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Assess basic reproducibility elements."""
        try:
            prompt = f"""
You are an expert research analyst. Provide a basic assessment of the reproducibility of this research study.

PAPER CONTENT:
{text_content[:6000]}

{f"SPECIFIC CRITERIA TO ASSESS: {', '.join(assessment_criteria)}" if assessment_criteria else ""}

Provide basic reproducibility assessment in JSON format:
{{
  "reproducibility_score": 0.0-1.0,  // Calculate actual score based on content analysis
  "methodological_detail": "Assessment of methodological detail provided",
  "data_availability": "Information about data availability",
  "code_availability": "Information about code availability",
  "reproducibility_barriers": [
    "Barrier 1",
    "Barrier 2"
  ],
  "recommendations": [
    "Recommendation 1",
    "Recommendation 2"
  ]
}}

IMPORTANT: Calculate the reproducibility_score based on actual content analysis. Consider:
- Methodological detail provided (0.0-0.3 points)
- Data availability mentioned (0.0-0.3 points) 
- Code availability mentioned (0.0-0.2 points)
- Reproducibility barriers identified (0.0-0.2 points)
- Provide a realistic score between 0.0 and 1.0 based on the actual content

Focus on the most essential reproducibility elements.
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-4o-mini",
                max_tokens=1000,
                temperature=0.0  # Deterministic for consistency
            )
            
            if llm_response:
                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    return {"error": "Could not parse reproducibility assessment"}
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Basic reproducibility assessment failed: {str(e)}")
            return {"error": str(e)}
    
    def _assess_detailed_reproducibility(self, text_content: str, assessment_criteria: Optional[List[str]], 
                                        methodology_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Assess detailed reproducibility using a comprehensive two-phase approach.

        PHASE 1: Section-Level Analysis
        - Scan entire paper to identify sections with reproducibility practices (good or bad)
        - Extract complete text of each section
        - Flag as positive practice (helps reproducibility) or negative practice (hinders reproducibility)

        PHASE 2: Detailed Verification with Chain-of-Thought
        - Verify each flagged section
        - Determine if it's actually a good/bad practice
        - Provide explicit reasoning
        - Calculate reproducibility score based on confirmed practices
        """
        try:
            # PHASE 1: Identify sections with reproducibility practices
            logger.info("🔍 PHASE 1: Identifying sections with reproducibility practices across the paper...")
            
            # Extract methodology information for context
            methodology_context = ""
            if methodology_data:
                detected_methodologies = methodology_data.get("detected_methodologies", {})
                methodologies_list = detected_methodologies.get("methodologies", [])
                if methodologies_list:
                    methodology_types = [m.get("type", "Unknown") for m in methodologies_list[:3]]
                    methodology_context = f"\n\nDETECTED METHODOLOGIES: {', '.join(methodology_types)}\n"
                    methodology_context += "Consider how these methodology types typically affect reproducibility. For example:\n"
                    methodology_context += "- RCTs and systematic reviews typically have higher reproducibility standards\n"
                    methodology_context += "- Qualitative studies may have different reproducibility expectations\n"
                    methodology_context += "- Laboratory experiments often have detailed protocols\n"

            section_analysis_prompt = f"""
You are an expert in research reproducibility. Your task is to analyze this research paper and identify SECTIONS that contain reproducibility practices (either good or bad).

PAPER CONTENT:
{text_content[:8000]}

{methodology_context}

{f"SPECIFIC CRITERIA TO ASSESS: {', '.join(assessment_criteria)}" if assessment_criteria else ""}

PHASE 1 INSTRUCTIONS - SECTION-LEVEL REPRODUCIBILITY ANALYSIS:
Your goal is to scan through the ENTIRE paper and identify specific sections or passages that relate to reproducibility.

CRITICAL: For each section, extract the COMPLETE text so reviewers can see full context.

For each reproducibility-related section, provide:
1. Section name/location (e.g., "Methods - Data Availability", "Methods - Software Specification", "Methods - Procedural Detail")
2. The FULL TEXT of the section (100-500 words minimum - include complete context)
3. Practice type: "positive" (helps reproducibility) or "negative" (hinders reproducibility)
4. Reproducibility aspect: data_availability, code_availability, methodological_detail, materials_specification, software_environment, documentation, open_science_practices
5. Initial assessment of quality/completeness
6. Preliminary impact on reproducibility

Think systematically through these reproducibility aspects:

**POSITIVE PRACTICES (Things that HELP reproducibility):**

**HIGH-VALUE INDICATORS:**
- **Detailed Methodology**: Step-by-step procedures with exact parameters, timings, temperatures, concentrations; clear protocols others can follow exactly
- **Complete Data Availability**: Raw data in public repositories (OSF, Figshare, Dryad, Zenodo), with DOIs, clear data dictionaries, processing scripts
- **Code Transparency**: Full analysis scripts on GitHub/GitLab, version numbers, commented code, dependency lists, computational environment details
- **Material Specifications**: Precise details - brand names, catalog numbers, lot numbers, concentrations, suppliers, equipment models with version numbers
- **Pre-registration**: Study registered before data collection (ClinicalTrials.gov, OSF, AsPredicted), prevents selective reporting
- **Statistical Transparency**: All analyses reported (including negative results), sensitivity analyses, effect sizes with confidence intervals, power calculations
- **Sample Documentation**: Exact sample sizes with justification, participant demographics, detailed inclusion/exclusion criteria, randomization methods with code

**MEDIUM-VALUE INDICATORS:**
- **Software Environment**: Software versions (R 4.2.1, Python 3.9), package versions, operating system, computational environment specifications
- **Supplementary Materials**: Detailed appendices, additional methods, questionnaires, interview protocols, coding schemes
- **Documentation Quality**: README files, code comments, analysis notebooks (Jupyter/R Markdown), data processing pipelines
- **Time/Duration Specifics**: Exact incubation times, wait periods, intervention durations (not "briefly" or "overnight")
- **Measurement Protocols**: Specific measurement instruments, calibration procedures, inter-rater reliability, measurement schedules
- **Quality Control**: Validation procedures, pilot testing, quality checks, negative controls, positive controls

**LOW-VALUE BUT POSITIVE:**
- **Open Access**: Paper freely available, preprints shared
- **Replication Encouragement**: Authors explicitly welcome replication attempts
- **Data Upon Reasonable Request**: Contact provided, data sharing willingness stated
- **Collaboration Statements**: Multi-site studies with shared protocols

**NEGATIVE PRACTICES (Things that HINDER reproducibility):**

**HIGH-SEVERITY BARRIERS:**
- **Vague Methods**: Imprecise language like "samples were incubated briefly", "standard procedures", "appropriate methods", "as needed", "until ready"
- **No Data Sharing**: No mention of data availability, data kept private without justification, "data not available" without reason
- **Missing Code**: Computational analyses described but no code shared, "available upon request" (rarely fulfilled), proprietary analysis tools
- **Analytical Flexibility**: Signs of p-hacking, HARKing (hypothesizing after results known), outcome switching, selective reporting
- **Publication Bias Indicators**: Only positive results reported, missing negative findings, incomplete reporting of all outcomes measured
- **Proprietary Dependencies**: Critical reliance on expensive commercial software without free alternatives, custom equipment without specifications

**MEDIUM-SEVERITY BARRIERS:**
- **Underspecified Software**: "We used R" without version or packages, "SPSS was used" without specifics, missing dependency information
- **Incomplete Methods**: Key steps missing, unclear procedures, can't determine exact protocol from description
- **Missing Parameters**: No temperatures, timings, concentrations, pH values, specific settings
- **Sample Issues**: Unclear sampling method, convenience sampling without acknowledgment, selection bias not addressed
- **Statistical Issues**: Multiple testing without correction, optional stopping, incomplete statistical reporting
- **Materials Vagueness**: "Commercial kits were used" without names, "standard reagents", equipment without models

**LOW-SEVERITY BUT CONCERNING:**
- **Access Restrictions**: Paywalls for supplementary data, restricted access to materials, IRB restrictions without alternatives
- **Poor Documentation**: Minimal or no code comments, unclear variable names, missing metadata
- **Closed Science Practices**: No preprints, no pre-registration mentioned, conference presentations only
- **Limited Sharing**: "Available from authors" but no persistent identifier or repository

Provide your analysis in JSON format:
{{
  "reproducibility_sections": [
    {{
      "section_name": "Name/location of the section (e.g., 'Methods - Data Availability Statement')",
      "full_section_text": "COMPLETE TEXT of the entire section/paragraph (100-500 words). Include full context.",
      "practice_type": "positive | negative",
      "reproducibility_aspect": "data_availability | code_availability | methodological_detail | software_environment | materials_specification | documentation | open_science_practices | barriers",
      "initial_assessment": "Brief assessment of quality/completeness",
      "preliminary_impact": "How this helps or hinders reproducibility",
      "page_hint": "Rough location in paper"
    }}
  ]
}}

IMPORTANT INSTRUCTIONS FOR CREATIVE DETECTION:

1. **BE CREATIVE IN FINDING INDICATORS**: Don't just look for explicit "data available at..." statements. Look for:
   - Specific numerical parameters (temperatures, times, concentrations) = good methodological detail
   - Vague language ("briefly", "overnight", "standard methods") = poor methodological detail
   - Brand names and model numbers mentioned = good material specification
   - Generic descriptions ("commercial kit", "appropriate methods") = poor specification
   - Specific software versions ("R 4.2.1", "Python 3.9") = good environment documentation
   - Just software names ("we used SPSS") = poor environment documentation
   - Effect sizes, confidence intervals, power analyses = good statistical transparency
   - Just p-values without effect sizes = limited statistical transparency

2. **INFER FROM ABSENCE**: If you don't see:
   - Any mention of data sharing → flag as "negative practice: missing data"
   - Any specific timing/temperature details → flag as "negative practice: vague methods"
   - Any software version numbers → flag as "negative practice: underspecified software"
   - Any mention of pre-registration → (don't flag, but note absence in assessment)

3. **LOOK FOR RED FLAGS**:
   - Phrases like "data available upon request" (often unfulfilled)
   - "Standard procedures were followed" (not reproducible)
   - "Appropriate statistical tests" (which ones?)
   - "Samples were processed as needed" (how exactly?)
   - Multiple outcomes measured but only some reported (publication bias)

4. **GIVE CREDIT FOR PARTIAL EFFORTS**:
   - Even if data isn't in repository, mention of willingness to share is positive (low-value)
   - Even if methods are imperfect, specific details are better than none
   - Supplementary materials, even if incomplete, show transparency effort

5. **BE SYSTEMATIC**: Scan through these sections specifically:
   - Methods → Look for procedure details, timing, materials, software
   - Data Availability Statement → Repository links, DOIs, access info
   - Statistical Analysis section → Complete reporting, all analyses, effect sizes
   - Materials/Equipment lists → Specifications, catalog numbers, versions
   - Code/Software mentions → GitHub links, version numbers, packages
   - End of paper → Data availability, code availability, supplementary materials

**CRITICAL**: Extract the FULL SECTION TEXT. Look for what's PRESENT (positive) AND what's CONSPICUOUSLY ABSENT (negative).

Be thorough and creative - even papers without explicit data sharing statements can have reproducibility strengths in methodological detail!
"""

            # Phase 1: Section identification
            section_response = self._get_openai_client().generate_completion(
                prompt=section_analysis_prompt,
                model="gpt-4o-mini",
                max_tokens=3500,
                temperature=0.2  # Low temperature for systematic analysis
            )

            if not section_response:
                logger.error("❌ PHASE 1 failed: No response from LLM")
                return {"error": "No response from Phase 1 (section analysis)"}

            try:
                phase1_result = json.loads(section_response)
                reproducibility_sections = phase1_result.get("reproducibility_sections", [])
                logger.info(f"✅ PHASE 1 complete: {len(reproducibility_sections)} reproducibility-related sections identified")

                # Log details of flagged sections
                positive_count = sum(1 for s in reproducibility_sections if s.get('practice_type') == 'positive')
                negative_count = sum(1 for s in reproducibility_sections if s.get('practice_type') == 'negative')
                logger.info(f"   - {positive_count} positive practices (help reproducibility)")
                logger.info(f"   - {negative_count} negative practices (hinder reproducibility)")

                for idx, section in enumerate(reproducibility_sections):
                    logger.info(f"   Section {idx+1}: {section.get('section_name')} - {section.get('practice_type')} ({section.get('reproducibility_aspect')})")

            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse Phase 1 response: {str(e)}")
                logger.error(f"Response was: {section_response[:500]}")
                return {"error": "Failed to parse section analysis results"}

            if not reproducibility_sections:
                logger.warning("⚠️  No explicit reproducibility sections found - attempting creative inference...")

                # CREATIVE INFERENCE PHASE: Make educated guesses based on what we can see
                inference_prompt = f"""
You are a reproducibility expert. No explicit reproducibility sections were found, but you must still assess the paper creatively.

PAPER CONTENT:
{text_content[:8000]}

CREATIVE INFERENCE TASK:
Even without explicit data/code availability statements, you can still assess reproducibility by looking at:

1. **Methodological Detail Present**:
   - Are there ANY specific numbers? (sample sizes, temperatures, times, statistical values)
   - Are procedures described at all, even if vaguely?
   - Score based on what IS there, not what's missing

2. **Implicit Indicators**:
   - Statistical reporting (p-values, effect sizes, CIs) = some transparency
   - Sample size mentioned = some methodological detail
   - Software mentioned (even without version) = some environment info
   - Any procedural descriptions = some methodological detail

3. **Reasonable Baseline Score**:
   - If paper has methods section with ANY detail → 0.15-0.25
   - If paper reports statistics → +0.05
   - If paper mentions any tools/software → +0.02-0.04
   - If paper has reasonable sample description → +0.03

**DO NOT GIVE 0.0 SCORE** unless the paper literally has NO methods section and NO statistics.

Provide your INFERENCE in JSON format:
{{
  "inferred_practices": [
    {{
      "aspect": "methodological_detail | statistical_reporting | sample_description | software_mention",
      "evidence": "What you can see in the paper (quote specific text)",
      "quality": "minimal | basic | adequate",
      "score_contribution": 0.02-0.15,
      "reasoning": "Why this contributes to reproducibility even if incomplete"
    }}
  ],
  "inferred_barriers": [
    {{
      "barrier": "What's clearly missing",
      "severity": "low | medium | high",
      "evidence": "How you know it's missing"
    }}
  ],
  "reproducibility_score": 0.15-0.40,
  "score_reasoning": "Explicit reasoning for the score based on what IS present",
  "methodological_detail": "Assessment based on what exists",
  "data_availability": "Assessment (likely 'not mentioned' but state what IS there)",
  "code_availability": "Assessment (likely 'not mentioned' but state what IS there)",
  "recommendations": ["Specific recommendations to improve"]
}}

CRITICAL RULES:
- MINIMUM SCORE: 0.15 if there's any methods section
- LOOK FOR POSITIVES: Find what IS there, not just what's missing
- BE GENEROUS: Partial information is better than nothing
- USE INFERENCE: If paper discusses results, there must have been SOME methods

Think creatively - make educated guesses!
"""

                inference_response = self._get_openai_client().generate_completion(
                    prompt=inference_prompt,
                    model="gpt-4o-mini",
                    max_tokens=2000,
                    temperature=0.3  # Slightly higher for creative inference
                )

                if inference_response:
                    try:
                        inferred_result = json.loads(inference_response)

                        # Convert inferred_practices to good_practices format
                        good_practices = []
                        for practice in inferred_result.get("inferred_practices", []):
                            good_practices.append({
                                "section_name": f"Inferred - {practice.get('aspect', 'Unknown')}",
                                "practice_category": "methodological_detail",
                                "description": f"Inferred practice: {practice.get('evidence', '')}",
                                "full_section_text": practice.get("evidence", ""),
                                "evidence": practice.get("evidence", ""),
                                "quality_rating": practice.get("quality", "basic"),
                                "completeness": 0.3,
                                "impact_on_reproducibility": practice.get("reasoning", ""),
                                "verification_reasoning": f"Inferred from available evidence: {practice.get('reasoning', '')}",
                                "confidence_percentage": 60
                            })

                        # Convert inferred_barriers to bad_practices format
                        bad_practices = []
                        for barrier in inferred_result.get("inferred_barriers", []):
                            bad_practices.append({
                                "section_name": f"Missing - {barrier.get('barrier', 'Unknown')}",
                                "practice_category": "missing_data",
                                "description": barrier.get("barrier", ""),
                                "full_section_text": barrier.get("evidence", ""),
                                "evidence": barrier.get("evidence", ""),
                                "severity": barrier.get("severity", "medium"),
                                "impact_on_reproducibility": "This missing information hinders reproducibility",
                                "verification_reasoning": f"Inferred absence: {barrier.get('evidence', '')}",
                                "confidence_percentage": 70
                            })

                        # Adjust inferred score with methodology baseline
                        methodology_baseline, methodology_adjustment = self._calculate_methodology_based_score(methodology_data)
                        inferred_score = inferred_result.get("reproducibility_score", methodology_baseline)
                        adjusted_inferred_score = max(methodology_baseline * 0.8, min(1.0, inferred_score + methodology_adjustment))
                        
                        logger.info(f"✅ CREATIVE INFERENCE complete: Inferred {inferred_score:.2f}, adjusted to {adjusted_inferred_score:.2f} (methodology baseline: {methodology_baseline:.2f})")
                        logger.info(f"   - {len(good_practices)} practices inferred")
                        logger.info(f"   - {len(bad_practices)} barriers identified")

                        return {
                            "reproducibility_score": adjusted_inferred_score,
                            "good_practices": good_practices,
                            "bad_practices": bad_practices,
                            "methodological_detail": inferred_result.get("methodological_detail", "Limited information available"),
                            "data_availability": inferred_result.get("data_availability", "Not mentioned"),
                            "code_availability": inferred_result.get("code_availability", "Not mentioned"),
                            "reproducibility_barriers": inferred_result.get("inferred_barriers", []),
                            "recommendations": inferred_result.get("recommendations", []),
                            "overall_assessment": f"Assessment based on inference. Score reasoning: {inferred_result.get('score_reasoning', '')}"
                        }
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse inference response: {str(e)}")

                # Ultimate fallback with methodology-based baseline
                methodology_baseline, _ = self._calculate_methodology_based_score(methodology_data)
                logger.warning(f"⚠️  Inference failed - using methodology-based baseline: {methodology_baseline:.2f}")
                return {
                    "reproducibility_score": methodology_baseline,  # Use methodology-based baseline
                    "good_practices": [{
                        "section_name": "Baseline - Methods Section Exists",
                        "practice_category": "methodological_detail",
                        "description": "Paper contains a methods section with some procedural information",
                        "quality_rating": "basic",
                        "completeness": 0.3,
                        "confidence_percentage": 50
                    }],
                    "bad_practices": [{
                        "section_name": "Missing - Data Availability",
                        "practice_category": "missing_data",
                        "description": "No data availability statement found",
                        "severity": "high",
                        "confidence_percentage": 80
                    }, {
                        "section_name": "Missing - Code Availability",
                        "practice_category": "missing_code",
                        "description": "No code availability information found",
                        "severity": "high",
                        "confidence_percentage": 80
                    }],
                    "methodological_detail": "Basic methods section present, but lacking specific reproducibility details",
                    "data_availability": "Not mentioned in paper",
                    "code_availability": "Not mentioned in paper",
                    "reproducibility_barriers": [
                        {"barrier": "No data sharing statement", "severity": "high"},
                        {"barrier": "No code sharing information", "severity": "high"}
                    ],
                    "recommendations": [
                        "Add data availability statement with repository link",
                        "Share analysis code on GitHub or similar platform",
                        "Include more specific methodological details (parameters, versions, procedures)"
                    ],
                    "overall_assessment": "Paper has basic methods but lacks explicit reproducibility practices. Score of 0.20 based on minimal baseline assessment."
                }

            # PHASE 2: Detailed verification with chain-of-thought reasoning
            logger.info(f"🔍 PHASE 2: Verifying {len(reproducibility_sections)} reproducibility sections...")

            verification_prompt = f"""
You are a rigorous reproducibility expert. You will now VERIFY each reproducibility section identified in Phase 1.

PAPER CONTENT:
{text_content[:8000]}

REPRODUCIBILITY SECTIONS TO VERIFY:
{json.dumps(reproducibility_sections, indent=2)}

PHASE 2 INSTRUCTIONS - DETAILED VERIFICATION WITH CHAIN-OF-THOUGHT:

For EACH reproducibility section, you must:

1. **RE-EXAMINE THE EVIDENCE**: Look at the full section text and context
2. **APPLY CHAIN-OF-THOUGHT REASONING**:
   - ANALYZE: What specific reproducibility information is provided (or missing)?
   - CONTEXT: What are best practices in this research field?
   - EVALUATE: Is this truly a good/bad practice, or is it acceptable given constraints?
   - QUALITY: How complete and useful is this information?
   - IMPACT: How significantly does this affect someone's ability to reproduce the study?
3. **MAKE A DECISION**: Is this actually a good practice or bad practice?
4. **PROVIDE EXPLICIT REASONING**: Explain your decision step-by-step

CRITICAL CLASSIFICATION THRESHOLD:
- Only REJECT/RECLASSIFY a practice if you are >90% CONFIDENT it's misclassified
- When in doubt (50-90% confidence), keep the original classification with appropriate reasoning
- Better to flag for human review than to miss important reproducibility issues

Provide your verification in JSON format:
{{
  "good_practices": [
    {{
      "section_name": "Name of the section (from Phase 1)",
      "practice_category": "data_availability | code_availability | methodological_detail | software_environment | materials_specification | documentation | open_science_practices",
      "description": "Clear description of the good practice",
      "full_section_text": "The COMPLETE text from Phase 1's full_section_text - preserve exactly",
      "evidence": "Specific quotes demonstrating the good practice",
      "quality_rating": "excellent | good | adequate",
      "completeness": "How complete is this practice (0.0-1.0)",
      "impact_on_reproducibility": "Specific explanation of how this helps reproducibility",
      "verification_reasoning": "DETAILED chain-of-thought explanation of WHY this IS a good practice",
      "confidence_percentage": 50-100
    }}
  ],
  "bad_practices": [
    {{
      "section_name": "Name of the section (from Phase 1)",
      "practice_category": "missing_data | missing_code | vague_methods | underspecified_software | proprietary_dependencies | poor_documentation | access_barriers",
      "description": "Clear description of the bad practice or missing information",
      "full_section_text": "The COMPLETE text from Phase 1's full_section_text - preserve exactly",
      "evidence": "Specific quotes or description of what's missing",
      "severity": "low | medium | high",
      "impact_on_reproducibility": "Specific explanation of how this hinders reproducibility",
      "verification_reasoning": "DETAILED chain-of-thought explanation of WHY this IS a bad practice",
      "confidence_percentage": 50-100
    }}
  ],
  "reclassified_sections": [
    {{
      "section_name": "Name of the section",
      "original_classification": "positive or negative",
      "reclassification_reasoning": "Why this was reclassified (only if >90% confident)",
      "confidence_percentage": 90-100
    }}
  ],
  "reproducibility_score": 0.0-1.0,
  "score_breakdown": {{
    "data_availability_score": 0.0-0.25,
    "code_availability_score": 0.0-0.25,
    "methodological_detail_score": 0.0-0.25,
    "documentation_score": 0.0-0.15,
    "environment_specification_score": 0.0-0.10
  }},
  "methodological_detail": "Overall assessment of methodological detail",
  "data_availability": "Summary of data availability practices",
  "code_availability": "Summary of code availability practices",
  "reproducibility_barriers": [
    {{
      "barrier": "Description of barrier",
      "severity": "low | medium | high",
      "impact": "How this affects reproducibility"
    }}
  ],
  "recommendations": ["Specific, actionable recommendations to improve reproducibility"],
  "overall_assessment": "Comprehensive summary of reproducibility"
}}

SCORING GUIDELINES (BE GENEROUS - reward partial efforts):

**Data Availability (0.25 max):**
- 0.25: Full raw data in public repository with DOI, data dictionary, processing scripts
- 0.20: Raw data in repository, good documentation
- 0.15: Partial data shared, or data with limited documentation
- 0.10: Supplementary data files included with paper
- 0.05: "Data available upon reasonable request" with contact
- 0.03: Willingness to share stated but no details
- 0.0: No mention of data sharing

**Code Availability (0.25 max):**
- 0.25: Full analysis code on GitHub/GitLab with dependencies, README, comments
- 0.20: Full code shared with good documentation
- 0.15: Code shared but minimal documentation
- 0.10: Partial code or pseudocode provided
- 0.05: "Code available upon request" or basic scripts in supplementary
- 0.02: Analysis steps described in detail (even without actual code)
- 0.0: Computational analysis with no code or description

**Methodological Detail (0.25 max):**
- 0.25: Complete step-by-step procedures with ALL parameters (times, temps, concentrations, equipment models)
- 0.20: Very detailed methods, only minor details missing
- 0.15: Good detail with some specifics (exact times, some parameters)
- 0.10: Adequate description but missing key parameters or using some vague language
- 0.05: Basic methods with significant vagueness ("briefly", "standard methods", "as needed")
- 0.02: Minimal methods, mostly vague
- 0.0: Methods section completely inadequate

**Documentation & Transparency (0.15 max):**
- 0.15: Excellent supplementary materials, pre-registration, all analyses reported, effect sizes, CIs
- 0.12: Good documentation, most analyses reported, some effect sizes
- 0.09: Adequate documentation, supplementary materials present
- 0.06: Basic documentation, some transparency
- 0.03: Minimal transparency, only positive results
- 0.0: Poor transparency, evidence of selective reporting

**Environment Specification (0.10 max):**
- 0.10: Full environment: software versions, package versions, OS, computational details, hardware if relevant
- 0.08: Good: software versions, main package versions
- 0.06: Adequate: software named with some version info
- 0.04: Minimal: software named without versions ("we used R", "SPSS analysis")
- 0.02: Very minimal: just mentions tools vaguely
- 0.0: No software/environment information

**BONUS/PENALTY MODIFIERS:**
- +0.05: Pre-registration mentioned
- +0.03: Replication study or replication encouraged
- +0.02: Open access publication
- +0.02: Multi-site collaboration with shared protocol
- -0.05: Evidence of p-hacking or HARKing
- -0.03: "Data available upon request" with no fulfillment mechanism
- -0.05: Critical vague language ("briefly", "standard", "appropriate") throughout methods

**MINIMUM SCORE**: Even a poor paper should score at least 0.10-0.20 if:
- Methods section exists (even if vague): +0.05
- Some statistical details provided: +0.03
- Any attempt at transparency: +0.02

VERIFICATION STANDARDS:
- PRESERVE the full_section_text from Phase 1
- Only reclassify if >90% confident of misclassification
- Distinguish between "missing information" (bad practice) and "acceptable given constraints"
- Provide specific evidence with quotes
- Calculate reproducibility_score based on confirmed practices
- **BE CREATIVE AND THOROUGH**: Look for subtle indicators, not just explicit statements
- **REWARD PARTIAL EFFORTS**: A paper with detailed methods but no data sharing should still score 0.25-0.35
- **DON'T DEFAULT TO 0.0**: Almost every paper has SOME reproducibility elements (methods description, statistical tests)

CHAIN-OF-THOUGHT TEMPLATE:
1. "The evidence shows..." (what specific details are present or absent)
2. "In the context of reproducibility best practices..." (what's the standard)
3. "This is/is not a good practice because..." (explicit reasoning)
4. "My confidence level is X% because..." (certainty)
5. "The quality/severity is X because..." (how complete/problematic)
6. "The impact on reproducibility is..." (practical effect)
7. "The specific score contribution is..." (be explicit about scoring)
8. "Therefore, my conclusion is..." (final decision)

CRITICAL REMINDERS:
- Be conservative in reclassifying - only reclassify if >90% certain!
- ALWAYS find at least 3-5 reproducibility sections (positive or negative) - be creative!
- Even vague methods are better than no methods - give partial credit
- Look for SPECIFIC NUMBERS (temperatures, times, sample sizes, versions) - these are gold!
- Flag VAGUE LANGUAGE ("briefly", "standard", "appropriate") - these hurt reproducibility
"""

            # Phase 2: Rigorous verification
            verification_response = self._get_openai_client().generate_completion(
                prompt=verification_prompt,
                model="gpt-4o-mini",
                max_tokens=4500,
                temperature=0.0  # Deterministic for consistency
            )

            if not verification_response:
                logger.error("❌ PHASE 2 failed: No response from LLM")
                return {"error": "No response from Phase 2 (verification)"}

            try:
                result = json.loads(verification_response)
                good_practices = result.get("good_practices", [])
                bad_practices = result.get("bad_practices", [])
                reclassified = result.get("reclassified_sections", [])

                logger.info(f"✅ PHASE 2 complete:")
                logger.info(f"   - {len(good_practices)} GOOD practices confirmed")
                logger.info(f"   - {len(bad_practices)} BAD practices confirmed")
                logger.info(f"   - {len(reclassified)} sections reclassified")
                logger.info(f"   - Reproducibility Score: {result.get('reproducibility_score', 0.0):.2f}")

                # Log details
                for idx, practice in enumerate(good_practices[:5]):
                    logger.info(f"   Good Practice {idx+1}: {practice.get('section_name')} ({practice.get('quality_rating')})")

                for idx, practice in enumerate(bad_practices[:5]):
                    logger.info(f"   Bad Practice {idx+1}: {practice.get('section_name')} ({practice.get('severity')} severity)")

                return result

            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse Phase 2 response: {str(e)}")
                logger.error(f"Response was: {verification_response[:500]}")
                # Fallback
                return {
                    "good_practices": [],
                    "bad_practices": [],
                    "reproducibility_score": 0.3,
                    "methodological_detail": verification_response[:500],
                    "data_availability": "Could not parse assessment",
                    "code_availability": "Could not parse assessment",
                    "reproducibility_barriers": [],
                    "recommendations": [],
                    "error": "Failed to parse verification response"
                }

        except Exception as e:
            logger.error(f"❌ Detailed reproducibility assessment failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e)}
