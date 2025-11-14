"""
Evidence Collector for QualiLens.

This module provides utilities to collect and structure evidence traces
with page references and bounding box coordinates for visualization.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class EvidenceItem:
    """Represents a single evidence item with location information."""
    id: str
    category: str  # 'bias', 'methodology', 'reproducibility', 'statistics', etc.
    text_snippet: str
    rationale: str
    page_number: Optional[int] = None
    bounding_box: Optional[Dict[str, float]] = None  # {x, y, width, height} in normalized coordinates (0-1)
    confidence: Optional[float] = None
    severity: Optional[str] = None  # 'low', 'medium', 'high'
    score_impact: Optional[float] = None  # How this evidence affects the score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class EvidenceCollector:
    """Collects and manages evidence traces from analysis tools."""
    
    def __init__(self, pdf_pages: Optional[List[str]] = None):
        """
        Initialize evidence collector.
        
        Args:
            pdf_pages: List of page texts for page number detection
        """
        self.pdf_pages = pdf_pages or []
        self.evidence_items: List[EvidenceItem] = []
        self._evidence_counter = 0
    
    def add_evidence(
        self,
        category: str,
        text_snippet: str,
        rationale: str,
        page_number: Optional[int] = None,
        bounding_box: Optional[Dict[str, float]] = None,
        confidence: Optional[float] = None,
        severity: Optional[str] = None,
        score_impact: Optional[float] = None
    ) -> str:
        """
        Add an evidence item.
        
        Args:
            category: Evidence category (bias, methodology, etc.)
            text_snippet: The text that serves as evidence
            rationale: Explanation of why this is evidence
            page_number: Page number where evidence appears
            bounding_box: Bounding box coordinates {x, y, width, height} (0-1 normalized)
            confidence: Confidence level (0-1)
            severity: Severity level
            score_impact: Impact on score
            
        Returns:
            Evidence ID
        """
        evidence_id = f"evidence_{self._evidence_counter}"
        self._evidence_counter += 1
        
        # Try to detect page number if not provided
        if page_number is None and self.pdf_pages:
            page_number = self._detect_page_number(text_snippet)
        
        # Try to estimate bounding box if not provided
        if bounding_box is None and page_number is not None:
            bounding_box = self._estimate_bounding_box(text_snippet, page_number)
        
        evidence = EvidenceItem(
            id=evidence_id,
            category=category,
            text_snippet=text_snippet[:500],  # Limit snippet length
            rationale=rationale,
            page_number=page_number,
            bounding_box=bounding_box,
            confidence=confidence,
            severity=severity,
            score_impact=score_impact
        )
        
        self.evidence_items.append(evidence)
        logger.info(f"✅ Added evidence: {evidence_id} ({category}) - Page: {page_number}, Snippet: {text_snippet[:50]}...")
        
        return evidence_id
    
    def _detect_page_number(self, text_snippet: str) -> Optional[int]:
        """
        Detect which page contains the text snippet.
        
        Args:
            text_snippet: Text to find
            
        Returns:
            Page number (1-indexed) or None
        """
        if not self.pdf_pages:
            return None
        
        # Normalize text for comparison
        snippet_normalized = re.sub(r'\s+', ' ', text_snippet.strip().lower())
        
        # Search through pages
        for idx, page_text in enumerate(self.pdf_pages):
            page_normalized = re.sub(r'\s+', ' ', page_text.lower())
            
            # Check if snippet appears in this page (with some tolerance)
            if len(snippet_normalized) > 20:
                # Use substring matching for longer snippets
                if snippet_normalized[:100] in page_normalized:
                    return idx + 1  # 1-indexed
            else:
                # For short snippets, check if key words appear
                words = snippet_normalized.split()
                if len(words) >= 3:
                    matching_words = sum(1 for word in words if word in page_normalized)
                    if matching_words >= len(words) * 0.6:  # 60% word match
                        return idx + 1
        
        return None
    
    def _estimate_bounding_box(
        self,
        text_snippet: str,
        page_number: int
    ) -> Optional[Dict[str, float]]:
        """
        Estimate bounding box coordinates for text snippet.
        
        This is a simplified estimation. In a production system, you would
        use PDF text extraction with actual coordinates.
        
        Args:
            text_snippet: Text snippet
            page_number: Page number (1-indexed)
            
        Returns:
            Estimated bounding box {x, y, width, height} in normalized coordinates
        """
        # This is a placeholder - in production, you'd use actual PDF coordinates
        # For now, return a default position in the middle of the page
        return {
            "x": 0.1,  # 10% from left
            "y": 0.4,  # 40% from top
            "width": 0.8,  # 80% width
            "height": 0.1  # 10% height
        }
    
    def get_evidence_by_category(self, category: str) -> List[EvidenceItem]:
        """Get all evidence items for a specific category."""
        return [e for e in self.evidence_items if e.category == category]
    
    def get_evidence_by_page(self, page_number: int) -> List[EvidenceItem]:
        """Get all evidence items for a specific page."""
        return [e for e in self.evidence_items if e.page_number == page_number]
    
    def get_all_evidence(self) -> List[Dict[str, Any]]:
        """Get all evidence items as dictionaries."""
        return [e.to_dict() for e in self.evidence_items]
    
    def get_evidence_summary(self) -> Dict[str, Any]:
        """Get summary statistics of evidence."""
        categories = {}
        for evidence in self.evidence_items:
            cat = evidence.category
            if cat not in categories:
                categories[cat] = {
                    "count": 0,
                    "pages": set(),
                    "severities": {}
                }
            categories[cat]["count"] += 1
            if evidence.page_number:
                categories[cat]["pages"].add(evidence.page_number)
            if evidence.severity:
                categories[cat]["severities"][evidence.severity] = \
                    categories[cat]["severities"].get(evidence.severity, 0) + 1
        
        # Convert sets to lists for JSON serialization
        for cat_data in categories.values():
            cat_data["pages"] = sorted(list(cat_data["pages"]))
        
        return {
            "total_evidence": len(self.evidence_items),
            "categories": categories,
            "pages_with_evidence": sorted(set(
                e.page_number for e in self.evidence_items if e.page_number
            ))
        }

