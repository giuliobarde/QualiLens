"""
Time estimation utility using chain-of-thought reasoning.

This module provides intelligent time estimation for analysis operations
by considering multiple factors and using a chain-of-thought approach.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TimeEstimator:
    """
    Estimates processing time using chain-of-thought reasoning.
    
    Chain of thought:
    1. Base time for each operation type
    2. Scale by file size (for PDF parsing)
    3. Scale by number of tools (for LLM analysis)
    4. Add network/API latency overhead
    5. Add safety margin (better to overestimate)
    """
    
    # Base times in seconds (conservative estimates)
    BASE_CLASSIFICATION_TIME = 0.5
    BASE_AGENT_SELECTION_TIME = 0.3
    BASE_PDF_PARSING_TIME = 2.0  # Base time for small PDFs
    BASE_PDF_PARSING_PER_MB = 1.0  # Additional time per MB
    BASE_LLM_CALL_TIME = 8.0  # Average LLM API call time
    BASE_TOOL_EXECUTION_TIME = 5.0  # Base time per tool
    BASE_EVIDENCE_COLLECTION_TIME = 2.0
    BASE_SCORING_TIME = 1.5
    BASE_COMPILATION_TIME = 1.0
    
    # Network/API overhead (percentage)
    NETWORK_OVERHEAD_FACTOR = 1.2  # 20% overhead for network latency
    SAFETY_MARGIN_FACTOR = 1.3  # 30% safety margin (better to overestimate)
    
    # LLM call factors
    LLM_CALLS_PER_TOOL = 1.5  # Average number of LLM calls per tool
    LLM_PARALLEL_FACTOR = 0.6  # Parallel execution reduces time by 40%
    
    def estimate_total_time(
        self,
        file_size_mb: float = 0.0,
        has_pdf: bool = False,
        num_tools: int = 8,
        analysis_level: str = "comprehensive",
        parallel_execution: bool = True
    ) -> float:
        """
        Estimate total processing time using chain-of-thought reasoning.
        
        Args:
            file_size_mb: File size in MB
            has_pdf: Whether PDF parsing is needed
            num_tools: Number of analysis tools to run
            analysis_level: Analysis level (basic, detailed, comprehensive)
            parallel_execution: Whether tools run in parallel
            
        Returns:
            float: Estimated total time in seconds
        """
        logger.info(f"Estimating time: file_size={file_size_mb}MB, has_pdf={has_pdf}, "
                   f"num_tools={num_tools}, level={analysis_level}, parallel={parallel_execution}")
        
        # Step 1: Classification and agent selection
        classification_time = self.BASE_CLASSIFICATION_TIME
        agent_selection_time = self.BASE_AGENT_SELECTION_TIME
        logger.debug(f"  Classification: {classification_time}s")
        logger.debug(f"  Agent selection: {agent_selection_time}s")
        
        # Step 2: PDF parsing (if needed)
        pdf_parsing_time = 0.0
        if has_pdf:
            # Base time + time per MB, with scaling for large files
            pdf_parsing_time = (
                self.BASE_PDF_PARSING_TIME +
                (file_size_mb * self.BASE_PDF_PARSING_PER_MB)
            )
            # Large files take proportionally more time
            if file_size_mb > 5:
                pdf_parsing_time *= 1.2
            logger.debug(f"  PDF parsing: {pdf_parsing_time:.1f}s (file size: {file_size_mb}MB)")
        
        # Step 3: LLM analysis time
        # Each tool makes ~1.5 LLM calls on average
        # If parallel: tools run concurrently, so time is max(parallel_tools) + sequential_tools
        # If sequential: time is sum of all tools
        
        if parallel_execution:
            # Phase 1: Independent tools run in parallel (6 tools typically)
            # Time = max time of parallel tools
            parallel_tools = min(6, num_tools)  # Usually 6 tools run in parallel
            parallel_llm_time = (
                self.BASE_LLM_CALL_TIME * self.LLM_CALLS_PER_TOOL * self.LLM_PARALLEL_FACTOR
            )
            
            # Phase 2: Dependent tools (reproducibility, quality) run sequentially
            sequential_tools = max(0, num_tools - parallel_tools)
            sequential_llm_time = (
                sequential_tools * self.BASE_LLM_CALL_TIME * self.LLM_CALLS_PER_TOOL
            )
            
            llm_analysis_time = parallel_llm_time + sequential_llm_time
            logger.debug(f"  LLM analysis (parallel): {llm_analysis_time:.1f}s "
                        f"(parallel: {parallel_llm_time:.1f}s, sequential: {sequential_llm_time:.1f}s)")
        else:
            # Sequential execution: sum of all tool times
            llm_analysis_time = (
                num_tools * self.BASE_LLM_CALL_TIME * self.LLM_CALLS_PER_TOOL
            )
            logger.debug(f"  LLM analysis (sequential): {llm_analysis_time:.1f}s")
        
        # Step 4: Tool execution overhead (non-LLM operations)
        tool_overhead = num_tools * self.BASE_TOOL_EXECUTION_TIME * 0.3  # 30% of base time
        if parallel_execution:
            tool_overhead *= self.LLM_PARALLEL_FACTOR
        logger.debug(f"  Tool overhead: {tool_overhead:.1f}s")
        
        # Step 5: Evidence collection
        evidence_time = self.BASE_EVIDENCE_COLLECTION_TIME
        if has_pdf and file_size_mb > 2:
            evidence_time += file_size_mb * 0.5  # More pages = more evidence processing
        logger.debug(f"  Evidence collection: {evidence_time:.1f}s")
        
        # Step 6: Scoring
        scoring_time = self.BASE_SCORING_TIME
        if analysis_level == "comprehensive":
            scoring_time *= 1.5  # More complex scoring
        logger.debug(f"  Scoring: {scoring_time:.1f}s")
        
        # Step 7: Compilation
        compilation_time = self.BASE_COMPILATION_TIME
        logger.debug(f"  Compilation: {compilation_time:.1f}s")
        
        # Step 8: Sum all components
        base_total = (
            classification_time +
            agent_selection_time +
            pdf_parsing_time +
            llm_analysis_time +
            tool_overhead +
            evidence_time +
            scoring_time +
            compilation_time
        )
        logger.debug(f"  Base total: {base_total:.1f}s")
        
        # Step 9: Apply network overhead
        with_network = base_total * self.NETWORK_OVERHEAD_FACTOR
        logger.debug(f"  With network overhead: {with_network:.1f}s")
        
        # Step 10: Apply safety margin (better to overestimate)
        final_estimate = with_network * self.SAFETY_MARGIN_FACTOR
        logger.debug(f"  Final estimate (with safety margin): {final_estimate:.1f}s")
        
        logger.info(f"Time estimation complete: {final_estimate:.1f}s")
        return final_estimate
    
    def estimate_stage_time(
        self,
        stage: str,
        file_size_mb: float = 0.0,
        num_tools: int = 0,
        tools_remaining: int = 0
    ) -> float:
        """
        Estimate time for a specific stage.
        
        Args:
            stage: Stage name
            file_size_mb: File size in MB
            num_tools: Total number of tools
            tools_remaining: Number of tools remaining
            
        Returns:
            float: Estimated time in seconds
        """
        stage_times = {
            "classification": self.BASE_CLASSIFICATION_TIME,
            "agent_selection": self.BASE_AGENT_SELECTION_TIME,
            "pdf_parsing": (
                self.BASE_PDF_PARSING_TIME +
                (file_size_mb * self.BASE_PDF_PARSING_PER_MB)
            ),
            "llm_analysis": (
                tools_remaining * self.BASE_LLM_CALL_TIME * self.LLM_CALLS_PER_TOOL
            ),
            "tool_execution": (
                tools_remaining * self.BASE_TOOL_EXECUTION_TIME * 0.3
            ),
            "evidence_collection": self.BASE_EVIDENCE_COLLECTION_TIME,
            "scoring": self.BASE_SCORING_TIME,
            "compilation": self.BASE_COMPILATION_TIME
        }
        
        base_time = stage_times.get(stage, 1.0)
        return base_time * self.NETWORK_OVERHEAD_FACTOR * self.SAFETY_MARGIN_FACTOR


# Global instance
_time_estimator = TimeEstimator()


def get_time_estimator() -> TimeEstimator:
    """Get the global time estimator instance."""
    return _time_estimator

