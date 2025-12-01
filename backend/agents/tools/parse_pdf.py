# parse_pdf.py
# Tool: ParsePDFTool — PDF parsing for agentic paper analysis pipelines (QualiLens-ready)

from __future__ import annotations

import io
import os
import re
import json
import math
import hashlib
import logging
import multiprocessing
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

# Third-party (all optional except at least one extractor)
# Preferred:
#   pip install pymupdf
# Fallbacks:
#   pip install pdfminer.six pypdf
try:
    import fitz  # PyMuPDF
    _HAVE_MUPDF = True
except Exception:
    _HAVE_MUPDF = False

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
    _HAVE_PDFMINER = True
except Exception:
    _HAVE_PDFMINER = False

try:
    from PyPDF2 import PdfReader
    _HAVE_PYPDF2 = True
except Exception:
    _HAVE_PYPDF2 = False

# OCR dependencies (optional)
try:
    import pytesseract
    from PIL import Image
    _HAVE_TESSERACT = True
except Exception:
    _HAVE_TESSERACT = False
    pytesseract = None  # type: ignore

# Local base class
try:
    from .base_tool import BaseTool, ToolMetadata
except Exception:
    # Minimal stub for standalone usage/tests if base_tool isn't importable
    class BaseTool:
        name: str = ""
        description: str = ""
        def run(self, *args, **kwargs):  # type: ignore
            raise NotImplementedError
    
    class ToolMetadata:
        def __init__(self, name: str, description: str, parameters: Dict[str, Any], examples: List[str], category: str = "general"):
            self.name = name
            self.description = description
            self.parameters = parameters
            self.examples = examples
            self.category = category

logger = logging.getLogger(__name__)


# -----------------------------
# Data structures
# -----------------------------

@dataclass
class PDFMetadata:
    title: Optional[str]
    authors: Optional[str]
    subject: Optional[str]
    creator: Optional[str]
    producer: Optional[str]
    creation_date: Optional[str]
    modification_date: Optional[str]
    file_size_bytes: Optional[int]
    sha256: Optional[str]


@dataclass
class Section:
    name: str
    start_char: int
    end_char: int
    text: str


# -----------------------------
# Utility functions
# -----------------------------

SECTION_PATTERNS = [
    # Core academic sections
    r"^\s*abstract\s*$",
    r"^\s*background\s*$",
    r"^\s*introduction\s*$",

    # Methodology sections (expanded for better detection)
    r"^\s*methods?\s*$",
    r"^\s*methodology\s*$",
    r"^\s*materials\s+and\s+methods\s*$",
    r"^\s*methods\s+and\s+materials\s*$",
    r"^\s*study\s+design\s*$",
    r"^\s*experimental\s+(design|procedure|methods?)\s*$",
    r"^\s*research\s+(design|methods?|methodology)\s*$",
    r"^\s*participants\s+(and\s+methods?)?\s*$",
    r"^\s*subjects\s+(and\s+methods?)?\s*$",
    r"^\s*procedure[s]?\s*$",
    r"^\s*data\s+collection\s*$",
    r"^\s*sampling\s+(methods?|procedure)?\s*$",

    # Results and analysis
    r"^\s*results?\s*$",
    r"^\s*findings?\s*$",
    r"^\s*analysis\s*$",
    r"^\s*statistical\s+analysis\s*$",

    # Discussion sections
    r"^\s*discussion\s*$",
    r"^\s*results\s+and\s+discussion\s*$",
    r"^\s*interpretation\s*$",

    # Other sections
    r"^\s*limitations?\s*$",
    r"^\s*conclusion[s]?\s*$",
    r"^\s*implications?\s*$",
    r"^\s*recommenda­tions?\s*$",
    r"^\s*acknowledg(e)?ments?\s*$",
    r"^\s*references?\s*$",
    r"^\s*bibliography\s*$",
    r"^\s*supplementary\s+(materials?|information|data)\s*$",
    r"^\s*appendix\s*$",
    r"^\s*appendices\s*$",
]

SECTION_REGEX = re.compile(
    "(" + "|".join(SECTION_PATTERNS) + ")", flags=re.IGNORECASE | re.MULTILINE
)

DOI_REGEX = re.compile(
    r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b", flags=re.IGNORECASE
)

URL_REGEX = re.compile(
    r"\bhttps?://[^\s)]+", flags=re.IGNORECASE
)

FIG_TAB_REGEX = re.compile(
    r"^\s*(figure|fig\.|table)\s*\d+[:.)]?", flags=re.IGNORECASE | re.MULTILINE
)

# Citation/reference extraction patterns
REFERENCE_SECTION_PATTERNS = [
    r"^\s*references?\s*$",
    r"^\s*bibliography\s*$",
    r"^\s*works?\s+cited\s*$",
    r"^\s*literature\s+cited\s*$",
    r"^\s*citations?\s*$",
]

REFERENCE_SECTION_REGEX = re.compile(
    "(" + "|".join(REFERENCE_SECTION_PATTERNS) + ")", flags=re.IGNORECASE | re.MULTILINE
)


def _read_file_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _normalize_text(text: str) -> str:
    """
    Enhanced text normalization for academic papers.
    Handles hyphenation, ligatures, special characters, and preserves important structure.
    """
    # 1) Fix common ligatures (often mangled in PDFs)
    ligature_map = {
        "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl",
        "\ufb05": "ft", "\ufb06": "st"
    }
    for lig, replacement in ligature_map.items():
        text = text.replace(lig, replacement)

    # 2) Merge hyphenated line breaks: "exam-\nple" -> "example"
    # Be careful to only merge real word breaks, not list items or math
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)

    # 3) Replace soft hyphen U+00AD and other invisible characters
    text = text.replace("\u00ad", "")  # Soft hyphen
    text = text.replace("\u200b", "")  # Zero-width space
    text = text.replace("\u200c", "")  # Zero-width non-joiner
    text = text.replace("\u200d", "")  # Zero-width joiner
    text = text.replace("\ufeff", "")  # Zero-width no-break space / BOM

    # 4) Fix common PDF extraction issues
    # Remove excessive spaces within lines (but preserve paragraph breaks)
    text = re.sub(r"([^\n])[ \t]{2,}", r"\1 ", text)

    # 5) Normalize various unicode dashes and quotes
    text = text.replace("\u2013", "-")  # en dash
    text = text.replace("\u2014", "-")  # em dash
    text = text.replace("\u2018", "'")  # left single quote
    text = text.replace("\u2019", "'")  # right single quote
    text = text.replace("\u201c", '"')  # left double quote
    text = text.replace("\u201d", '"')  # right double quote

    # 6) Normalize Windows and Mac newlines to Unix
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 7) Remove trailing/leading spaces on lines
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)

    # 8) Reduce excessive newlines (more than 3 in a row) to 2 (paragraph break)
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    # 9) Fix common OCR errors in academic text
    # Fix "et al ." -> "et al."
    text = re.sub(r"\bet\s+al\s*\.\s+", "et al. ", text)
    # Fix "e .g ." -> "e.g."
    text = re.sub(r"\be\s*\.\s*g\s*\.\s*", "e.g. ", text)
    # Fix "i .e ." -> "i.e."
    text = re.sub(r"\bi\s*\.\s*e\s*\.\s*", "i.e. ", text)

    return text.strip()


