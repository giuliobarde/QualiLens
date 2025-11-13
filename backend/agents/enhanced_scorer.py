"""
Enhanced Scoring System for QualiLens (Phase 2 - Revised).

This module provides deterministic weighted scoring:
- Base methodology: 60% of final score
- Bias assessment: 20% of final score (inverted - fewer biases = higher score)
- Reproducibility: 10% of final score
- Research gaps: 10% of final score

Formula: Final = (Methodology * 0.6) + (Bias * 0.2) + (Reproducibility * 0.1) + (Research_Gaps * 0.1)
"""

import logging
import hashlib
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class EnhancedScorer:
    """
    Enhanced scoring system using weighted components for comprehensive quality assessment.

    Weights:
    - Methodology: 60%
    - Bias: 20%
    - Reproducibility: 10%
    - Research Gaps: 10%
    """

    # Component weights
    METHODOLOGY_WEIGHT = 0.60
    BIAS_WEIGHT = 0.20
    REPRODUCIBILITY_WEIGHT = 0.10
    RESEARCH_GAPS_WEIGHT = 0.10

    def __init__(self, openai_client=None):
        """
        Initialize the enhanced scorer.

        Args:
            openai_client: OpenAI client for LLM-based components (optional)
        """
        self.openai_client = openai_client

    def calculate_final_score(self,
                            base_methodology_score: float,
                            text_content: str,
                            reproducibility_data: Optional[Dict[str, Any]] = None,
                            bias_data: Optional[Dict[str, Any]] = None,
                            research_gaps_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate final score using weighted components.

        Formula: Final = (Methodology * 0.6) + (Bias * 0.2) + (Reproducibility * 0.1) + (Gaps * 0.1)

        Args:
            base_methodology_score: Base score from methodology analysis (0-100)
            text_content: Paper content for analysis
            reproducibility_data: Reproducibility analysis results
            bias_data: Bias detection results
            research_gaps_data: Research gaps identification results

        Returns:
            Dict with final score and detailed breakdown
        """
        try:
            # Calculate component scores (all 0-100)
            methodology_score = base_methodology_score
            bias_score = self._calculate_bias_score(bias_data)
            reproducibility_score = self._calculate_reproducibility_score(text_content, reproducibility_data)
            research_gaps_score = self._calculate_research_gaps_score(research_gaps_data)

            logger.info(f"Component Scores (0-100):")
            logger.info(f"  Methodology: {methodology_score}")
            logger.info(f"  Bias: {bias_score}")
            logger.info(f"  Reproducibility: {reproducibility_score}")
            logger.info(f"  Research Gaps: {research_gaps_score}")

            # Calculate weighted final score
            final_score = (
                (methodology_score * self.METHODOLOGY_WEIGHT) +
                (bias_score * self.BIAS_WEIGHT) +
                (reproducibility_score * self.REPRODUCIBILITY_WEIGHT) +
                (research_gaps_score * self.RESEARCH_GAPS_WEIGHT)
            )

            # Ensure score stays within bounds
            final_score = min(100.0, max(0.0, final_score))

            logger.info(f"Weighted Contributions:")
            logger.info(f"  Methodology: {methodology_score * self.METHODOLOGY_WEIGHT:.1f} pts (60%)")
            logger.info(f"  Bias: {bias_score * self.BIAS_WEIGHT:.1f} pts (20%)")
            logger.info(f"  Reproducibility: {reproducibility_score * self.REPRODUCIBILITY_WEIGHT:.1f} pts (10%)")
            logger.info(f"  Research Gaps: {research_gaps_score * self.RESEARCH_GAPS_WEIGHT:.1f} pts (10%)")
            logger.info(f"  FINAL SCORE: {final_score:.1f}")

            return {
                "final_score": round(final_score, 1),
                "component_scores": {
                    "methodology": round(methodology_score, 1),
                    "bias": round(bias_score, 1),
                    "reproducibility": round(reproducibility_score, 1),
                    "research_gaps": round(research_gaps_score, 1)
                },
                "weighted_contributions": {
                    "methodology": round(methodology_score * self.METHODOLOGY_WEIGHT, 1),
                    "bias": round(bias_score * self.BIAS_WEIGHT, 1),
                    "reproducibility": round(reproducibility_score * self.REPRODUCIBILITY_WEIGHT, 1),
                    "research_gaps": round(research_gaps_score * self.RESEARCH_GAPS_WEIGHT, 1)
                },
                "weights": {
                    "methodology": self.METHODOLOGY_WEIGHT,
                    "bias": self.BIAS_WEIGHT,
                    "reproducibility": self.REPRODUCIBILITY_WEIGHT,
                    "research_gaps": self.RESEARCH_GAPS_WEIGHT
                }
            }

        except Exception as e:
            logger.error(f"Enhanced scoring failed: {str(e)}")
            return {
                "final_score": base_methodology_score * self.METHODOLOGY_WEIGHT,
                "component_scores": {
                    "methodology": base_methodology_score,
                    "bias": 0,
                    "reproducibility": 0,
                    "research_gaps": 0
                },
                "error": str(e)
            }

    def _calculate_bias_score(self, bias_data: Optional[Dict[str, Any]]) -> float:
        """
        Calculate bias score (0-100), inverted so fewer biases = higher score.

        Scoring:
        - Start with 100 points
        - Subtract points for each bias based on severity:
          * High severity: -20 points
          * Medium severity: -10 points
          * Low severity: -5 points
        - Critical bias types (selection, confounding, publication): additional -10 points
        - Minimum score: 0

        Args:
            bias_data: Bias detection results

        Returns:
            Score from 0-100 (100 = no biases, 0 = many severe biases)
        """
        try:
            if not bias_data or not bias_data.get("success"):
                logger.info("No bias data available, using neutral score: 50")
                return 50.0  # Neutral if no data

            detected_biases = bias_data.get("detected_biases", [])

            if not detected_biases:
                logger.info("No biases detected - perfect bias score: 100")
                return 100.0  # Perfect score

            # Start with perfect score
            score = 100.0
            critical_bias_types = ["selection_bias", "confounding_bias", "publication_bias"]

            for bias in detected_biases:
                severity = bias.get("severity", "medium")
                bias_type = bias.get("bias_type", "unknown")
                penalty = 0.0

                # Base penalty by severity
                if severity == "high":
                    penalty = 20.0
                elif severity == "medium":
                    penalty = 10.0
                elif severity == "low":
                    penalty = 5.0

                # Additional penalty for critical bias types
                if bias_type in critical_bias_types:
                    penalty += 10.0

                score -= penalty

            # Ensure score doesn't go below 0
            score = max(0.0, score)

            logger.info(f"Bias Score: {score:.1f}/100 ({len(detected_biases)} biases detected)")

            return score

        except Exception as e:
            logger.error(f"Bias scoring failed: {str(e)}")
            return 50.0  # Neutral on error

    def _calculate_reproducibility_score(self,
                                        text_content: str,
                                        reproducibility_data: Optional[Dict[str, Any]]) -> float:
        """
        Calculate reproducibility score (0-100) using comprehensive multi-factor analysis.

        Evaluates 8 key reproducibility dimensions with quality assessment:
        1. Data Availability (25 pts) - Is data actually accessible?
        2. Code Availability (20 pts) - Is analysis code provided?
        3. Methods Detail (15 pts) - Can methods be replicated?
        4. Materials/Resources (10 pts) - Are materials specified?
        5. Statistical Transparency (10 pts) - Are analyses reproducible?
        6. Pre-registration (10 pts) - Was study pre-registered?
        7. Documentation Quality (5 pts) - Is documentation comprehensive?
        8. Version Control (5 pts) - Are specific versions documented?

        Args:
            text_content: Paper content
            reproducibility_data: Reproducibility analysis results

        Returns:
            Score from 0-100 (100 = fully reproducible, 0 = not reproducible)
        """
        try:
            score = 0.0
            text_lower = text_content.lower()

            # Component scores (more granular than simple keywords)
            components = {}

            # 1. DATA AVAILABILITY (25 points) - Most critical
            data_score = 0.0
            # Check for actual data sharing (not just mention)
            if any(ind in text_lower for ind in ["data available at", "data deposited", "data can be accessed"]):
                data_score += 10.0  # Explicit availability statement
            if any(ind in text_lower for ind in ["github.com/", "osf.io/", "figshare.com/", "zenodo.org/", "dryad.org/"]):
                data_score += 10.0  # Actual repository link (contains /)
            if "doi" in text_lower and "data" in text_lower:
                data_score += 5.0  # DOI for data

            components["data_availability"] = min(25.0, data_score)
            score += components["data_availability"]

            # 2. CODE AVAILABILITY (20 points)
            code_score = 0.0
            if any(ind in text_lower for ind in ["code available at", "analysis code", "scripts available"]):
                code_score += 8.0  # Explicit code availability
            if any(ind in text_lower for ind in ["github.com/", "gitlab.com/", "bitbucket.org/"]):
                code_score += 8.0  # Code repository link
            if any(ind in text_lower for ind in ["jupyter notebook", "r markdown", "analysis pipeline"]):
                code_score += 4.0  # Documented analysis workflow

            components["code_availability"] = min(20.0, code_score)
            score += components["code_availability"]

            # 3. METHODS DETAIL (15 points) - Can someone replicate?
            methods_score = 0.0
            methods_indicators = [
                ("detailed method", 3.0),
                ("step-by-step", 3.0),
                ("protocol", 2.0),
                ("supplementary method", 2.0),
                ("see supplementary", 2.0),
                ("procedure", 2.0),
                ("materials and methods", 2.0)
            ]
            for indicator, points in methods_indicators:
                if indicator in text_lower:
                    methods_score += points

            components["methods_detail"] = min(15.0, methods_score)
            score += components["methods_detail"]

            # 4. MATERIALS/RESOURCES (10 points)
            materials_score = 0.0
            if any(ind in text_lower for ind in ["material available", "materials and reagents", "reagent"]):
                materials_score += 3.0
            if any(ind in text_lower for ind in ["equipment", "instrument", "apparatus"]):
                materials_score += 3.0
            if "rrid:" in text_lower:  # Research Resource Identifier
                materials_score += 2.0
            if any(ind in text_lower for ind in ["catalog number", "cat#", "catalogue no"]):
                materials_score += 2.0

            components["materials"] = min(10.0, materials_score)
            score += components["materials"]

            # 5. STATISTICAL TRANSPARENCY (10 points)
            stats_score = 0.0
            if any(ind in text_lower for ind in ["statistical software", "statistical analysis", "statistical package"]):
                stats_score += 2.0
            if any(ind in text_lower for ind in ["r version", "python version", "spss version", "stata version", "sas version"]):
                stats_score += 3.0  # Specific software version
            if any(ind in text_lower for ind in ["random seed", "seed =", "set.seed"]):
                stats_score += 3.0  # Reproducible randomness
            if any(ind in text_lower for ind in ["confidence interval", "effect size", "power analysis"]):
                stats_score += 2.0

            components["statistical_transparency"] = min(10.0, stats_score)
            score += components["statistical_transparency"]

            # 6. PRE-REGISTRATION (10 points)
            prereg_score = 0.0
            if any(ind in text_lower for ind in ["pre-registered", "preregistered", "pre registered"]):
                prereg_score += 5.0
            if any(ind in text_lower for ind in ["clinicaltrials.gov", "osf.io/register", "aspredicted.org", "registered report"]):
                prereg_score += 5.0  # Specific registration platform

            components["preregistration"] = min(10.0, prereg_score)
            score += components["preregistration"]

            # 7. DOCUMENTATION QUALITY (5 points)
            doc_score = 0.0
            if any(ind in text_lower for ind in ["supplementary material", "supplementary information", "supplementary file"]):
                doc_score += 2.0
            if any(ind in text_lower for ind in ["readme", "documentation", "user guide"]):
                doc_score += 2.0
            if any(ind in text_lower for ind in ["tutorial", "walkthrough", "example"]):
                doc_score += 1.0

            components["documentation"] = min(5.0, doc_score)
            score += components["documentation"]

            # 8. VERSION CONTROL (5 points)
            version_score = 0.0
            if any(ind in text_lower for ind in ["version", "v.", "ver."]):
                version_score += 2.0
            if any(ind in text_lower for ind in ["commit", "release", "tag"]):
                version_score += 2.0
            if "doi" in text_lower:
                version_score += 1.0

            components["version_control"] = min(5.0, version_score)
            score += components["version_control"]

            # Ensure final score is within bounds
            score = min(100.0, max(0.0, score))

            # Log detailed component breakdown
            logger.info(f"Reproducibility Components:")
            for component, comp_score in components.items():
                logger.info(f"  {component}: {comp_score:.1f}")
            logger.info(f"Reproducibility Score: {score:.1f}/100")

            return score

        except Exception as e:
            logger.error(f"Reproducibility scoring failed: {str(e)}")
            return 50.0  # Neutral on error

    def _calculate_research_gaps_score(self, research_gaps_data: Optional[Dict[str, Any]]) -> float:
        """
        Calculate research gaps score (0-100).

        Scoring based on quantity and quality of identified gaps:
        - 0 gaps: 0 points
        - 1-2 gaps: 40 points
        - 3-5 gaps: 70 points
        - 6-10 gaps: 90 points
        - 10+ gaps: 100 points

        Bonuses for:
        - Future directions provided: +10 points (capped)
        - Theoretical gaps: +5 points
        - Methodological gaps: +5 points

        Args:
            research_gaps_data: Research gaps identification results

        Returns:
            Score from 0-100 (100 = many well-articulated gaps, 0 = no gaps)
        """
        try:
            if not research_gaps_data or not research_gaps_data.get("success"):
                logger.info("No research gaps data available, using minimal score: 20")
                return 20.0  # Low score if no data

            research_gaps = research_gaps_data.get("research_gaps", [])
            gaps_count = len(research_gaps)

            # Base score by gap count
            if gaps_count == 0:
                score = 0.0
            elif gaps_count <= 2:
                score = 40.0
            elif gaps_count <= 5:
                score = 70.0
            elif gaps_count <= 10:
                score = 90.0
            else:
                score = 100.0

            # Bonuses
            future_directions = research_gaps_data.get("future_directions", [])
            if future_directions and len(future_directions) > 0:
                score = min(100.0, score + 10.0)

            theoretical_gaps = research_gaps_data.get("theoretical_gaps", [])
            if theoretical_gaps and len(theoretical_gaps) > 0:
                score = min(100.0, score + 5.0)

            methodological_gaps = research_gaps_data.get("methodological_gaps", [])
            if methodological_gaps and len(methodological_gaps) > 0:
                score = min(100.0, score + 5.0)

            logger.info(f"Research Gaps Score: {score:.1f}/100 ({gaps_count} gaps identified)")

            return score

        except Exception as e:
            logger.error(f"Research gaps scoring failed: {str(e)}")
            return 20.0  # Low score on error

    def _assess_reproducibility_from_text(self, text_content: str) -> float:
        """
        Assess reproducibility using deterministic keyword analysis.

        Returns score from 0-100 based on presence of reproducibility indicators.

        Args:
            text_content: Paper content

        Returns:
            Score from 0-100
        """
        score = 0.0
        text_lower = text_content.lower()

        # Data availability indicators (+20 points)
        data_indicators = ["data available", "data accessible", "public repository", "github", "osf.io", "figshare", "zenodo"]
        if any(indicator in text_lower for indicator in data_indicators):
            score += 20.0

        # Code availability indicators (+20 points)
        code_indicators = ["code available", "source code", "github.com", "gitlab", "analysis script", "r script", "python code"]
        if any(indicator in text_lower for indicator in code_indicators):
            score += 20.0

        # Methods detail indicators (+20 points)
        methods_indicators = ["detailed method", "step-by-step", "protocol", "procedure", "supplementary method"]
        indicator_count = sum(1 for indicator in methods_indicators if indicator in text_lower)
        score += min(20.0, indicator_count * 5.0)

        # Materials availability (+15 points)
        materials_indicators = ["material available", "reagent", "equipment", "instrument", "software version"]
        materials_count = sum(1 for indicator in materials_indicators if indicator in text_lower)
        score += min(15.0, materials_count * 4.0)

        # Statistical details (+15 points)
        stats_indicators = ["statistical software", "r version", "python", "spss", "stata", "random seed", "confidence interval"]
        stats_count = sum(1 for indicator in stats_indicators if indicator in text_lower)
        score += min(15.0, stats_count * 3.0)

        # Pre-registration (+10 points)
        prereg_indicators = ["pre-registered", "preregistered", "clinicaltrials.gov", "registered protocol"]
        if any(indicator in text_lower for indicator in prereg_indicators):
            score += 10.0

        return min(100.0, score)

    def get_scoring_summary(self, scoring_result: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of the scoring.

        Args:
            scoring_result: Result from calculate_final_score()

        Returns:
            Formatted summary string
        """
        final_score = scoring_result.get('final_score', 0)
        component_scores = scoring_result.get('component_scores', {})
        weighted_contributions = scoring_result.get('weighted_contributions', {})

        summary = f"""
Scoring Summary (Weighted System):
===================================
Final Score: {final_score}/100

Component Scores (0-100):
  Methodology:     {component_scores.get('methodology', 0):.1f}
  Bias:            {component_scores.get('bias', 0):.1f}
  Reproducibility: {component_scores.get('reproducibility', 0):.1f}
  Research Gaps:   {component_scores.get('research_gaps', 0):.1f}

Weighted Contributions:
  Methodology (60%):     {weighted_contributions.get('methodology', 0):.1f} pts
  Bias (20%):            {weighted_contributions.get('bias', 0):.1f} pts
  Reproducibility (10%): {weighted_contributions.get('reproducibility', 0):.1f} pts
  Research Gaps (10%):   {weighted_contributions.get('research_gaps', 0):.1f} pts
"""
        return summary
