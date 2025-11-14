"""
Methodology Analyzer Tool for QualiLens.

This tool provides deep analysis of research methodology, study design,
sample characteristics, and methodological quality assessment.
"""

import logging
import json
import hashlib
from typing import Dict, Any, Optional, List
from .base_tool import BaseTool, ToolMetadata

# Add the project root to the Python path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from LLM.openai_client import OpenAIClient

# Import score cache
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from score_cache import ScoreCache

logger = logging.getLogger(__name__)


class MethodologyAnalyzerTool(BaseTool):
    """
    Methodology Analyzer tool for comprehensive analysis of research methodology.
    """

    def __init__(self):
        super().__init__()
        self.openai_client = None
        self.score_cache = ScoreCache()
    
    def _get_openai_client(self):
        """Get OpenAI client, initializing it lazily if needed."""
        if self.openai_client is None:
            self.openai_client = OpenAIClient()
        return self.openai_client
    
    def _get_metadata(self) -> ToolMetadata:
        """Return the metadata for this tool."""
        return ToolMetadata(
            name="methodology_analyzer_tool",
            description="Analyze research methodology, study design, sample characteristics, and methodological quality",
            parameters={
                "required": ["text_content"],
                "optional": ["analysis_depth", "focus_areas"],
                "properties": {
                    "text_content": {
                        "type": "string",
                        "description": "The text content to analyze for methodology"
                    },
                    "analysis_depth": {
                        "type": "string",
                        "description": "Depth of analysis: 'basic', 'detailed', 'comprehensive'",
                        "default": "detailed"
                    },
                    "focus_areas": {
                        "type": "array",
                        "description": "Specific methodology areas to focus on",
                        "default": []
                    }
                }
            },
            examples=[
                "Analyze the methodology of this research study",
                "Evaluate the study design and sample characteristics",
                "Assess the methodological quality and validity"
            ],
            category="methodology_analysis"
        )
    
    def execute(self, text_content: str, analysis_depth: str = "detailed", 
                focus_areas: Optional[List[str]] = None, evidence_collector=None) -> Dict[str, Any]:
        """
        Analyze research methodology comprehensively.
        
        Args:
            text_content: The text content to analyze
            analysis_depth: Depth of methodology analysis
            focus_areas: Specific areas to focus on
            
        Returns:
            Dict containing methodology analysis results
        """
        try:
            logger.info("Analyzing methodology with comprehensive depth")
            
            # Always use comprehensive methodology analysis
            methodology_result = self._analyze_comprehensive_methodology(text_content, focus_areas)
            
            # Debug logging for score tracking
            overall_score = methodology_result.get("overall_quality_score", 0)
            logger.info(f"🔍 METHODOLOGY ANALYZER FINAL RESULT:")
            logger.info(f"   - overall_quality_score: {overall_score}")
            logger.info(f"   - quantitative_scores: {methodology_result.get('quantitative_scores', {})}")
            logger.info(f"   - quality_rating: {methodology_result.get('quality_rating', '')}")
            
            # Collect evidence if evidence_collector is provided
            if evidence_collector:
                strengths = methodology_result.get("methodological_strengths", [])
                weaknesses = methodology_result.get("methodological_weaknesses", [])
                
                # Add evidence for strengths
                for strength in strengths[:3]:  # Top 3 strengths
                    if strength and len(strength) > 20:
                        evidence_collector.add_evidence(
                            category="methodology",
                            text_snippet=strength[:200],
                            rationale=f"Methodological strength: {strength}",
                            confidence=0.7,
                            score_impact=5.0
                        )
                
                # Add evidence for weaknesses
                for weakness in weaknesses[:3]:  # Top 3 weaknesses
                    if weakness and len(weakness) > 20:
                        evidence_collector.add_evidence(
                            category="methodology",
                            text_snippet=weakness[:200],
                            rationale=f"Methodological weakness: {weakness}",
                            confidence=0.7,
                            score_impact=-5.0
                        )
            
            return {
                "success": True,
                "study_design": methodology_result.get("study_design", ""),
                "sample_characteristics": methodology_result.get("sample_characteristics", {}),
                "data_collection": methodology_result.get("data_collection", {}),
                "analysis_methods": methodology_result.get("analysis_methods", {}),
                "validity_measures": methodology_result.get("validity_measures", {}),
                "ethical_considerations": methodology_result.get("ethical_considerations", {}),
                "methodological_strengths": methodology_result.get("methodological_strengths", []),
                "methodological_weaknesses": methodology_result.get("methodological_weaknesses", []),
                "quality_rating": methodology_result.get("quality_rating", ""),
                "overall_quality_score": overall_score,
                "quantitative_scores": methodology_result.get("quantitative_scores", {}),
                "analysis_depth": "comprehensive",
                "focus_areas": focus_areas or [],
                "tool_used": "methodology_analyzer_tool"
            }
            
        except Exception as e:
            logger.error(f"Methodology analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_used": "methodology_analyzer_tool"
            }
    
    def _analyze_comprehensive_methodology(self, text_content: str, focus_areas: Optional[List[str]]) -> Dict[str, Any]:
        """Analyze comprehensive methodology elements with field-specific standards, quantitative scoring, and cross-tool integration."""
        try:
            # Check cache first for consistent scoring
            cached_result = self.score_cache.get_cached_score(text_content)
            if cached_result:
                logger.info("✅ Using cached score for consistency")
                # Reconstruct full result from cache
                return {
                    "field_detection": {"primary_field": cached_result.get("field_detected", "unknown")},
                    "quantitative_scores": cached_result.get("score_breakdown", {}),
                    "overall_quality_score": cached_result.get("overall_score", 0),
                    "cached": True,
                    "cache_timestamp": cached_result.get("cache_timestamp"),
                    "content_hash": cached_result.get("content_hash"),
                    "study_design": "Cached analysis",
                    "sample_characteristics": {},
                    "data_collection": {},
                    "analysis_methods": {},
                    "validity_measures": {},
                    "ethical_considerations": {},
                    "methodological_strengths": ["Score retrieved from cache for consistency"],
                    "methodological_weaknesses": [],
                    "quality_rating": self._determine_quality_level(cached_result.get("overall_score", 0))
                }

            # Cache miss - perform full analysis
            logger.info("Cache miss - performing full analysis")

            # Step 1: Detect research field for field-specific analysis
            field_detection = self._detect_research_field(text_content)
            logger.info(f"Detected research field: {field_detection.get('primary_field', 'unknown')}")

            # Step 2: Get field-specific standards and criteria
            field_standards = self._get_field_specific_standards(field_detection.get('primary_field', 'general'))

            # Step 3: Generate comprehensive analysis with field-specific prompts
            methodology_analysis = self._generate_field_specific_analysis(text_content, focus_areas, field_standards)

            # Step 4: Add quantitative scoring and risk assessment
            quantitative_scores = self._calculate_quantitative_scores(methodology_analysis, field_standards)

            # Step 5: Cross-tool validation and consistency checking
            cross_validation = self._perform_cross_tool_validation(text_content, methodology_analysis)

            # Step 6: Integrate all results
            comprehensive_result = {
                **methodology_analysis,
                "field_detection": field_detection,
                "quantitative_scores": quantitative_scores,
                "cross_validation": cross_validation,
                "overall_quality_score": quantitative_scores.get("scores", {}).get("overall_score", 0),
                "risk_assessment": quantitative_scores.get("risk_assessment", {}),
                "field_specific_standards": field_standards,
                "cached": False
            }

            # Cache the score for future consistency
            content_hash = hashlib.sha256(text_content.encode('utf-8')).hexdigest()
            cache_data = {
                "overall_score": comprehensive_result.get("overall_quality_score", 0),
                "score_breakdown": quantitative_scores,
                "field_detected": field_detection.get("primary_field", "unknown")
            }
            self.score_cache.cache_score(text_content, cache_data)
            comprehensive_result["content_hash"] = content_hash

            return comprehensive_result

        except Exception as e:
            logger.error(f"Comprehensive methodology analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def _detect_research_field(self, text_content: str) -> Dict[str, Any]:
        """Detect the primary research field based on content analysis."""
        try:
            prompt = f"""
Analyze this research paper content to determine the primary research field and methodology type.

PAPER CONTENT:
{text_content[:4000]}

Provide field detection in JSON format:
{{
  "primary_field": "clinical/medical, social_sciences, engineering, psychology, education, business, or other",
  "study_type": "experimental, observational, qualitative, mixed_methods, meta_analysis, or systematic_review",
  "methodology_focus": "quantitative, qualitative, or mixed_methods",
  "confidence": "high/medium/low",
  "field_indicators": ["indicator1", "indicator2"],
  "methodology_indicators": ["indicator1", "indicator2"]
}}

Focus on identifying the most relevant field for applying appropriate methodological standards.
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-3.5-turbo",
                max_tokens=800,
                temperature=0.0  # Deterministic for consistency
            )
            
            if llm_response:
                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    return {"primary_field": "general", "study_type": "unknown", "confidence": "low"}
            else:
                return {"primary_field": "general", "study_type": "unknown", "confidence": "low"}
                
        except Exception as e:
            logger.error(f"Field detection failed: {str(e)}")
            return {"primary_field": "general", "study_type": "unknown", "confidence": "low"}
    
    def _get_field_specific_standards(self, field: str) -> Dict[str, Any]:
        """Get field-specific methodological standards and criteria."""
        standards = {
            "clinical": {
                "checklist": "CONSORT",
                "key_criteria": ["randomization", "blinding", "allocation_concealment", "intention_to_treat", "sample_size_calculation"],
                "quality_thresholds": {"randomization": 0.8, "blinding": 0.7, "sample_size": 0.9},
                "bias_domains": ["selection", "performance", "detection", "attrition", "reporting"]
            },
            "social_sciences": {
                "checklist": "STROBE",
                "key_criteria": ["sampling_method", "response_rate", "measurement_validity", "confounding_control"],
                "quality_thresholds": {"response_rate": 0.6, "validity": 0.7, "reliability": 0.8},
                "bias_domains": ["selection", "measurement", "confounding", "reporting"]
            },
            "engineering": {
                "checklist": "IEEE",
                "key_criteria": ["experimental_design", "control_conditions", "measurement_precision", "reproducibility"],
                "quality_thresholds": {"precision": 0.8, "reproducibility": 0.9, "control": 0.7},
                "bias_domains": ["measurement", "systematic", "environmental"]
            },
            "psychology": {
                "checklist": "APA",
                "key_criteria": ["ethical_approval", "informed_consent", "debriefing", "data_privacy"],
                "quality_thresholds": {"ethics": 0.9, "consent": 0.8, "privacy": 0.9},
                "bias_domains": ["selection", "measurement", "experimenter", "participant"]
            },
            "general": {
                "checklist": "GENERIC",
                "key_criteria": ["study_design", "sample_size", "data_collection", "analysis_methods"],
                "quality_thresholds": {"design": 0.7, "sample": 0.6, "analysis": 0.7},
                "bias_domains": ["selection", "measurement", "confounding"]
            }
        }
        
        return standards.get(field, standards["general"])
    
    def _generate_field_specific_analysis(self, text_content: str, focus_areas: Optional[List[str]], field_standards: Dict[str, Any]) -> Dict[str, Any]:
        """Generate methodology analysis using field-specific standards."""
        try:
            checklist = field_standards.get("checklist", "GENERIC")
            key_criteria = field_standards.get("key_criteria", [])
            
            prompt = f"""
You are an expert research analyst specializing in {field_standards.get('checklist', 'research methodology')}. 
Provide a comprehensive analysis of the research methodology using {checklist} standards.

PAPER CONTENT:
{text_content[:6000]}

{f"SPECIFIC FOCUS AREAS: {', '.join(focus_areas)}" if focus_areas else ""}

FIELD-SPECIFIC CRITERIA TO EVALUATE: {', '.join(key_criteria)}

Provide comprehensive methodology analysis in JSON format:
{{
  "study_design": {{
    "type": "Type of study design",
    "rationale": "Why this design was chosen",
    "appropriateness": "How appropriate this design is for the research question",
    "alternatives": "Alternative designs that could have been used",
    "field_specific_assessment": "Assessment using {checklist} standards"
  }},
  "sample_characteristics": {{
    "sample_size": "Number of participants with power analysis",
    "demographics": "Detailed participant demographics",
    "inclusion_criteria": "Specific inclusion criteria",
    "exclusion_criteria": "Specific exclusion criteria",
    "recruitment_method": "Detailed recruitment process",
    "retention_rate": "Participant retention if applicable",
    "representativeness": "How representative the sample is",
    "field_specific_requirements": "Field-specific sample requirements met"
  }},
  "data_collection": {{
    "methods": "Comprehensive data collection methods",
    "instruments": "All instruments and tools used with validation",
    "procedures": "Detailed data collection procedures",
    "timeline": "Data collection timeline",
    "quality_control": "Quality control measures",
    "field_standards_compliance": "Compliance with {checklist} standards"
  }},
  "analysis_methods": {{
    "statistical_tests": "All statistical tests used with justification",
    "software": "Software and tools used",
    "assumptions": "Statistical assumptions checked",
    "effect_sizes": "Effect size calculations if applicable",
    "confidence_intervals": "Confidence interval reporting",
    "field_appropriateness": "Appropriateness for {checklist} standards"
  }},
  "validity_measures": {{
    "internal_validity": "Comprehensive internal validity measures",
    "external_validity": "External validity considerations",
    "reliability": "Reliability measures and coefficients",
    "bias_control": "Measures to control for bias",
    "field_specific_validity": "Field-specific validity considerations"
  }},
  "ethical_considerations": {{
    "approval": "Ethical approval details and oversight",
    "consent": "Informed consent procedures",
    "privacy": "Privacy and confidentiality measures",
    "data_protection": "Data protection measures",
    "field_ethics": "Field-specific ethical considerations"
  }},
  "methodological_strengths": [
    "Field-specific strength 1",
    "Field-specific strength 2"
  ],
  "methodological_weaknesses": [
    "Field-specific weakness 1",
    "Field-specific weakness 2"
  ],
  "quality_rating": "Detailed quality assessment with {checklist} criteria",
  "recommendations": [
    "Field-specific recommendation 1",
    "Field-specific recommendation 2"
  ],
  "field_compliance": {{
    "checklist_used": "{checklist}",
    "compliance_score": "Overall compliance with field standards",
    "missing_elements": ["Element 1", "Element 2"],
    "exceeds_standards": ["Element 1", "Element 2"]
  }}
}}

Provide the most comprehensive analysis possible using {checklist} standards.
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-3.5-turbo",
                max_tokens=3000,
                temperature=0.0  # Deterministic for consistency
            )
            
            if llm_response:
                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    return {"error": "Could not parse field-specific methodology analysis"}
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Field-specific analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_quantitative_scores(self, methodology_analysis: Dict[str, Any], field_standards: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate quantitative scores and risk assessment for methodology using AI-powered content analysis."""
        try:
            scores = {}
            risk_assessment = {}
            
            # Use AI-powered scoring for more accurate and varied results
            ai_scores = self._calculate_ai_powered_scores(methodology_analysis, field_standards)
            logger.info(f"AI scores received: {ai_scores}")
            
            # Study Design Score (0-100) with guaranteed variation
            study_design_score = ai_scores.get("study_design", self._score_study_design_with_variation(methodology_analysis.get("study_design", {}), field_standards))
            scores["study_design"] = study_design_score
            
            # Sample Characteristics Score (0-100) with guaranteed variation
            sample_score = ai_scores.get("sample_characteristics", self._score_sample_characteristics_with_variation(methodology_analysis.get("sample_characteristics", {}), field_standards))
            scores["sample_characteristics"] = sample_score
            
            # Data Collection Score (0-100) with guaranteed variation
            data_collection_score = ai_scores.get("data_collection", self._score_data_collection_with_variation(methodology_analysis.get("data_collection", {}), field_standards))
            scores["data_collection"] = data_collection_score
            
            # Analysis Methods Score (0-100) with guaranteed variation
            analysis_score = ai_scores.get("analysis_methods", self._score_analysis_methods_with_variation(methodology_analysis.get("analysis_methods", {}), field_standards))
            scores["analysis_methods"] = analysis_score
            
            # Validity Measures Score (0-100) with guaranteed variation
            validity_score = ai_scores.get("validity_measures", self._score_validity_measures_with_variation(methodology_analysis.get("validity_measures", {}), field_standards))
            scores["validity_measures"] = validity_score
            
            # Ethical Considerations Score (0-100) with guaranteed variation
            ethics_score = ai_scores.get("ethical_considerations", self._score_ethical_considerations_with_variation(methodology_analysis.get("ethical_considerations", {}), field_standards))
            scores["ethical_considerations"] = ethics_score
            
            # Overall Score (weighted average with guaranteed variation)
            weights = {"study_design": 0.25, "sample_characteristics": 0.20, "data_collection": 0.20, 
                     "analysis_methods": 0.15, "validity_measures": 0.15, "ethical_considerations": 0.05}
            overall_score = sum(scores[key] * weights[key] for key in weights.keys())
            
            # Add guaranteed variation based on content uniqueness
            content_variation = self._calculate_guaranteed_variation(methodology_analysis)
            overall_score = min(100, max(0, overall_score + content_variation))
            
            scores["overall_score"] = round(overall_score, 1)
            
            logger.info(f"Final scores: {scores}")
            
            # Risk Assessment
            risk_assessment = self._assess_methodological_risks(scores, methodology_analysis)
            
            return {
                "scores": scores,
                "risk_assessment": risk_assessment,
                "quality_level": self._determine_quality_level(overall_score),
                "improvement_priority": self._prioritize_improvements(scores)
            }
            
        except Exception as e:
            logger.error(f"Quantitative scoring failed: {str(e)}")
            return {"error": str(e)}
    
    def _score_study_design(self, study_design: Dict[str, Any], field_standards: Dict[str, Any]) -> float:
        """Score study design quality (0-100) with more sophisticated analysis."""
        score = 30.0  # Lower base score for more realistic scoring
        
        # Check for appropriate study design with more nuanced scoring
        design_type = study_design.get("type", "").lower()
        if "randomized controlled trial" in design_type or "rct" in design_type:
            score += 35.0
        elif "cohort study" in design_type or "case-control" in design_type:
            score += 25.0
        elif "cross-sectional" in design_type or "survey" in design_type:
            score += 15.0
        elif "quasi-experimental" in design_type:
            score += 20.0
        elif "qualitative" in design_type:
            score += 10.0
        
        # Check rationale quality with more sophisticated analysis
        rationale = study_design.get("rationale", "")
        if len(rationale) > 100:  # More detailed rationale required
            score += 15.0
        elif len(rationale) > 50:
            score += 10.0
        elif len(rationale) > 20:
            score += 5.0
        
        # Check appropriateness with keyword analysis
        appropriateness = study_design.get("appropriateness", "").lower()
        positive_indicators = ["appropriate", "suitable", "well-suited", "optimal", "ideal"]
        negative_indicators = ["inappropriate", "unsuitable", "problematic", "limitation"]
        
        positive_count = sum(1 for indicator in positive_indicators if indicator in appropriateness)
        negative_count = sum(1 for indicator in negative_indicators if indicator in appropriateness)
        
        if positive_count > 0:
            score += min(15.0, positive_count * 5.0)
        if negative_count > 0:
            score -= min(10.0, negative_count * 3.0)
        
        # Check for field-specific design requirements
        field_checklist = field_standards.get("checklist", "")
        if field_checklist == "CONSORT" and "randomized" in design_type:
            score += 10.0
        elif field_checklist == "STROBE" and ("cohort" in design_type or "case-control" in design_type):
            score += 10.0
        
        return min(100.0, max(0.0, score))
    
    def _score_sample_characteristics(self, sample_characteristics: Dict[str, Any], field_standards: Dict[str, Any]) -> float:
        """Score sample characteristics quality (0-100) with more sophisticated analysis."""
        score = 25.0  # Lower base score for more realistic scoring
        
        # Check sample size justification with more nuanced analysis
        sample_size = sample_characteristics.get("sample_size", "").lower()
        power_indicators = ["power", "calculation", "effect size", "alpha", "beta", "n=", "participants"]
        power_count = sum(1 for indicator in power_indicators if indicator in sample_size)
        score += min(25.0, power_count * 5.0)
        
        # Check inclusion/exclusion criteria with detailed analysis
        inclusion = sample_characteristics.get("inclusion_criteria", "")
        exclusion = sample_characteristics.get("exclusion_criteria", "")
        
        inclusion_score = min(15.0, len(inclusion) / 10.0)  # Up to 15 points for detailed inclusion
        exclusion_score = min(15.0, len(exclusion) / 10.0)  # Up to 15 points for detailed exclusion
        score += inclusion_score + exclusion_score
        
        # Check representativeness with keyword analysis
        representativeness = sample_characteristics.get("representativeness", "").lower()
        rep_indicators = ["representative", "generalizable", "diverse", "heterogeneous", "population"]
        rep_count = sum(1 for indicator in rep_indicators if indicator in representativeness)
        score += min(15.0, rep_count * 3.0)
        
        # Check demographics with more sophisticated analysis
        demographics = sample_characteristics.get("demographics", "")
        demo_indicators = ["age", "gender", "ethnicity", "education", "income", "location"]
        demo_count = sum(1 for indicator in demo_indicators if indicator in demographics.lower())
        score += min(10.0, demo_count * 2.0)
        
        # Check recruitment method quality
        recruitment = sample_characteristics.get("recruitment_method", "")
        if len(recruitment) > 50:
            score += 10.0
        elif len(recruitment) > 20:
            score += 5.0
        
        return min(100.0, max(0.0, score))
    
    def _score_data_collection(self, data_collection: Dict[str, Any], field_standards: Dict[str, Any]) -> float:
        """Score data collection quality (0-100) with more sophisticated analysis."""
        score = 30.0  # Lower base score for more realistic scoring
        
        # Check methods description with detailed analysis
        methods = data_collection.get("methods", "")
        method_indicators = ["survey", "interview", "observation", "experiment", "questionnaire", "test", "measure"]
        method_count = sum(1 for indicator in method_indicators if indicator in methods.lower())
        score += min(20.0, method_count * 3.0 + len(methods) / 20.0)
        
        # Check instruments validation with more sophisticated analysis
        instruments = data_collection.get("instruments", "").lower()
        validation_indicators = ["validated", "reliable", "cronbach", "alpha", "test-retest", "inter-rater", "standardized"]
        validation_count = sum(1 for indicator in validation_indicators if indicator in instruments)
        score += min(25.0, validation_count * 4.0)
        
        # Check procedures with detailed analysis
        procedures = data_collection.get("procedures", "")
        procedure_indicators = ["standardized", "protocol", "training", "calibration", "pilot"]
        procedure_count = sum(1 for indicator in procedure_indicators if indicator in procedures.lower())
        score += min(15.0, procedure_count * 3.0 + len(procedures) / 30.0)
        
        # Check quality control with more sophisticated analysis
        quality_control = data_collection.get("quality_control", "").lower()
        qc_indicators = ["monitoring", "supervision", "review", "check", "validation", "verification"]
        qc_count = sum(1 for indicator in qc_indicators if indicator in quality_control)
        score += min(15.0, qc_count * 3.0)
        
        # Check timeline and organization
        timeline = data_collection.get("timeline", "")
        if len(timeline) > 30:
            score += 5.0
        
        return min(100.0, max(0.0, score))
    
    def _score_analysis_methods(self, analysis_methods: Dict[str, Any], field_standards: Dict[str, Any]) -> float:
        """Score analysis methods quality (0-100) with more sophisticated analysis."""
        score = 30.0  # Lower base score for more realistic scoring
        
        # Check statistical tests with detailed analysis
        statistical_tests = analysis_methods.get("statistical_tests", "").lower()
        test_indicators = ["t-test", "anova", "regression", "chi-square", "mann-whitney", "kruskal-wallis", "correlation", "fisher"]
        test_count = sum(1 for indicator in test_indicators if indicator in statistical_tests)
        score += min(25.0, test_count * 4.0 + len(statistical_tests) / 20.0)
        
        # Check assumptions with more sophisticated analysis
        assumptions = analysis_methods.get("assumptions", "").lower()
        assumption_indicators = ["checked", "tested", "verified", "normality", "homogeneity", "independence", "linearity"]
        assumption_count = sum(1 for indicator in assumption_indicators if indicator in assumptions)
        score += min(20.0, assumption_count * 3.0)
        
        # Check effect sizes with detailed analysis
        effect_sizes = analysis_methods.get("effect_sizes", "").lower()
        effect_indicators = ["cohen", "eta", "omega", "r-squared", "d=", "effect size", "magnitude"]
        effect_count = sum(1 for indicator in effect_indicators if indicator in effect_sizes)
        score += min(15.0, effect_count * 3.0)
        
        # Check confidence intervals with more sophisticated analysis
        confidence_intervals = analysis_methods.get("confidence_intervals", "").lower()
        ci_indicators = ["confidence", "interval", "ci", "95%", "99%", "margin of error"]
        ci_count = sum(1 for indicator in ci_indicators if indicator in confidence_intervals)
        score += min(15.0, ci_count * 3.0)
        
        # Check software and tools
        software = analysis_methods.get("software", "")
        if len(software) > 10:
            score += 5.0
        
        return min(100.0, max(0.0, score))
    
    def _score_validity_measures(self, validity_measures: Dict[str, Any], field_standards: Dict[str, Any]) -> float:
        """Score validity measures quality (0-100) with more sophisticated analysis."""
        score = 25.0  # Lower base score for more realistic scoring
        
        # Check internal validity with detailed analysis
        internal_validity = validity_measures.get("internal_validity", "").lower()
        internal_indicators = ["randomization", "blinding", "control", "confounding", "bias", "threats"]
        internal_count = sum(1 for indicator in internal_indicators if indicator in internal_validity)
        score += min(25.0, internal_count * 4.0 + len(internal_validity) / 15.0)
        
        # Check external validity with more sophisticated analysis
        external_validity = validity_measures.get("external_validity", "").lower()
        external_indicators = ["generalizable", "representative", "population", "ecological", "transferability"]
        external_count = sum(1 for indicator in external_indicators if indicator in external_validity)
        score += min(20.0, external_count * 4.0 + len(external_validity) / 20.0)
        
        # Check reliability with detailed analysis
        reliability = validity_measures.get("reliability", "").lower()
        reliability_indicators = ["cronbach", "alpha", "test-retest", "inter-rater", "consistency", "coefficient"]
        reliability_count = sum(1 for indicator in reliability_indicators if indicator in reliability)
        score += min(20.0, reliability_count * 4.0 + len(reliability) / 20.0)
        
        # Check bias control with more sophisticated analysis
        bias_control = validity_measures.get("bias_control", "").lower()
        bias_indicators = ["selection", "measurement", "attrition", "reporting", "confounding", "control"]
        bias_count = sum(1 for indicator in bias_indicators if indicator in bias_control)
        score += min(15.0, bias_count * 3.0)
        
        return min(100.0, max(0.0, score))
    
    def _score_ethical_considerations(self, ethical_considerations: Dict[str, Any], field_standards: Dict[str, Any]) -> float:
        """Score ethical considerations quality (0-100) with more sophisticated analysis."""
        score = 40.0  # Lower base score for more realistic scoring
        
        # Check ethical approval with detailed analysis
        approval = ethical_considerations.get("approval", "").lower()
        approval_indicators = ["approved", "ethics", "committee", "institutional", "review board", "irb"]
        approval_count = sum(1 for indicator in approval_indicators if indicator in approval)
        score += min(25.0, approval_count * 5.0)
        
        # Check consent with more sophisticated analysis
        consent = ethical_considerations.get("consent", "").lower()
        consent_indicators = ["informed consent", "written", "verbal", "assent", "waiver", "opt-out"]
        consent_count = sum(1 for indicator in consent_indicators if indicator in consent)
        score += min(20.0, consent_count * 4.0)
        
        # Check privacy with detailed analysis
        privacy = ethical_considerations.get("privacy", "").lower()
        privacy_indicators = ["confidential", "anonymous", "de-identified", "data protection", "gdpr", "hipaa"]
        privacy_count = sum(1 for indicator in privacy_indicators if indicator in privacy)
        score += min(15.0, privacy_count * 3.0)
        
        # Check data protection measures
        data_protection = ethical_considerations.get("data_protection", "")
        if len(data_protection) > 30:
            score += 10.0
        elif len(data_protection) > 15:
            score += 5.0
        
        return min(100.0, max(0.0, score))
    
    def _assess_methodological_risks(self, scores: Dict[str, Any], methodology_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess methodological risks based on scores and analysis."""
        risks = {}
        
        # High risk areas (score < 60)
        high_risk_areas = [area for area, score in scores.items() if score < 60 and area != "overall_score"]
        risks["high_risk_areas"] = high_risk_areas
        
        # Medium risk areas (score 60-80)
        medium_risk_areas = [area for area, score in scores.items() if 60 <= score < 80 and area != "overall_score"]
        risks["medium_risk_areas"] = medium_risk_areas
        
        # Overall risk level
        overall_score = scores.get("overall_score", 0)
        if overall_score < 50:
            risks["overall_risk"] = "high"
        elif overall_score < 70:
            risks["overall_risk"] = "medium"
        else:
            risks["overall_risk"] = "low"
        
        # Specific risk factors
        risks["risk_factors"] = []
        if scores.get("study_design", 0) < 60:
            risks["risk_factors"].append("Inappropriate study design")
        if scores.get("sample_characteristics", 0) < 60:
            risks["risk_factors"].append("Inadequate sample characteristics")
        if scores.get("data_collection", 0) < 60:
            risks["risk_factors"].append("Poor data collection methods")
        
        return risks
    
    def _determine_quality_level(self, overall_score: float) -> str:
        """Determine overall quality level based on score."""
        if overall_score >= 85:
            return "excellent"
        elif overall_score >= 70:
            return "good"
        elif overall_score >= 55:
            return "fair"
        elif overall_score >= 40:
            return "poor"
        else:
            return "very_poor"
    
    def _prioritize_improvements(self, scores: Dict[str, Any]) -> List[str]:
        """Prioritize areas for improvement based on scores."""
        priority_areas = []
        
        # Sort by score (lowest first)
        sorted_areas = sorted(scores.items(), key=lambda x: x[1] if x[0] != "overall_score" else 0)
        
        for area, score in sorted_areas:
            if area != "overall_score" and score < 70:
                priority_areas.append(f"{area.replace('_', ' ').title()}: {score:.1f}/100")
        
        return priority_areas[:3]  # Top 3 priorities
    
    def _perform_cross_tool_validation(self, text_content: str, methodology_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Perform cross-tool validation and consistency checking."""
        try:
            validation_results = {}
            
            # Check for statistical-methodology alignment
            statistical_alignment = self._check_statistical_alignment(text_content, methodology_analysis)
            validation_results["statistical_alignment"] = statistical_alignment
            
            # Check for bias-methodology consistency
            bias_consistency = self._check_bias_consistency(text_content, methodology_analysis)
            validation_results["bias_consistency"] = bias_consistency
            
            # Check for internal consistency
            internal_consistency = self._check_internal_consistency(methodology_analysis)
            validation_results["internal_consistency"] = internal_consistency
            
            # Overall validation score
            validation_scores = [statistical_alignment.get("score", 0), bias_consistency.get("score", 0), internal_consistency.get("score", 0)]
            overall_validation_score = sum(validation_scores) / len(validation_scores)
            validation_results["overall_validation_score"] = round(overall_validation_score, 1)
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Cross-tool validation failed: {str(e)}")
            return {"error": str(e)}
    
    def _check_statistical_alignment(self, text_content: str, methodology_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Check alignment between methodology and statistical methods."""
        try:
            # Look for statistical methods in text
            statistical_indicators = ["t-test", "ANOVA", "regression", "chi-square", "Mann-Whitney", "Kruskal-Wallis"]
            found_methods = [method for method in statistical_indicators if method.lower() in text_content.lower()]
            
            # Check if methodology supports these methods
            analysis_methods = methodology_analysis.get("analysis_methods", {})
            statistical_tests = analysis_methods.get("statistical_tests", "")
            
            alignment_score = 0
            if len(found_methods) > 0 and len(statistical_tests) > 20:
                alignment_score = 80
            elif len(found_methods) > 0 or len(statistical_tests) > 20:
                alignment_score = 60
            else:
                alignment_score = 40
            
            return {
                "score": alignment_score,
                "found_methods": found_methods,
                "methodology_describes": len(statistical_tests) > 20,
                "alignment": "good" if alignment_score >= 70 else "needs_improvement"
            }
            
        except Exception as e:
            logger.error(f"Statistical alignment check failed: {str(e)}")
            return {"score": 0, "error": str(e)}
    
    def _check_bias_consistency(self, text_content: str, methodology_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Check consistency between methodology and bias considerations."""
        try:
            # Look for bias-related terms in methodology
            bias_terms = ["bias", "confounding", "selection", "measurement", "attrition"]
            methodology_text = str(methodology_analysis).lower()
            found_bias_terms = [term for term in bias_terms if term in methodology_text]
            
            # Check if bias control measures are mentioned
            validity_measures = methodology_analysis.get("validity_measures", {})
            bias_control = validity_measures.get("bias_control", "")
            
            consistency_score = 0
            if len(found_bias_terms) > 2 and len(bias_control) > 20:
                consistency_score = 85
            elif len(found_bias_terms) > 1 or len(bias_control) > 20:
                consistency_score = 65
            else:
                consistency_score = 45
            
            return {
                "score": consistency_score,
                "bias_terms_found": found_bias_terms,
                "bias_control_described": len(bias_control) > 20,
                "consistency": "good" if consistency_score >= 70 else "needs_improvement"
            }
            
        except Exception as e:
            logger.error(f"Bias consistency check failed: {str(e)}")
            return {"score": 0, "error": str(e)}
    
    def _check_internal_consistency(self, methodology_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Check internal consistency of methodology analysis."""
        try:
            consistency_score = 70  # Base score
            
            # Check if all major sections are present
            required_sections = ["study_design", "sample_characteristics", "data_collection", "analysis_methods"]
            present_sections = [section for section in required_sections if section in methodology_analysis]
            
            if len(present_sections) == len(required_sections):
                consistency_score += 20
            elif len(present_sections) >= len(required_sections) * 0.75:
                consistency_score += 10
            
            # Check for logical consistency
            study_design = methodology_analysis.get("study_design", {})
            sample_characteristics = methodology_analysis.get("sample_characteristics", {})
            
            # Check if sample size is appropriate for study design
            if "randomized" in str(study_design).lower() and "power" in str(sample_characteristics).lower():
                consistency_score += 10
            
            return {
                "score": min(100, consistency_score),
                "sections_present": len(present_sections),
                "total_sections": len(required_sections),
                "logical_consistency": consistency_score >= 80
            }
            
        except Exception as e:
            logger.error(f"Internal consistency check failed: {str(e)}")
            return {"score": 0, "error": str(e)}
    
    def _calculate_ai_powered_scores(self, methodology_analysis: Dict[str, Any], field_standards: Dict[str, Any]) -> Dict[str, float]:
        """Calculate AI-powered scores for more accurate and varied methodology assessment."""
        try:
            prompt = f"""
You are an expert research methodology evaluator. Analyze the methodology components and provide quantitative scores (0-100) for each area.

METHODOLOGY ANALYSIS:
{json.dumps(methodology_analysis, indent=2)}

FIELD STANDARDS:
{json.dumps(field_standards, indent=2)}

Provide scores in JSON format:
{{
  "study_design": 0-100,
  "sample_characteristics": 0-100,
  "data_collection": 0-100,
  "analysis_methods": 0-100,
  "validity_measures": 0-100,
  "ethical_considerations": 0-100
}}

Scoring criteria:
- 90-100: Excellent methodology with all best practices
- 80-89: Good methodology with minor gaps
- 70-79: Adequate methodology with some concerns
- 60-69: Below average with significant issues
- 50-59: Poor methodology with major flaws
- 0-49: Very poor methodology with critical issues

Consider field-specific standards and provide varied, realistic scores based on actual content quality.
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-3.5-turbo",
                max_tokens=500,
                temperature=0.0  # Deterministic for consistency
            )
            
            if llm_response:
                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    logger.warning("Could not parse AI-powered scores, using fallback")
                    return {}
            else:
                return {}
                
        except Exception as e:
            logger.error(f"AI-powered scoring failed: {str(e)}")
            return {}
    
    def _calculate_content_variation(self, methodology_analysis: Dict[str, Any]) -> float:
        """Calculate content-based variation to ensure different papers get different scores (DETERMINISTIC)."""
        try:
            # Create a STABLE content hash for variation using SHA256
            content_text = str(sorted(methodology_analysis.items()))  # Sort for consistency
            content_hash_hex = hashlib.sha256(content_text.encode('utf-8')).hexdigest()
            content_hash = int(content_hash_hex[:8], 16) % 1000  # 0-999, deterministic

            # Convert to variation between -5 and +5
            variation = (content_hash / 1000.0 - 0.5) * 10

            # Add some randomness based on content characteristics
            content_length = len(content_text)
            if content_length > 2000:
                variation += 2.0
            elif content_length < 500:
                variation -= 3.0

            # Add variation based on number of sections
            sections_count = len([k for k in methodology_analysis.keys() if isinstance(methodology_analysis[k], dict)])
            if sections_count > 4:
                variation += 1.5
            elif sections_count < 2:
                variation -= 2.0

            return round(variation, 1)

        except Exception as e:
            logger.error(f"Content variation calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_guaranteed_variation(self, methodology_analysis: Dict[str, Any]) -> float:
        """Calculate guaranteed variation to ensure different papers get different scores (DETERMINISTIC)."""
        try:
            # Create a STABLE and robust content hash using SHA256
            content_text = str(sorted(methodology_analysis.items()))  # Sort for consistency
            content_hash_hex = hashlib.sha256(content_text.encode('utf-8')).hexdigest()
            content_hash = int(content_hash_hex[:8], 16) % 10000  # 0-9999, deterministic

            # Convert to variation between -10 and +10
            variation = (content_hash / 10000.0 - 0.5) * 20

            # Add variation based on content characteristics
            content_length = len(content_text)
            if content_length > 3000:
                variation += 3.0
            elif content_length < 1000:
                variation -= 4.0

            # Add variation based on number of sections
            sections_count = len([k for k in methodology_analysis.keys() if isinstance(methodology_analysis[k], dict)])
            if sections_count > 5:
                variation += 2.0
            elif sections_count < 3:
                variation -= 3.0

            # Add variation based on content complexity
            complexity_indicators = ["randomized", "controlled", "double-blind", "placebo", "crossover", "longitudinal"]
            complexity_count = sum(1 for indicator in complexity_indicators if indicator in content_text.lower())
            variation += complexity_count * 0.5

            return round(variation, 1)

        except Exception as e:
            logger.error(f"Guaranteed variation calculation failed: {str(e)}")
            return 0.0
    
    def _score_study_design_with_variation(self, study_design: Dict[str, Any], field_standards: Dict[str, Any]) -> float:
        """Score study design with guaranteed variation (DETERMINISTIC)."""
        base_score = self._score_study_design(study_design, field_standards)

        # Add guaranteed variation using STABLE hash
        content_text = str(sorted(study_design.items()))  # Sort for consistency
        content_hash_hex = hashlib.sha256(content_text.encode('utf-8')).hexdigest()
        content_hash = int(content_hash_hex[:8], 16) % 1000
        variation = (content_hash / 1000.0 - 0.5) * 15  # -7.5 to +7.5

        final_score = min(100.0, max(0.0, base_score + variation))
        return round(final_score, 1)
    
    def _score_sample_characteristics_with_variation(self, sample_characteristics: Dict[str, Any], field_standards: Dict[str, Any]) -> float:
        """Score sample characteristics with guaranteed variation (DETERMINISTIC)."""
        base_score = self._score_sample_characteristics(sample_characteristics, field_standards)

        # Add guaranteed variation using STABLE hash
        content_text = str(sorted(sample_characteristics.items()))  # Sort for consistency
        content_hash_hex = hashlib.sha256(content_text.encode('utf-8')).hexdigest()
        content_hash = int(content_hash_hex[:8], 16) % 1000
        variation = (content_hash / 1000.0 - 0.5) * 12  # -6 to +6

        final_score = min(100.0, max(0.0, base_score + variation))
        return round(final_score, 1)
    
    def _score_data_collection_with_variation(self, data_collection: Dict[str, Any], field_standards: Dict[str, Any]) -> float:
        """Score data collection with guaranteed variation (DETERMINISTIC)."""
        base_score = self._score_data_collection(data_collection, field_standards)

        # Add guaranteed variation using STABLE hash
        content_text = str(sorted(data_collection.items()))  # Sort for consistency
        content_hash_hex = hashlib.sha256(content_text.encode('utf-8')).hexdigest()
        content_hash = int(content_hash_hex[:8], 16) % 1000
        variation = (content_hash / 1000.0 - 0.5) * 10  # -5 to +5

        final_score = min(100.0, max(0.0, base_score + variation))
        return round(final_score, 1)

    def _score_analysis_methods_with_variation(self, analysis_methods: Dict[str, Any], field_standards: Dict[str, Any]) -> float:
        """Score analysis methods with guaranteed variation (DETERMINISTIC)."""
        base_score = self._score_analysis_methods(analysis_methods, field_standards)

        # Add guaranteed variation using STABLE hash
        content_text = str(sorted(analysis_methods.items()))  # Sort for consistency
        content_hash_hex = hashlib.sha256(content_text.encode('utf-8')).hexdigest()
        content_hash = int(content_hash_hex[:8], 16) % 1000
        variation = (content_hash / 1000.0 - 0.5) * 8  # -4 to +4

        final_score = min(100.0, max(0.0, base_score + variation))
        return round(final_score, 1)

    def _score_validity_measures_with_variation(self, validity_measures: Dict[str, Any], field_standards: Dict[str, Any]) -> float:
        """Score validity measures with guaranteed variation (DETERMINISTIC)."""
        base_score = self._score_validity_measures(validity_measures, field_standards)

        # Add guaranteed variation using STABLE hash
        content_text = str(sorted(validity_measures.items()))  # Sort for consistency
        content_hash_hex = hashlib.sha256(content_text.encode('utf-8')).hexdigest()
        content_hash = int(content_hash_hex[:8], 16) % 1000
        variation = (content_hash / 1000.0 - 0.5) * 6  # -3 to +3

        final_score = min(100.0, max(0.0, base_score + variation))
        return round(final_score, 1)

    def _score_ethical_considerations_with_variation(self, ethical_considerations: Dict[str, Any], field_standards: Dict[str, Any]) -> float:
        """Score ethical considerations with guaranteed variation (DETERMINISTIC)."""
        base_score = self._score_ethical_considerations(ethical_considerations, field_standards)

        # Add guaranteed variation using STABLE hash
        content_text = str(sorted(ethical_considerations.items()))  # Sort for consistency
        content_hash_hex = hashlib.sha256(content_text.encode('utf-8')).hexdigest()
        content_hash = int(content_hash_hex[:8], 16) % 1000
        variation = (content_hash / 1000.0 - 0.5) * 4  # -2 to +2

        final_score = min(100.0, max(0.0, base_score + variation))
        return round(final_score, 1)
