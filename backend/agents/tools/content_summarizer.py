"""
Enhanced Content Summarizer Tool for QualiLens.

This tool provides comprehensive content summarization with multiple summary types
and executive summary generation for research papers.
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


class ContentSummarizerTool(BaseTool):
    """
    Enhanced Content Summarizer tool for comprehensive paper summarization.
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
            name="content_summarizer_tool",
            description="Generate comprehensive summaries including executive summary, key findings, and structured summaries",
            parameters={
                "required": ["text_content"],
                "optional": ["summary_type", "max_length", "focus_areas"],
                "properties": {
                    "text_content": {
                        "type": "string",
                        "description": "The text content to summarize"
                    },
                    "summary_type": {
                        "type": "string",
                        "description": "Type of summary: 'executive', 'comprehensive', 'key_findings', 'structured'",
                        "default": "comprehensive"
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum length of summary in words",
                        "default": 500
                    },
                    "focus_areas": {
                        "type": "array",
                        "description": "Specific areas to focus on in summary",
                        "default": []
                    }
                }
            },
            examples=[
                "Generate an executive summary of this research paper",
                "Create a comprehensive summary focusing on methodology and results",
                "Summarize the key findings and implications"
            ],
            category="content_analysis"
        )
    
    def execute(self, text_content: str, summary_type: str = "comprehensive", 
                max_length: int = 500, focus_areas: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive content summaries.
        
        Args:
            text_content: The text content to summarize
            summary_type: Type of summary to generate
            max_length: Maximum length of summary in words
            focus_areas: Specific areas to focus on
            
        Returns:
            Dict containing the generated summary and metadata
        """
        try:
            logger.info(f"Generating {summary_type} summary with max length {max_length}")
            
            # Create appropriate prompt based on summary type
            if summary_type == "executive":
                summary_result = self._generate_executive_summary(text_content, max_length, focus_areas)
            elif summary_type == "key_findings":
                summary_result = self._generate_key_findings_summary(text_content, max_length, focus_areas)
            elif summary_type == "structured":
                summary_result = self._generate_structured_summary(text_content, max_length, focus_areas)
            else:  # comprehensive
                summary_result = self._generate_comprehensive_summary(text_content, max_length, focus_areas)
            
            # For comprehensive summaries, extract all fields
            result = {
                "success": True,
                "summary_type": summary_type,
                "summary": summary_result.get("summary", ""),
                "key_points": summary_result.get("key_points", []),
                "executive_summary": summary_result.get("executive_summary", ""),
                "word_count": summary_result.get("word_count", 0),
                "focus_areas": focus_areas or [],
                "tool_used": "content_summarizer_tool"
            }
            
            # Add comprehensive summary fields if available
            if summary_type == "comprehensive":
                result["methodology_highlights"] = summary_result.get("methodology_highlights", "")
                result["main_results"] = summary_result.get("main_results", "")
                result["implications"] = summary_result.get("implications", "")
                result["strengths"] = summary_result.get("strengths", [])
                result["limitations"] = summary_result.get("limitations", [])
            
            return result
            
        except Exception as e:
            logger.error(f"Content summarization failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_used": "content_summarizer_tool"
            }
    
    def _generate_executive_summary(self, text_content: str, max_length: int, focus_areas: Optional[List[str]]) -> Dict[str, Any]:
        """Generate executive summary."""
        try:
            prompt = f"""
You are an expert research analyst. Create a concise executive summary of this research paper.

PAPER CONTENT:
{text_content[:6000]}

REQUIREMENTS:
- Maximum {max_length} words
- Focus on the most important findings and implications
- Write for a senior executive audience
- Highlight key contributions and significance

{f"SPECIFIC FOCUS AREAS: {', '.join(focus_areas)}" if focus_areas else ""}

Please provide the executive summary in JSON format:
{{
  "executive_summary": "2-3 sentence executive summary",
  "key_contributions": ["Contribution 1", "Contribution 2"],
  "significance": "Why this research matters",
  "implications": "What this means for the field"
}}

Focus on clarity, impact, and the most important aspects for decision-makers.
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-4o-mini",
                max_tokens=800
            )
            
            if llm_response:
                try:
                    result = json.loads(llm_response)
                    result["word_count"] = len(result.get("executive_summary", "").split())
                    return result
                except json.JSONDecodeError:
                    return {
                        "summary": llm_response,
                        "executive_summary": llm_response,
                        "key_points": [],
                        "word_count": len(llm_response.split())
                    }
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Executive summary generation failed: {str(e)}")
            return {"error": str(e)}
    
    def _generate_key_findings_summary(self, text_content: str, max_length: int, focus_areas: Optional[List[str]]) -> Dict[str, Any]:
        """Generate key findings summary."""
        try:
            prompt = f"""
You are an expert research analyst. Extract and summarize the key findings from this research paper.

PAPER CONTENT:
{text_content[:6000]}

REQUIREMENTS:
- Maximum {max_length} words
- Focus on the most important findings and results
- Highlight novel discoveries and significant results

{f"SPECIFIC FOCUS AREAS: {', '.join(focus_areas)}" if focus_areas else ""}

Please provide the key findings in JSON format:
{{
  "key_findings": [
    "Finding 1 with supporting evidence",
    "Finding 2 with supporting evidence",
    "Finding 3 with supporting evidence"
  ],
  "novel_discoveries": [
    "Novel discovery 1",
    "Novel discovery 2"
  ],
  "significant_results": [
    "Significant result 1",
    "Significant result 2"
  ],
  "implications": "What these findings mean"
}}

Focus on the most important and novel findings.
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-4o-mini",
                max_tokens=1000
            )
            
            if llm_response:
                try:
                    result = json.loads(llm_response)
                    # Create a combined summary
                    all_findings = result.get("key_findings", []) + result.get("novel_discoveries", []) + result.get("significant_results", [])
                    combined_summary = ". ".join(all_findings[:5])  # Limit to top 5 findings
                    result["summary"] = combined_summary
                    result["word_count"] = len(combined_summary.split())
                    return result
                except json.JSONDecodeError:
                    return {
                        "summary": llm_response,
                        "key_points": [],
                        "word_count": len(llm_response.split())
                    }
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Key findings summary generation failed: {str(e)}")
            return {"error": str(e)}
    
    def _generate_structured_summary(self, text_content: str, max_length: int, focus_areas: Optional[List[str]]) -> Dict[str, Any]:
        """Generate structured summary."""
        try:
            prompt = f"""
