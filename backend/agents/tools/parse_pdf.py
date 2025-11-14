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
    r"^\s*abstract\s*$",
    r"^\s*background\s*$",
    r"^\s*introduction\s*$",
    r"^\s*methods?\s*$",
    r"^\s*materials\s+and\s+methods\s*$",
    r"^\s*results?\s*$",
    r"^\s*discussion\s*$",
    r"^\s*results\s+and\s+discussion\s*$",
    r"^\s*limitations?\s*$",
    r"^\s*conclusion[s]?\s*$",
    r"^\s*acknowledg(e)?ments?\s*$",
    r"^\s*references?\s*$",
    r"^\s*supplementary\s+(materials?|information)\s*$",
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
    # Fix common ligatures & hyphenation at line breaks, collapse excessive whitespace
    # 1) Merge hyphenated line breaks: "exam-\nple" -> "example"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # 2) Replace soft hyphen U+00AD if present
    text = text.replace("\u00ad", "")
    # 3) Convert multiple spaces/tabs to single spaces, but keep newlines
    text = re.sub(r"[ \t]+", " ", text)
    # 4) Normalize Windows newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # 5) Remove trailing spaces on lines
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()


def _chunk_text(text: str, target_chars: int = 4000, overlap: int = 200) -> List[str]:
    """
    Simple, model-agnostic chunker by characters with overlap.
    target_chars≈4000 keeps chunks safely under ~1500-2000 tokens for most LLMs.
    """
    chunks: List[str] = []
    i = 0
    n = len(text)
    if n == 0:
        return chunks
    while i < n:
        end = min(n, i + target_chars)
        chunk = text[i:end]
        chunks.append(chunk)
        if end == n:
            break
        i = max(end - overlap, i + 1)
    return chunks


def _split_sections(full_text: str) -> List[Section]:
    """
    Heuristic: look for common scholarly headings on their own lines (multiline regex).
    Build sections spanning from heading to next heading (or end).
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
        sections.append(Section(name=name, start_char=start, end_char=end, text=body))
    return sections


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

def _extract_with_pymupdf(path: str) -> Tuple[List[str], Dict[str, Any]]:
    doc = fitz.open(path)
    pages = [doc.load_page(i).get_text("text") for i in range(len(doc))]
    info = doc.metadata or {}
    # PyMuPDF metadata keys: title, author, subject, keywords, creator, producer, creationDate, modDate
    meta = {
        "title": info.get("title"),
        "authors": info.get("author"),
        "subject": info.get("subject"),
        "creator": info.get("creator"),
        "producer": info.get("producer"),
        "creation_date": info.get("creationDate"),
        "modification_date": info.get("modDate"),
    }
    return pages, meta


def _extract_with_pdfminer(path: str) -> Tuple[List[str], Dict[str, Any]]:
    # pdfminer returns one long string; we’ll split by form feed if present, else by heuristic
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
    return pages, meta


def _extract_with_pypdf2(path: str) -> Tuple[List[str], Dict[str, Any]]:
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
    return pages, meta


def extract_pdf(path: str) -> Tuple[List[str], PDFMetadata]:
    """
    Returns (pages_text_list, metadata)
    Preference: PyMuPDF > pdfminer > PyPDF2
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"PDF not found: {path}")

    file_bytes = _read_file_bytes(path)
    sha = _sha256(file_bytes)
    size = len(file_bytes)

    pages: List[str] = []
    meta_dict: Dict[str, Any] = {}

    last_err: Optional[Exception] = None

    if _HAVE_MUPDF:
        try:
            pages, meta_dict = _extract_with_pymupdf(path)
        except Exception as e:
            last_err = e
            logger.warning("PyMuPDF extraction failed: %s", e)

    if not pages and _HAVE_PDFMINER:
        try:
            pages, meta_dict = _extract_with_pdfminer(path)
        except Exception as e:
            last_err = e
            logger.warning("pdfminer extraction failed: %s", e)

    if not pages and _HAVE_PYPDF2:
        try:
            pages, meta_dict = _extract_with_pypdf2(path)
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
    return pages, meta


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
        pages, meta = extract_pdf(file_path)

        if max_pages is not None and max_pages > 0:
            pages = pages[:max_pages]

        full_text = "\n\n".join(p for p in pages if p)
        full_text = _normalize_text(full_text)

        # Heuristic sectioning
        sections = _split_sections(full_text)

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
            "text": full_text,
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