def _chunk_text(text: str, target_chars: int = 4000, overlap: int = 200) -> List[str]:
    """
    Enhanced, semantic-aware chunker that tries to preserve section boundaries and paragraph structure.
    target_chars≈4000 keeps chunks safely under ~1500-2000 tokens for most LLMs.
    """
    chunks: List[str] = []
    i = 0
    n = len(text)
    if n == 0:
        return chunks

    while i < n:
        end = min(n, i + target_chars)

        # Try to find a good break point (paragraph or sentence boundary)
        if end < n:
            # Look for paragraph break (double newline) within last 500 chars
            search_start = max(i + target_chars - 500, i)
            paragraph_break = text.rfind("\n\n", search_start, end)
            if paragraph_break > i:
                end = paragraph_break + 2  # Include the newlines

            # If no paragraph break, try sentence boundary
            elif end < n:
                # Look for sentence endings: . ! ? followed by space or newline
                search_start = max(i + target_chars - 300, i)
                for punct in [". ", ".\n", "! ", "!\n", "? ", "?\n"]:
                    last_sent = text.rfind(punct, search_start, end)
                    if last_sent > i:
                        end = last_sent + len(punct)
                        break

        chunk = text[i:end].strip()
        if chunk:  # Only add non-empty chunks
            chunks.append(chunk)

        if end >= n:
            break

        # Smart overlap: try to start next chunk at a natural boundary
        overlap_start = max(end - overlap, i + 1)
        # Look for paragraph or sentence start in overlap region
        next_para = text.find("\n\n", overlap_start, end)
        if next_para > 0:
            i = next_para + 2
        else:
            i = overlap_start

    return chunks


def _split_sections(full_text: str) -> List[Section]:
    """
    Enhanced section detection with better handling of methodology sections.
    Looks for common scholarly headings and builds sections from heading to next heading.
    """
    sections: List[Section] = []
    matches = list(SECTION_REGEX.finditer(full_text))
    if not matches:
        # Return everything as a single "Body" section
        return [Section(name="Body", start_char=0, end_char=len(full_text), text=full_text)]

    # Prepend synthetic start if text before first heading is meaningful
    first_start = matches[0].start()
    if first_start > 50:
        sections.append(Section(name="Preamble", start_char=0, end_char=first_start, text=full_text[:first_start]))

    for idx, m in enumerate(matches):
        name = m.group(0).strip().title()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(full_text)
        body = full_text[start:end].strip()

        # Normalize methodology section names for consistency
        name_lower = name.lower()
        if any(keyword in name_lower for keyword in ["method", "procedure", "design", "material", "participant", "subject", "sampling", "data collection"]):
            # Mark as methodology section
            if "methodology" not in name_lower and "methods" not in name_lower:
                name = f"{name} (Methodology)"

        sections.append(Section(name=name, start_char=start, end_char=end, text=body))
    return sections


def _extract_methodology_context(sections: List[Section], full_text: str) -> str:
    """
    Extract and combine all methodology-related sections for better LLM analysis.
    Returns a focused text snippet containing methodology information.
    """
    methodology_text_parts = []

    for section in sections:
        section_name_lower = section.name.lower()
        # Check if this is a methodology-related section
        if any(keyword in section_name_lower for keyword in
               ["method", "procedure", "design", "material", "participant",
                "subject", "sampling", "data collection", "experimental"]):
            methodology_text_parts.append(f"\n\n=== {section.name} ===\n{section.text}")

    if methodology_text_parts:
        return "".join(methodology_text_parts)

    # Fallback: try to find methodology content by keywords if no section found
    # Look for paragraphs containing methodology indicators
    paragraphs = full_text.split("\n\n")
    methodology_paragraphs = []

    for para in paragraphs:
        para_lower = para.lower()
        if len(para) > 100 and any(keyword in para_lower for keyword in
                                   ["we conducted", "we used", "participants were", "subjects were",
                                    "data were collected", "study design", "sample size", "randomized",
                                    "we recruited", "inclusion criteria", "exclusion criteria"]):
            methodology_paragraphs.append(para)

    if methodology_paragraphs:
        return "\n\n".join(methodology_paragraphs[:10])  # Limit to first 10 paragraphs

    return ""


def _extract_fig_table_cues(text: str) -> List[str]:
    # Return the lines that look like Figure/Table captions
    cues = []
    for m in FIG_TAB_REGEX.finditer(text):
        # capture a few words after the match line for context
        start = m.start()
        line_end = text.find("\n", start)
        if line_end == -1:
            line_end = min(start + 200, len(text))
        snippet_end = min(line_end + 200, len(text))
        cues.append(text[start:snippet_end].strip())
    return cues


def _extract_references_section(full_text: str, sections: List[Section]) -> Optional[str]:
    """
    Extract the references/bibliography section from the text.
    Returns the text content of the references section, or None if not found.
    """
    # First, try to find it in sections (most reliable)
    for section in sections:
        section_name_lower = section.name.lower()
        if any(keyword in section_name_lower for keyword in ["reference", "bibliography", "works cited", "literature cited"]):
            # Additional validation: references section should have some citation-like content
            section_text = section.text.strip()
            if len(section_text) > 50:
                # Check if it contains citation indicators
                has_citations = (
                    DOI_REGEX.search(section_text) or
                    re.search(r'\b(19|20)\d{2}\b', section_text) or  # Years
                    re.search(r'\b(vol\.|volume|journal|published)\b', section_text, re.IGNORECASE) or
                    re.search(r'[A-Z][a-z]+,\s+[A-Z]\.', section_text)  # Author patterns
                )
                if has_citations:
                    return section_text
    
    # If not found in sections, try direct regex search
    ref_match = REFERENCE_SECTION_REGEX.search(full_text)
    if ref_match:
        # Find the start of the references section
        start_pos = ref_match.end()
        
        # Look for the next major section or end of document
        # Common patterns: next section heading, appendix, or end of text
        next_section_patterns = [
            r"\n\s*(?:appendix|supplementary|acknowledgment|acknowledgement)\s*\n",
            r"\n\s*(?:figure|table)\s+\d+",
            r"\n\s*(?:proof|lemma|theorem|corollary)\s+",  # Mathematical sections
        ]
        
        end_pos = len(full_text)
        for pattern in next_section_patterns:
            next_match = re.search(pattern, full_text[start_pos:], re.IGNORECASE | re.MULTILINE)
            if next_match:
                end_pos = min(end_pos, start_pos + next_match.start())
        
        references_text = full_text[start_pos:end_pos].strip()
        # Validate that it looks like a references section
        if len(references_text) > 50:
            # Check if it contains citation indicators
            has_citations = (
                DOI_REGEX.search(references_text) or
                re.search(r'\b(19|20)\d{2}\b', references_text) or  # Years
                re.search(r'\b(vol\.|volume|journal|published)\b', references_text, re.IGNORECASE) or
                re.search(r'[A-Z][a-z]+,\s+[A-Z]\.', references_text)  # Author patterns
            )
            if has_citations:
                return references_text
    
    return None


