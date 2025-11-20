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


def _safe_int(x: Any) -> Optional[int]:
    try:
        return int(x)
    except Exception:
        return None


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
    Preference: PyMuPDF > pdfminer > PyPDF2
    
    pages_with_coords: List of dicts with page_num, text_blocks (with bboxes), page_width, page_height
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