You are an expert research analyst. Create a structured summary of this research paper.

PAPER CONTENT:
{text_content[:6000]}

REQUIREMENTS:
- Maximum {max_length} words total
- Provide structured sections for different aspects
- Be comprehensive but concise

{f"SPECIFIC FOCUS AREAS: {', '.join(focus_areas)}" if focus_areas else ""}

Please provide a structured summary in JSON format:
{{
  "background": "Background and context",
  "objective": "Research objectives and questions",
  "methodology": "Key methodological approach",
  "results": "Main results and findings",
  "conclusions": "Main conclusions and implications",
  "significance": "Why this research is important"
}}

Provide clear, structured information for each section.
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-4o-mini",
                max_tokens=1200
            )
            
            if llm_response:
                try:
                    result = json.loads(llm_response)
                    # Create a combined summary
                    sections = [result.get("background", ""), result.get("objective", ""), 
                               result.get("methodology", ""), result.get("results", ""), 
                               result.get("conclusions", "")]
                    combined_summary = " ".join([s for s in sections if s])
                    result["summary"] = combined_summary
                    result["word_count"] = len(combined_summary.split())
                    return result
                except json.JSONDecodeError:
                    return {
                        "summary": llm_response,
                        "key_points": [],
                        "word_count": len(llm_response.split())
                    }
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Structured summary generation failed: {str(e)}")
            return {"error": str(e)}
    
    def _generate_comprehensive_summary(self, text_content: str, max_length: int, focus_areas: Optional[List[str]]) -> Dict[str, Any]:
        """Generate comprehensive summary."""
        try:
            prompt = f"""
You are an expert research analyst. Create a comprehensive summary of this research paper.

PAPER CONTENT:
{text_content[:6000]}

REQUIREMENTS:
- Maximum {max_length} words
- Provide a complete overview of the research
- Include methodology, results, and implications
- Be comprehensive but accessible

{f"SPECIFIC FOCUS AREAS: {', '.join(focus_areas)}" if focus_areas else ""}

Please provide a comprehensive summary in JSON format:
{{
  "summary": "Comprehensive summary of the entire paper",
  "key_points": [
    "Key point 1",
    "Key point 2",
    "Key point 3"
  ],
  "methodology_highlights": "Key methodological aspects",
  "main_results": "Main results and findings",
  "implications": "Implications and significance",
  "strengths": ["Strength 1", "Strength 2"],
  "limitations": ["Limitation 1", "Limitation 2"]
}}

Provide a thorough but concise overview of the entire research.
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-4o-mini",
                max_tokens=1500
            )
            
            if llm_response:
                # CRITICAL: Strip markdown code fences if present (```json ... ```)
                cleaned_response = llm_response.strip()
                # Remove opening fence (```json or ```)
                if cleaned_response.startswith("```"):
                    # Find the first newline after ```
                    first_newline = cleaned_response.find("\n")
                    if first_newline > 0:
                        cleaned_response = cleaned_response[first_newline:].strip()
                    else:
                        # No newline, just remove ```
                        cleaned_response = cleaned_response.replace("```json", "").replace("```", "").strip()
                    # Remove closing fence (```)
                    if cleaned_response.endswith("```"):
                        cleaned_response = cleaned_response[:-3].strip()
                
                try:
                    result = json.loads(cleaned_response)
                    result["word_count"] = len(result.get("summary", "").split())
                    # CRITICAL: Ensure we return a proper dict, not a JSON string
                    # If the LLM returned the entire JSON as a string in the summary field, extract it
                    if isinstance(result.get("summary"), str) and result.get("summary", "").strip().startswith("{"):
                        try:
                            # The summary field itself is JSON, parse it
                            nested_json = json.loads(result["summary"])
                            # Merge the nested JSON into the result
                            result.update(nested_json)
                        except:
                            # If parsing fails, keep the original structure
                            pass
                    return result
                except json.JSONDecodeError:
                    # If LLM response is not JSON, try to extract JSON from it
                    if cleaned_response.startswith("{") or cleaned_response.startswith("["):
                        try:
                            # Try parsing the entire response as JSON
                            result = json.loads(cleaned_response)
                            result["word_count"] = len(result.get("summary", "").split())
                            return result
                        except:
                            pass
                    # Fallback: return as plain text summary
                    return {
                        "summary": cleaned_response,
                        "key_points": [],
                        "word_count": len(cleaned_response.split())
                    }
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Comprehensive summary generation failed: {str(e)}")
            return {"error": str(e)}
