"""
Enhanced Content Summarizer Tool for QualiLens.

This tool provides comprehensive content summarization with multiple summary types,
executive summary generation, and PRISMA/CONSORT-style structured summaries for research papers.
"""

import logging
import json
import re
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
            description="Generate comprehensive summaries including executive summary, key findings, structured summaries, and PRISMA/CONSORT-style formatted summaries",
            parameters={
                "required": ["text_content"],
                "optional": ["summary_type", "max_length", "focus_areas", "format_type", "version"],
                "properties": {
                    "text_content": {
                        "type": "string",
                        "description": "The text content to summarize"
                    },
                    "summary_type": {
                        "type": "string",
                        "description": "Type of summary: 'executive', 'comprehensive', 'key_findings', 'structured', 'prisma', 'consort'",
                        "default": "comprehensive"
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum length of summary in words",
                        "default": 800
                    },
                    "focus_areas": {
                        "type": "array",
                        "description": "Specific areas to focus on in summary",
                        "default": []
                    },
                    "format_type": {
                        "type": "string",
                        "description": "For PRISMA/CONSORT: 'prisma' for systematic reviews, 'consort' for randomized controlled trials, 'auto' for automatic detection",
                        "default": "auto"
                    },
                    "version": {
                        "type": "string",
                        "description": "Summary version: 'concise' (≤200 words) or 'extended' (≤600 words). Applies to PRISMA/CONSORT summaries.",
                        "default": "extended"
                    }
                }
            },
            examples=[
                "Generate an executive summary of this research paper",
                "Create a comprehensive summary focusing on methodology and results",
                "Summarize the key findings and implications",
                "Generate a PRISMA-style structured summary (concise version)",
                "Generate a CONSORT-style structured summary (extended version)"
            ],
            category="content_analysis"
        )
    
    def execute(self, text_content: str, summary_type: str = "comprehensive", 
                max_length: int = 800, focus_areas: Optional[List[str]] = None,
                format_type: str = "auto", version: str = "extended") -> Dict[str, Any]:
        """
        Generate comprehensive content summaries with PRISMA/CONSORT support.
        
        Args:
            text_content: The text content to summarize
            summary_type: Type of summary to generate
            max_length: Maximum length of summary in words (overridden for PRISMA/CONSORT)
            focus_areas: Specific areas to focus on
            format_type: For PRISMA/CONSORT: 'prisma', 'consort', or 'auto'
            version: 'concise' (≤200 words) or 'extended' (≤600 words) for PRISMA/CONSORT
            
        Returns:
            Dict containing the generated summary and metadata
        """
        try:
            # Handle PRISMA/CONSORT structured summaries
            if summary_type in ["prisma", "consort"]:
                # Determine format: use summary_type if explicitly specified, otherwise use format_type or detect
                if summary_type in ["prisma", "consort"]:
                    final_format = summary_type
                elif format_type != "auto":
                    final_format = format_type
                else:
                    final_format = self._detect_study_type(text_content)
                word_limit = 200 if version == "concise" else 600
                summary_result = self._generate_structured_guideline_summary(
                    text_content, final_format, final_format, word_limit, focus_areas
                )
            else:
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
            
            # Build result dictionary
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
            
            # Add PRISMA/CONSORT specific fields
            if summary_type in ["prisma", "consort"]:
                result["format_type"] = summary_result.get("format_type", format_type)
                result["version"] = version
                result["structured_sections"] = summary_result.get("structured_sections", {})
                result["export_ready"] = summary_result.get("export_ready", "")
                result["compliance_check"] = summary_result.get("compliance_check", {})
            
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
        """Generate key findings summary with detailed quantitative information."""
        try:
            content_length = min(len(text_content), 10000)
            
            prompt = f"""
You are an expert research analyst. Extract and summarize the key findings from this research paper with specific quantitative data.

PAPER CONTENT:
{text_content[:content_length]}

CRITICAL REQUIREMENTS:
- Extract EXACT numbers, statistics, percentages, effect sizes, p-values, confidence intervals
- Each finding must include specific quantitative data
- Focus on primary and secondary outcomes with exact results
- Include comparative data (treatment vs control, before vs after, etc.)
- Highlight statistical significance and effect sizes

{f"SPECIFIC FOCUS AREAS: {', '.join(focus_areas)}" if focus_areas else ""}

Please provide the key findings in JSON format with specific quantitative data:
{{
  "key_findings": [
    "Specific finding with exact numbers, percentages, effect sizes, and statistical significance (e.g., 'Treatment X demonstrated a mean improvement of 4.2 points (95% CI: 3.1-5.3, p<0.001) compared to placebo')",
    "Another specific finding with quantitative data and comparisons",
    "Third finding with statistical details and effect sizes"
  ],
  "novel_discoveries": [
    "Novel discovery 1 with specific quantitative results",
    "Novel discovery 2 with data"
  ],
  "significant_results": [
    "Significant result 1 with p-values and effect sizes",
    "Significant result 2 with confidence intervals"
  ],
  "implications": "What these findings mean based on the quantitative results"
}}

IMPORTANT: Every finding must include specific numbers, statistics, or quantitative comparisons. Avoid generic statements.
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-4o-mini",
                max_tokens=1800,  # Increased for more detailed findings
                temperature=0.2
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
        """Generate structured summary with detailed information."""
        try:
            content_length = min(len(text_content), 10000)
            
            prompt = f"""