def _parse_citation(citation_text: str, citation_num: int) -> Dict[str, Any]:
    """
    Parse a single citation entry into structured format.
    Handles multiple citation styles: APA, MLA, Chicago, Vancouver, IEEE, etc.
    
    Returns a dict with parsed fields: authors, title, journal, year, doi, etc.
    """
    citation_text = citation_text.strip()
    if not citation_text or len(citation_text) < 10:
        return {"raw": citation_text, "citation_number": citation_num}
    
    parsed = {
        "raw": citation_text,
        "citation_number": citation_num,
        "authors": [],
        "title": None,
        "journal": None,
        "book_title": None,
        "publisher": None,
        "year": None,
        "volume": None,
        "issue": None,
        "pages": None,
        "doi": None,
        "url": None,
        "citation_style": None,
    }
    
    # Extract DOI
    doi_match = DOI_REGEX.search(citation_text)
    if doi_match:
        parsed["doi"] = doi_match.group(1)
    
    # Extract URL
    url_match = URL_REGEX.search(citation_text)
    if url_match:
        parsed["url"] = url_match.group(0)
    
    # Extract year (4-digit year, typically between 1900-2100)
    year_patterns = [
        r"\b(19|20)\d{2}\b",  # 1900-2099
        r"\((\d{4})\)",  # (2023)
        r"\[(\d{4})\]",  # [2023]
    ]
    for pattern in year_patterns:
        year_match = re.search(pattern, citation_text)
        if year_match:
            year_str = year_match.group(1) if year_match.lastindex else year_match.group(0)
            try:
                year = int(year_str)
                if 1900 <= year <= 2100:
                    parsed["year"] = year
                    break
            except ValueError:
                continue
    
    # Try to identify citation style and parse accordingly
    
    # APA Style: Author, A. A., & Author, B. B. (Year). Title. Journal, Volume(Issue), Pages. DOI
    if re.search(r"\((\d{4})\)\.\s+[A-Z]", citation_text) or re.search(r"\.\s+[A-Z][a-z]+,\s+\d+", citation_text):
        parsed["citation_style"] = "APA"
        # Extract authors (before year)
        if parsed["year"]:
            year_pos = citation_text.find(str(parsed["year"]))
            authors_text = citation_text[:year_pos].strip()
            # Split by comma and "&" or "and"
            authors = re.split(r",\s*(?:and|&)\s*|,\s*", authors_text)
            parsed["authors"] = [a.strip() for a in authors if a.strip() and len(a.strip()) > 2]
        
        # Extract journal (often after title, before volume)
        journal_match = re.search(r"\.\s+([A-Z][^,]+?),\s+(\d+)", citation_text)
        if journal_match:
            parsed["journal"] = journal_match.group(1).strip()
            parsed["volume"] = journal_match.group(2)
        
        # Extract pages (format: pp. 123-145 or 123-145)
        pages_match = re.search(r"(?:pp\.\s*)?(\d+)\s*[-–]\s*(\d+)", citation_text)
        if pages_match:
            parsed["pages"] = f"{pages_match.group(1)}-{pages_match.group(2)}"
    
    # Vancouver/Numeric Style: Author. Title. Journal. Year;Volume(Issue):Pages.
    elif re.search(r"\.\s+\d{4}\s*;\s*\d+", citation_text) or re.search(r"\.\s+\d{4}\s*:\s*\d+", citation_text):
        parsed["citation_style"] = "Vancouver"
        # Extract authors (first sentence before period)
        first_period = citation_text.find(".")
        if first_period > 0:
            authors_text = citation_text[:first_period].strip()
            parsed["authors"] = [authors_text] if authors_text else []
        
        # Extract journal (between title and year)
        if parsed["year"]:
            year_str = str(parsed["year"])
            year_pos = citation_text.find(year_str)
            if year_pos > 0:
                # Look backwards for journal name
                before_year = citation_text[:year_pos].strip()
                # Find last period before year
                last_period = before_year.rfind(".")
                if last_period > 0:
                    journal_candidate = before_year[last_period+1:].strip()
                    if len(journal_candidate) > 3:
                        parsed["journal"] = journal_candidate
        
        # Extract volume and pages (format: 2023;15(3):123-145)
        volume_pages_match = re.search(rf"{parsed['year']}\s*;\s*(\d+)(?:\((\d+)\))?\s*:\s*(\d+[-–]?\d*)", citation_text)
        if volume_pages_match:
            parsed["volume"] = volume_pages_match.group(1)
            if volume_pages_match.group(2):
                parsed["issue"] = volume_pages_match.group(2)
            parsed["pages"] = volume_pages_match.group(3)
    
    # IEEE Style: A. Author, "Title," Journal, vol. X, no. Y, pp. Z, Year.
    elif re.search(r'"[^"]+",\s*[A-Z]', citation_text) and re.search(r"vol\.\s*\d+", citation_text, re.IGNORECASE):
        parsed["citation_style"] = "IEEE"
        # Extract title (in quotes)
        title_match = re.search(r'"([^"]+)"', citation_text)
        if title_match:
            parsed["title"] = title_match.group(1)
        
        # Extract authors (before title)
        if title_match:
            authors_text = citation_text[:title_match.start()].strip().rstrip(",")
            authors = re.split(r",\s*", authors_text)
            parsed["authors"] = [a.strip() for a in authors if a.strip()]
        
        # Extract volume
        vol_match = re.search(r"vol\.\s*(\d+)", citation_text, re.IGNORECASE)
        if vol_match:
            parsed["volume"] = vol_match.group(1)
        
        # Extract issue
        issue_match = re.search(r"no\.\s*(\d+)", citation_text, re.IGNORECASE)
        if issue_match:
            parsed["issue"] = issue_match.group(1)
        
        # Extract pages
        pages_match = re.search(r"pp\.\s*(\d+[-–]?\d*)", citation_text, re.IGNORECASE)
        if pages_match:
            parsed["pages"] = pages_match.group(1)
    
    # MLA Style: Author. "Title." Journal, vol. X, no. Y, Year, pp. Z.
    elif re.search(r'"[^"]+",\s*[A-Z]', citation_text) and re.search(r"vol\.\s*\d+", citation_text, re.IGNORECASE):
        # Similar to IEEE but different ordering
        if not parsed["citation_style"]:
            parsed["citation_style"] = "MLA"
            title_match = re.search(r'"([^"]+)"', citation_text)
            if title_match:
                parsed["title"] = title_match.group(1)
    
    # Chicago Style: Author. "Title." Journal Volume, no. Issue (Year): Pages.
    elif re.search(r"\(\d{4}\)\s*:\s*\d+", citation_text):
        parsed["citation_style"] = "Chicago"
        # Extract authors (first part before period)
        first_period = citation_text.find(".")
        if first_period > 0:
            authors_text = citation_text[:first_period].strip()
            parsed["authors"] = [authors_text] if authors_text else []
    
    # Generic fallback: try to extract common elements
    if not parsed["citation_style"]:
        parsed["citation_style"] = "Unknown"
        
        # Try to extract title (often in quotes or italics, or first capitalized phrase)
        title_match = re.search(r'"([^"]+)"', citation_text)
        if title_match:
            parsed["title"] = title_match.group(1)
        else:
            # Look for capitalized phrase that might be a title
            title_candidate = re.search(r"\.\s+([A-Z][^.]{10,80})\.", citation_text)
            if title_candidate:
                parsed["title"] = title_candidate.group(1).strip()
        
        # Extract authors (first part, often ends with comma or period)
        if not parsed["authors"]:
            # Look for name patterns: "Last, First" or "First Last"
            author_match = re.search(r"^([A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-z]+)*)", citation_text)
            if author_match:
                parsed["authors"] = [author_match.group(1).strip()]
        
        # Extract journal (often capitalized, before volume/year)
        if not parsed["journal"]:
            journal_match = re.search(r"\.\s+([A-Z][A-Za-z\s&]+?)(?:,\s*(?:vol\.|no\.|\d{4}))", citation_text)
            if journal_match:
                journal_candidate = journal_match.group(1).strip()
                if len(journal_candidate) > 3 and len(journal_candidate) < 100:
                    parsed["journal"] = journal_candidate
    
    # Extract volume and issue if not already extracted
    if not parsed["volume"]:
        vol_match = re.search(r"(?:vol\.|volume|vol)\s*[:\s]*(\d+)", citation_text, re.IGNORECASE)
        if vol_match:
            parsed["volume"] = vol_match.group(1)
    
    if not parsed["issue"]:
        issue_match = re.search(r"(?:no\.|number|issue|iss)\s*[:\s]*(\d+)", citation_text, re.IGNORECASE)
        if issue_match:
            parsed["issue"] = issue_match.group(1)
    
    if not parsed["pages"]:
        pages_match = re.search(r"(?:pp?\.|pages?)\s*[:\s]*(\d+[-–]?\d*)", citation_text, re.IGNORECASE)
        if pages_match:
            parsed["pages"] = pages_match.group(1)
    
    return parsed


