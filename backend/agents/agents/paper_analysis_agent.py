"""
Enhanced Paper Analysis Agent for QualiLens.

This agent orchestrates multiple specialized tools to provide comprehensive
paper analysis including summarization, bias detection, methodology analysis,
and quality assessment.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentResponse
from ..question_classifier import ClassificationResult, QueryType

logger = logging.getLogger(__name__)


class PaperAnalysisAgent(BaseAgent):
    """
    Enhanced agent responsible for comprehensive paper analysis using multiple specialized tools.
    """
    
    def _get_name(self) -> str:
        """Return the name of this agent."""
        return "paper_analysis_agent"
    
    def _get_description(self) -> str:
        """Return the description of this agent."""
        return "Comprehensive paper analysis using multiple specialized tools for summarization, bias detection, methodology analysis, and quality assessment"
    
    def _get_capabilities(self) -> List[str]:
        """Return the capabilities of this agent."""
        return [
            "comprehensive_paper_analysis",
            "pdf_parsing",
            "content_summarization",
            "bias_detection",
            "methodology_analysis",
            "quality_assessment",
            "research_queries"
        ]
    
    def can_handle(self, query: str, classification: ClassificationResult) -> bool:
        """
        Determine if this agent can handle the given query.
        
        Args:
            query (str): The user query
            classification (ClassificationResult): The classification result
            
        Returns:
            bool: True if this agent can handle the query
        """
        logger.info(f"Paper Analysis Agent can_handle called with query: {query}")
        logger.info(f"Classification query_type: {classification.query_type}")
        logger.info(f"Classification suggested_tool: {classification.suggested_tool}")
        
        # Handle paper analysis queries
        if classification.query_type == QueryType.PAPER_ANALYSIS:
            logger.info("Handling as paper_analysis query type")
            return True
        
        # Handle queries that require paper analysis tools
        paper_analysis_tools = [
            "paper_analyzer_tool",
            "parse_pdf_tool",
            "link_analyzer_tool",
            "text_section_analyzer_tool"
        ]
        
        if classification.suggested_tool in paper_analysis_tools:
            logger.info(f"Handling as paper analysis tool: {classification.suggested_tool}")
            return True
        
        # Handle detailed analysis requests
        detailed_analysis_keywords = [
            "detailed analysis", "comprehensive analysis", "summary", "key discoveries",
            "methodology analysis", "results analysis", "quality assessment", "analysis level: comprehensive"
        ]
        
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in detailed_analysis_keywords):
            logger.info(f"Handling as detailed analysis query with keywords: {[kw for kw in detailed_analysis_keywords if kw in query_lower]}")
            return True
        
        logger.info("Paper Analysis Agent cannot handle this query")
        return False
    
    def process_query(self, query: str, classification: ClassificationResult) -> AgentResponse:
        """
        Process a user query using the multi-tool analysis pipeline.
        
        Args:
            query (str): The user query
            classification (ClassificationResult): The classification result
            
        Returns:
            AgentResponse: Response from the agent
        """
        start_time = datetime.now()
        tools_used = []
        
        try:
            # Determine analysis level based on query
            analysis_level = self._determine_analysis_level(query)
            logger.info(f"Starting {analysis_level} analysis for query: {query}")
            logger.info(f"Analysis level determined: {analysis_level}")
            
            # Step 1: Parse PDF if needed
            text_content = None
            pdf_metadata = None
            
            if classification.suggested_tool == "parse_pdf" or "pdf" in query.lower():
                pdf_result = self._parse_pdf_if_needed(classification.extracted_parameters)
                if pdf_result and pdf_result.get("success"):
                    text_content = pdf_result.get("text", "")
                    pdf_metadata = pdf_result.get("metadata", {})
                    tools_used.append("parse_pdf")
            
            # If no text content from PDF parsing, try to get it from other sources
            if not text_content:
                text_content = self._extract_text_content(classification.extracted_parameters)
            
            # If still no text content, use the query itself as text content for analysis
            if not text_content:
                text_content = query
                logger.info(f"Using query as text content for analysis: {query[:100]}...")
            
            if not text_content:
                return AgentResponse(
                    success=False,
                    result=None,
                    agent_name=self.name,
                    tools_used=tools_used,
                    error_message="No text content available for analysis",
                    execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    timestamp=start_time
                )
            
            # Step 2: Run analysis pipeline based on level
            logger.info(f"Running analysis pipeline for level: {analysis_level}")
            logger.info(f"Text content length: {len(text_content) if text_content else 0}")
            analysis_results = self._run_analysis_pipeline(text_content, analysis_level, query)
            tools_used.extend(analysis_results.get("tools_used", []))
            logger.info(f"Analysis pipeline completed. Tools used: {analysis_results.get('tools_used', [])}")
            logger.info(f"Analysis results keys: {list(analysis_results.keys())}")
            logger.info(f"Total tools used so far: {tools_used}")
            
            # Step 3: Integrate results
            logger.info("Integrating analysis results...")
            integrated_result = self._integrate_analysis_results(
                text_content, analysis_results, pdf_metadata, query
            )
            logger.info(f"Integrated result keys: {list(integrated_result.keys())}")
            logger.info(f"Final tools used: {tools_used}")
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.info(f"Returning successful response with {len(tools_used)} tools used")
            return AgentResponse(
                success=True,
                result=integrated_result,
                agent_name=self.name,
                tools_used=tools_used,
                error_message=None,
                execution_time_ms=execution_time,
                timestamp=start_time
            )
            
        except Exception as e:
            logger.error(f"Paper analysis agent error: {str(e)}")
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return AgentResponse(
                success=False,
                result=None,
                agent_name=self.name,
                tools_used=tools_used,
                error_message=f"Paper analysis agent failed: {str(e)}",
                execution_time_ms=execution_time,
                timestamp=start_time
            )
    
    def _determine_analysis_level(self, query: str) -> str:
        """Always return comprehensive analysis level."""
        return "comprehensive"
    
    def _parse_pdf_if_needed(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse PDF if file path is provided."""
        file_path = params.get('file_path') or params.get('file_path')
        if file_path:
            try:
                return self.execute_tool("parse_pdf", file_path=file_path)
            except Exception as e:
                logger.error(f"PDF parsing failed: {str(e)}")
                return None
        return None
    
    def _extract_text_content(self, params: Dict[str, Any]) -> Optional[str]:
        """Extract text content from various sources."""
        # Try different parameter names for text content
        text_sources = ['text_content', 'text', 'content', 'paper_text']
        for source in text_sources:
            if source in params and params[source]:
                return params[source]
        return None
    
    def _run_analysis_pipeline(self, text_content: str, analysis_level: str, query: str) -> Dict[str, Any]:
        """Run comprehensive analysis pipeline with all tools."""
        results = {
            "tools_used": [],
            "analysis_level": "comprehensive"
        }
        
        try:
            logger.info("Executing comprehensive analysis with all tools")
            
            # Content summarization
            summary_result = self.execute_tool(
                "content_summarizer_tool",
                text_content=text_content,
                summary_type="comprehensive",
                max_length=800
            )
            if summary_result.get("success"):
                results["content_summary"] = summary_result
                results["tools_used"].append("content_summarizer_tool")
            
            # Bias detection
            bias_result = self.execute_tool(
                "bias_detection_tool",
                text_content=text_content,
                severity_threshold="low"
            )
            if bias_result.get("success"):
                results["bias_analysis"] = bias_result
                results["tools_used"].append("bias_detection_tool")
            
            # Methodology analysis
            methodology_result = self.execute_tool(
                "methodology_analyzer_tool",
                text_content=text_content,
                analysis_depth="comprehensive"
            )
            if methodology_result.get("success"):
                results["methodology_analysis"] = methodology_result
                results["tools_used"].append("methodology_analyzer_tool")
            
            # Statistical validation
            statistical_result = self.execute_tool(
                "statistical_validator_tool",
                text_content=text_content,
                validation_level="comprehensive"
            )
            if statistical_result.get("success"):
                results["statistical_analysis"] = statistical_result
                results["tools_used"].append("statistical_validator_tool")
            
            # Reproducibility assessment
            reproducibility_result = self.execute_tool(
                "reproducibility_assessor_tool",
                text_content=text_content,
                reproducibility_level="detailed"
            )
            if reproducibility_result.get("success"):
                results["reproducibility_analysis"] = reproducibility_result
                results["tools_used"].append("reproducibility_assessor_tool")
            
            # Research gap identification
            gap_result = self.execute_tool(
                "research_gap_identifier_tool",
                text_content=text_content,
                future_focus="comprehensive"
            )
            if gap_result.get("success"):
                results["research_gap_analysis"] = gap_result
                results["tools_used"].append("research_gap_identifier_tool")
            
            # Citation analysis
            citation_result = self.execute_tool(
                "citation_analyzer_tool",
                text_content=text_content,
                analysis_type="bibliometric"
            )
            if citation_result.get("success"):
                results["citation_analysis"] = citation_result
                results["tools_used"].append("citation_analyzer_tool")
            
            # Quality assessment (using results from all other tools)
            quality_result = self.execute_tool(
                "quality_assessor_tool",
                analysis_results=results
            )
            if quality_result.get("success"):
                results["quality_assessment"] = quality_result
                results["tools_used"].append("quality_assessor_tool")
            
            return results
            
        except Exception as e:
            logger.error(f"Analysis pipeline failed: {str(e)}")
            return {
                "tools_used": results["tools_used"],
                "error": str(e),
                "analysis_level": "comprehensive"
            }
    
    def _integrate_analysis_results(self, text_content: str, analysis_results: Dict[str, Any], 
                                  pdf_metadata: Optional[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Integrate all analysis results into a comprehensive response."""
        try:
            integrated_result = {
                "success": True,
                "analysis_level": analysis_results.get("analysis_level", "comprehensive"),
                "tools_used": analysis_results.get("tools_used", []),
                "query": query,
                "text_length": len(text_content),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # Add PDF metadata if available
            if pdf_metadata:
                integrated_result["pdf_metadata"] = pdf_metadata
            
            # Add content summary if available
            if "content_summary" in analysis_results:
                summary_data = analysis_results["content_summary"]
                integrated_result["executive_summary"] = summary_data.get("executive_summary", "")
                integrated_result["key_points"] = summary_data.get("key_points", [])
                integrated_result["summary"] = summary_data.get("summary", "")
            
            # Add bias analysis if available
            if "bias_analysis" in analysis_results:
                bias_data = analysis_results["bias_analysis"]
                integrated_result["detected_biases"] = bias_data.get("detected_biases", [])
                integrated_result["bias_summary"] = bias_data.get("bias_summary", "")
                integrated_result["limitations"] = bias_data.get("limitations", [])
                integrated_result["confounding_factors"] = bias_data.get("confounding_factors", [])
            
            # Add methodology analysis if available
            if "methodology_analysis" in analysis_results:
                methodology_data = analysis_results["methodology_analysis"]
                logger.info(f"🔍 METHODOLOGY DATA IN INTEGRATION:")
                logger.info(f"   - methodology_data keys: {list(methodology_data.keys())}")
                logger.info(f"   - overall_quality_score: {methodology_data.get('overall_quality_score')}")
                logger.info(f"   - quantitative_scores: {methodology_data.get('quantitative_scores', {})}")
                
                integrated_result["study_design"] = methodology_data.get("study_design", "")
                integrated_result["sample_characteristics"] = methodology_data.get("sample_characteristics", {})
                integrated_result["methodological_strengths"] = methodology_data.get("methodological_strengths", [])
                integrated_result["methodological_weaknesses"] = methodology_data.get("methodological_weaknesses", [])
                integrated_result["methodology_quality_rating"] = methodology_data.get("quality_rating", "")
                # Add the overall quality score from methodology analysis
                if methodology_data.get("overall_quality_score"):
                    integrated_result["overall_quality_score"] = methodology_data.get("overall_quality_score")
                    logger.info(f"✅ SET overall_quality_score to: {methodology_data.get('overall_quality_score')}")
                else:
                    logger.warning(f"⚠️ NO overall_quality_score found in methodology_data")
            
            # Add statistical analysis if available
            if "statistical_analysis" in analysis_results:
                statistical_data = analysis_results["statistical_analysis"]
                integrated_result["statistical_tests_used"] = statistical_data.get("statistical_tests_used", [])
                integrated_result["test_appropriateness"] = statistical_data.get("test_appropriateness", {})
                integrated_result["statistical_concerns"] = statistical_data.get("statistical_concerns", [])
                integrated_result["statistical_recommendations"] = statistical_data.get("recommendations", [])
            
            # Add reproducibility analysis if available
            if "reproducibility_analysis" in analysis_results:
                reproducibility_data = analysis_results["reproducibility_analysis"]
                integrated_result["reproducibility_score"] = reproducibility_data.get("reproducibility_score", 0.0)
                integrated_result["reproducibility_barriers"] = reproducibility_data.get("reproducibility_barriers", [])
                integrated_result["data_availability"] = reproducibility_data.get("data_availability", "")
                integrated_result["code_availability"] = reproducibility_data.get("code_availability", "")
            
            # Add research gap analysis if available
            if "research_gap_analysis" in analysis_results:
                gap_data = analysis_results["research_gap_analysis"]
                integrated_result["research_gaps"] = gap_data.get("research_gaps", [])
                integrated_result["future_directions"] = gap_data.get("future_directions", [])
                integrated_result["unaddressed_questions"] = gap_data.get("unaddressed_questions", [])
                integrated_result["methodological_gaps"] = gap_data.get("methodological_gaps", [])
                integrated_result["theoretical_gaps"] = gap_data.get("theoretical_gaps", [])
            
            # Add citation analysis if available
            if "citation_analysis" in analysis_results:
                citation_data = analysis_results["citation_analysis"]
                integrated_result["total_citations"] = citation_data.get("total_citations", 0)
                integrated_result["citation_quality"] = citation_data.get("citation_quality", "")
                integrated_result["reference_analysis"] = citation_data.get("reference_analysis", {})
                integrated_result["citation_gaps"] = citation_data.get("citation_gaps", [])
                integrated_result["bibliometric_indicators"] = citation_data.get("bibliometric_indicators", {})
            
            # Add quality assessment if available (but don't override methodology score)
            if "quality_assessment" in analysis_results:
                quality_data = analysis_results["quality_assessment"]
                
                # Only use quality assessor score if no methodology score exists
                if not integrated_result.get("overall_quality_score") or integrated_result.get("overall_quality_score") == 0:
                    integrated_result["overall_quality_score"] = quality_data.get("overall_quality_score", 0.0)
                    logger.info(f"⚠️ Using quality assessor score: {quality_data.get('overall_quality_score', 0.0)}")
                else:
                    logger.info(f"✅ Keeping methodology analyzer score: {integrated_result.get('overall_quality_score')} (ignoring quality assessor: {quality_data.get('overall_quality_score', 0.0)})")
                
                integrated_result["quality_breakdown"] = quality_data.get("quality_breakdown", {})
                integrated_result["quality_strengths"] = quality_data.get("strengths", [])
                integrated_result["quality_weaknesses"] = quality_data.get("weaknesses", [])
                integrated_result["quality_recommendations"] = quality_data.get("recommendations", [])
                integrated_result["quality_confidence_level"] = quality_data.get("confidence_level", "")
                integrated_result["scoring_criteria_used"] = quality_data.get("scoring_criteria_used", [])
            
            # Generate overall assessment
            integrated_result["overall_assessment"] = self._generate_overall_assessment(analysis_results)
            
            # Debug logging for final result
            logger.info(f"🔍 FINAL INTEGRATED RESULT:")
            logger.info(f"   - overall_quality_score: {integrated_result.get('overall_quality_score')}")
            logger.info(f"   - methodology_quality_rating: {integrated_result.get('methodology_quality_rating')}")
            logger.info(f"   - All keys: {list(integrated_result.keys())}")
            
            return integrated_result
            
        except Exception as e:
            logger.error(f"Result integration failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "raw_results": analysis_results
            }
    
    def _generate_overall_assessment(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an overall assessment based on all analysis results."""
        assessment = {
            "analysis_completeness": "partial",
            "key_strengths": [],
            "key_concerns": [],
            "overall_quality": "unknown"
        }
        
        try:
            # Assess completeness
            available_analyses = [key for key in analysis_results.keys() 
                               if key not in ["tools_used", "analysis_level", "error"]]
            # Always comprehensive analysis
            assessment["analysis_completeness"] = "comprehensive"
            
            # Extract key strengths from methodology analysis
            if "methodology_analysis" in analysis_results:
                methodology_data = analysis_results["methodology_analysis"]
                strengths = methodology_data.get("methodological_strengths", [])
                assessment["key_strengths"].extend(strengths[:3])  # Top 3 strengths
            
            # Extract key concerns from bias analysis
            if "bias_analysis" in analysis_results:
                bias_data = analysis_results["bias_analysis"]
                limitations = bias_data.get("limitations", [])
                detected_biases = bias_data.get("detected_biases", [])
                assessment["key_concerns"].extend(limitations[:2])  # Top 2 limitations
                assessment["key_concerns"].extend([bias.get("description", "") for bias in detected_biases[:2]])
            
            # Extract additional concerns from Phase 2 tools
            if "statistical_analysis" in analysis_results:
                statistical_data = analysis_results["statistical_analysis"]
                statistical_concerns = statistical_data.get("statistical_concerns", [])
                assessment["key_concerns"].extend([concern.get("concern", "") for concern in statistical_concerns[:2]])
            
            if "reproducibility_analysis" in analysis_results:
                reproducibility_data = analysis_results["reproducibility_analysis"]
                barriers = reproducibility_data.get("reproducibility_barriers", [])
                assessment["key_concerns"].extend([barrier.get("barrier", "") for barrier in barriers[:2]])
            
            # Determine overall quality based on multiple factors
            quality_indicators = []
            
            # Methodology quality
            if "methodology_analysis" in analysis_results:
                quality_rating = analysis_results["methodology_analysis"].get("quality_rating", "").lower()
                if "high" in quality_rating:
                    quality_indicators.append("high")
                elif "medium" in quality_rating:
                    quality_indicators.append("medium")
                elif "low" in quality_rating:
                    quality_indicators.append("low")
            
            # Statistical quality
            if "statistical_analysis" in analysis_results:
                statistical_quality = analysis_results["statistical_analysis"].get("overall_quality", "").lower()
                if "high" in statistical_quality:
                    quality_indicators.append("high")
                elif "medium" in statistical_quality:
                    quality_indicators.append("medium")
                elif "low" in statistical_quality:
                    quality_indicators.append("low")
            
            # Reproducibility score
            if "reproducibility_analysis" in analysis_results:
                reproducibility_score = analysis_results["reproducibility_analysis"].get("reproducibility_score", 0.0)
                if reproducibility_score >= 0.8:
                    quality_indicators.append("high")
                elif reproducibility_score >= 0.6:
                    quality_indicators.append("medium")
                else:
                    quality_indicators.append("low")
            
            # Determine overall quality
            if quality_indicators:
                high_count = quality_indicators.count("high")
                medium_count = quality_indicators.count("medium")
                low_count = quality_indicators.count("low")
                
                if high_count >= 2:
                    assessment["overall_quality"] = "high"
                elif medium_count >= 2 or (high_count >= 1 and medium_count >= 1):
                    assessment["overall_quality"] = "medium"
                elif low_count >= 2:
                    assessment["overall_quality"] = "low"
                else:
                    assessment["overall_quality"] = "mixed"
            
            return assessment
            
        except Exception as e:
            logger.error(f"Overall assessment generation failed: {str(e)}")
            return assessment
