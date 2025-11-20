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
    
    def __init__(self, pdf_pages: Optional[List[str]] = None, pages_with_coords: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize evidence collector.
        
        Args:
            pdf_pages: List of page texts for page number detection
            pages_with_coords: List of dicts with page_num, text_blocks (with bboxes), page_width, page_height
        """
        self.pdf_pages = pdf_pages or []
        self.pages_with_coords = pages_with_coords or []
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
        
        # Try to detect page number and find actual location if not provided
        if page_number is None and self.pdf_pages:
            page_number = self._detect_page_number(text_snippet)
        
        # Try to find actual bounding box using coordinate data
        # This might also help us find the correct page number
        if bounding_box is None:
            if self.pages_with_coords and len(self.pages_with_coords) > 0:
                # If we don't have a page number, try to find it by searching all pages
                if page_number is None:
                    # Search all pages for the text and find the best match
                    best_page = None
                    best_bbox = None
                    best_score = 0
                    
                    for page_coord in self.pages_with_coords:
                        test_page_num = page_coord.get("page_num")
                        test_bbox = self._find_text_location(text_snippet, test_page_num)
                        if test_bbox:
                            # Calculate match quality (prefer pages with better text matches)
                            text_blocks = page_coord.get("text_blocks", [])
                            snippet_normalized = re.sub(r'\s+', ' ', text_snippet.strip().lower())
                            match_score = 0
                            
                            for block in text_blocks:
                                block_text = block.get("text", "").lower()
                                if snippet_normalized in block_text or block_text in snippet_normalized:
                                    match_score = 1.0
                                    break
                                # Calculate word overlap
                                block_words = [w for w in block_text.split() if len(w) > 2]
                                snippet_words = [w for w in snippet_normalized.split() if len(w) > 2]
                                if len(block_words) > 0 and len(snippet_words) > 0:
                                    matching_words = sum(1 for word in snippet_words if word in block_words)
                                    word_score = matching_words / max(len(snippet_words), len(block_words))
                                    match_score = max(match_score, word_score)
                            
                            if match_score > best_score:
                                best_score = match_score
                                best_page = test_page_num
                                best_bbox = test_bbox
                    
                    if best_page and best_bbox:
                        page_number = best_page
                        bounding_box = best_bbox
                        logger.info(f"✅ Found text location for evidence {evidence_id} on page {best_page} (match score: {best_score:.2f}) by searching all pages")
                    else:
                        # Couldn't find on any page, use estimate
                        page_number = 1
                        logger.warning(f"⚠️ Could not detect page number for evidence {evidence_id}, defaulting to page 1")
                        bounding_box = self._estimate_bounding_box(text_snippet, page_number)
                else:
                    # We have a page number, try to find location on that page
                    bounding_box = self._find_text_location(text_snippet, page_number)
                    if bounding_box:
                        logger.info(f"✅ Found text location for evidence {evidence_id} on page {page_number}")
                    else:
                        # Try searching other pages if not found on specified page
                        logger.warning(f"⚠️ Could not find text on page {page_number}, searching other pages...")
                        best_page = None
                        best_bbox = None
                        best_score = 0
                        
                        for page_coord in self.pages_with_coords:
                            test_page_num = page_coord.get("page_num")
                            if test_page_num != page_number:
                                test_bbox = self._find_text_location(text_snippet, test_page_num)
                                if test_bbox:
                                    # Calculate match quality
                                    text_blocks = page_coord.get("text_blocks", [])
                                    snippet_normalized = re.sub(r'\s+', ' ', text_snippet.strip().lower())
                                    match_score = 0
                                    
                                    for block in text_blocks:
                                        block_text = block.get("text", "").lower()
                                        if snippet_normalized in block_text or block_text in snippet_normalized:
                                            match_score = 1.0
                                            break
                                        # Calculate word overlap
                                        block_words = [w for w in block_text.split() if len(w) > 2]
                                        snippet_words = [w for w in snippet_normalized.split() if len(w) > 2]
                                        if len(block_words) > 0 and len(snippet_words) > 0:
                                            matching_words = sum(1 for word in snippet_words if word in block_words)
                                            word_score = matching_words / max(len(snippet_words), len(block_words))
                                            match_score = max(match_score, word_score)
                                    
                                    if match_score > best_score:
                                        best_score = match_score
                                        best_page = test_page_num
                                        best_bbox = test_bbox
                        
                        if best_page and best_bbox:
                            page_number = best_page
                            bounding_box = best_bbox
                            logger.info(f"✅ Found text location for evidence {evidence_id} on page {best_page} (match score: {best_score:.2f}, was incorrectly assigned to page {page_number})")
                        else:
                            logger.warning(f"⚠️ Could not find text location on any page, using estimate for evidence {evidence_id}")
                            bounding_box = self._estimate_bounding_box(text_snippet, page_number)
            else:
                # No coordinate data available
                if page_number is None:
                    page_number = 1
                    logger.warning(f"⚠️ Could not detect page number for evidence {evidence_id}, defaulting to page 1")
                bounding_box = self._estimate_bounding_box(text_snippet, page_number)
        
        # Always set a page number (default to 1 if still not found)
        if page_number is None:
            page_number = 1
            logger.warning(f"⚠️ Could not detect page number for evidence {evidence_id}, defaulting to page 1")
        
        # Ensure bounding box is always set
        if not bounding_box:
            logger.error(f"❌ Failed to set bounding box for evidence {evidence_id}, using default")
            bounding_box = {
                "x": 0.1,
                "y": 0.3,
                "width": 0.8,
                "height": 0.15
            }
        
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
        logger.info(f"✅ Added evidence: {evidence_id} ({category}) - Page: {page_number}, BBox: {bounding_box}, Snippet: {text_snippet[:50]}...")
        
        # Debug: Log evidence details
        logger.debug(f"Evidence details: {evidence.to_dict()}")
        
        # Log summary of evidence distribution by page
        if len(self.evidence_items) % 5 == 0 or len(self.evidence_items) == 1:
            page_distribution = {}
            for ev in self.evidence_items:
                page = ev.page_number or 1
                page_distribution[page] = page_distribution.get(page, 0) + 1
            logger.info(f"📊 Evidence distribution by page (total: {len(self.evidence_items)}): {page_distribution}")
        
        return evidence_id
    
    def _detect_page_number(self, text_snippet: str) -> Optional[int]:
        """
        Detect which page contains the text snippet.
        Improved to find the best match across all pages, not just the first match.
        
        Args:
            text_snippet: Text to find
            
        Returns:
            Page number (1-indexed) or None
        """
        if not self.pdf_pages:
            return None
        
        # Normalize text for comparison
        snippet_normalized = re.sub(r'\s+', ' ', text_snippet.strip().lower())
        snippet_words = [w for w in snippet_normalized.split() if len(w) > 2]  # Filter short words
        
        if len(snippet_words) == 0:
            return None
        
        # First, try to use coordinate data to find the page
        if self.pages_with_coords:
            best_page = None
            best_score = 0
            
            for page_coord in self.pages_with_coords:
                page_num = page_coord.get("page_num")
                text_blocks = page_coord.get("text_blocks", [])
                
                # Check if any text block on this page matches
                for block in text_blocks:
                    block_text = block.get("text", "").lower()
                    block_normalized = re.sub(r'\s+', ' ', block_text.strip())
                    
                    # Calculate match score
                    if snippet_normalized in block_normalized or block_normalized in snippet_normalized:
                        # Exact match - this is definitely the right page
                        logger.debug(f"✅ Found exact match for snippet on page {page_num} using coordinate data")
                        return page_num
                    
                    # Check word overlap
                    block_words = [w for w in block_normalized.split() if len(w) > 2]
                    if len(block_words) > 0:
                        matching_words = sum(1 for word in snippet_words if word in block_words)
                        match_score = matching_words / max(len(snippet_words), len(block_words))
                        if match_score > best_score:
                            best_score = match_score
                            best_page = page_num
            
            # If we found a good match using coordinate data, use it
            if best_page and best_score >= 0.5:
                logger.debug(f"✅ Found best match (score: {best_score:.2f}) for snippet on page {best_page} using coordinate data")
                return best_page
        
        # Fallback: search through page text
        best_page = None
        best_score = 0
        
        for idx, page_text in enumerate(self.pdf_pages):
            page_normalized = re.sub(r'\s+', ' ', page_text.lower())
            
            # Calculate match score
            match_score = 0
            
            # Check if snippet appears in this page
            if len(snippet_normalized) > 20:
                # Use substring matching for longer snippets
                if snippet_normalized[:100] in page_normalized:
                    # Calculate how much of the snippet appears
                    snippet_len = len(snippet_normalized)
                    if snippet_normalized in page_normalized:
                        match_score = 1.0  # Full match
                    else:
                        # Partial match - calculate overlap
                        matched_chars = 0
                        for i in range(min(100, len(snippet_normalized))):
                            if snippet_normalized[i] in page_normalized:
                                matched_chars += 1
                        match_score = matched_chars / snippet_len
            else:
                # For short snippets, check word overlap
                page_words = [w for w in page_normalized.split() if len(w) > 2]
                if len(page_words) > 0:
                    matching_words = sum(1 for word in snippet_words if word in page_words)
                    match_score = matching_words / max(len(snippet_words), len(page_words))
            
            # Track the best match
            if match_score > best_score:
                best_score = match_score
                best_page = idx + 1  # 1-indexed
        
        # Only return if we have a reasonable match (at least 50% overlap)
        if best_page and best_score >= 0.5:
            logger.debug(f"✅ Found best match (score: {best_score:.2f}) for snippet on page {best_page} using text search")
            return best_page
        
        return None
    
    def _find_text_location(
        self,
        text_snippet: str,
        page_number: int
    ) -> Optional[Dict[str, float]]:
        """
        Find actual text location in PDF using coordinate data.
        Improved to handle multi-block evidence and combine bounding boxes.
        
        Args:
            text_snippet: Text snippet to find
            page_number: Page number (1-indexed)
            
        Returns:
            Bounding box {x, y, width, height} in normalized coordinates (0-1)
        """
        if not self.pages_with_coords:
            return self._estimate_bounding_box(text_snippet, page_number)
        
        # Find the page with coordinates
        page_data = None
        for page_coord in self.pages_with_coords:
            if page_coord.get("page_num") == page_number:
                page_data = page_coord
                break
        
        if not page_data:
            logger.warning(f"⚠️ No coordinate data for page {page_number}")
            return self._estimate_bounding_box(text_snippet, page_number)
        
        text_blocks = page_data.get("text_blocks", [])
        if not text_blocks:
            logger.warning(f"⚠️ No text blocks for page {page_number}")
            return self._estimate_bounding_box(text_snippet, page_number)
        
        # Normalize text snippet for matching
        snippet_normalized = re.sub(r'\s+', ' ', text_snippet.strip().lower())
        snippet_words = [w for w in snippet_normalized.split() if len(w) > 2]  # Filter out very short words
        
        if len(snippet_words) == 0:
            return self._estimate_bounding_box(text_snippet, page_number)
        
        # Strategy 1: Try exact substring match first (most accurate)
        matching_blocks = []
        for i, block in enumerate(text_blocks):
            block_text = block.get("text", "").lower()
            block_normalized = re.sub(r'\s+', ' ', block_text.strip())
            
            # Check if snippet is contained in block or vice versa
            if snippet_normalized in block_normalized or block_normalized in snippet_normalized:
                matching_blocks.append((i, block, 1.0))
                logger.debug(f"✅ Exact match found in block {i}: {block_text[:50]}...")
        
        # Strategy 2: If no exact match, try fuzzy matching across multiple blocks
        if not matching_blocks:
            # Try to find blocks that contain significant word overlap
            for i, block in enumerate(text_blocks):
                block_text = block.get("text", "").lower()
                block_words = [w for w in block_text.split() if len(w) > 2]
                
                if len(block_words) == 0:
                    continue
                
                # Count matching words (case-insensitive)
                matching_words = sum(1 for word in snippet_words if word in block_words)
                match_ratio = matching_words / max(len(snippet_words), len(block_words))
                
                # Require at least 50% word overlap for a match
                if match_ratio >= 0.5:
                    matching_blocks.append((i, block, match_ratio))
                    logger.debug(f"✅ Fuzzy match (score: {match_ratio:.2f}) in block {i}: {block_text[:50]}...")
        
        # Strategy 3: If still no match, try finding blocks containing key phrases
        if not matching_blocks and len(snippet_words) >= 3:
            # Extract key phrases (2-3 word combinations)
            key_phrases = []
            for i in range(len(snippet_words) - 1):
                key_phrases.append(' '.join(snippet_words[i:i+2]))
            if len(snippet_words) >= 3:
                key_phrases.append(' '.join(snippet_words[:3]))
            
            for i, block in enumerate(text_blocks):
                block_text = block.get("text", "").lower()
                # Check if any key phrase appears in this block
                for phrase in key_phrases:
                    if phrase in block_text:
                        matching_blocks.append((i, block, 0.4))
                        logger.debug(f"✅ Key phrase match in block {i}: {phrase}")
                        break
        
        # Combine matching blocks if evidence spans multiple blocks
        if matching_blocks:
            # Sort by match score (descending) and block index
            matching_blocks.sort(key=lambda x: (-x[2], x[0]))
            
            # Get the best matching block(s)
            # If we have multiple adjacent blocks, combine them
            combined_blocks = []
            last_index = -1
            
            for idx, block, score in matching_blocks:
                # If this block is adjacent to the last one (within 3 blocks), combine
                if last_index >= 0 and idx - last_index <= 3:
                    combined_blocks.append(block)
                elif len(combined_blocks) == 0:
                    # Start a new group
                    combined_blocks = [block]
                else:
                    # Break - non-adjacent block
                    break
                last_index = idx
            
            # If we have multiple blocks, combine their bounding boxes
            if len(combined_blocks) > 1:
                logger.debug(f"📦 Combining {len(combined_blocks)} blocks for evidence")
                min_x = min(b.get("x", 0) for b in combined_blocks)
                min_y = min(b.get("y", 0) for b in combined_blocks)
                max_x = max(b.get("x", 0) + b.get("width", 0) for b in combined_blocks)
                max_y = max(b.get("y", 0) + b.get("height", 0) for b in combined_blocks)
                
                return {
                    "x": min_x,
                    "y": min_y,
                    "width": max_x - min_x,
                    "height": max_y - min_y
                }
            else:
                # Single block match
                best_block = combined_blocks[0] if combined_blocks else matching_blocks[0][1]
                bbox = {
                    "x": best_block.get("x", 0.1),
                    "y": best_block.get("y", 0.4),
                    "width": best_block.get("width", 0.8),
                    "height": best_block.get("height", 0.1)
                }
                logger.info(f"✅ Found text location: page {page_number}, bbox: {bbox}")
                return bbox
        
        # Final fallback: estimate
        logger.warning(f"⚠️ Could not find text location for snippet: {text_snippet[:50]}... on page {page_number}")
        return self._estimate_bounding_box(text_snippet, page_number)
    
    def _estimate_bounding_box(
        self,
        text_snippet: str,
        page_number: int
    ) -> Dict[str, float]:
        """
        Estimate bounding box coordinates for text snippet.
        
        This is a fallback when coordinate data is not available.
        Uses a simple heuristic based on text length and page number.
        
        Args:
            text_snippet: Text snippet
            page_number: Page number (1-indexed)
            
        Returns:
            Estimated bounding box {x, y, width, height} in normalized coordinates (0-1)
        """
        # Calculate height based on text length (rough estimate)
        # Assume ~50 characters per line, ~10 lines per paragraph
        text_length = len(text_snippet)
        estimated_lines = max(1, min(10, text_length / 50))
        estimated_height = min(0.3, max(0.05, estimated_lines * 0.03))
        
        # Vary position slightly based on page number to avoid all evidence on same spot
        page_offset = ((page_number - 1) * 0.1) % 0.5  # Cycle through page positions
        
        return {
            "x": 0.1,  # 10% from left
            "y": 0.2 + page_offset,  # Vary vertical position by page
            "width": 0.8,  # 80% width
            "height": estimated_height  # Dynamic height based on text
        }
    
    def get_evidence_by_category(self, category: str) -> List[EvidenceItem]:
        """Get all evidence items for a specific category."""
        return [e for e in self.evidence_items if e.category == category]
    
    def get_evidence_by_page(self, page_number: int) -> List[EvidenceItem]:
        """Get all evidence items for a specific page."""
        return [e for e in self.evidence_items if e.page_number == page_number]
    
    def get_all_evidence(self) -> List[Dict[str, Any]]:
        """Get all evidence items as dictionaries."""
        evidence_list = [e.to_dict() for e in self.evidence_items]
        
        # Log summary of evidence distribution
        page_distribution = {}
        for ev in self.evidence_items:
            page = ev.page_number or 1
            page_distribution[page] = page_distribution.get(page, 0) + 1
        
        logger.info(f"📊 Final evidence distribution by page (total: {len(evidence_list)}): {page_distribution}")
        logger.info(f"📄 Pages with evidence: {sorted(page_distribution.keys())}")
        
        return evidence_list
    
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