def _is_valid_citation(citation_text: str) -> bool:
    """
    Validate if a text snippet is likely a real citation.
    Filters out proof text, mathematical expressions, and other non-citation content.
    
    Returns True if the text appears to be a valid citation.
    """
    if not citation_text or len(citation_text.strip()) < 20:
        return False
    
    text_lower = citation_text.lower()
    text_stripped = citation_text.strip()
    
    # Filter out proof language and mathematical content
    proof_indicators = [
        r'\bby\s+induction\b',
        r'\bthe\s+proof\s+is\b',
        r'\bwe\s+prove\b',
        r'\bproof\s+by\b',
        r'\blet\s+\w+\s+be\b',
        r'\bthus\s+\w+',
        r'\bassume\s+that\b',
        r'\bsuppose\s+that\b',
        r'\bit\s+follows\s+that\b',
        r'\bwe\s+show\s+that\b',
        r'\bwe\s+have\b',
        r'\bconsider\s+the\b',
    ]
    
    for pattern in proof_indicators:
        if re.search(pattern, text_lower):
            return False
    
    # Filter out mathematical expressions (Greek letters, subscripts, mathematical operators)
    # Citations rarely contain complex mathematical notation
    greek_letters = r'[αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ]'
    if re.search(greek_letters, citation_text):
        # Allow if it's part of a DOI or URL, but not if it's standalone math
        if not (DOI_REGEX.search(citation_text) or URL_REGEX.search(citation_text)):
            # Check if it's mostly mathematical (high ratio of Greek/math symbols)
            math_chars = len(re.findall(greek_letters + r'|[\^_\{\}\(\)\[\]=\+\-×÷]', citation_text))
            if math_chars > len(citation_text) * 0.1:  # More than 10% math symbols
                return False
    
    # Filter out text that starts with common proof words
    proof_starters = ['let ', 'we ', 'thus ', 'therefore ', 'hence ', 'assume ', 'suppose ']
    first_words = text_stripped[:20].lower()
    if any(first_words.startswith(starter) for starter in proof_starters):
        # But allow if it has citation indicators
        has_citation_indicators = (
            DOI_REGEX.search(citation_text) or
            URL_REGEX.search(citation_text) or
            re.search(r'\b(19|20)\d{2}\b', citation_text) or  # Year
            re.search(r'\b(vol\.|volume|journal|published|press|university|edition)\b', text_lower)
        )
        if not has_citation_indicators:
            return False
    
    # Citations should have at least one of these indicators:
    citation_indicators = [
        DOI_REGEX.search(citation_text),  # DOI
        URL_REGEX.search(citation_text),  # URL
        re.search(r'\b(19|20)\d{2}\b', citation_text),  # Year (1900-2099)
        re.search(r'\b(vol\.|volume|vol\.|no\.|number|issue|pp\.|pages?|journal|journal of|proceedings|conference|workshop|symposium)\b', text_lower),  # Publication indicators
        re.search(r'\b(published|press|university|publisher|edition|ed\.|editor|eds\.)\b', text_lower),  # Publisher indicators
        re.search(r'[A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+', citation_text),  # Author name pattern (e.g., "Smith, J. R.")
        re.search(r'[A-Z][a-z]+,\s+[A-Z]\.', citation_text),  # Author name pattern (e.g., "Smith, J.")
    ]
    
    # If it has at least one citation indicator, it's likely valid
    if any(citation_indicators):
        return True
    
    # If it's very short and has no indicators, it's probably not a citation
    if len(citation_text.strip()) < 50:
        return False
    
    # Check for author-like patterns (Last, First or First Last with initials)
    author_patterns = [
        r'^[A-Z][a-z]+,\s+[A-Z]\.',  # "Smith, J."
        r'^[A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+',  # "Smith J. R."
        r'^[A-Z][a-z]+\s+and\s+[A-Z][a-z]+',  # "Smith and Jones"
        r'^[A-Z][a-z]+,\s+[A-Z]\.\s+[A-Z]\.',  # "Smith, J. R."
    ]
    
    if any(re.match(pattern, text_stripped) for pattern in author_patterns):
        return True
    
    # If none of the above, it's probably not a citation
    return False


def _extract_citations(references_text: str) -> List[Dict[str, Any]]:
    """
    Extract individual citations from the references section.
    Handles various numbering formats and citation styles.
    Filters out non-citation text (proofs, mathematical expressions, etc.).
    
    Returns a list of parsed citation dictionaries.
    """
    if not references_text or len(references_text.strip()) < 20:
        return []
    
    citations = []
    
    # Split references by common patterns
    # Patterns for citation starts:
    # 1. Numbered: "1.", "1)", "[1]", "(1)"
    # 2. Bulleted: "-", "•", "*"
    # 3. Author-year: "Author, A. (2023)"
    
    # Try numbered format first (most common)
    numbered_pattern = re.compile(
        r"^\s*(?:\[?\d+\]?[.)]\s*|\(\d+\)\s*)", 
        re.MULTILINE | re.IGNORECASE
    )
    
    # Split by numbered citations
    parts = re.split(numbered_pattern, references_text)
    
    # If splitting by numbers didn't work well, try other methods
    if len(parts) < 3:
        # Try splitting by bullet points or line breaks with indentation
        # Look for lines that start with common citation patterns
        lines = references_text.split("\n")
        current_citation = []
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                if current_citation:
                    citation_text = " ".join(current_citation).strip()
                    if len(citation_text) > 20:
                        citations.append(_parse_citation(citation_text, len(citations) + 1))
                    current_citation = []
                continue
            
            # Check if this line starts a new citation
            is_new_citation = (
                re.match(r"^\d+[.)]\s*", line_stripped) or
                re.match(r"^\[?\d+\]?\s*", line_stripped) or
                re.match(r"^[•\-\*]\s*", line_stripped) or
                (current_citation and 
                 re.match(r"^[A-Z][a-z]+\s+[A-Z]", line_stripped) and
                 len(current_citation) > 0 and
                 len(" ".join(current_citation)) > 50)
            )
            
            if is_new_citation and current_citation:
                # Save previous citation
                citation_text = " ".join(current_citation).strip()
                if len(citation_text) > 20 and _is_valid_citation(citation_text):
                    citations.append(_parse_citation(citation_text, len(citations) + 1))
                current_citation = []
            
            current_citation.append(line_stripped)
        
        # Add last citation
        if current_citation:
            citation_text = " ".join(current_citation).strip()
            if len(citation_text) > 20 and _is_valid_citation(citation_text):
                citations.append(_parse_citation(citation_text, len(citations) + 1))
    else:
        # Process numbered citations
        citation_num = 1
        for part in parts[1:]:  # Skip first empty part before first number
            part = part.strip()
            if len(part) > 20 and _is_valid_citation(part):  # Validate before adding
                # Clean up: remove leading numbers/bullets if any
                part = re.sub(r"^\s*[•\-\*]\s*", "", part)
                citations.append(_parse_citation(part, citation_num))
                citation_num += 1
    
    # If we still don't have many citations, try a more aggressive approach
    # But be more careful with validation
    if len(citations) < 3:
        # Split by double newlines or periods followed by newlines (end of citation)
        # This is a fallback for poorly formatted references
        potential_citations = re.split(r"\n\s*\n|\.\s*\n(?=[A-Z])", references_text)
        if len(potential_citations) > len(citations):
            citations = []
            for i, cit_text in enumerate(potential_citations, 1):
                cit_text = cit_text.strip()
                # Validate before adding - be stricter in fallback mode
                if len(cit_text) > 30 and _is_valid_citation(cit_text):
                    citations.append(_parse_citation(cit_text, i))
    
    logger.info(f"Extracted {len(citations)} citations from references section")
    return citations