You are an expert research analyst. Create a detailed structured summary of this research paper with specific quantitative information.

PAPER CONTENT:
{text_content[:content_length]}

REQUIREMENTS:
- Maximum {max_length} words total across all sections
- Include specific numbers, statistics, and quantitative findings
- Be comprehensive and information-dense
- Distribute words appropriately: Background (15%), Objective (10%), Methodology (25%), Results (35%), Conclusions (15%)

{f"SPECIFIC FOCUS AREAS: {', '.join(focus_areas)}" if focus_areas else ""}

Please provide a structured summary in JSON format with detailed, quantitative information:
{{
  "background": "Detailed background with context, research gap, and rationale (include specific statistics or prevalence if mentioned)",
  "objective": "Research objectives and questions with specific hypotheses or endpoints",
  "methodology": "Detailed methodological approach including study design, sample size, duration, interventions, and key procedures",
  "results": "Detailed results with specific quantitative findings, effect sizes, p-values, confidence intervals, and statistical significance",
  "conclusions": "Main conclusions with specific implications and recommendations",
  "significance": "Why this research is important with practical or theoretical impact"
}}

IMPORTANT: Include specific numbers, statistics, and quantitative data in each section. Make it information-rich.
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-4o-mini",
                max_tokens=2000,  # Increased for more detailed structured content
                temperature=0.2
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
        """Generate comprehensive summary with rich, detailed information."""
        try:
            # Use more content for better analysis
            content_length = min(len(text_content), 12000)
            
            prompt = f"""
You are an expert research analyst with deep expertise in scientific paper analysis. Create a comprehensive, information-dense summary of this research paper.

PAPER CONTENT:
{text_content[:content_length]}

CRITICAL REQUIREMENTS:
1. SUMMARY SECTION (200-{max_length} words): Write a detailed, informative paragraph that includes:
   - Study design and methodology (e.g., randomized controlled trial, sample size, duration)
   - Specific interventions, treatments, or methods used
   - Key quantitative findings with exact numbers, statistics, effect sizes, p-values where available
   - Primary and secondary outcomes with specific results
   - Participant characteristics (age range, sample size, demographics if mentioned)
   - Statistical significance and confidence intervals if reported
   - Clinical or practical significance
   - Safety and adverse events information
   - Main conclusions and implications

2. KEY POINTS (4-7 points): Extract the most important findings as standalone statements. Each point should:
   - Include specific quantitative data (numbers, percentages, effect sizes, p-values)
   - Be substantial and informative (not generic)
   - Highlight novel discoveries or significant results
   - Reference specific outcomes or measurements
   - Format: "Finding X demonstrated [specific result] with [statistics], compared to [comparison]."

3. LIMITATIONS (2-4 limitations): Identify concrete study limitations such as:
   - Sample size constraints
   - Study duration or follow-up limitations
   - Generalizability issues (single-center, specific population, etc.)
   - Methodological constraints
   - Missing data or incomplete reporting
   - Potential biases

4. STRENGTHS (2-3 strengths): Identify methodological strengths:
   - Study design quality
   - Sample size adequacy
   - Statistical rigor
   - Reporting completeness

{f"SPECIFIC FOCUS AREAS: {', '.join(focus_areas)}" if focus_areas else ""}

IMPORTANT: 
- Extract EXACT numbers, statistics, and quantitative findings from the paper
- Be specific and detailed - avoid generic statements
- Include all relevant quantitative data (sample sizes, effect sizes, percentages, p-values, confidence intervals)
- Make the summary information-dense and valuable
- Ensure key_points contain substantial, specific findings with data

Return ONLY valid JSON (no markdown formatting):
{{
  "summary": "Detailed, information-rich summary paragraph (150-{max_length} words) with specific findings, statistics, and quantitative results",
  "key_points": [
    "Specific finding 1 with exact numbers and statistics",
    "Specific finding 2 with quantitative data",
    "Specific finding 3 with effect sizes or percentages",
    "Specific finding 4 with comparative results"
  ],
  "methodology_highlights": "Detailed methodological description including study design, sample size, duration, interventions",
  "main_results": "Detailed results section with specific quantitative findings, statistical significance, effect sizes",
  "implications": "Practical and theoretical implications based on the findings",
  "strengths": [
    "Specific methodological strength 1",
    "Specific methodological strength 2"
  ],
  "limitations": [
    "Specific limitation 1 with context",
    "Specific limitation 2 with context",
    "Specific limitation 3 if applicable"
  ]
}}
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-4o-mini",
                max_tokens=2500,  # Increased for more detailed output
                temperature=0.2  # Slightly higher for more natural language while maintaining accuracy
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
                    
                    # Validate and enhance summary quality
                    summary_text = result.get("summary", "")
                    summary_words = len(summary_text.split()) if summary_text else 0
                    
                    # If summary is too short, try to enhance it by combining with other fields
                    if summary_words < 100 and max_length >= 200:
                        # Combine summary with methodology and results if available
                        enhanced_parts = [summary_text]
                        if result.get("methodology_highlights"):
                            enhanced_parts.append(result["methodology_highlights"])
                        if result.get("main_results"):
                            enhanced_parts.append(result["main_results"])
                        if enhanced_parts:
                            result["summary"] = " ".join([p for p in enhanced_parts if p and p.strip()])
                            summary_words = len(result["summary"].split())
                    
                    # Ensure key_points are substantial
                    key_points = result.get("key_points", [])
                    if not key_points or len(key_points) < 3:
                        # Try to extract from other fields
                        if result.get("main_results"):
                            key_points.append(result["main_results"])
                        if result.get("methodology_highlights"):
                            key_points.append(result["methodology_highlights"])
                        result["key_points"] = key_points[:5]  # Limit to 5
                    
                    # Ensure limitations are present
                    limitations = result.get("limitations", [])
                    if not limitations or len(limitations) < 2:
                        # Add a generic limitation if none found
                        if not limitations:
                            limitations = ["Study limitations should be reviewed in the original paper"]
                        result["limitations"] = limitations
                    
                    result["word_count"] = summary_words
                    
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
                    
                    # Log summary quality metrics
                    logger.info(f"Generated comprehensive summary: {summary_words} words, {len(key_points)} key points, {len(limitations)} limitations")
                    
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
    
    def _detect_study_type(self, text_content: str) -> str:
        """
        Detect study type to determine appropriate reporting guideline (PRISMA or CONSORT).
        
        Args:
            text_content: The text content to analyze
            
        Returns:
            'prisma' for systematic reviews/meta-analyses, 'consort' for RCTs, 'prisma' as default
        """
        text_lower = text_content.lower()
        
        # Keywords for systematic reviews/meta-analyses (PRISMA)
        prisma_keywords = [
            "systematic review", "meta-analysis", "meta analysis", "systematic literature review",
            "systematic search", "prisma", "preferred reporting items", "inclusion criteria",
            "exclusion criteria", "study selection", "risk of bias assessment", "quality assessment"
        ]
        
        # Keywords for randomized controlled trials (CONSORT)
        consort_keywords = [
            "randomized controlled trial", "rct", "randomized trial", "random allocation",
            "randomized", "randomly assigned", "randomization", "control group", "intervention group",
            "consort", "trial registration", "clinical trial", "participants were randomized"
        ]
        
        prisma_score = sum(1 for keyword in prisma_keywords if keyword in text_lower)
        consort_score = sum(1 for keyword in consort_keywords if keyword in text_lower)
        
        if consort_score > prisma_score and consort_score >= 2:
            return "consort"
        elif prisma_score >= 2:
            return "prisma"
        else:
            # Default to PRISMA for general research papers
            return "prisma"
    
    def _count_words(self, text: str) -> int:
        """Count words in text."""
        return len(re.findall(r'\b\w+\b', text))
    
    def _enforce_word_limit(self, text: str, max_words: int) -> str:
        """
        Enforce word limit by truncating intelligently at sentence boundaries.
        
        Args:
            text: Text to truncate
            max_words: Maximum number of words
            
        Returns:
            Truncated text that respects word limit
        """
        words = text.split()
        if len(words) <= max_words:
            return text
        
        # Truncate to max_words
        truncated_words = words[:max_words]
        truncated_text = " ".join(truncated_words)
        
        # Try to end at a sentence boundary
        last_period = truncated_text.rfind('.')
        last_exclamation = truncated_text.rfind('!')
        last_question = truncated_text.rfind('?')
        
        last_sentence_end = max(last_period, last_exclamation, last_question)
        if last_sentence_end > max_words * 0.7:  # Only if we don't lose too much
            truncated_text = truncated_text[:last_sentence_end + 1]
        
        return truncated_text.strip()
    
    def _generate_structured_guideline_summary(self, text_content: str, summary_type: str, 
                                             format_type: str, word_limit: int, 
                                             focus_areas: Optional[List[str]]) -> Dict[str, Any]:
        """
        Generate PRISMA or CONSORT-style structured summary with strict word limit enforcement.
        
        Args:
            text_content: The text content to summarize
            summary_type: 'prisma' or 'consort'
            format_type: Detected or specified format type
            word_limit: Strict word limit (200 for concise, 600 for extended)
            focus_areas: Specific areas to focus on
            
        Returns:
            Dict containing structured summary with all required sections
        """
        try:
            # Determine which template to use
            is_prisma = (format_type == "prisma" or summary_type == "prisma")
            guideline_name = "PRISMA" if is_prisma else "CONSORT"
            version_label = "concise" if word_limit == 200 else "extended"
            
            logger.info(f"Generating {guideline_name}-style {version_label} summary (≤{word_limit} words)")
            
            # Get appropriate template
            if is_prisma:
                template = self._get_prisma_template(word_limit)
            else:
                template = self._get_consort_template(word_limit)
            
            # Create comprehensive prompt
            prompt = f"""
