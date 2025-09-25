"""
Quality Assessor Tool for QualiLens.

This tool provides comprehensive quality assessment with numerical scoring (0-100)
based on all other analysis results. The scoring must be reproducible and
based on specific criteria.
"""

import logging
from typing import Dict, Any, Optional, List
from .base_tool import BaseTool, ToolMetadata

logger = logging.getLogger(__name__)


class QualityAssessorTool(BaseTool):
    """
    Quality Assessor tool for comprehensive quality evaluation with numerical scoring.
    """
    
    def _get_metadata(self) -> ToolMetadata:
        """Return the metadata for this tool."""
        return ToolMetadata(
            name="quality_assessor_tool",
            description="Assess overall paper quality with numerical scoring (0-100) based on comprehensive criteria",
            parameters={
                "required": ["analysis_results"],
                "optional": ["scoring_criteria", "weight_factors"],
                "properties": {
                    "analysis_results": {
                        "type": "object",
                        "description": "Results from all other analysis tools"
                    },
                    "scoring_criteria": {
                        "type": "array",
                        "description": "Specific criteria to use for scoring",
                        "default": []
                    },
                    "weight_factors": {
                        "type": "object",
                        "description": "Weight factors for different quality dimensions",
                        "default": {}
                    }
                }
            },
            examples=[
                "Assess overall paper quality with numerical score",
                "Evaluate quality based on methodology and results",
                "Generate reproducible quality score"
            ],
            category="quality_assessment"
        )
    
    def execute(self, analysis_results: Dict[str, Any], scoring_criteria: Optional[List[str]] = None,
                weight_factors: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Assess overall paper quality with numerical scoring.
        
        Args:
            analysis_results: Results from all other analysis tools
            scoring_criteria: Specific criteria to use for scoring
            weight_factors: Weight factors for different quality dimensions
            
        Returns:
            Dict containing quality assessment with numerical score
        """
        try:
            logger.info("Assessing overall paper quality with numerical scoring")
            
            # Default weight factors for quality dimensions
            default_weights = {
                "methodology": 0.25,      # Study design and methodology quality
                "statistics": 0.20,       # Statistical validity and rigor
                "bias": 0.20,             # Bias detection and limitations
                "reproducibility": 0.15,   # Reproducibility and transparency
                "novelty": 0.10,          # Research novelty and contribution
                "presentation": 0.10      # Clarity and presentation quality
            }
            
            # Use provided weights or defaults
            weights = weight_factors if weight_factors else default_weights
            
            # Calculate quality scores for each dimension
            quality_scores = self._calculate_quality_dimensions(analysis_results, weights)
            
            # Calculate overall weighted score
            overall_score = self._calculate_overall_score(quality_scores, weights)
            
            # Generate quality assessment
            assessment = self._generate_quality_assessment(quality_scores, overall_score, analysis_results)
            
            return {
                "success": True,
                "overall_quality_score": round(overall_score, 1),
                "quality_breakdown": quality_scores,
                "scoring_criteria_used": self._get_scoring_criteria(),
                "strengths": assessment["strengths"],
                "weaknesses": assessment["weaknesses"],
                "recommendations": assessment["recommendations"],
                "confidence_level": assessment["confidence_level"],
                "detailed_scores": assessment["detailed_scores"],
                "tool_used": "quality_assessor_tool"
            }
            
        except Exception as e:
            logger.error(f"Quality assessment failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_used": "quality_assessor_tool"
            }
    
    def _calculate_quality_dimensions(self, analysis_results: Dict[str, Any], weights: Dict[str, float]) -> Dict[str, Any]:
        """Calculate quality scores for each dimension."""
        scores = {}
        
        # Methodology Quality (0-100)
        methodology_score = self._score_methodology(analysis_results.get("methodology", {}))
        scores["methodology"] = {
            "score": methodology_score,
            "weight": weights["methodology"],
            "weighted_score": methodology_score * weights["methodology"]
        }
        
        # Statistical Quality (0-100)
        statistics_score = self._score_statistics(analysis_results.get("statistics", {}))
        scores["statistics"] = {
            "score": statistics_score,
            "weight": weights["statistics"],
            "weighted_score": statistics_score * weights["statistics"]
        }
        
        # Bias Assessment (0-100, inverted - lower bias = higher score)
        bias_score = self._score_bias(analysis_results.get("bias_detection", {}))
        scores["bias"] = {
            "score": bias_score,
            "weight": weights["bias"],
            "weighted_score": bias_score * weights["bias"]
        }
        
        # Reproducibility (0-100)
        reproducibility_score = self._score_reproducibility(analysis_results.get("reproducibility", {}))
        scores["reproducibility"] = {
            "score": reproducibility_score,
            "weight": weights["reproducibility"],
            "weighted_score": reproducibility_score * weights["reproducibility"]
        }
        
        # Novelty/Contribution (0-100)
        novelty_score = self._score_novelty(analysis_results.get("research_gaps", {}), analysis_results.get("summary", {}))
        scores["novelty"] = {
            "score": novelty_score,
            "weight": weights["novelty"],
            "weighted_score": novelty_score * weights["novelty"]
        }
        
        # Presentation Quality (0-100)
        presentation_score = self._score_presentation(analysis_results.get("summary", {}), analysis_results.get("citations", {}))
        scores["presentation"] = {
            "score": presentation_score,
            "weight": weights["presentation"],
            "weighted_score": presentation_score * weights["presentation"]
        }
        
        return scores
    
    def _score_methodology(self, methodology_data: Dict[str, Any]) -> float:
        """Score methodology quality (0-100)."""
        if not methodology_data or not methodology_data.get("success"):
            return 30.0  # Default low score for missing data
        
        score = 50.0  # Base score
        
        # Study design quality
        study_design = methodology_data.get("study_design", {})
        if study_design.get("design_type") in ["randomized_controlled_trial", "quasi_experimental"]:
            score += 20.0
        elif study_design.get("design_type") in ["observational", "case_study"]:
            score += 10.0
        
        # Sample size adequacy
        sample_info = methodology_data.get("sample_characteristics", {})
        if sample_info.get("sample_size_justification") == "adequate":
            score += 15.0
        elif sample_info.get("sample_size_justification") == "partially_adequate":
            score += 8.0
        
        # Data collection methods
        data_collection = methodology_data.get("data_collection", {})
        if data_collection.get("methods_clearly_described"):
            score += 10.0
        
        # Validity considerations
        validity = methodology_data.get("validity", {})
        if validity.get("internal_validity") == "high":
            score += 5.0
        if validity.get("external_validity") == "high":
            score += 5.0
        
        return min(100.0, max(0.0, score))
    
    def _score_statistics(self, statistics_data: Dict[str, Any]) -> float:
        """Score statistical quality (0-100)."""
        if not statistics_data or not statistics_data.get("success"):
            return 30.0
        
        score = 40.0  # Base score
        
        # Statistical methods appropriateness
        methods = statistics_data.get("statistical_methods", {})
        if methods.get("methods_appropriate"):
            score += 20.0
        if methods.get("assumptions_checked"):
            score += 15.0
        
        # Effect sizes and confidence intervals
        results = statistics_data.get("statistical_results", {})
        if results.get("effect_sizes_provided"):
            score += 15.0
        if results.get("confidence_intervals_provided"):
            score += 10.0
        
        return min(100.0, max(0.0, score))
    
    def _score_bias(self, bias_data: Dict[str, Any]) -> float:
        """Score bias assessment (0-100, inverted - lower bias = higher score)."""
        if not bias_data or not bias_data.get("success"):
            return 50.0  # Neutral score for missing data
        
        score = 80.0  # Start with high score
        
        # Reduce score based on detected biases
        detected_biases = bias_data.get("detected_biases", [])
        for bias in detected_biases:
            severity = bias.get("severity", "medium")
            if severity == "high":
                score -= 20.0
            elif severity == "medium":
                score -= 10.0
            elif severity == "low":
                score -= 5.0
        
        # Additional penalty for critical bias types
        critical_biases = ["selection_bias", "confounding_bias", "publication_bias"]
        for bias in detected_biases:
            if bias.get("bias_type") in critical_biases and bias.get("severity") == "high":
                score -= 15.0
        
        return min(100.0, max(0.0, score))
    
    def _score_reproducibility(self, reproducibility_data: Dict[str, Any]) -> float:
        """Score reproducibility (0-100)."""
        if not reproducibility_data or not reproducibility_data.get("success"):
            return 30.0
        
        score = 50.0  # Base score
        
        # Data availability
        data_availability = reproducibility_data.get("data_availability", {})
        if data_availability.get("data_publicly_available"):
            score += 20.0
        if data_availability.get("code_available"):
            score += 15.0
        
        # Methodology transparency
        methodology = reproducibility_data.get("methodology_transparency", {})
        if methodology.get("methods_clearly_described"):
            score += 10.0
        if methodology.get("parameters_specified"):
            score += 10.0
        
        # Reproducibility assessment
        assessment = reproducibility_data.get("reproducibility_assessment", {})
        if assessment.get("reproducibility_score") == "high":
            score += 15.0
        elif assessment.get("reproducibility_score") == "medium":
            score += 8.0
        
        return min(100.0, max(0.0, score))
    
    def _score_novelty(self, research_gaps_data: Dict[str, Any], summary_data: Dict[str, Any]) -> float:
        """Score novelty and contribution (0-100)."""
        score = 50.0  # Base score
        
        # Research gaps indicate novelty potential
        if research_gaps_data and research_gaps_data.get("success"):
            gaps = research_gaps_data.get("research_gaps", [])
            if len(gaps) > 0:
                score += 20.0  # Having identified gaps suggests novelty
        
        # Summary quality indicators
        if summary_data and summary_data.get("success"):
            key_findings = summary_data.get("key_findings", [])
            if len(key_findings) > 3:  # Multiple significant findings
                score += 15.0
            if summary_data.get("novelty_mentioned"):
                score += 15.0
        
        return min(100.0, max(0.0, score))
    
    def _score_presentation(self, summary_data: Dict[str, Any], citations_data: Dict[str, Any]) -> float:
        """Score presentation quality (0-100)."""
        score = 50.0  # Base score
        
        # Summary clarity
        if summary_data and summary_data.get("success"):
            if summary_data.get("clarity_score") == "high":
                score += 20.0
            elif summary_data.get("clarity_score") == "medium":
                score += 10.0
        
        # Citation quality
        if citations_data and citations_data.get("success"):
            citation_quality = citations_data.get("citation_quality", {})
            if citation_quality.get("recent_citations_ratio", 0) > 0.3:  # 30% recent citations
                score += 15.0
            if citation_quality.get("high_impact_sources_ratio", 0) > 0.5:  # 50% high-impact sources
                score += 15.0
        
        return min(100.0, max(0.0, score))
    
    def _calculate_overall_score(self, quality_scores: Dict[str, Any], weights: Dict[str, float]) -> float:
        """Calculate overall weighted quality score."""
        total_weighted_score = sum(dim["weighted_score"] for dim in quality_scores.values())
        total_weight = sum(weights.values())
        
        if total_weight == 0:
            return 0.0
        
        return total_weighted_score / total_weight
    
    def _generate_quality_assessment(self, quality_scores: Dict[str, Any], overall_score: float, 
                                   analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive quality assessment."""
        strengths = []
        weaknesses = []
        recommendations = []
        
        # Analyze strengths and weaknesses
        for dimension, scores in quality_scores.items():
            if scores["score"] >= 80:
                strengths.append(f"Excellent {dimension} quality (score: {scores['score']:.1f})")
            elif scores["score"] <= 40:
                weaknesses.append(f"Poor {dimension} quality (score: {scores['score']:.1f})")
        
        # Generate recommendations
        if quality_scores["methodology"]["score"] < 60:
            recommendations.append("Improve study design and methodology description")
        if quality_scores["statistics"]["score"] < 60:
            recommendations.append("Enhance statistical analysis and reporting")
        if quality_scores["bias"]["score"] < 60:
            recommendations.append("Address identified biases and limitations")
        if quality_scores["reproducibility"]["score"] < 60:
            recommendations.append("Improve data and code availability for reproducibility")
        
        # Determine confidence level
        if overall_score >= 85:
            confidence_level = "Very High"
        elif overall_score >= 70:
            confidence_level = "High"
        elif overall_score >= 55:
            confidence_level = "Medium"
        elif overall_score >= 40:
            confidence_level = "Low"
        else:
            confidence_level = "Very Low"
        
        return {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "confidence_level": confidence_level,
            "detailed_scores": quality_scores
        }
    
    def _get_scoring_criteria(self) -> List[str]:
        """Return the scoring criteria used."""
        return [
            "Methodology Quality (25%): Study design, sample size, data collection methods, validity",
            "Statistical Quality (20%): Method appropriateness, assumptions, effect sizes, confidence intervals",
            "Bias Assessment (20%): Selection bias, measurement bias, confounding, publication bias",
            "Reproducibility (15%): Data availability, code availability, methodology transparency",
            "Novelty/Contribution (10%): Research gaps, key findings, innovation",
            "Presentation Quality (10%): Clarity, citation quality, recent sources"
        ]