def _safe_int(x: Any) -> Optional[int]:
    try:
        return int(x)
    except Exception:
        return None


# -----------------------------
# OCR Functions
# -----------------------------

def _needs_ocr(pages: List[str], threshold_chars_per_page: int = 50) -> bool:
    """
    Determine if a PDF needs OCR processing.
    
    A PDF is considered to need OCR if:
    - The average number of characters per page is below the threshold
    - Or if most pages have very little text
    
    Args:
        pages: List of extracted text strings (one per page)
        threshold_chars_per_page: Minimum characters per page to consider text extraction successful
        
    Returns:
        True if OCR is needed, False otherwise
    """
    if not pages:
        return True
    
    # Calculate average characters per page
    total_chars = sum(len(page.strip()) for page in pages)
    avg_chars_per_page = total_chars / len(pages) if pages else 0
    
    # Count pages with very little text
    low_text_pages = sum(1 for page in pages if len(page.strip()) < threshold_chars_per_page)
    low_text_ratio = low_text_pages / len(pages) if pages else 1.0
    
    # Need OCR if average is too low OR if most pages have little text
    needs_ocr = avg_chars_per_page < threshold_chars_per_page or low_text_ratio > 0.7
    
    if needs_ocr:
        logger.info(
            f"[OCR] PDF appears to be scanned (avg_chars/page={avg_chars_per_page:.1f}, "
            f"low_text_ratio={low_text_ratio:.2f}). Tesseract OCR will be used."
        )
    
    return needs_ocr


def _ocr_page_with_confidence(
    page_image: Image.Image,
    word_confidence_threshold: int = 60,
    char_confidence_threshold: int = 70
) -> str:
    """
    Extract text from a single page image using Tesseract OCR with confidence filtering.
    
    Args:
        page_image: PIL Image object of the page
        word_confidence_threshold: Minimum word confidence (0-100), default 60
        char_confidence_threshold: Minimum character confidence (0-100), default 70
        
    Returns:
        Extracted text with low-confidence words/characters filtered out
    """
    if not _HAVE_TESSERACT:
        raise RuntimeError("Tesseract OCR is not available. Install pytesseract and tesseract-ocr.")
    
    # Use Tesseract 5.x with LSTM models (default in Tesseract 5.x)
    # Get detailed data including confidence scores
    logger.debug("[OCR] Processing page image with Tesseract (word_conf≥60%, char_conf≥70%)")
    ocr_data = pytesseract.image_to_data(
        page_image,
        output_type=pytesseract.Output.DICT,
        lang='eng',  # Default to English, can be extended for multilingual support
    )
    
    # Filter words and characters based on confidence thresholds
    filtered_text_parts = []
    current_line_words = []
    last_line_num = None
    
    num_words = len(ocr_data['text'])
    
    for i in range(num_words):
        word = ocr_data['text'][i].strip()
        word_conf = int(ocr_data['conf'][i]) if ocr_data['conf'][i] != -1 else 0
        line_num = ocr_data['line_num'][i]
        
        # Skip empty words
        if not word:
            continue
        
        # Check word-level confidence
        if word_conf < word_confidence_threshold:
            # Word confidence is too low, but we can still check individual characters
            # For now, skip low-confidence words entirely
            continue
        
        # Check character-level confidence (approximate)
        # Tesseract doesn't provide per-character confidence in standard output,
        # so we use word confidence as a proxy. For stricter filtering, we could
        # use Tesseract's TSV output format, but that's more complex.
        # The word confidence threshold already provides good filtering.
        
        # Handle line breaks
        if last_line_num is not None and line_num != last_line_num:
            if current_line_words:
                filtered_text_parts.append(' '.join(current_line_words))
                current_line_words = []
        
        current_line_words.append(word)
        last_line_num = line_num
    
    # Add remaining words
    if current_line_words:
        filtered_text_parts.append(' '.join(current_line_words))
    
    result_text = '\n'.join(filtered_text_parts)
    
    # Additional character-level filtering using regex to remove obvious OCR errors
    # This is a heuristic approach since we don't have per-character confidence
    # Remove words that are mostly non-alphanumeric (likely OCR artifacts)
    words = result_text.split()
    filtered_words = []
    for word in words:
        # Keep words that have at least 50% alphanumeric characters
        alnum_ratio = sum(1 for c in word if c.isalnum()) / len(word) if word else 0
        if alnum_ratio >= 0.5 or len(word) <= 2:  # Keep short words (likely valid)
            filtered_words.append(word)
    
    result_text = ' '.join(filtered_words)
    
    return result_text


def _ocr_single_page(args: Tuple[str, int, Dict[str, Any]]) -> Tuple[int, str]:
    """
    Process a single page for OCR (used in parallel processing).
    
    Args:
        args: Tuple of (pdf_path, page_num, page_info)
            - pdf_path: Path to PDF file
            - page_num: Page number (0-indexed)
            - page_info: Dict with page metadata (optional)
            
    Returns:
        Tuple of (page_num, extracted_text)
    """
    pdf_path, page_num, page_info = args
    
    try:
        # Open PDF and get page
        if _HAVE_MUPDF:
            doc = fitz.open(pdf_path)
            page = doc.load_page(page_num)
            
            # Convert page to image (300 DPI for good OCR quality)
            logger.debug(f"[OCR] Converting page {page_num + 1} to image (300 DPI)")
            mat = fitz.Matrix(300/72, 300/72)  # 300 DPI scaling
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            page_image = Image.open(io.BytesIO(img_data))
            
            doc.close()
        else:
            # Fallback: try pdf2image if available, otherwise skip
            logger.warning(f"[OCR] PyMuPDF not available for OCR page {page_num + 1}, skipping")
            return (page_num, "")
        
        # Perform OCR with confidence filtering
        logger.debug(f"[OCR] Running Tesseract OCR on page {page_num + 1}")
        text = _ocr_page_with_confidence(page_image)
        char_count = len(text.strip())
        logger.debug(f"[OCR] Page {page_num + 1} OCR complete: {char_count} characters extracted")
        
        return (page_num, text)
        
    except Exception as e:
        logger.error(f"[OCR] Error during OCR for page {page_num + 1}: {e}")
        return (page_num, "")


