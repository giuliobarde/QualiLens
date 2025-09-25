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
                "optional": ["analysis_type", "citation_focus"],
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
                citation_focus: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze citations and references.
        
        Args:
            text_content: The text content to analyze
            analysis_type: Type of citation analysis
            citation_focus: Specific aspects to focus on
            
        Returns:
            Dict containing citation analysis results
        """
        try:
            logger.info(f"Analyzing citations with type: {analysis_type}")
            
            # Generate citation analysis based on type
            if analysis_type == "basic":
                citation_result = self._analyze_basic_citations(text_content, citation_focus)
            elif analysis_type == "bibliometric":
                citation_result = self._analyze_bibliometric_citations(text_content, citation_focus)
            else:  # detailed
                citation_result = self._analyze_detailed_citations(text_content, citation_focus)
            
            return {
                "success": True,
                "total_citations": citation_result.get("total_citations", 0),
                "citation_quality": citation_result.get("citation_quality", ""),
                "reference_analysis": citation_result.get("reference_analysis", {}),
                "bibliometric_indicators": citation_result.get("bibliometric_indicators", {}),
                "citation_gaps": citation_result.get("citation_gaps", []),
                "recommendations": citation_result.get("recommendations", []),
                "analysis_type": analysis_type,
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
    
    def _analyze_basic_citations(self, text_content: str, citation_focus: Optional[List[str]]) -> Dict[str, Any]:
        """Analyze basic citation elements."""
        try:
            prompt = f"""
You are an expert research analyst. Provide a basic analysis of the citations and references in this research paper.

PAPER CONTENT:
{text_content[:6000]}

{f"SPECIFIC ASPECTS TO FOCUS ON: {', '.join(citation_focus)}" if citation_focus else ""}

Provide basic citation analysis in JSON format:
{{
  "total_citations": 50,  // Estimated number of citations
  "citation_quality": "Assessment of citation quality",
  "reference_analysis": {{
    "recent_sources": "How recent are the sources?",
    "authoritative_sources": "Are sources authoritative?",
    "coverage": "How well does the literature coverage appear?"
  }},
  "bibliometric_indicators": {{
    "citation_count": "Estimated citation count",
    "source_diversity": "Diversity of sources"
  }},
  "citation_gaps": [
    "Gap 1",
    "Gap 2"
  ],
  "recommendations": [
    "Recommendation 1",
    "Recommendation 2"
  ]
}}

Focus on the most essential citation elements.
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-3.5-turbo",
                max_tokens=1000
            )
            
            if llm_response:
                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    return {"error": "Could not parse citation analysis"}
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Basic citation analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_detailed_citations(self, text_content: str, citation_focus: Optional[List[str]]) -> Dict[str, Any]:
        """Analyze detailed citation elements."""
        try:
            prompt = f"""
You are an expert research analyst. Provide a detailed analysis of the citations and references in this research paper.

PAPER CONTENT:
{text_content[:6000]}

{f"SPECIFIC ASPECTS TO FOCUS ON: {', '.join(citation_focus)}" if citation_focus else ""}

Provide detailed citation analysis in JSON format:
{{
  "total_citations": 50,  // Estimated number of citations
  "citation_quality": {{
    "relevance": "How relevant are the citations?",
    "authority": "How authoritative are the sources?",
    "currency": "How current are the sources?",
    "coverage": "How comprehensive is the coverage?"
  }},
  "reference_analysis": {{
    "recent_sources": {{
      "last_5_years": "Number of sources from last 5 years",
      "last_10_years": "Number of sources from last 10 years",
      "older_sources": "Number of older sources"
    }},
    "source_types": {{
      "journal_articles": "Number of journal articles",
      "books": "Number of books",
      "conference_papers": "Number of conference papers",
      "other": "Other source types"
    }},
    "geographic_diversity": "Geographic diversity of sources",
    "language_diversity": "Language diversity of sources"
  }},
  "bibliometric_indicators": {{
    "citation_count": "Estimated citation count",
    "source_diversity": "Diversity of sources",
    "impact_factors": "Assessment of journal impact factors",
    "h_index_considerations": "H-index considerations"
  }},
  "citation_gaps": [
    {{
      "gap": "Description of citation gap",
      "significance": "Why this gap is important",
      "suggested_sources": "Suggested sources to address gap"
    }}
  ],
  "recommendations": [
    "Detailed recommendation 1",
    "Detailed recommendation 2"
  ]
}}

Provide comprehensive analysis of all citation aspects.
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-3.5-turbo",
                max_tokens=1500
            )
            
            if llm_response:
                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    return {"error": "Could not parse detailed citation analysis"}
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Detailed citation analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_bibliometric_citations(self, text_content: str, citation_focus: Optional[List[str]]) -> Dict[str, Any]:
        """Analyze bibliometric citation elements."""
        try:
            prompt = f"""
You are an expert bibliometrician. Provide a comprehensive bibliometric analysis of the citations and references in this research paper.

PAPER CONTENT:
{text_content[:6000]}

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
                model="gpt-3.5-turbo",
                max_tokens=2000
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