You are an expert research analyst specializing in {guideline_name} reporting guidelines. Create a structured summary following {guideline_name} standards.

PAPER CONTENT:
{text_content[:8000]}

REQUIREMENTS:
- STRICT WORD LIMIT: Maximum {word_limit} words TOTAL across all sections
- Follow {guideline_name} reporting structure exactly
- Be precise, factual, and evidence-based
- Use clear, concise language
- Include all required sections from the template
- Ensure word count compliance - this is critical

{f"SPECIFIC FOCUS AREAS: {', '.join(focus_areas)}" if focus_areas else ""}

TEMPLATE STRUCTURE:
{template}

IMPORTANT: 
1. The total word count across ALL sections must be ≤{word_limit} words
2. Distribute words appropriately across sections based on importance
3. Return ONLY valid JSON, no markdown formatting
4. Include a "word_count" field with the total word count
5. Include an "export_ready" field with a formatted version ready for inclusion in reports

Provide the structured summary in JSON format following the template exactly.
"""
            
            # Generate with higher token limit for structured content
            max_tokens = 2000 if word_limit == 600 else 1200
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-4o-mini",
                max_tokens=max_tokens,
                temperature=0.1  # Lower temperature for more consistent structure
            )
            
            if not llm_response:
                return {"error": "No response from LLM"}
            
            # Parse JSON response
            cleaned_response = llm_response.strip()
            # Remove markdown code fences if present
            if cleaned_response.startswith("```"):
                first_newline = cleaned_response.find("\n")
                if first_newline > 0:
                    cleaned_response = cleaned_response[first_newline:].strip()
                cleaned_response = cleaned_response.replace("```json", "").replace("```", "").strip()
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3].strip()
            
            try:
                result = json.loads(cleaned_response)
                
                # Extract structured sections
                structured_sections = {}
                export_parts = []
                
                # Build structured sections and export-ready format
                for key, value in result.items():
                    if key not in ["word_count", "export_ready", "compliance_check"]:
                        if isinstance(value, str) and value.strip():
                            structured_sections[key] = value
                            # Format for export
                            section_title = key.replace("_", " ").title()
                            export_parts.append(f"{section_title}:\n{value}\n")
                
                # Create combined summary
                combined_summary = " ".join([v for v in structured_sections.values() if isinstance(v, str)])
                
                # Enforce word limit strictly
                actual_word_count = self._count_words(combined_summary)
                if actual_word_count > word_limit:
                    logger.warning(f"Summary exceeded word limit ({actual_word_count} > {word_limit}), truncating...")
                    combined_summary = self._enforce_word_limit(combined_summary, word_limit)
                    actual_word_count = self._count_words(combined_summary)
                
                # Create export-ready formatted version
                export_ready = "\n".join(export_parts).strip()
                if not export_ready:
                    export_ready = combined_summary
                
                # Compliance check
                compliance_check = {
                    "guideline": guideline_name,
                    "word_limit": word_limit,
                    "actual_words": actual_word_count,
                    "within_limit": actual_word_count <= word_limit,
                    "sections_completed": len([k for k, v in structured_sections.items() if v and v.strip()]),
                    "version": version_label
                }
                
                result.update({
                    "summary": combined_summary,
                    "structured_sections": structured_sections,
                    "export_ready": export_ready,
                    "word_count": actual_word_count,
                    "format_type": format_type,
                    "compliance_check": compliance_check
                })
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                # Fallback: try to extract structured content from plain text
                return {
                    "summary": cleaned_response[:word_limit * 6],  # Rough estimate
                    "structured_sections": {},
                    "export_ready": cleaned_response,
                    "word_count": self._count_words(cleaned_response),
                    "format_type": format_type,
                    "error": "JSON parsing failed, returned plain text"
                }
                
        except Exception as e:
            logger.error(f"{guideline_name} summary generation failed: {str(e)}")
            return {"error": str(e)}
    
    def _get_prisma_template(self, word_limit: int) -> str:
        """
        Get PRISMA template structure based on word limit.
        
        Args:
            word_limit: Maximum words (200 for concise, 600 for extended)
            
        Returns:
            Template string for PRISMA structure
        """
        if word_limit == 200:
            # Concise PRISMA template (≤200 words)
            return """
{
  "title": "Brief descriptive title (5-10 words)",
  "background": "Context and rationale (30-40 words)",
  "objectives": "Primary and secondary objectives (25-35 words)",
  "methods": "Search strategy, databases, selection criteria, data extraction (60-80 words)",
  "results": "Number of studies, key findings, main outcomes (50-60 words)",
  "conclusions": "Main conclusions and implications (20-30 words)",
  "word_count": 0
}
"""
        else:
            # Extended PRISMA template (≤600 words)
            return """
{
  "title": "Descriptive title (10-15 words)",
  "background": "Context, rationale, and research gap (80-100 words)",
  "objectives": "Primary and secondary objectives with PICO elements (50-70 words)",
  "methods": {
    "search_strategy": "Databases searched, search terms, date ranges (60-80 words)",
    "selection_criteria": "Inclusion and exclusion criteria (40-50 words)",
    "data_extraction": "Data extraction process and quality assessment (40-50 words)",
    "synthesis": "Methods for data synthesis and analysis (30-40 words)"
  },
  "results": {
    "study_selection": "Number of studies identified, screened, included (40-50 words)",
    "study_characteristics": "Key characteristics of included studies (50-60 words)",
    "synthesis_of_results": "Main findings, effect sizes, heterogeneity (80-100 words)",
    "risk_of_bias": "Quality assessment results (30-40 words)"
  },
  "discussion": {
    "summary_of_evidence": "Key findings and their interpretation (50-60 words)",
    "limitations": "Study limitations and potential biases (40-50 words)",
    "implications": "Implications for practice, policy, or research (40-50 words)"
  },
  "conclusions": "Main conclusions and recommendations (30-40 words)",
  "word_count": 0
}
"""
    
    def _get_consort_template(self, word_limit: int) -> str:
        """
        Get CONSORT template structure based on word limit.
        
        Args:
            word_limit: Maximum words (200 for concise, 600 for extended)
            
        Returns:
            Template string for CONSORT structure
        """
        if word_limit == 200:
            # Concise CONSORT template (≤200 words)
            return """
{
  "title": "Brief descriptive title with study design (5-10 words)",
  "background": "Context and rationale (30-40 words)",
  "objectives": "Primary and secondary objectives (25-35 words)",
  "methods": {
    "trial_design": "Study design and settings (20-25 words)",
    "participants": "Eligibility criteria, recruitment (30-40 words)",
    "interventions": "Intervention and control groups (25-35 words)",
    "outcomes": "Primary and secondary outcomes (20-30 words)"
  },
  "results": {
    "participant_flow": "Numbers randomized, analyzed (25-30 words)",
    "baseline_data": "Baseline characteristics (20-25 words)",
    "outcomes": "Primary and secondary outcomes with effect sizes (40-50 words)"
  },
  "conclusions": "Main conclusions and implications (20-30 words)",
  "word_count": 0
}
"""
        else:
            # Extended CONSORT template (≤600 words)
            return """
{
  "title": "Descriptive title with study design (10-15 words)",
  "background": "Context, rationale, and research gap (80-100 words)",
  "objectives": "Primary and secondary objectives with hypothesis (50-70 words)",
  "methods": {
    "trial_design": "Study design, settings, locations, dates (50-60 words)",
    "participants": {
      "eligibility": "Eligibility criteria for participants (40-50 words)",
      "recruitment": "Recruitment methods and settings (30-40 words)"
    },
    "interventions": {
      "intervention_group": "Intervention details, how and when administered (50-60 words)",
      "control_group": "Control group details and procedures (40-50 words)"
    },
    "outcomes": {
      "primary_outcomes": "Primary outcome measures, how and when assessed (40-50 words)",
      "secondary_outcomes": "Secondary outcome measures (30-40 words)"
    },
    "sample_size": "Sample size calculation and rationale (30-40 words)",
    "randomization": "Randomization method, allocation concealment (40-50 words)",
    "blinding": "Blinding procedures, who was blinded (30-40 words)",
    "statistical_methods": "Statistical methods for analysis (40-50 words)"
  },
  "results": {
    "participant_flow": "Numbers of participants randomized, allocated, analyzed, lost to follow-up (50-60 words)",
    "baseline_data": "Baseline demographic and clinical characteristics (40-50 words)",
    "outcomes": {
      "primary_outcomes": "Primary outcome results with effect sizes, confidence intervals (60-80 words)",
      "secondary_outcomes": "Secondary outcome results (40-50 words)",
      "adverse_events": "Adverse events and harms (30-40 words)"
    }
  },
  "discussion": {
    "interpretation": "Interpretation of results in context of existing evidence (60-80 words)",
    "limitations": "Trial limitations and potential biases (40-50 words)",
    "generalisability": "Generalisability and external validity (30-40 words)",
    "implications": "Implications for practice, policy, or research (40-50 words)"
  },
  "conclusions": "Main conclusions and recommendations (40-50 words)",
  "word_count": 0
}
"""