def _extract_with_ocr(
    path: str,
    num_cores: Optional[int] = None
) -> Tuple[List[str], Dict[str, Any], List[Dict[str, Any]]]:
    """
    Extract text from a scanned PDF using Tesseract OCR with parallel processing.
    
    Uses multiprocessing.Pool with N-2 cores (where N is total CPU cores) for parallel
    page processing to achieve target performance of ≥1 page/second.
    
    Args:
        path: Path to PDF file
        num_cores: Number of cores to use (default: max(1, cpu_count() - 2))
        
    Returns:
        Tuple of (pages_text, metadata, pages_with_coords)
    """
    if not _HAVE_TESSERACT:
        raise RuntimeError(
            "Tesseract OCR is not available. "
            "Install pytesseract (pip install pytesseract) and tesseract-ocr system package."
        )
    
    if not _HAVE_MUPDF:
        raise RuntimeError(
            "PyMuPDF is required for OCR processing. "
            "Install pymupdf (pip install pymupdf)."
        )
    
    logger.info(f"[OCR] ===== Starting Tesseract OCR extraction =====")
    logger.info(f"[OCR] PDF file: {os.path.basename(path)}")
    
    # Verify Tesseract is available
    try:
        tesseract_version = pytesseract.get_tesseract_version()
        logger.info(f"[OCR] Tesseract version: {tesseract_version}")
    except Exception as e:
        logger.warning(f"[OCR] Could not get Tesseract version: {e}")
    
    # Open PDF to get page count and metadata
    doc = fitz.open(path)
    num_pages = len(doc)
    logger.info(f"[OCR] Total pages to process: {num_pages}")
    
    # Get metadata
    info = doc.metadata or {}
    meta = {
        "title": info.get("title"),
        "authors": info.get("author"),
        "subject": info.get("subject"),
        "creator": info.get("creator"),
        "producer": info.get("producer"),
        "creation_date": info.get("creationDate"),
        "modification_date": info.get("modDate"),
    }
    
    doc.close()
    
    # Determine number of cores for parallel processing (N-2 cores)
    if num_cores is None:
        total_cores = multiprocessing.cpu_count()
        num_cores = max(1, total_cores - 2)
        # Don't use more cores than pages
        num_cores = min(num_cores, num_pages)
    
    logger.info(f"[OCR] Using {num_cores} cores for parallel processing")
    logger.info(f"[OCR] Processing {num_pages} pages with Tesseract OCR (confidence filtering: word≥60%, char≥70%)")
    
    # Prepare arguments for parallel processing
    page_args = [
        (path, page_num, {}) for page_num in range(num_pages)
    ]
    
    # Process pages in parallel
    pages_text = [""] * num_pages
    pages_with_coords: List[Dict[str, Any]] = []
    
    try:
        logger.info(f"[OCR] Starting parallel OCR processing...")
        with multiprocessing.Pool(processes=num_cores) as pool:
            results = pool.map(_ocr_single_page, page_args)
        
        # Sort results by page number and extract text
        results.sort(key=lambda x: x[0])
        total_chars = 0
        for page_num, text in results:
            pages_text[page_num] = text
            total_chars += len(text.strip())
        
        # Create pages_with_coords structure (simplified for OCR, no precise coordinates)
        for page_num in range(num_pages):
            pages_with_coords.append({
                "page_num": page_num + 1,  # 1-indexed
                "text_blocks": [],  # OCR doesn't provide precise coordinates
                "page_width": 0,
                "page_height": 0,
                "ocr_processed": True  # Flag to indicate OCR was used
            })
        
        avg_chars_per_page = total_chars / num_pages if num_pages > 0 else 0
        logger.info(f"[OCR] ===== OCR extraction completed successfully =====")
        logger.info(f"[OCR] Processed {num_pages} pages, extracted {total_chars:,} total characters ({avg_chars_per_page:.1f} avg/page)")
        
    except Exception as e:
        logger.error(f"[OCR] ===== Error during parallel OCR processing =====")
        logger.error(f"[OCR] Error details: {e}")
        raise
    
    return pages_text, meta, pages_with_coords


# -----------------------------
# Extractors
# -----------------------------

def _extract_with_pymupdf(path: str) -> Tuple[List[str], Dict[str, Any], List[Dict[str, Any]]]:
    """
    Enhanced PDF text extraction with coordinate information for evidence highlighting.
    Handles multi-column layouts and preserves reading order.

    Returns:
        Tuple of (pages_text, metadata, pages_with_coords)
        pages_with_coords: List of dicts with page_num, text_blocks (with bboxes)
    """
    doc = fitz.open(path)
    pages = []
    pages_with_coords = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        # Use "blocks" mode for better multi-column support
        # This preserves reading order better than "text" mode
        try:
            # Try to extract with layout preservation (better for multi-column)
            page_text = page.get_text("blocks")
            # Sort blocks by vertical position (y0) then horizontal (x0) for proper reading order
            sorted_blocks = sorted(page_text, key=lambda b: (int(b[1] / 50), b[0]))  # Group by ~50pt vertical bands
            page_text_str = "\n".join(block[4] for block in sorted_blocks if len(block) > 4 and block[4].strip())
        except:
            # Fallback to simple text extraction
            page_text_str = page.get_text("text")

        pages.append(page_text_str)
        
        # Extract text with coordinates for evidence highlighting
        text_dict = page.get_text("dict")
        page_width = page.rect.width
        page_height = page.rect.height
        
        # Extract text blocks with bounding boxes
        # We extract both line-level and span-level blocks for better matching
        text_blocks = []
        for block in text_dict.get("blocks", []):
            if "lines" in block:  # Text block
                block_text = ""
                block_bbox = None
                for line in block["lines"]:
                    line_text = ""
                    line_bbox = None
                    span_blocks = []  # Collect spans for this line
                    
                    for span in line["spans"]:
                        span_text = span["text"]
                        if not span_text.strip():
                            continue
                            
                        line_text += span_text
                        # Get bounding box for this span
                        span_bbox = span.get("bbox", [0, 0, 0, 0])
                        
                        # Extract span-level block for more precise matching
                        if span_bbox and all(v > 0 for v in span_bbox[:2]) and span_bbox[2] > span_bbox[0] and span_bbox[3] > span_bbox[1]:
                            span_normalized = {
                                "x": span_bbox[0] / page_width,
                                "y": span_bbox[1] / page_height,
                                "width": (span_bbox[2] - span_bbox[0]) / page_width,
                                "height": (span_bbox[3] - span_bbox[1]) / page_height,
                                "text": span_text.strip(),
                                "raw_bbox": span_bbox
                            }
                            # Only add if span has meaningful text (at least 3 chars)
                            if len(span_text.strip()) >= 3:
                                span_blocks.append(span_normalized)
                        
                        if line_bbox is None:
                            line_bbox = list(span_bbox)
                        else:
                            # Expand bbox to include this span
                            line_bbox[0] = min(line_bbox[0], span_bbox[0])  # x0
                            line_bbox[1] = min(line_bbox[1], span_bbox[1])  # y0
                            line_bbox[2] = max(line_bbox[2], span_bbox[2])  # x1
                            line_bbox[3] = max(line_bbox[3], span_bbox[3])  # y1
                    
                    # Add line-level block (for broader matching)
                    if line_text.strip() and line_bbox:
                        normalized_bbox = {
                            "x": line_bbox[0] / page_width,
                            "y": line_bbox[1] / page_height,
                            "width": (line_bbox[2] - line_bbox[0]) / page_width,
                            "height": (line_bbox[3] - line_bbox[1]) / page_height,
                            "text": line_text.strip(),
                            "raw_bbox": line_bbox
                        }
                        text_blocks.append(normalized_bbox)
                        block_text += line_text + " "
                        
                        if block_bbox is None:
                            block_bbox = list(line_bbox)
                        else:
                            block_bbox[0] = min(block_bbox[0], line_bbox[0])
                            block_bbox[1] = min(block_bbox[1], line_bbox[1])
                            block_bbox[2] = max(block_bbox[2], line_bbox[2])
                            block_bbox[3] = max(block_bbox[3], line_bbox[3])
                    
                    # Also add span-level blocks for more precise matching
                    # (but only if they're not too small to avoid clutter)
                    for span_block in span_blocks:
                        if span_block["width"] > 0.01 and span_block["height"] > 0.005:  # Minimum size threshold
                            text_blocks.append(span_block)
        
        pages_with_coords.append({
            "page_num": page_num + 1,  # 1-indexed
            "text_blocks": text_blocks,
            "page_width": page_width,
            "page_height": page_height
        })
    
    info = doc.metadata or {}
    meta = {
        "title": info.get("title"),
        "authors": info.get("author"),
        "subject": info.get("subject"),
        "creator": info.get("creator"),
        "producer": info.get("producer"),
        "creation_date": info.get("creationDate"),
        "modification_date": info.get("modDate"),
    }
    return pages, meta, pages_with_coords


