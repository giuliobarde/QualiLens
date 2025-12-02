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
        
        # CRITICAL FIX: When we have coordinate data, always search all pages first
        # This is more accurate than text-based page detection which can give false positives
        # Store the original page_number for logging purposes
        original_page_number = page_number
        
        # Try to find actual bounding box using coordinate data
        # This is the most accurate method and will also determine the correct page number
        if bounding_box is None:
            if self.pages_with_coords and len(self.pages_with_coords) > 0:
                # Always search all pages when we have coordinate data - this is more accurate
                # than text-based page detection which can match on wrong pages
                best_page = None
                best_bbox = None
                best_score = 0
                
                # Search all pages for the text and find the best match
                # CRITICAL: Only accept high-quality matches to avoid false positives
                logger.debug(f"🔍 Searching all {len(self.pages_with_coords)} pages for evidence {evidence_id} with snippet: {text_snippet[:100]}...")
                for page_coord in self.pages_with_coords:
                    test_page_num = page_coord.get("page_num")
                    test_bbox = self._find_text_location(text_snippet, test_page_num)
                    if test_bbox:
                        logger.debug(f"  📄 Page {test_page_num}: Found potential match, calculating quality...")
                        # Calculate match quality (prefer pages with better text matches)
                        text_blocks = page_coord.get("text_blocks", [])
                        snippet_normalized = re.sub(r'\s+', ' ', text_snippet.strip().lower())
                        match_score = 0
                        is_exact_match = False
                        
                        for block in text_blocks:
                            block_text = block.get("text", "").lower()
                            block_normalized = re.sub(r'\s+', ' ', block_text.strip())
                            
                            # Exact substring match gets highest score
                            if snippet_normalized in block_normalized:
                                match_score = 1.0
                                is_exact_match = True
                                break
                            # Check reverse (block in snippet) - also exact match
                            elif block_normalized in snippet_normalized and len(block_normalized) > 20:
                                match_score = 0.95
                                is_exact_match = True
                                break
                            # Calculate word overlap for fuzzy matching
                            block_words = [w for w in block_normalized.split() if len(w) > 2]
                            snippet_words = [w for w in snippet_normalized.split() if len(w) > 2]
                            if len(block_words) > 0 and len(snippet_words) > 0:
                                matching_words = sum(1 for word in snippet_words if word in block_words)
                                word_score = matching_words / max(len(snippet_words), len(block_words))
                                match_score = max(match_score, word_score)
                        
                        # CRITICAL: Only accept matches with at least 80% quality
                        # Prefer exact matches over fuzzy matches
                        # If we have an exact match, use it immediately (don't search further)
                        if is_exact_match:
                            logger.info(f"✅ Found EXACT match for evidence {evidence_id} on page {test_page_num}, using this page")
                            best_page = test_page_num
                            best_bbox = test_bbox
                            best_score = 1.0
                            break  # Stop searching - we found the exact page
                        elif match_score >= 0.8 and match_score > best_score:
                            # Only update if this is a better fuzzy match
                            logger.debug(f"  📄 Page {test_page_num}: Good fuzzy match (score: {match_score:.2f}), updating best match")
                            best_score = match_score
                            best_page = test_page_num
                            best_bbox = test_bbox
                        else:
                            logger.debug(f"  📄 Page {test_page_num}: Match found but quality too low (score: {match_score:.2f} < 0.8 or not better than current best: {best_score:.2f})")
                
                # Only accept matches with at least 80% quality to avoid false positives
                if best_page and best_bbox and best_score >= 0.8:
                    # Update page_number to the correct page found via coordinate search
                    if original_page_number and original_page_number != best_page:
                        logger.info(f"✅ Found text location for evidence {evidence_id} on page {best_page} (match score: {best_score:.2f}, was incorrectly assigned to page {original_page_number})")
                    else:
                        logger.info(f"✅ Found text location for evidence {evidence_id} on page {best_page} (match score: {best_score:.2f})")
                    page_number = best_page
                    bounding_box = best_bbox
                else:
                    # No good match found (either no match or quality too low)
                    if best_page and best_bbox:
                        logger.warning(f"⚠️ Found text on page {best_page} but match quality ({best_score:.2f}) is too low (< 0.8) for evidence {evidence_id}, trying fallback")
                    # Couldn't find on any page using coordinate data
                    # Fall back to text-based page detection if we don't have a page number
                    if page_number is None and self.pdf_pages:
                        page_number = self._detect_page_number(text_snippet)
                    
                    if page_number is None:
                        page_number = 1
                        logger.warning(f"⚠️ Could not detect page number for evidence {evidence_id}, defaulting to page 1")
                    else:
                        logger.warning(f"⚠️ Could not find text location using coordinate data for evidence {evidence_id}, using estimated bbox on page {page_number}")
                    bounding_box = self._estimate_bounding_box(text_snippet, page_number)
            else:
                # No coordinate data available - use text-based page detection
                if page_number is None and self.pdf_pages:
                    page_number = self._detect_page_number(text_snippet)
                
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
        
        # Don't truncate here - let the tools handle truncation at sentence boundaries
        # Only apply a very generous limit to prevent memory issues (5000 chars)
        max_snippet_length = 5000
        final_snippet = text_snippet[:max_snippet_length] if len(text_snippet) > max_snippet_length else text_snippet
        
        evidence = EvidenceItem(
            id=evidence_id,
            category=category,
            text_snippet=final_snippet,
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
            # Require at least 70% match for coordinate-based detection (more strict)
            if best_page and best_score >= 0.7:
                logger.debug(f"✅ Found best match (score: {best_score:.2f}) for snippet on page {best_page} using coordinate data")
                return best_page
        
        # Fallback: search through page text
        # This is less accurate than coordinate-based search, so be more strict
        best_page = None
        best_score = 0
        
        for idx, page_text in enumerate(self.pdf_pages):
            page_normalized = re.sub(r'\s+', ' ', page_text.lower())
            
            # Calculate match score
            match_score = 0
            
            # Check if snippet appears in this page
            if len(snippet_normalized) > 20:
                # Use substring matching for longer snippets - prefer exact matches
                if snippet_normalized in page_normalized:
                    match_score = 1.0  # Full exact match - highest confidence
                elif snippet_normalized[:100] in page_normalized:
                    # Partial match - calculate how much of the snippet appears
                    snippet_len = len(snippet_normalized)
                    # Count how many characters of the snippet appear in the page
                    matched_chars = 0
                    for i in range(min(len(snippet_normalized), 200)):  # Check up to 200 chars
                        if i < len(snippet_normalized) and snippet_normalized[i] in page_normalized:
                            matched_chars += 1
                    match_score = matched_chars / snippet_len
            else:
                # For short snippets, check word overlap - require high overlap
                page_words = [w for w in page_normalized.split() if len(w) > 2]
                if len(page_words) > 0 and len(snippet_words) > 0:
                    matching_words = sum(1 for word in snippet_words if word in page_words)
                    match_score = matching_words / max(len(snippet_words), len(page_words))
            
            # Track the best match
            if match_score > best_score:
                best_score = match_score
                best_page = idx + 1  # 1-indexed
        
        # Require at least 70% match for text-based detection (more strict than before)
        # This reduces false positives where text might appear on multiple pages
        if best_page and best_score >= 0.7:
            logger.debug(f"✅ Found best match (score: {best_score:.2f}) for snippet on page {best_page} using text search")
            return best_page
        
        # If no good match found, return None (don't guess)
        logger.debug(f"⚠️ No good match found for snippet (best score: {best_score:.2f}), returning None")
        return None
    
    def _find_text_location(
        self,
        text_snippet: str,
        page_number: int
    ) -> Optional[Dict[str, float]]:
        """
        Find actual text location in PDF using coordinate data.
        CRITICAL: This must find EXACT evidence text, no more, no less.
        Uses precise substring matching and tight bounding boxes.
        
        Args:
            text_snippet: Text snippet to find (should be exact quote from PDF)
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
        
        # Normalize text snippet for matching (preserve word boundaries)
        snippet_normalized = re.sub(r'\s+', ' ', text_snippet.strip().lower())
        snippet_words = [w for w in snippet_normalized.split() if len(w) > 2]  # Filter out very short words
        
        if len(snippet_words) == 0:
            return self._estimate_bounding_box(text_snippet, page_number)
        
        # CRITICAL: Strategy 1 - Exact substring match (highest priority)
        # This is the most accurate - find blocks that contain the exact evidence text
        # Prefer smaller blocks (spans) over larger blocks (lines) for tighter highlighting
        exact_matches = []
        for i, block in enumerate(text_blocks):
            block_text = block.get("text", "")
            block_normalized = re.sub(r'\s+', ' ', block_text.strip().lower())
            
            # Check if snippet is contained in block (exact substring match)
            if snippet_normalized in block_normalized:
                # Calculate what portion of the block text this represents
                block_length = len(block_normalized)
                snippet_length = len(snippet_normalized)
                
                if block_length > 0:
                    snippet_ratio = snippet_length / block_length
                    
                    # Use the block's bounding box
                    block_bbox = {
                        "x": block.get("x", 0),
                        "y": block.get("y", 0),
                        "width": block.get("width", 0),
                        "height": block.get("height", 0)
                    }
                    
                    # Calculate block "size" (area) - prefer smaller blocks for tighter highlighting
                    block_area = block_bbox.get("width", 0) * block_bbox.get("height", 0)
                    
                    # Score: exact match gets 1.0, but prefer blocks where snippet is larger portion
                    # and blocks with smaller area (more precise)
                    match_score = 1.0
                    if snippet_ratio >= 0.8:
                        match_score = 1.0  # Snippet is most of the block - perfect
                    elif snippet_ratio >= 0.5:
                        match_score = 0.98  # Snippet is significant portion
                    else:
                        match_score = 0.95  # Snippet is part of block
                    
                    # Prefer smaller blocks (spans) - they give tighter highlighting
                    # Blocks with area < 0.01 are likely spans (more precise)
                    if block_area < 0.01:
                        match_score += 0.02  # Bonus for small blocks (spans)
                    
                    exact_matches.append((i, block, match_score, block_bbox, block_area))
                    logger.debug(f"✅ Exact match (ratio: {snippet_ratio:.2f}, area: {block_area:.4f}) in block {i}: {block_text[:50]}...")
        
        # If we found exact matches, use the best one
        # Prefer: 1) Higher match score, 2) Smaller block area (tighter highlighting)
        if exact_matches:
            # Sort by match score (descending), then by block area (ascending - prefer smaller blocks)
            exact_matches.sort(key=lambda x: (-x[2], x[4]))
            best_match = exact_matches[0]
            best_block = best_match[1]
            best_bbox = best_match[3]
            
            # Use the block's bounding box directly (should be tight, especially for spans)
            result_bbox = {
                "x": best_bbox.get("x", best_block.get("x", 0.1)),
                "y": best_bbox.get("y", best_block.get("y", 0.4)),
                "width": best_bbox.get("width", best_block.get("width", 0.8)),
                "height": best_bbox.get("height", best_block.get("height", 0.1))
            }
            
            logger.info(f"✅ Found exact text location: page {page_number}, bbox: {result_bbox}, match_score: {best_match[2]:.2f}, area: {best_match[4]:.4f}, snippet: {text_snippet[:50]}...")
            return result_bbox
        
        # Strategy 2: High-precision fuzzy match (require 80%+ word overlap)
        # Only use this if exact match fails, and require very high match quality
        high_precision_matches = []
        for i, block in enumerate(text_blocks):
            block_text = block.get("text", "").lower()
            block_normalized = re.sub(r'\s+', ' ', block_text.strip())
            block_words = [w for w in block_normalized.split() if len(w) > 2]
            
            if len(block_words) == 0:
                continue
            
            # Count matching words (case-insensitive)
            matching_words = sum(1 for word in snippet_words if word in block_words)
            match_ratio = matching_words / max(len(snippet_words), len(block_words))
            
            # CRITICAL: Require at least 80% word overlap for fuzzy match (was 50%)
            # This ensures we only match when the evidence text is truly present
            if match_ratio >= 0.8:
                # Also check that the matched words appear in order (more precise)
                snippet_word_indices = [block_words.index(w) for w in snippet_words if w in block_words]
                if len(snippet_word_indices) >= len(snippet_words) * 0.8:
                    # Words appear in similar order - good match
                    is_ordered = all(snippet_word_indices[i] <= snippet_word_indices[i+1] 
                                    for i in range(len(snippet_word_indices)-1))
                    if is_ordered or len(snippet_word_indices) == len(snippet_words):
                        # Calculate block area - prefer smaller blocks (spans) for tighter highlighting
                        block_bbox = {
                            "x": block.get("x", 0),
                            "y": block.get("y", 0),
                            "width": block.get("width", 0),
                            "height": block.get("height", 0)
                        }
                        block_area = block_bbox.get("width", 0) * block_bbox.get("height", 0)
                        high_precision_matches.append((i, block, match_ratio, block_area))
                        logger.debug(f"✅ High-precision fuzzy match (score: {match_ratio:.2f}, area: {block_area:.4f}) in block {i}: {block_text[:50]}...")
        
        # If we found high-precision matches, use the best one
        # Prefer: 1) Higher match score, 2) Smaller block area (tighter highlighting)
        if high_precision_matches:
            # Sort by match score (descending), then by block area (ascending - prefer smaller blocks)
            high_precision_matches.sort(key=lambda x: (-x[2], x[3]))
            best_match = high_precision_matches[0]
            best_block = best_match[1]
            
            # Use the block's bounding box (should be reasonably tight, especially for spans)
            result_bbox = {
                "x": best_block.get("x", 0.1),
                "y": best_block.get("y", 0.4),
                "width": best_block.get("width", 0.8),
                "height": best_block.get("height", 0.1)
            }
            
            logger.info(f"✅ Found high-precision text location: page {page_number}, bbox: {result_bbox}, match_score: {best_match[2]:.2f}, area: {best_match[3]:.4f}")
            return result_bbox
        
        # Strategy 3: Try to find evidence by searching for longest unique phrase
        # Extract the longest meaningful phrase (3+ words) from the snippet
        if len(snippet_words) >= 3:
            # Try phrases of different lengths, starting with longest
            for phrase_len in range(min(5, len(snippet_words)), 2, -1):
                for start_idx in range(len(snippet_words) - phrase_len + 1):
                    phrase_words = snippet_words[start_idx:start_idx + phrase_len]
                    phrase = ' '.join(phrase_words)
                    
                    for i, block in enumerate(text_blocks):
                        block_text = block.get("text", "").lower()
                        block_normalized = re.sub(r'\s+', ' ', block_text.strip())
                        
                        if phrase in block_normalized:
                            # Found the phrase - use this block
                            result_bbox = {
                                "x": block.get("x", 0.1),
                                "y": block.get("y", 0.4),
                                "width": block.get("width", 0.8),
                                "height": block.get("height", 0.1)
                            }
                            logger.info(f"✅ Found phrase match: page {page_number}, phrase: {phrase[:30]}..., bbox: {result_bbox}")
                            return result_bbox
        
        # Final fallback: estimate (but log warning)
        logger.warning(f"⚠️ Could not find exact text location for snippet: {text_snippet[:50]}... on page {page_number}. Using estimate.")
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

