"""
Citation Analyzer Tool for QualiLens.

This tool analyzes references, citations, and bibliometric information.
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


class CitationAnalyzerTool(BaseTool):
    """
    Citation Analyzer tool for analyzing references and citations.
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
            name="citation_analyzer_tool",
            description="Analyze references, citations, and bibliometric information",
            parameters={
                "required": ["text_content"],
                "optional": ["analysis_type", "citation_focus", "extracted_citations"],
                "properties": {
                    "text_content": {
                        "type": "string",
                        "description": "The text content to analyze for citations"
                    },
                    "analysis_type": {
                        "type": "string",
                        "description": "Type of citation analysis: 'basic', 'detailed', 'bibliometric'",
                        "default": "detailed"
                    },
                    "citation_focus": {
                        "type": "array",
                        "description": "Specific aspects of citations to focus on",
                        "default": []
                    },
                    "extracted_citations": {
                        "type": "array",
                        "description": "Pre-extracted citations from PDF parsing (optional)",
                        "default": []
                    }
                }
            },
            examples=[
                "Analyze the references and citations in this paper",
                "Evaluate citation quality and relevance",
                "Assess bibliometric indicators"
            ],
            category="citation_analysis"
        )
    
    def execute(self, text_content: str, analysis_type: str = "detailed",
                citation_focus: Optional[List[str]] = None,
                extracted_citations: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Analyze citations and references.
        
        Args:
            text_content: The text content to analyze
            analysis_type: Type of citation analysis
            citation_focus: Specific aspects to focus on
            extracted_citations: Pre-extracted citations from PDF parsing (optional)
            
        Returns:
            Dict containing citation analysis results
        """
        try:
            logger.info("Analyzing citations with bibliometric type")
            
            # Use extracted citations if available, otherwise analyze from text
            if extracted_citations and len(extracted_citations) > 0:
                logger.info(f"Using {len(extracted_citations)} pre-extracted citations")
                citation_result = self._analyze_bibliometric_citations(
                    text_content, citation_focus, extracted_citations
                )
                # Use actual count from extracted citations if LLM didn't provide a better estimate
                total_citations = citation_result.get("total_citations", len(extracted_citations))
                if total_citations < len(extracted_citations):
                    total_citations = len(extracted_citations)
            else:
                logger.info("No pre-extracted citations found, analyzing from text content")
                citation_result = self._analyze_bibliometric_citations(
                    text_content, citation_focus, None
                )
                total_citations = citation_result.get("total_citations", 0)
            
            return {
                "success": True,
                "total_citations": total_citations,
                "citation_quality": citation_result.get("citation_quality", ""),
                "reference_analysis": citation_result.get("reference_analysis", {}),
                "bibliometric_indicators": citation_result.get("bibliometric_indicators", {}),
                "citation_gaps": citation_result.get("citation_gaps", []),
                "recommendations": citation_result.get("recommendations", []),
                "extracted_citations_count": len(extracted_citations) if extracted_citations else 0,
                "extracted_citations": extracted_citations if extracted_citations else [],
                "analysis_type": "bibliometric",
                "citation_focus": citation_focus or [],
                "tool_used": "citation_analyzer_tool"
            }
            
        except Exception as e:
            logger.error(f"Citation analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_used": "citation_analyzer_tool"
            }
    
    def _analyze_bibliometric_citations(self, text_content: str, citation_focus: Optional[List[str]], 
                                        extracted_citations: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Analyze bibliometric citation elements."""
        try:
            # Build citations context if extracted citations are available
            citations_context = ""
            if extracted_citations and len(extracted_citations) > 0:
                citations_summary = []
                for i, cit in enumerate(extracted_citations[:50], 1):  # Limit to first 50 for prompt
                    cit_info = f"Citation {i}:"
                    if cit.get("authors"):
                        cit_info += f" Authors: {', '.join(cit['authors'][:3])}"
                    if cit.get("title"):
                        cit_info += f" Title: {cit['title'][:100]}"
                    if cit.get("journal"):
                        cit_info += f" Journal: {cit['journal']}"
                    if cit.get("year"):
                        cit_info += f" Year: {cit['year']}"
                    if cit.get("doi"):
                        cit_info += f" DOI: {cit['doi']}"
                    citations_summary.append(cit_info)
                
                citations_context = f"""
EXTRACTED CITATIONS FROM PDF ({len(extracted_citations)} total):
{chr(10).join(citations_summary)}
"""
            
            prompt = f"""
You are an expert bibliometrician. Provide a comprehensive bibliometric analysis of the citations and references in this research paper.

PAPER CONTENT:
{text_content[:6000]}

{citations_context}

{f"SPECIFIC ASPECTS TO FOCUS ON: {', '.join(citation_focus)}" if citation_focus else ""}

Provide bibliometric citation analysis in JSON format:
{{
  "total_citations": 50,  // Estimated number of citations
  "citation_quality": {{
    "relevance": "How relevant are the citations?",
    "authority": "How authoritative are the sources?",
    "currency": "How current are the sources?",
    "coverage": "How comprehensive is the coverage?",
    "balance": "How balanced is the citation approach?"
  }},
  "reference_analysis": {{
    "recent_sources": {{
      "last_5_years": "Number of sources from last 5 years",
      "last_10_years": "Number of sources from last 10 years",
      "older_sources": "Number of older sources",
      "trend_analysis": "Analysis of temporal trends"
    }},
    "source_types": {{
      "journal_articles": "Number of journal articles",
      "books": "Number of books",
      "conference_papers": "Number of conference papers",
      "reports": "Number of reports",
      "other": "Other source types"
    }},
    "geographic_diversity": {{
      "countries": "Geographic diversity of sources",
      "regions": "Regional distribution",
      "international_coverage": "International coverage assessment"
    }},
    "language_diversity": "Language diversity of sources",
    "author_diversity": "Author diversity considerations"
  }},
  "bibliometric_indicators": {{
    "citation_count": "Estimated citation count",
    "source_diversity": "Diversity of sources",
    "impact_factors": "Assessment of journal impact factors",
    "h_index_considerations": "H-index considerations",
    "citation_networks": "Citation network analysis",
    "co_citation_analysis": "Co-citation analysis"
  }},
  "citation_patterns": {{
    "self_citations": "Self-citation analysis",
    "cross_disciplinary": "Cross-disciplinary citations",
    "methodological_citations": "Methodological citations",
    "theoretical_citations": "Theoretical citations"
  }},
  "citation_gaps": [
    {{
      "gap": "Description of citation gap",
      "significance": "Why this gap is important",
      "suggested_sources": "Suggested sources to address gap",
      "impact": "Impact of addressing this gap"
    }}
  ],
  "recommendations": [
    "Bibliometric recommendation 1",
    "Bibliometric recommendation 2"
  ],
  "overall_assessment": "Overall bibliometric assessment"
}}

Provide the most comprehensive bibliometric analysis possible.
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-4o-mini",
                max_tokens=2000,
                temperature=0.0  # Deterministic for consistency
            )
            
            if llm_response:
                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    return {"error": "Could not parse bibliometric citation analysis"}
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Bibliometric citation analysis failed: {str(e)}")
            return {"error": str(e)}