def _extract_with_pdfminer(path: str) -> Tuple[List[str], Dict[str, Any], List[Dict[str, Any]]]:
    # pdfminer returns one long string; we'll split by form feed if present, else by heuristic
    text = pdfminer_extract_text(path)
    # Try page splits
    pages = re.split(r"\f", text) if "\f" in text else text.split("\x0c")
    if len(pages) == 1:  # fallback: very rough page split on multiple newlines
        pages = re.split(r"\n{3,}", text)
    meta: Dict[str, Any] = {}
    # Metadata via PyPDF2 if available
    if _HAVE_PYPDF2:
        try:
            reader = PdfReader(path)
            info = reader.metadata or {}
            meta = {
                "title": getattr(info, "title", None),
                "authors": getattr(info, "author", None),
                "subject": getattr(info, "subject", None),
                "creator": getattr(info, "creator", None),
                "producer": getattr(info, "producer", None),
                "creation_date": getattr(info, "creation_date", None),
                "modification_date": getattr(info, "modification_date", None),
            }
        except Exception:
            pass
    # No coordinates available from pdfminer
    pages_with_coords: List[Dict[str, Any]] = []
    return pages, meta, pages_with_coords


def _extract_with_pypdf2(path: str) -> Tuple[List[str], Dict[str, Any], List[Dict[str, Any]]]:
    reader = PdfReader(path)
    pages = [page.extract_text() or "" for page in reader.pages]
    info = reader.metadata or {}
    meta = {
        "title": getattr(info, "title", None),
        "authors": getattr(info, "author", None),
        "subject": getattr(info, "subject", None),
        "creator": getattr(info, "creator", None),
        "producer": getattr(info, "producer", None),
        "creation_date": getattr(info, "creation_date", None),
        "modification_date": getattr(info, "modification_date", None),
    }
    # No coordinates available from PyPDF2
    pages_with_coords: List[Dict[str, Any]] = []
    return pages, meta, pages_with_coords


