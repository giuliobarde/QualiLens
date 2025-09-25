"""
Paper Analyzer Tool for QualiLens.

This tool uses LLM to extract key research data from papers including methodologies,
sample sizes, participants, results, and other important research information.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .base_tool import BaseTool, ToolMetadata

# Add the project root to the Python path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from LLM.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


@dataclass
class ResearchData:
    """Structured research data extracted from papers."""
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    methodology: Optional[str] = None
    study_design: Optional[str] = None
    sample_size: Optional[int] = None
    participants: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    conclusions: Optional[str] = None
    limitations: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    publication_year: Optional[int] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    research_questions: Optional[List[str]] = None
    hypotheses: Optional[List[str]] = None
    statistical_tests: Optional[List[str]] = None
    effect_sizes: Optional[Dict[str, Any]] = None
    confidence_intervals: Optional[Dict[str, Any]] = None
    p_values: Optional[Dict[str, Any]] = None
    effect_direction: Optional[str] = None
    clinical_significance: Optional[str] = None
    practical_implications: Optional[str] = None
    future_research: Optional[List[str]] = None


@dataclass
class PaperSummary:
    """Comprehensive paper summary structure."""
    executive_summary: Optional[str] = None
    key_findings: Optional[List[str]] = None
    methodology_summary: Optional[str] = None
    results_summary: Optional[str] = None
    implications: Optional[str] = None
    significance: Optional[str] = None
    contribution_to_field: Optional[str] = None


@dataclass
class KeyDiscovery:
    """Structure for key discoveries in the paper."""
    discovery: str
    significance: str
    evidence: str
    implications: str
    confidence_level: str


@dataclass
class DetailedAnalysis:
    """Comprehensive analysis structure."""
    paper_summary: Optional[PaperSummary] = None
    key_discoveries: Optional[List[KeyDiscovery]] = None
    methodology_analysis: Optional[Dict[str, Any]] = None
    results_analysis: Optional[Dict[str, Any]] = None
    statistical_analysis: Optional[Dict[str, Any]] = None
    quality_assessment: Optional[Dict[str, Any]] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    research_gaps: Optional[List[str]] = None
    future_directions: Optional[List[str]] = None


class PaperAnalyzerTool(BaseTool):
    """
    Tool for analyzing research papers and extracting key data using LLM.
    """
    
    def __init__(self):
        super().__init__()
        self.openai_client = None
    
    def _get_openai_client(self):
        """Get OpenAI client, initializing it lazily if needed."""
        if self.openai_client is None:
            self.openai_client = OpenAIClient()
        return self.openai_client
        
    def get_name(self) -> str:
        """Return the name of this tool."""
        return "paper_analyzer_tool"
    
    def get_description(self) -> str:
        """Return the description of this tool."""
        return "Analyzes research papers and extracts key data including methodologies, sample sizes, participants, results, and other research information using LLM"
    
    def get_examples(self) -> List[str]:
        """Return example queries for this tool."""
        return [
            "Analyze this research paper and extract key findings",
            "What is the methodology used in this study?",
            "Extract sample size and participant demographics",
            "What are the main results and conclusions?",
            "Analyze the statistical significance and effect sizes"
        ]
    
    def _get_metadata(self) -> ToolMetadata:
        """Return metadata for this tool."""
        return ToolMetadata(
            name=self.get_name(),
            description=self.get_description(),
            category="research_analysis",
            parameters={
                "required": ["text_content"],
                "optional": ["query", "extract_level"]
            },
            examples=self.get_examples()
        )
    
    def execute(self, text_content: str, query: Optional[str] = None, extract_level: str = "comprehensive") -> Dict[str, Any]:
        """
        Analyze research paper text and extract key data using LLM.
        
        Args:
            text_content (str): The text content of the research paper
            query (Optional[str]): Specific query about what to extract
            extract_level (str): Level of extraction - "basic", "comprehensive", or "detailed"
            
        Returns:
            Dict[str, Any]: Extracted research data and analysis
        """
        try:
            logger.info(f"Analyzing paper content with extract_level: {extract_level}")
            
            # Create extraction prompt based on query and extract level
            extraction_prompt = self._create_extraction_prompt(text_content, query, extract_level)
            
            # Use LLM to extract structured data
            llm_response = self._get_openai_client().generate_completion(
                prompt=extraction_prompt,
                model="gpt-3.5-turbo",
                max_tokens=2000
            )
            
            if not llm_response:
                raise Exception("Failed to get LLM response")
            
            # Parse the LLM response
            extracted_data = self._parse_llm_response(llm_response)
            
            # Create comprehensive result
            result = {
                "success": True,
                "extracted_data": extracted_data,
                "raw_llm_response": llm_response,
                "extract_level": extract_level,
                "query": query,
                "tool_used": "paper_analyzer_tool"
            }
            
            logger.info("Successfully extracted research data from paper")
            return result
            
        except Exception as e:
            logger.error(f"Paper analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_used": "paper_analyzer_tool"
            }
    
    def generate_detailed_analysis(self, text_content: str, query: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive detailed analysis including summary and key discoveries.
        
        Args:
            text_content (str): The text content of the research paper
            query (Optional[str]): Specific query about what to analyze
            
        Returns:
            Dict[str, Any]: Comprehensive analysis with summary and key discoveries
        """
        try:
            logger.info("Generating detailed paper analysis with summary and key discoveries")
            
            # Generate paper summary
            summary_result = self._generate_paper_summary(text_content, query)
            
            # Generate key discoveries
            discoveries_result = self._generate_key_discoveries(text_content, query)
            
            # Generate methodology analysis
            methodology_result = self._generate_methodology_analysis(text_content)
            
            # Generate results analysis
            results_result = self._generate_results_analysis(text_content)
            
            # Generate quality assessment
            quality_result = self._generate_quality_assessment(text_content)
            
            # Combine all analyses
            detailed_analysis = {
                "success": True,
                "paper_summary": summary_result,
                "key_discoveries": discoveries_result,
                "methodology_analysis": methodology_result,
                "results_analysis": results_result,
                "quality_assessment": quality_result,
                "tool_used": "paper_analyzer_tool",
                "analysis_type": "detailed_comprehensive"
            }
            
            logger.info("Successfully generated detailed paper analysis")
            return detailed_analysis
            
        except Exception as e:
            logger.error(f"Detailed analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_used": "paper_analyzer_tool"
            }
    
    def _create_extraction_prompt(self, text_content: str, query: Optional[str], extract_level: str) -> str:
        """Create the extraction prompt for the LLM."""
        
        base_prompt = f"""
You are a research analyst tasked with extracting key information from academic papers. 
Analyze the following text and extract structured research data.

TEXT TO ANALYZE:
{text_content[:8000]}  # Limit to avoid token limits

EXTRACTION LEVEL: {extract_level}

Please extract the following information in JSON format:
"""
        
        if extract_level == "basic":
            extraction_fields = """
{
  "title": "Paper title",
  "authors": ["Author 1", "Author 2"],
  "abstract": "Brief abstract",
  "methodology": "Research methodology used",
  "sample_size": 123,
  "main_results": "Key findings",
  "conclusions": "Main conclusions"
}
"""
        elif extract_level == "comprehensive":
            extraction_fields = """
{
  "title": "Paper title",
  "authors": ["Author 1", "Author 2"],
  "abstract": "Brief abstract",
  "methodology": "Research methodology used",
  "study_design": "Type of study design",
  "sample_size": 123,
  "participants": {
    "demographics": "Participant demographics",
    "inclusion_criteria": "Inclusion criteria",
    "exclusion_criteria": "Exclusion criteria"
  },
  "results": {
    "primary_outcomes": "Primary outcomes",
    "secondary_outcomes": "Secondary outcomes",
    "statistical_significance": "Statistical significance results"
  },
  "conclusions": "Main conclusions",
  "limitations": ["Limitation 1", "Limitation 2"],
  "keywords": ["keyword1", "keyword2"],
  "publication_year": 2023,
  "journal": "Journal name",
  "doi": "DOI if available"
}
"""
        else:  # detailed
            extraction_fields = """
{
  "title": "Paper title",
  "authors": ["Author 1", "Author 2"],
  "abstract": "Brief abstract",
  "methodology": "Research methodology used",
  "study_design": "Type of study design",
  "sample_size": 123,
  "participants": {
    "demographics": "Participant demographics",
    "inclusion_criteria": "Inclusion criteria",
    "exclusion_criteria": "Exclusion criteria",
    "recruitment_method": "How participants were recruited"
  },
  "results": {
    "primary_outcomes": "Primary outcomes",
    "secondary_outcomes": "Secondary outcomes",
    "statistical_significance": "Statistical significance results",
    "effect_sizes": "Effect sizes reported",
    "confidence_intervals": "Confidence intervals",
    "p_values": "P-values reported"
  },
  "conclusions": "Main conclusions",
  "limitations": ["Limitation 1", "Limitation 2"],
  "keywords": ["keyword1", "keyword2"],
  "publication_year": 2023,
  "journal": "Journal name",
  "doi": "DOI if available",
  "research_questions": ["Research question 1", "Research question 2"],
  "hypotheses": ["Hypothesis 1", "Hypothesis 2"],
  "statistical_tests": ["Test 1", "Test 2"],
  "effect_direction": "Direction of effects",
  "clinical_significance": "Clinical significance",
  "practical_implications": "Practical implications",
  "future_research": ["Future research direction 1", "Future research direction 2"]
}
"""
        
        if query:
            base_prompt += f"\nSPECIFIC QUERY: {query}\n"
            base_prompt += "Focus on answering this specific query while extracting the requested information.\n"
        
        base_prompt += f"""
{extraction_fields}

IMPORTANT INSTRUCTIONS:
1. Extract only information that is explicitly stated in the text
2. If information is not available, use null for that field
3. For numbers (sample_size, publication_year), use actual numbers, not strings
4. For lists (authors, keywords, limitations), use proper JSON arrays
5. Be precise and accurate in your extraction
6. If the text is incomplete or unclear, note this in the relevant fields
7. Return ONLY valid JSON, no additional text or explanations

Please analyze the text and return the extracted data in the exact JSON format specified above.
"""
        
        return base_prompt
    
    def _parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """Parse the LLM response and extract structured data."""
        try:
            # Try to find JSON in the response
            import re
            
            # Look for JSON pattern in the response
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # If no JSON found, return the raw response in a structured format
                return {
                    "raw_analysis": llm_response,
                    "parsing_error": "Could not extract structured JSON from LLM response"
                }
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from LLM response: {str(e)}")
            return {
                "raw_analysis": llm_response,
                "parsing_error": f"JSON parsing failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return {
                "raw_analysis": llm_response,
                "parsing_error": f"Parsing error: {str(e)}"
            }
    
    def analyze_paper_sections(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze specific sections of a paper for targeted extraction.
        
        Args:
            sections: List of paper sections with 'name' and 'text' fields
            
        Returns:
            Dict containing section-specific analysis
        """
        try:
            section_analyses = {}
            
            for section in sections:
                section_name = section.get('name', 'unknown')
                section_text = section.get('text', '')
                
                if not section_text.strip():
                    continue
                
                # Create section-specific prompt
                prompt = f"""
Analyze the following section from a research paper and extract key information.

SECTION: {section_name}
CONTENT: {section_text[:2000]}

Extract relevant information for this section in JSON format:
{{
  "section_type": "{section_name}",
  "key_points": ["Point 1", "Point 2"],
  "important_data": "Important data or findings",
  "statistics": "Any statistics mentioned",
  "methodology_notes": "Methodology details if applicable",
  "results_notes": "Results details if applicable"
}}
"""
                
                llm_response = self._get_openai_client().generate_completion(
                    prompt=prompt,
                    model="gpt-3.5-turbo",
                    max_tokens=1000
                )
                
                if llm_response:
                    try:
                        section_analysis = json.loads(llm_response)
                        section_analyses[section_name] = section_analysis
                    except json.JSONDecodeError:
                        section_analyses[section_name] = {
                            "raw_analysis": llm_response,
                            "parsing_error": "Could not parse JSON"
                        }
            
            return {
                "success": True,
                "section_analyses": section_analyses,
                "tool_used": "paper_analyzer_tool"
            }
            
        except Exception as e:
            logger.error(f"Section analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_used": "paper_analyzer_tool"
            }
    
    def _generate_paper_summary(self, text_content: str, query: Optional[str]) -> Dict[str, Any]:
        """Generate comprehensive paper summary."""
        try:
            prompt = f"""
You are an expert research analyst. Create a comprehensive summary of this research paper.

PAPER CONTENT:
{text_content[:6000]}

Please provide a detailed summary in JSON format:
{{
  "executive_summary": "A 2-3 sentence executive summary of the paper's main contribution",
  "key_findings": [
    "Key finding 1",
    "Key finding 2",
    "Key finding 3"
  ],
  "methodology_summary": "Brief summary of the research methodology and approach",
  "results_summary": "Summary of the main results and outcomes",
  "implications": "What this research means for the field and practice",
  "significance": "Why this research is important and novel",
  "contribution_to_field": "How this research advances the field"
}}

Focus on clarity, accuracy, and highlighting the most important aspects.
"""
            
            if query:
                prompt += f"\nSPECIFIC FOCUS: {query}\n"
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-3.5-turbo",
                max_tokens=1500
            )
            
            if llm_response:
                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    return {"raw_summary": llm_response, "parsing_error": "Could not parse JSON"}
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return {"error": str(e)}
    
    def _generate_key_discoveries(self, text_content: str, query: Optional[str]) -> Dict[str, Any]:
        """Generate key discoveries with significance analysis."""
        try:
            prompt = f"""
You are an expert research analyst. Identify and analyze the key discoveries in this research paper.

PAPER CONTENT:
{text_content[:6000]}

Extract the most important discoveries in JSON format:
{{
  "key_discoveries": [
    {{
      "discovery": "Description of the discovery",
      "significance": "Why this discovery is important",
      "evidence": "What evidence supports this discovery",
      "implications": "What this discovery means for the field",
      "confidence_level": "High/Medium/Low based on evidence quality"
    }}
  ],
  "novel_contributions": [
    "Novel contribution 1",
    "Novel contribution 2"
  ],
  "breakthrough_findings": [
    "Breakthrough finding 1",
    "Breakthrough finding 2"
  ]
}}

Focus on discoveries that are novel, significant, or have important implications.
"""
            
            if query:
                prompt += f"\nSPECIFIC FOCUS: {query}\n"
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-3.5-turbo",
                max_tokens=1500
            )
            
            if llm_response:
                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    return {"raw_discoveries": llm_response, "parsing_error": "Could not parse JSON"}
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Key discoveries generation failed: {str(e)}")
            return {"error": str(e)}
    
    def _generate_methodology_analysis(self, text_content: str) -> Dict[str, Any]:
        """Generate detailed methodology analysis."""
        try:
            prompt = f"""
You are an expert research analyst. Analyze the methodology of this research paper.

PAPER CONTENT:
{text_content[:6000]}

Provide methodology analysis in JSON format:
{{
  "study_design": "Type of study design and rationale",
  "sample_characteristics": "Sample size, demographics, and selection criteria",
  "data_collection": "How data was collected and instruments used",
  "analysis_methods": "Statistical or analytical methods used",
  "validity_measures": "Measures taken to ensure validity and reliability",
  "ethical_considerations": "Ethical approvals and considerations",
  "limitations": "Methodological limitations identified",
  "strengths": "Methodological strengths",
  "quality_rating": "Overall methodology quality (High/Medium/Low)"
}}
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-3.5-turbo",
                max_tokens=1200
            )
            
            if llm_response:
                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    return {"raw_methodology": llm_response, "parsing_error": "Could not parse JSON"}
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Methodology analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def _generate_results_analysis(self, text_content: str) -> Dict[str, Any]:
        """Generate detailed results analysis."""
        try:
            prompt = f"""
You are an expert research analyst. Analyze the results of this research paper.

PAPER CONTENT:
{text_content[:6000]}

Provide results analysis in JSON format:
{{
  "primary_outcomes": "Main results and primary outcomes",
  "secondary_outcomes": "Secondary results and outcomes",
  "statistical_significance": "Statistical significance of key findings",
  "effect_sizes": "Effect sizes and their interpretation",
  "confidence_intervals": "Confidence intervals and their meaning",
  "clinical_significance": "Clinical or practical significance",
  "unexpected_findings": "Any unexpected or surprising results",
  "negative_findings": "Negative results or non-significant findings",
  "results_interpretation": "How to interpret these results"
}}
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-3.5-turbo",
                max_tokens=1200
            )
            
            if llm_response:
                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    return {"raw_results": llm_response, "parsing_error": "Could not parse JSON"}
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Results analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def _generate_quality_assessment(self, text_content: str) -> Dict[str, Any]:
        """Generate quality assessment of the paper."""
        try:
            prompt = f"""
You are an expert research analyst. Assess the quality of this research paper.

PAPER CONTENT:
{text_content[:6000]}

Provide quality assessment in JSON format:
{{
  "overall_quality": "High/Medium/Low with justification",
  "strengths": [
    "Strength 1",
    "Strength 2"
  ],
  "weaknesses": [
    "Weakness 1",
    "Weakness 2"
  ],
  "research_gaps": [
    "Gap 1",
    "Gap 2"
  ],
  "future_directions": [
    "Future direction 1",
    "Future direction 2"
  ],
  "reproducibility": "Assessment of study reproducibility",
  "generalizability": "Assessment of result generalizability",
  "bias_assessment": "Assessment of potential biases",
  "recommendations": "Recommendations for improvement"
}}
"""
            
            llm_response = self._get_openai_client().generate_completion(
                prompt=prompt,
                model="gpt-3.5-turbo",
                max_tokens=1200
            )
            
            if llm_response:
                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    return {"raw_quality": llm_response, "parsing_error": "Could not parse JSON"}
            else:
                return {"error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Quality assessment failed: {str(e)}")
            return {"error": str(e)}
