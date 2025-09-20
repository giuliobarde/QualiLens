"""
Parse PDF tool for QualiLens.

This module contains the ParsePDF tool for QualiLens.
"""

import hashlib, fitz, re
from typing import Any, Dict, List, Optional
from .base_tool import BaseTool

class ParsePDFTool(BaseTool):
    """
    Parse PDF tool for QualiLens.
    """
    def __init__(self, *, preserve_bbox: bool = False):
        super().__init__()
        self.name = "parse_pdf"
        self.description = "Parse a PDF into paragraphs with page numbers and coarse sections."
        self.preserve_bbox = preserve_bbox
        self.parameters = {
            "required": ["pdf_file"],
            "optional": [],
            "properties": {
                "pdf_file": {
                    "type": "string",
                    "description": "The path to the PDF file to parse."
                }
            }
        }
    
    def _hash(self, b: bytes) -> str:
        return hashlib.sha256(b).hexdigest()[:16]

    def _load(self, pdf_bytes: bytes, max_pages: Optional[int] = None, keep_bbox: bool = False):
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        rows = []
        for i in range(len(doc) if not max_pages else min(max_pages, len(doc))):
            page = doc[i]
            if keep_bbox:
                for x0, y0, x1, y1, txt, *_ in page.get_text("blocks"):
                    t = (txt or "").strip()
                    if len(t) >= 40:
                        rows.append({
                            "page": i + 1,
                            "bbox": (x0, y0, x1, y1),
                            "text": t
                        })
            else:
                txt = page.get_text("text")
                for para in [p.strip() for p in txt.split("\n\n") if p.strip()]:
                    rows.append({
                        "page": i + 1,
                        "text": para
                    })
        return rows, len(doc)

    def _tag_sections(self, rows: List[Dict[str, Any]]):
        headers = {
            "abstract":"Abstract","introduction":"Introduction",
            "methods":"Methods","materials and methods":"Methods",
            "results":"Results","discussion":"Discussion",
            "conclusion":"Discussion","limitations":"Discussion",
            "references":"References","supplement":"Supplement"
        }
        cur = None; seen = []
        for r in rows:
            first = r["text"].split("\n",1)[0].strip().lower()
            for k,v in headers.items():
                if re.fullmatch(rf"{k}\s*:?\s*$", first):
                    cur = v
                    if v not in seen: seen.append(v)
            r["section"] = cur
        return seen

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if "pdf_bytes" in payload:
            pdf_bytes = payload["pdf_bytes"]
        elif "pdf_path" in payload:
            with open(payload["pdf_path"], "rb") as f:
                pdf_bytes = f.read()
        else:
            raise ValueError("Provide 'pdf_bytes' or 'pdf_path'.")

        opts = payload.get("options", {})
        keep_bbox = bool(opts.get("preserve_bbox", False))
        max_pages = opts.get("max_pages")
        return_sections = bool(opts.get("return_sections", True))

        doc_id = self._hash(pdf_bytes)
        rows, total_pages = self._load(pdf_bytes, max_pages=max_pages, keep_bbox=keep_bbox)
        headings = self._tag_sections(rows)

        out = {"doc_id": doc_id, "pages": total_pages, "detected_headings": headings}
        if return_sections:
            out["sections"] = rows
        return out