def extract_pdf(path: str) -> Tuple[List[str], PDFMetadata, List[Dict[str, Any]]]:
    """
    Returns (pages_text_list, metadata, pages_with_coords)
    Preference: PyMuPDF > pdfminer > PyPDF2 > OCR (if needed)
    
    pages_with_coords: List of dicts with page_num, text_blocks (with bboxes), page_width, page_height
    
    OCR is automatically used as a fallback when:
    - Text extraction fails completely, OR
    - Extracted text is too sparse (indicating a scanned PDF)
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"PDF not found: {path}")

    file_bytes = _read_file_bytes(path)
    sha = _sha256(file_bytes)
    size = len(file_bytes)

    pages: List[str] = []
    meta_dict: Dict[str, Any] = {}
    pages_with_coords: List[Dict[str, Any]] = []

    last_err: Optional[Exception] = None

    # Try standard text extraction methods first
    if _HAVE_MUPDF:
        try:
            pages, meta_dict, pages_with_coords = _extract_with_pymupdf(path)
        except Exception as e:
            last_err = e
            logger.warning("PyMuPDF extraction failed: %s", e)

    if not pages and _HAVE_PDFMINER:
        try:
            pages, meta_dict, pages_with_coords = _extract_with_pdfminer(path)
        except Exception as e:
            last_err = e
            logger.warning("pdfminer extraction failed: %s", e)

    if not pages and _HAVE_PYPDF2:
        try:
            pages, meta_dict, pages_with_coords = _extract_with_pypdf2(path)
        except Exception as e:
            last_err = e
            logger.warning("PyPDF2 extraction failed: %s", e)

    # Check if OCR is needed (scanned PDF detection)
    # OCR is needed if:
    # 1. No text was extracted at all, OR
    # 2. The extracted text is too sparse (average < 50 chars per page)
    if pages:
        # Check if OCR is needed even though we have some text
        needs_ocr_check = _needs_ocr(pages)
        if not needs_ocr_check:
            # Log that OCR was checked but not needed (for visibility)
            if _HAVE_TESSERACT:
                logger.info("[OCR] Tesseract available but not needed - PDF has sufficient text (machine-readable)")
            else:
                logger.debug("[OCR] OCR check: PDF has sufficient text, Tesseract not installed")
    
    if not pages or _needs_ocr(pages):
        if _HAVE_TESSERACT and _HAVE_MUPDF:
            logger.info("[OCR] Text extraction insufficient or failed. Attempting Tesseract OCR...")
            try:
                pages, meta_dict, pages_with_coords = _extract_with_ocr(path)
                logger.info("[OCR] Tesseract OCR extraction completed successfully")
            except Exception as e:
                logger.error(f"[OCR] Tesseract OCR extraction failed: {e}")
                if not pages:
                    # If we still have no pages and OCR failed, raise error
                    raise RuntimeError(
                        f"Could not extract text from PDF using standard methods or OCR. "
                        f"Last error: {last_err if last_err else e}"
                    )
        elif not pages:
            # OCR not available and no text extracted
            if not _HAVE_TESSERACT:
                logger.warning("[OCR] Tesseract OCR not available. Install pytesseract and tesseract-ocr for scanned PDF support.")
            elif not _HAVE_MUPDF:
                logger.warning("[OCR] PyMuPDF not available. Required for OCR processing.")
            raise RuntimeError(
                f"Could not extract text from PDF. Last error: {last_err}. "
                f"OCR is not available (install pytesseract and tesseract-ocr for scanned PDFs)."
            )

    if not pages:
        raise RuntimeError(f"Could not extract text from PDF. Last error: {last_err}")

    # Normalize pages
    pages = [_normalize_text(p) for p in pages]
    meta = PDFMetadata(
        title=meta_dict.get("title"),
        authors=meta_dict.get("authors"),
        subject=meta_dict.get("subject"),
        creator=meta_dict.get("creator"),
        producer=meta_dict.get("producer"),
        creation_date=meta_dict.get("creation_date"),
        modification_date=meta_dict.get("modification_date"),
        file_size_bytes=size,
        sha256=sha,
    )
    return pages, meta, pages_with_coords


# -----------------------------
# Tool implementation
# -----------------------------

class ParsePDFTool(BaseTool):
    """
    Parse PDF tool for QualiLens.

    Usage:
        tool = ParsePDFTool()
        result = tool.execute(file_path="/path/to/paper.pdf", chunk_chars=4000, overlap=200)

    Returns a dict with:
        {
          "metadata": {...},
          "num_pages": int,
          "text": "full normalized text",
          "sections": [
              {"name": str, "start_char": int, "end_char": int, "text": str}, ...
          ],
          "chunks": ["...", "..."],
          "dois": ["10.1234/abcd..."],
          "urls": ["https://..."],
          "figure_table_cues": ["Figure 1: ...", "Table 2. ..."]
        }
    """

    def _get_metadata(self) -> ToolMetadata:
        """Return the metadata for this tool."""
        return ToolMetadata(
            name="parse_pdf",
            description="Extracts text, sections, and metadata from a PDF, returning analysis-ready chunks.",
            parameters={
                "required": ["file_path"],
                "optional": ["chunk_chars", "overlap", "max_pages"],
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the PDF file to parse"
                    },
                    "chunk_chars": {
                        "type": "integer",
                        "description": "Target characters per chunk (default: 4000)",
                        "default": 4000
                    },
                    "overlap": {
                        "type": "integer", 
                        "description": "Overlap characters between chunks (default: 200)",
                        "default": 200
                    },
                    "max_pages": {
                        "type": "integer",
                        "description": "Maximum number of pages to extract (optional)"
                    }
                }
            },
            examples=[
                "Parse the PDF at /path/to/paper.pdf",
                "Extract first 10 pages from research.pdf with 2000 character chunks",
                "Analyze the methodology section of study.pdf"
            ],
            category="pdf_analysis"
        )

    def execute(
        self,
        file_path: str,
        chunk_chars: int = 4000,
        overlap: int = 200,
        max_pages: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Parse a PDF and return structured content for downstream LLM agents.

        Args:
            file_path: Path to the PDF file.
            chunk_chars: Target characters per chunk (for LLM-friendly splitting).
            overlap: Overlap characters between chunks.
            max_pages: If set, limit extraction to the first N pages.

        Returns:
            Dict with metadata, text, sections, chunks, dois, urls, figure/table cues.
        """
        if not isinstance(file_path, str) or not file_path.lower().endswith(".pdf"):
            raise ValueError("file_path must be a path to a .pdf file")

        logger.info("Parsing PDF: %s", file_path)
        pages, meta, pages_with_coords = extract_pdf(file_path)

        if max_pages is not None and max_pages > 0:
            pages = pages[:max_pages]
            pages_with_coords = pages_with_coords[:max_pages]

        full_text = "\n\n".join(p for p in pages if p)
        full_text = _normalize_text(full_text)

        # Heuristic sectioning
        sections = _split_sections(full_text)

        # Extract methodology-focused context for better analysis
        methodology_context = _extract_methodology_context(sections, full_text)

        # Chunking
        chunks = _chunk_text(full_text, target_chars=chunk_chars, overlap=overlap)

        # References
        dois = sorted(set(m.group(1) for m in DOI_REGEX.finditer(full_text)))
        urls = sorted(set(URL_REGEX.findall(full_text)))
        
        # Extract citations from references section
        references_section = _extract_references_section(full_text, sections)
        citations = []
        if references_section:
            citations = _extract_citations(references_section)
            logger.info(f"Extracted {len(citations)} citations from references section")
        else:
            logger.warning("Could not find references section in PDF")

        # Figures/Tables cues
        figtab = _extract_fig_table_cues(full_text)

        result: Dict[str, Any] = {
            "success": True,
            "metadata": {
                "title": meta.title,
                "authors": meta.authors,
                "subject": meta.subject,
                "creator": meta.creator,
                "producer": meta.producer,
                "creation_date": meta.creation_date,
                "modification_date": meta.modification_date,
                "file_size_bytes": meta.file_size_bytes,
                "sha256": meta.sha256,
                "source_path": os.path.abspath(file_path),
            },
            "num_pages": len(pages),
            "pages": pages,  # Include pages for evidence collection
            "pages_with_coords": pages_with_coords,  # Include coordinate data for evidence highlighting
            "text": full_text,
            "methodology_context": methodology_context,  # NEW: Focused methodology extraction
            "sections": [
                {
                    "name": s.name,
                    "start_char": s.start_char,
                    "end_char": s.end_char,
                    "text": s.text,
                }
                for s in sections
            ],
            "chunks": chunks,
            "dois": dois,
            "urls": urls,
            "citations": citations,  # NEW: Extracted citations
            "references_section": references_section if references_section else None,  # NEW: Full references text
            "num_citations": len(citations),  # NEW: Count of extracted citations
            "figure_table_cues": figtab,
            "tool_used": "parse_pdf"
        }

        logger.info(
            "Parsed PDF '%s' — pages=%d, sections=%d, chunks=%d",
            os.path.basename(file_path),
            result["num_pages"],
            len(result["sections"]),
            len(result["chunks"]),
        )

        return result

    # Optional async hook for agent frameworks that support async tools
    async def arun(  # type: ignore
        self,
        file_path: str,
        chunk_chars: int = 4000,
        overlap: int = 200,
        max_pages: Optional[int] = None,
    ) -> Dict[str, Any]:
        # Simple passthrough to sync .execute() to keep behavior identical
        return self.execute(
            file_path=file_path,
            chunk_chars=chunk_chars,
            overlap=overlap,
            max_pages=max_pages,
        )


# -----------------------------
# CLI for quick manual testing
# -----------------------------

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Parse a PDF into sections/chunks.")
    parser.add_argument("pdf", help="Path to the PDF file")
    parser.add_argument("--chunk-chars", type=int, default=4000)
    parser.add_argument("--overlap", type=int, default=200)
    parser.add_argument("--max-pages", type=int, default=0, help="0 means no limit")
    parser.add_argument("--out", type=str, default="", help="Optional JSON output path")
    args = parser.parse_args()

    tool = ParsePDFTool()
    out = tool.execute(
        file_path=args.pdf,
        chunk_chars=args.chunk_chars,
        overlap=args.overlap,
        max_pages=args.max_pages if args.max_pages > 0 else None,
    )

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"Wrote: {args.out}")
    else:
        # Print just the metadata + first 500 chars to avoid console spam
        preview = {
            "metadata": out["metadata"],
            "num_pages": out["num_pages"],
            "sections": [s["name"] for s in out["sections"]],
            "chunks": len(out["chunks"]),
            "text_preview": out["text"][:500] + ("..." if len(out["text"]) > 500 else ""),
        }
        print(json.dumps(preview, ensure_ascii=False, indent=2))
