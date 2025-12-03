"""
Enhanced Paper Analysis Agent for QualiLens.

This agent orchestrates multiple specialized tools to provide comprehensive
paper analysis including summarization, bias detection, methodology analysis,
and quality assessment.
"""

import logging
import sys
import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentResponse
from ..question_classifier import ClassificationResult, QueryType

# Import scorers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from enhanced_scorer import EnhancedScorer
from evidence_based_scorer import EvidenceBasedScorer
from ..evidence_collector import EvidenceCollector
from ..progress_tracker import get_progress_tracker, ProcessingStage
from ..time_estimator import get_time_estimator

logger = logging.getLogger(__name__)


class PaperAnalysisAgent(BaseAgent):
    """
    Enhanced agent responsible for comprehensive paper analysis using multiple specialized tools.
    """
    
    def __init__(self, tool_registry):
        """Initialize the paper analysis agent."""
        super().__init__(tool_registry)
        self.custom_rubric_weights = None
    
    def set_rubric_weights(self, weights: Dict[str, float]):
        """
        Set custom rubric weights for scoring.
        
        Args:
            weights: Dictionary with keys: methodology, bias, reproducibility, research_gaps
        """
        self.custom_rubric_weights = weights
        logger.info(f"Custom rubric weights set: {weights}")
    
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
        progress_tracker = get_progress_tracker() if self.request_id else None
        
        try:
            # Determine analysis level based on query
            analysis_level = self._determine_analysis_level(query)
            logger.info(f"Starting {analysis_level} analysis for query: {query}")
            logger.info(f"Analysis level determined: {analysis_level}")
            
            if progress_tracker and self.request_id:
                progress_tracker.update_stage(
                    self.request_id,
                    ProcessingStage.AGENT_SELECTION,
                    message="Paper analysis agent selected",
                    progress=10.0
                )
            
            # Step 1: Parse PDF if needed
            text_content = None
            pdf_metadata = None
            pdf_pages = None
            pages_with_coords = None
            evidence_collector = None
            extracted_citations = None
            
            # Check if we have a file path to parse (from upload or query)
            file_path = None
            if classification.extracted_parameters:
                file_path = classification.extracted_parameters.get("file_path")
            
            # Also check if query mentions PDF or if suggested tool is parse_pdf
            should_parse_pdf = (
                classification.suggested_tool == "parse_pdf" or 
                "pdf" in query.lower() or 
                file_path is not None
            )
            
            # Store PDF result for later use (e.g., citations)
            pdf_result = None
            if should_parse_pdf:
                if progress_tracker and self.request_id:
                    progress_tracker.update_stage(
                        self.request_id,
                        ProcessingStage.PDF_PARSING,
                        message="Extracting text and metadata from PDF",
                        progress=15.0
                    )
                
                pdf_result = self._parse_pdf_if_needed(classification.extracted_parameters or {})
                if pdf_result and pdf_result.get("success"):
                    text_content = pdf_result.get("text", "")
                    pdf_metadata = pdf_result.get("metadata", {})
                    # Extract pages for evidence collection
                    if "pages" in pdf_result:
                        pdf_pages = pdf_result["pages"]
                        logger.info(f"Extracted {len(pdf_pages)} pages from PDF for evidence collection")
                    elif text_content:
                        # Fallback: split text into pages if not available
                        pdf_pages = text_content.split("\n\n")[:50]  # Limit to 50 pages
                        logger.info(f"Using fallback page splitting: {len(pdf_pages)} pages")
                    
                    # Extract coordinate data for evidence highlighting
                    if "pages_with_coords" in pdf_result:
                        pages_with_coords = pdf_result["pages_with_coords"]
                        logger.info(f"Extracted coordinate data for {len(pages_with_coords)} pages")
                    
                    # Extract citations if available
                    extracted_citations = pdf_result.get("citations", [])
                    if extracted_citations:
                        logger.info(f"Extracted {len(extracted_citations)} citations from PDF")
                    
                    tools_used.append("parse_pdf")
                    
                    if progress_tracker and self.request_id:
                        progress_tracker.update_stage(
                            self.request_id,
                            ProcessingStage.PDF_PARSING,
                            message=f"PDF parsed successfully ({len(pdf_pages) if pdf_pages else 0} pages)",
                            progress=25.0
                        )
            
            # Initialize evidence collector if we have PDF pages
            if pdf_pages:
                evidence_collector = EvidenceCollector(
                    pdf_pages=pdf_pages,
                    pages_with_coords=pages_with_coords
                )
            
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
            
            if progress_tracker and self.request_id:
                progress_tracker.update_stage(
                    self.request_id,
                    ProcessingStage.LLM_ANALYSIS,
                    message="Running comprehensive analysis with multiple AI tools",
                    progress=30.0
                )
            
            analysis_results = self._run_analysis_pipeline(
                text_content, analysis_level, query, evidence_collector, extracted_citations
            )
            tools_used.extend(analysis_results.get("tools_used", []))
            logger.info(f"Analysis pipeline completed. Tools used: {analysis_results.get('tools_used', [])}")
            logger.info(f"Analysis results keys: {list(analysis_results.keys())}")
            logger.info(f"Total tools used so far: {tools_used}")
            
            if progress_tracker and self.request_id:
                progress_tracker.update_stage(
                    self.request_id,
                    ProcessingStage.EVIDENCE_COLLECTION,
                    message="Collecting evidence and calculating scores",
                    progress=75.0
                )
            
            # Step 3: Integrate results
            logger.info("Integrating analysis results...")
            integrated_result = self._integrate_analysis_results(
                text_content, analysis_results, pdf_metadata, query, evidence_collector
            )
            logger.info(f"Integrated result keys: {list(integrated_result.keys())}")
            logger.info(f"Final tools used: {tools_used}")
            
            if progress_tracker and self.request_id:
                progress_tracker.update_stage(
                    self.request_id,
                    ProcessingStage.COMPILING,
                    message="Finalizing results",
                    progress=90.0
                )
            
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
        file_path = params.get('file_path')
        if file_path and os.path.exists(file_path):
            try:
                logger.info(f"Parsing PDF from file path: {file_path}")
                result = self.execute_tool("parse_pdf", file_path=file_path)
                logger.info(f"PDF parsing result - success: {result.get('success')}, pages: {result.get('num_pages', 0)}")
                return result
            except Exception as e:
                logger.error(f"PDF parsing failed: {str(e)}")
                return None
        else:
            logger.warning(f"PDF file path not found or invalid: {file_path}")
        return None
    
    def _extract_text_content(self, params: Dict[str, Any]) -> Optional[str]:
        """Extract text content from various sources."""
        # Try different parameter names for text content
        text_sources = ['text_content', 'text', 'content', 'paper_text']
        for source in text_sources:
            if source in params and params[source]:
                return params[source]
        return None
    
    def _run_analysis_pipeline(
        self, text_content: str, analysis_level: str, query: str, 
        evidence_collector: Optional[EvidenceCollector] = None,
        extracted_citations: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive analysis pipeline with all tools.
        Uses parallel execution for independent tools to speed up analysis.
        
        Execution strategy:
        1. Run independent tools in parallel (content_summary, bias, methodology, statistical, gap, citation)
        2. Run reproducibility (depends on methodology) after methodology completes
        3. Run quality assessment (depends on all) after all others complete
        """
        results = {
            "tools_used": [],
            "analysis_level": "comprehensive"
        }
        
        try:
            logger.info("Executing comprehensive analysis with parallel tool execution")
            
            # Use asyncio to run independent tools in parallel
            # Handle both sync and async contexts properly
            try:
                # Try to get the current event loop
                loop = asyncio.get_running_loop()
                # If we're in an async context, we need to use a different approach
                # For now, fall back to sequential execution if already in async context
                logger.warning("Already in async context, using sequential execution")
                return self._run_analysis_pipeline_sequential(text_content, analysis_level, query, evidence_collector)
            except RuntimeError:
                # No event loop running, we can create one
                try:
                    # Try to use asyncio.run (Python 3.7+)
                    results = asyncio.run(
                        self._run_analysis_pipeline_async(text_content, analysis_level, query, evidence_collector, extracted_citations)
                    )
                except RuntimeError:
                    # Fallback: create new event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        results = loop.run_until_complete(
                            self._run_analysis_pipeline_async(text_content, analysis_level, query, evidence_collector, extracted_citations)
                        )
                    finally:
                        loop.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Analysis pipeline failed: {str(e)}")
            return {
                "tools_used": results.get("tools_used", []),
                "error": str(e),
                "analysis_level": "comprehensive"
            }
    
    def _run_analysis_pipeline_sequential(
        self, text_content: str, analysis_level: str, query: str, 
        evidence_collector: Optional[EvidenceCollector] = None
    ) -> Dict[str, Any]:
        """
        Sequential fallback version of analysis pipeline.
        Used when async execution is not possible.
        """
        results = {
            "tools_used": [],
            "analysis_level": "comprehensive"
        }
        
        try:
            logger.info("Executing comprehensive analysis sequentially (fallback mode)")
            
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
                severity_threshold="low",
                evidence_collector=evidence_collector
            )
            if bias_result.get("success"):
                results["bias_analysis"] = bias_result
                results["tools_used"].append("bias_detection_tool")
            
            # Methodology analysis
            methodology_result = self.execute_tool(
                "methodology_analyzer_tool",
                text_content=text_content,
                analysis_depth="comprehensive",
                evidence_collector=evidence_collector
            )
            if methodology_result.get("success"):
                results["methodology_analysis"] = methodology_result
                results["tools_used"].append("methodology_analyzer_tool")
            
            # Statistical validation
            statistical_result = self.execute_tool(
                "statistical_validator_tool",
                text_content=text_content,
                validation_level="comprehensive",
                evidence_collector=evidence_collector
            )
            if statistical_result.get("success"):
                results["statistical_analysis"] = statistical_result
                results["tools_used"].append("statistical_validator_tool")
            
            # Reproducibility assessment (pass methodology data if available)
            methodology_data_for_repro = None
            if "methodology_analysis" in results and results["methodology_analysis"].get("success"):
                methodology_data_for_repro = results["methodology_analysis"]
            
            reproducibility_result = self.execute_tool(
                "reproducibility_assessor_tool",
                text_content=text_content,
                reproducibility_level="detailed",
                evidence_collector=evidence_collector,
                methodology_data=methodology_data_for_repro
            )
            if reproducibility_result.get("success"):
                results["reproducibility_analysis"] = reproducibility_result
                results["tools_used"].append("reproducibility_assessor_tool")
            
            # Research gap identification
            gap_result = self.execute_tool(
                "research_gap_identifier_tool",
                text_content=text_content,
                future_focus="comprehensive",
                evidence_collector=evidence_collector
            )
            if gap_result.get("success"):
                results["research_gap_analysis"] = gap_result
                results["tools_used"].append("research_gap_identifier_tool")
            
            # Citation analysis
            citation_result = self.execute_tool(
                "citation_analyzer_tool",
                text_content=text_content,
                analysis_type="bibliometric",
                extracted_citations=extracted_citations
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
            logger.error(f"Sequential analysis pipeline failed: {str(e)}")
            return {
                "tools_used": results.get("tools_used", []),
                "error": str(e),
                "analysis_level": "comprehensive"
            }
    
    async def _run_analysis_pipeline_async(
        self, text_content: str, analysis_level: str, query: str, 
        evidence_collector: Optional[EvidenceCollector] = None,
        extracted_citations: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Async version of analysis pipeline with parallel execution.
        
        Chain of thought:
        1. Identify independent tools that can run in parallel
        2. Execute them concurrently using asyncio.gather
        3. Wait for dependencies (reproducibility needs methodology)
        4. Execute final dependent tool (quality needs all)
        """
        results = {
            "tools_used": [],
            "analysis_level": "comprehensive"
        }
        
        try:
            logger.info("Starting parallel analysis pipeline execution")
            
            # PHASE 1: Execute independent tools in parallel
            # These tools don't depend on each other and can run concurrently
            logger.info("Phase 1: Executing independent tools in parallel...")
            
            async def run_tool_async(tool_name: str, **kwargs):
                """Helper to run a tool asynchronously."""
                try:
                    # Run tool in executor to avoid blocking
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        lambda: self.execute_tool(tool_name, **kwargs)
                    )
                    return tool_name, result
                except Exception as e:
                    logger.error(f"Tool {tool_name} failed: {str(e)}")
                    return tool_name, {"success": False, "error": str(e)}
            
            # Execute independent tools in parallel
            independent_tasks = [
                run_tool_async("content_summarizer_tool", text_content=text_content, summary_type="comprehensive", max_length=800),
                run_tool_async("bias_detection_tool", text_content=text_content, severity_threshold="low", evidence_collector=evidence_collector),
                run_tool_async("methodology_analyzer_tool", text_content=text_content, analysis_depth="comprehensive", evidence_collector=evidence_collector),
                run_tool_async("statistical_validator_tool", text_content=text_content, validation_level="comprehensive", evidence_collector=evidence_collector),
                run_tool_async("research_gap_identifier_tool", text_content=text_content, future_focus="comprehensive", evidence_collector=evidence_collector),
                run_tool_async("citation_analyzer_tool", text_content=text_content, analysis_type="bibliometric", extracted_citations=extracted_citations),
            ]
            
            # Wait for all independent tools to complete
            independent_results = await asyncio.gather(*independent_tasks, return_exceptions=True)
            
            # Process independent tool results
            for tool_name, tool_result in independent_results:
                if isinstance(tool_result, Exception):
                    logger.error(f"Tool {tool_name} raised exception: {str(tool_result)}")
                    continue
                
                if tool_result.get("success"):
                    if tool_name == "content_summarizer_tool":
                        results["content_summary"] = tool_result
                    elif tool_name == "bias_detection_tool":
                        results["bias_analysis"] = tool_result
                    elif tool_name == "methodology_analyzer_tool":
                        results["methodology_analysis"] = tool_result
                    elif tool_name == "statistical_validator_tool":
                        results["statistical_analysis"] = tool_result
                    elif tool_name == "research_gap_identifier_tool":
                        results["research_gap_analysis"] = tool_result
                    elif tool_name == "citation_analyzer_tool":
                        results["citation_analysis"] = tool_result
                    
                    results["tools_used"].append(tool_name)
            
            logger.info(f"Phase 1 complete. {len(results['tools_used'])} tools executed in parallel")
            
            # PHASE 2: Execute reproducibility assessment (depends on methodology)
            logger.info("Phase 2: Executing reproducibility assessment (depends on methodology)...")
            methodology_data_for_repro = None
            if "methodology_analysis" in results and results["methodology_analysis"].get("success"):
                methodology_data_for_repro = results["methodology_analysis"]
            
            reproducibility_result = await run_tool_async(
                "reproducibility_assessor_tool",
                text_content=text_content,
                reproducibility_level="detailed",
                evidence_collector=evidence_collector,
                methodology_data=methodology_data_for_repro
            )
            _, repro_result = reproducibility_result
            if repro_result.get("success"):
                results["reproducibility_analysis"] = repro_result
                results["tools_used"].append("reproducibility_assessor_tool")
            
            logger.info("Phase 2 complete")
            
            # PHASE 3: Execute quality assessment (depends on all other results)
            logger.info("Phase 3: Executing quality assessment (depends on all results)...")
            quality_result = await run_tool_async("quality_assessor_tool", analysis_results=results)
            _, quality_res = quality_result
            if quality_res.get("success"):
                results["quality_assessment"] = quality_res
                results["tools_used"].append("quality_assessor_tool")
            
            logger.info(f"Analysis pipeline complete. Total tools used: {len(results['tools_used'])}")
            return results
            
        except Exception as e:
            logger.error(f"Async analysis pipeline failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "tools_used": results.get("tools_used", []),
                "error": str(e),
                "analysis_level": "comprehensive"
            }
    
    def _integrate_analysis_results(
        self, text_content: str, analysis_results: Dict[str, Any], 
        pdf_metadata: Optional[Dict[str, Any]], query: str,
        evidence_collector: Optional[EvidenceCollector] = None
    ) -> Dict[str, Any]:
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
                
                # CRITICAL FIX: If summary is a JSON string (possibly wrapped in markdown), parse it and extract all fields
                summary_field = summary_data.get("summary", "")
                if isinstance(summary_field, str):
                    # Strip markdown code fences if present (```json ... ```)
                    cleaned_summary = summary_field.strip()
                    if cleaned_summary.startswith("```"):
                        # Find the first newline after ```
                        first_newline = cleaned_summary.find("\n")
                        if first_newline > 0:
                            cleaned_summary = cleaned_summary[first_newline:].strip()
                        else:
                            # No newline, just remove ```
                            cleaned_summary = cleaned_summary.replace("```json", "").replace("```", "").strip()
                        # Remove closing fence (```)
                        if cleaned_summary.endswith("```"):
                            cleaned_summary = cleaned_summary[:-3].strip()
                    
                    # Try to parse as JSON
                    if cleaned_summary.startswith("{") or cleaned_summary.startswith("["):
                        try:
                            import json
                            parsed_summary = json.loads(cleaned_summary)
                            # If parsing successful, merge all fields from parsed JSON
                            if isinstance(parsed_summary, dict):
                                # Extract all fields from parsed JSON
                                integrated_result["summary"] = parsed_summary.get("summary", "")
                                integrated_result["key_points"] = parsed_summary.get("key_points", summary_data.get("key_points", []))
                                integrated_result["methodology_highlights"] = parsed_summary.get("methodology_highlights", "")
                                integrated_result["main_results"] = parsed_summary.get("main_results", "")
                                integrated_result["implications"] = parsed_summary.get("implications", "")
                                integrated_result["summary_strengths"] = parsed_summary.get("strengths", [])
                                if "limitations" not in integrated_result or not integrated_result.get("limitations"):
                                    integrated_result["limitations"] = parsed_summary.get("limitations", [])
                                integrated_result["executive_summary"] = parsed_summary.get("executive_summary", summary_data.get("executive_summary", ""))
                            else:
                                # Parsed but not a dict, use original structure
                                integrated_result["executive_summary"] = summary_data.get("executive_summary", "")
                                integrated_result["key_points"] = summary_data.get("key_points", [])
                                integrated_result["summary"] = cleaned_summary
                        except (json.JSONDecodeError, ValueError):
                            # JSON parsing failed, use cleaned string (without markdown fences)
                            integrated_result["executive_summary"] = summary_data.get("executive_summary", "")
                            integrated_result["key_points"] = summary_data.get("key_points", [])
                            integrated_result["summary"] = cleaned_summary
                    else:
                        # Not JSON, use as-is
                        integrated_result["executive_summary"] = summary_data.get("executive_summary", "")
                        integrated_result["key_points"] = summary_data.get("key_points", [])
                        integrated_result["summary"] = cleaned_summary
                else:
                    # Normal case: summary is already a string or structured data
                    integrated_result["executive_summary"] = summary_data.get("executive_summary", "")
                    integrated_result["key_points"] = summary_data.get("key_points", [])
                    integrated_result["summary"] = summary_field
                    # Add comprehensive summary fields if available
                    if "methodology_highlights" in summary_data:
                        integrated_result["methodology_highlights"] = summary_data.get("methodology_highlights", "")
                    if "main_results" in summary_data:
                        integrated_result["main_results"] = summary_data.get("main_results", "")
                    if "implications" in summary_data:
                        integrated_result["implications"] = summary_data.get("implications", "")
                    if "strengths" in summary_data:
                        integrated_result["summary_strengths"] = summary_data.get("strengths", [])
                    if "limitations" in summary_data:
                        # Note: limitations might already be set from bias analysis, so we merge or use summary limitations
                        if "limitations" not in integrated_result or not integrated_result["limitations"]:
                            integrated_result["limitations"] = summary_data.get("limitations", [])
            
            # Add bias analysis if available
            if "bias_analysis" in analysis_results:
                bias_data = analysis_results["bias_analysis"]
                integrated_result["detected_biases"] = bias_data.get("detected_biases", [])
                integrated_result["bias_summary"] = bias_data.get("bias_summary", "")
                integrated_result["limitations"] = bias_data.get("limitations", [])
                integrated_result["confounding_factors"] = bias_data.get("confounding_factors", [])
                
                # Calculate bias score (inverted - fewer biases = higher score)
                detected_biases = bias_data.get("detected_biases", [])
                bias_score = 100.0  # Start with perfect score
                for bias in detected_biases:
                    severity = bias.get("severity", "medium")
                    if severity == "high":
                        bias_score -= 20.0
                    elif severity == "medium":
                        bias_score -= 10.0
                    elif severity == "low":
                        bias_score -= 5.0
                bias_score = max(0.0, bias_score)
                
                if not integrated_result.get("component_scores"):
                    integrated_result["component_scores"] = {}
                integrated_result["component_scores"]["bias"] = bias_score
            
            # Add methodology analysis if available
            if "methodology_analysis" in analysis_results:
                methodology_data = analysis_results["methodology_analysis"]
                logger.info(f"🔍 METHODOLOGY DATA IN INTEGRATION:")
                logger.info(f"   - methodology_data keys: {list(methodology_data.keys())}")
                logger.info(f"   - overall_quality_score: {methodology_data.get('overall_quality_score')}")
                logger.info(f"   - quantitative_scores: {methodology_data.get('quantitative_scores', {})}")
                logger.info(f"   - cached: {methodology_data.get('cached', False)}")
                logger.info(f"   - content_hash: {methodology_data.get('content_hash', 'N/A')}")

                # NEW: Extract detected methodologies
                detected_methodologies = methodology_data.get("detected_methodologies", {})
                methodologies_list = detected_methodologies.get("methodologies", [])
                logger.info(f"   - detected_methodologies: {len(methodologies_list)} methodologies")
                for i, meth in enumerate(methodologies_list[:3]):  # Log first 3
                    logger.info(f"      {i+1}. {meth.get('type', 'Unknown')} - {meth.get('category', 'unknown')} - Quality: {meth.get('quality_assessment', {}).get('quality_rating', 'N/A')}")

                integrated_result["study_design"] = methodology_data.get("study_design", "")
                integrated_result["sample_characteristics"] = methodology_data.get("sample_characteristics", {})
                integrated_result["methodological_strengths"] = methodology_data.get("methodological_strengths", [])
                integrated_result["methodological_weaknesses"] = methodology_data.get("methodological_weaknesses", [])
                integrated_result["methodology_quality_rating"] = methodology_data.get("quality_rating", "")

                # NEW: Add detected methodologies to result
                integrated_result["detected_methodologies"] = detected_methodologies
                integrated_result["primary_methodology"] = detected_methodologies.get("primary_methodology", "Unknown")
                integrated_result["methodology_combination_assessment"] = detected_methodologies.get("methodology_combination_assessment", "")
                integrated_result["overall_methodological_approach"] = detected_methodologies.get("overall_methodological_approach", "")

                # Add cache metadata for transparency
                integrated_result["scoring_metadata"] = {
                    "cached": methodology_data.get("cached", False),
                    "cache_timestamp": methodology_data.get("cache_timestamp"),
                    "content_hash": methodology_data.get("content_hash")
                }

                # Extract component scores from methodology analysis
                # Note: We don't set overall_quality_score - frontend will calculate it
                if methodology_data.get("quantitative_scores", {}).get("scores"):
                    methodology_score = methodology_data["quantitative_scores"]["scores"].get("overall_score", 0.0)
                    if not integrated_result.get("component_scores"):
                        integrated_result["component_scores"] = {}
                    integrated_result["component_scores"]["methodology"] = methodology_score
                    logger.info(f"✅ SET methodology component score: {methodology_score}")
                else:
                    logger.warning(f"⚠️ NO methodology scores found in methodology_data")
            
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
                reproducibility_score = reproducibility_data.get("reproducibility_score", 0.0)
                # Convert from 0-1 scale to 0-100 if needed
                if reproducibility_score <= 1.0:
                    reproducibility_score = reproducibility_score * 100.0
                
                if not integrated_result.get("component_scores"):
                    integrated_result["component_scores"] = {}
                integrated_result["component_scores"]["reproducibility"] = reproducibility_score
                
                integrated_result["reproducibility_score"] = reproducibility_score
                integrated_result["reproducibility_barriers"] = reproducibility_data.get("reproducibility_barriers", [])
                integrated_result["data_availability"] = reproducibility_data.get("data_availability", "")
                integrated_result["code_availability"] = reproducibility_data.get("code_availability", "")
                # U-FR6: Include reproducibility summary with indicators
                integrated_result["reproducibility_summary"] = reproducibility_data.get("reproducibility_summary", {})
            
            # Add research gap analysis if available
            if "research_gap_analysis" in analysis_results:
                gap_data = analysis_results["research_gap_analysis"]
                integrated_result["research_gaps"] = gap_data.get("research_gaps", [])
                integrated_result["future_directions"] = gap_data.get("future_directions", [])
                integrated_result["unaddressed_questions"] = gap_data.get("unaddressed_questions", [])
                integrated_result["methodological_gaps"] = gap_data.get("methodological_gaps", [])
                integrated_result["theoretical_gaps"] = gap_data.get("theoretical_gaps", [])
                
                # Calculate research gaps score (more gaps = higher score)
                research_gaps = gap_data.get("research_gaps", [])
                gaps_count = len(research_gaps)
                if gaps_count == 0:
                    research_gaps_score = 0.0
                elif gaps_count <= 2:
                    research_gaps_score = 40.0
                elif gaps_count <= 5:
                    research_gaps_score = 70.0
                elif gaps_count <= 10:
                    research_gaps_score = 90.0
                else:
                    research_gaps_score = 100.0
                
                if not integrated_result.get("component_scores"):
                    integrated_result["component_scores"] = {}
                integrated_result["component_scores"]["research_gaps"] = research_gaps_score
            
            # Add citation analysis if available
            if "citation_analysis" in analysis_results:
                citation_data = analysis_results["citation_analysis"]
                integrated_result["total_citations"] = citation_data.get("total_citations", 0)
                integrated_result["citation_quality"] = citation_data.get("citation_quality", "")
                integrated_result["reference_analysis"] = citation_data.get("reference_analysis", {})
                integrated_result["citation_gaps"] = citation_data.get("citation_gaps", [])
                integrated_result["bibliometric_indicators"] = citation_data.get("bibliometric_indicators", {})
                # Include extracted citations for frontend display
                integrated_result["extracted_citations"] = citation_data.get("extracted_citations", [])
                integrated_result["citation_analysis"] = citation_data  # Keep full citation_analysis object
            
            # Add quality assessment if available - extract component scores
            if "quality_assessment" in analysis_results:
                quality_data = analysis_results["quality_assessment"]

                # Extract component scores from quality assessor
                if quality_data.get("component_scores"):
                    if not integrated_result.get("component_scores"):
                        integrated_result["component_scores"] = {}
                    # Merge component scores, preferring methodology from methodology analyzer if available
                    for key, value in quality_data["component_scores"].items():
                        if key not in integrated_result["component_scores"]:
                            integrated_result["component_scores"][key] = value
                    logger.info(f"✅ Merged component scores from quality assessor: {quality_data.get('component_scores')}")

                integrated_result["quality_breakdown"] = quality_data.get("quality_breakdown", {})
                integrated_result["quality_strengths"] = quality_data.get("strengths", [])
                integrated_result["quality_weaknesses"] = quality_data.get("weaknesses", [])
                integrated_result["quality_recommendations"] = quality_data.get("recommendations", [])
                integrated_result["quality_confidence_level"] = quality_data.get("confidence_level", "")
                integrated_result["scoring_criteria_used"] = quality_data.get("scoring_criteria_used", [])

            # PHASE 2: Ensure component scores are complete
            logger.info("🎯 Ensuring component scores are complete")
            
            # Get base methodology score from component_scores if available
            base_methodology_score = integrated_result.get("component_scores", {}).get("methodology", 0.0)
            
            # Get evidence items for scoring
            evidence_list = []
            if evidence_collector:
                evidence_list = evidence_collector.get_all_evidence()
                logger.info(f"📊 Using {len(evidence_list)} evidence items for scoring")

            if len(evidence_list) > 0:
                try:
                    # Use evidence-based scorer to get component scores
                    evidence_scorer = EvidenceBasedScorer()
                    evidence_result = evidence_scorer.calculate_score_from_evidence(
                        evidence_items=evidence_list,
                        base_methodology_score=base_methodology_score if base_methodology_score > 0 else None
                    )

                    # Update component scores (don't set overall_quality_score - frontend will calculate)
                    if not integrated_result.get("component_scores"):
                        integrated_result["component_scores"] = {}
                    integrated_result["component_scores"].update(evidence_result["component_scores"])
                    integrated_result["weighted_contributions"] = evidence_result["weighted_contributions"]
                    integrated_result["scoring_weights"] = evidence_result["weights"]
                    integrated_result["evidence_contributions"] = evidence_result.get("evidence_contributions", [])
                    integrated_result["evidence_count"] = evidence_result.get("evidence_count", 0)

                    logger.info(f"✅ Evidence-based component scores applied:")
                    logger.info(f"   Methodology: {evidence_result['component_scores']['methodology']}")
                    logger.info(f"   Bias: {evidence_result['component_scores']['bias']}")
                    logger.info(f"   Reproducibility: {evidence_result['component_scores']['reproducibility']}")
                    logger.info(f"   Evidence items: {len(evidence_list)}")

                except Exception as e:
                    logger.error(f"Evidence-based scoring failed: {str(e)}")
                    # Fallback to enhanced scorer if evidence-based fails
                    if base_methodology_score > 0:
                        try:
                            enhanced_scorer = EnhancedScorer()
                            enhanced_result = enhanced_scorer.calculate_final_score(
                                base_methodology_score=base_methodology_score,
                                text_content=text_content,
                                reproducibility_data=analysis_results.get("reproducibility_analysis"),
                                bias_data=analysis_results.get("bias_analysis"),
                                research_gaps_data=analysis_results.get("research_gap_analysis"),
                                custom_weights=self.custom_rubric_weights
                            )
                            if not integrated_result.get("component_scores"):
                                integrated_result["component_scores"] = {}
                            integrated_result["component_scores"].update(enhanced_result["component_scores"])
                            integrated_result["weighted_contributions"] = enhanced_result["weighted_contributions"]
                        except Exception as e2:
                            logger.error(f"Fallback enhanced scoring also failed: {str(e2)}")
                            logger.info("Continuing with available component scores")
            elif base_methodology_score > 0:
                # No evidence collected, use enhanced scorer as fallback to get component scores
                try:
                    enhanced_scorer = EnhancedScorer()
                    enhanced_result = enhanced_scorer.calculate_final_score(
                        base_methodology_score=base_methodology_score,
                        text_content=text_content,
                        reproducibility_data=analysis_results.get("reproducibility_analysis"),
                        bias_data=analysis_results.get("bias_analysis"),
                        research_gaps_data=analysis_results.get("research_gap_analysis"),
                        custom_weights=self.custom_rubric_weights
                    )
                    if not integrated_result.get("component_scores"):
                        integrated_result["component_scores"] = {}
                    integrated_result["component_scores"].update(enhanced_result["component_scores"])
                    integrated_result["weighted_contributions"] = enhanced_result["weighted_contributions"]
                    logger.info("⚠️ No evidence collected, using enhanced scorer fallback for component scores")
                except Exception as e:
                    logger.error(f"Enhanced scoring failed: {str(e)}")
                    logger.info("Continuing with available component scores")
            
            # Ensure component_scores has all required fields with defaults if missing
            if not integrated_result.get("component_scores"):
                integrated_result["component_scores"] = {}
            component_scores = integrated_result["component_scores"]
            if "methodology" not in component_scores:
                component_scores["methodology"] = 0.0
            if "bias" not in component_scores:
                component_scores["bias"] = 0.0
            if "reproducibility" not in component_scores:
                component_scores["reproducibility"] = 0.0
            if "research_gaps" not in component_scores:
                component_scores["research_gaps"] = 0.0

            # Generate overall assessment
            integrated_result["overall_assessment"] = self._generate_overall_assessment(analysis_results)
            
            # Add evidence traces if available
            if evidence_collector:
                evidence_list = evidence_collector.get_all_evidence()
                integrated_result["evidence_traces"] = evidence_list
                integrated_result["evidence_summary"] = evidence_collector.get_evidence_summary()
                logger.info(f"✅ Added {len(evidence_collector.evidence_items)} evidence items to result")
                logger.info(f"   Evidence categories: {set(e.get('category') for e in evidence_list)}")
                
                # If no evidence was collected, add some fallback evidence from analysis results
                if len(evidence_list) == 0:
                    logger.warning("⚠️ No evidence collected! Adding fallback evidence from analysis results...")
                    self._add_fallback_evidence(evidence_collector, analysis_results, text_content)
                    evidence_list = evidence_collector.get_all_evidence()
                    integrated_result["evidence_traces"] = evidence_list
                    integrated_result["evidence_summary"] = evidence_collector.get_evidence_summary()
                    logger.info(f"✅ Added {len(evidence_list)} fallback evidence items")
            else:
                logger.warning("⚠️ No evidence collector initialized - evidence traces will not be available")
            
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
    
    def _add_fallback_evidence(self, evidence_collector: EvidenceCollector, analysis_results: Dict[str, Any], text_content: str):
        """Add fallback evidence when tools don't collect any evidence."""
        try:
            # Add evidence from bias analysis
            if "bias_analysis" in analysis_results:
                bias_data = analysis_results["bias_analysis"]
                bias_summary = bias_data.get("bias_summary", "")
                if bias_summary and len(bias_summary) > 20:
                    evidence_collector.add_evidence(
                        category="bias",
                        text_snippet=bias_summary[:200],
                        rationale="Bias analysis summary",
                        confidence=0.6,
                        severity="medium"
                    )
            
            # Add evidence from methodology analysis
            if "methodology_analysis" in analysis_results:
                methodology_data = analysis_results["methodology_analysis"]
                quality_rating = methodology_data.get("quality_rating", "")
                if quality_rating and len(quality_rating) > 20:
                    evidence_collector.add_evidence(
                        category="methodology",
                        text_snippet=quality_rating[:200],
                        rationale="Methodology quality assessment",
                        confidence=0.7
                    )
            
            # Add evidence from reproducibility analysis
            if "reproducibility_analysis" in analysis_results:
                repro_data = analysis_results["reproducibility_analysis"]
                repro_score = repro_data.get("reproducibility_score", 0.0)
                if repro_score > 0:
                    evidence_collector.add_evidence(
                        category="reproducibility",
                        text_snippet=f"Reproducibility score: {repro_score:.2f}",
                        rationale=f"Study reproducibility assessment with score {repro_score:.2f}",
                        confidence=0.7,
                        score_impact=repro_score * 10.0
                    )
        except Exception as e:
            logger.error(f"Failed to add fallback evidence: {str(e)}")
    
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
