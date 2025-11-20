"""
Evidence-Based Scoring System for QualiLens.

This module calculates scores based on evidence items collected during analysis.
Each evidence item contributes to the score based on its category, severity, and impact.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EvidenceScoreContribution:
    """Represents how an evidence item contributes to the score."""
    evidence_id: str
    category: str
    score_impact: float
    weighted_impact: float
    component: str  # Which component this contributes to


class EvidenceBasedScorer:
    """
    Evidence-based scoring system that calculates scores from evidence items.
    
    Scoring weights by category:
    - Methodology: 60% (positive evidence adds, negative subtracts)
    - Bias: 20% (negative evidence subtracts, positive adds)
    - Reproducibility: 10% (positive evidence adds)
    - Statistics: 10% (positive evidence adds, negative subtracts)
    """
    
    # Component weights (same as EnhancedScorer for consistency)
    METHODOLOGY_WEIGHT = 0.60
    BIAS_WEIGHT = 0.20
    REPRODUCIBILITY_WEIGHT = 0.10
    STATISTICS_WEIGHT = 0.10
    
    # Base score (starting point)
    BASE_SCORE = 50.0  # Start at 50, evidence adjusts from there
    
    def __init__(self):
        """Initialize the evidence-based scorer."""
        pass
    
    def calculate_score_from_evidence(
        self,
        evidence_items: List[Dict[str, Any]],
        base_methodology_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate final score based on evidence items.
        
        Args:
            evidence_items: List of evidence items with category, score_impact, severity, etc.
            base_methodology_score: Optional base methodology score (if available from methodology analyzer)
            
        Returns:
            Dict with final score, component scores, and detailed breakdown
        """
        try:
            # Group evidence by category
            evidence_by_category = self._group_evidence_by_category(evidence_items)
            
            # Calculate component scores from evidence
            methodology_score = self._calculate_methodology_score(
                evidence_by_category.get("methodology", []),
                base_methodology_score
            )
            bias_score = self._calculate_bias_score(evidence_by_category.get("bias", []))
            reproducibility_score = self._calculate_reproducibility_score(
                evidence_by_category.get("reproducibility", [])
            )
            statistics_score = self._calculate_statistics_score(
                evidence_by_category.get("statistics", [])
            )
            
            # Calculate weighted final score
            final_score = (
                (methodology_score * self.METHODOLOGY_WEIGHT) +
                (bias_score * self.BIAS_WEIGHT) +
                (reproducibility_score * self.REPRODUCIBILITY_WEIGHT) +
                (statistics_score * self.STATISTICS_WEIGHT)
            )
            
            # Ensure score stays within bounds
            final_score = min(100.0, max(0.0, final_score))
            
            # Calculate weighted contributions
            weighted_contributions = {
                "methodology": methodology_score * self.METHODOLOGY_WEIGHT,
                "bias": bias_score * self.BIAS_WEIGHT,
                "reproducibility": reproducibility_score * self.REPRODUCIBILITY_WEIGHT,
                "statistics": statistics_score * self.STATISTICS_WEIGHT
            }
            
            # Calculate evidence contributions (for tooltips)
            evidence_contributions = self._calculate_evidence_contributions(evidence_items)
            
            logger.info(f"Evidence-Based Scoring:")
            logger.info(f"  Methodology: {methodology_score:.1f} × 60% = {weighted_contributions['methodology']:.1f} pts")
            logger.info(f"  Bias: {bias_score:.1f} × 20% = {weighted_contributions['bias']:.1f} pts")
            logger.info(f"  Reproducibility: {reproducibility_score:.1f} × 10% = {weighted_contributions['reproducibility']:.1f} pts")
            logger.info(f"  Statistics: {statistics_score:.1f} × 10% = {weighted_contributions['statistics']:.1f} pts")
            logger.info(f"  FINAL SCORE: {final_score:.1f}/100")
            logger.info(f"  Total evidence items: {len(evidence_items)}")
            
            return {
                "final_score": round(final_score, 1),
                "component_scores": {
                    "methodology": round(methodology_score, 1),
                    "bias": round(bias_score, 1),
                    "reproducibility": round(reproducibility_score, 1),
                    "statistics": round(statistics_score, 1)
                },
                "weighted_contributions": weighted_contributions,
                "weights": {
                    "methodology": self.METHODOLOGY_WEIGHT,
                    "bias": self.BIAS_WEIGHT,
                    "reproducibility": self.REPRODUCIBILITY_WEIGHT,
                    "statistics": self.STATISTICS_WEIGHT
                },
                "evidence_contributions": evidence_contributions,
                "evidence_count": len(evidence_items),
                "evidence_by_category": {
                    cat: len(items) for cat, items in evidence_by_category.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Evidence-based scoring failed: {str(e)}")
            return {
                "final_score": base_methodology_score or self.BASE_SCORE,
                "component_scores": {
                    "methodology": base_methodology_score or self.BASE_SCORE,
                    "bias": self.BASE_SCORE,
                    "reproducibility": self.BASE_SCORE,
                    "statistics": self.BASE_SCORE
                },
                "error": str(e)
            }
    
    def _group_evidence_by_category(self, evidence_items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group evidence items by category."""
        grouped = {}
        for evidence in evidence_items:
            category = evidence.get("category", "unknown")
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(evidence)
        return grouped
    
    def _calculate_methodology_score(
        self,
        methodology_evidence: List[Dict[str, Any]],
        base_score: Optional[float]
    ) -> float:
        """
        Calculate methodology score from evidence.
        
        Positive evidence (score_impact > 0) adds to score.
        Negative evidence (score_impact < 0) subtracts from score.
        """
        if base_score is not None:
            score = base_score
        else:
            score = self.BASE_SCORE
        
        # Adjust based on evidence
        for evidence in methodology_evidence:
            impact = evidence.get("score_impact", 0.0)
            score += impact
        
        # Normalize to 0-100
        return min(100.0, max(0.0, score))
    
    def _calculate_bias_score(self, bias_evidence: List[Dict[str, Any]]) -> float:
        """
        Calculate bias score from evidence.
        
        Bias evidence is typically negative (score_impact < 0).
        Fewer biases = higher score.
        Start with 100 and subtract for each bias.
        """
        score = 100.0  # Start with perfect score
        
        for evidence in bias_evidence:
            impact = evidence.get("score_impact", 0.0)
            # Impact is negative, so we subtract it (double negative = positive)
            score += impact  # impact is negative, so this subtracts
        
        # Normalize to 0-100
        return min(100.0, max(0.0, score))
    
    def _calculate_reproducibility_score(self, reproducibility_evidence: List[Dict[str, Any]]) -> float:
        """
        Calculate reproducibility score from evidence.
        
        Positive evidence adds to score.
        """
        score = self.BASE_SCORE
        
        for evidence in reproducibility_evidence:
            impact = evidence.get("score_impact", 0.0)
            score += impact
        
        # Normalize to 0-100
        return min(100.0, max(0.0, score))
    
    def _calculate_statistics_score(self, statistics_evidence: List[Dict[str, Any]]) -> float:
        """
        Calculate statistics score from evidence.
        
        Positive evidence adds, negative subtracts.
        """
        score = self.BASE_SCORE
        
        for evidence in statistics_evidence:
            impact = evidence.get("score_impact", 0.0)
            score += impact
        
        # Normalize to 0-100
        return min(100.0, max(0.0, score))
    
    def _calculate_evidence_contributions(self, evidence_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate how each evidence item contributes to the final score.
        
        Returns list of contributions for tooltips/hover display.
        """
        contributions = []
        
        for evidence in evidence_items:
            category = evidence.get("category", "unknown")
            impact = evidence.get("score_impact", 0.0)
            
            # Determine which component this contributes to
            if category == "methodology":
                weight = self.METHODOLOGY_WEIGHT
                component = "methodology"
            elif category == "bias":
                weight = self.BIAS_WEIGHT
                component = "bias"
            elif category == "reproducibility":
                weight = self.REPRODUCIBILITY_WEIGHT
                component = "reproducibility"
            elif category == "statistics":
                weight = self.STATISTICS_WEIGHT
                component = "statistics"
            else:
                weight = 0.0
                component = "other"
            
            # Calculate weighted contribution to final score
            weighted_impact = impact * weight
            
            contributions.append({
                "evidence_id": evidence.get("id", ""),
                "category": category,
                "component": component,
                "raw_impact": impact,
                "weighted_impact": round(weighted_impact, 2),
                "severity": evidence.get("severity", "medium"),
                "confidence": evidence.get("confidence", 0.5)
            })
        
        return contributions

