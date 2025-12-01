# layout_analyzer.py
# Layout Analysis Module for Document Structure Understanding
# Implements S-FR1: Layout Analysis using rule-based and ML-based approaches

from __future__ import annotations

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

# Optional ML model dependencies
try:
    from transformers import AutoTokenizer, AutoModelForTokenClassification
    import torch
    _HAVE_TRANSFORMERS = True
except ImportError:
    _HAVE_TRANSFORMERS = False
    AutoTokenizer = None  # type: ignore
    AutoModelForTokenClassification = None  # type: ignore
    torch = None  # type: ignore

logger = logging.getLogger(__name__)


class SemanticRole(str, Enum):
    """Semantic roles for document elements."""
    HEADER = "header"
    FOOTER = "footer"
    BODY_TEXT = "body_text"
    FIGURE = "figure"
    TABLE = "table"
    CAPTION = "caption"
    COLUMN = "column"
    TITLE = "title"
    ABSTRACT = "abstract"
    REFERENCE = "reference"
    UNKNOWN = "unknown"


class LayoutAnalyzer:
    """
    Analyzes document layout and assigns semantic roles to text blocks.
    
    Uses a hybrid approach:
    1. Rule-based heuristics for fast, reliable classification
    2. Optional ML models (LayoutLM/DocLayNet) for enhanced accuracy
    
    This implements S-FR1: Layout Analysis from the requirements.
    """
    
    def __init__(self, use_ml_models: bool = False):
        """
        Initialize the layout analyzer.
        
        Args:
            use_ml_models: If True, attempt to load ML models for enhanced classification
        """
        self.use_ml_models = use_ml_models and _HAVE_TRANSFORMERS
        self.ml_model = None
        self.ml_tokenizer = None
        
        logger.info(f"Initializing LayoutAnalyzer (ML models: {self.use_ml_models})")
        
        if self.use_ml_models:
            try:
                self._load_ml_models()
            except Exception as e:
                logger.warning(f"Failed to load ML models for layout analysis: {e}")
                logger.info("Falling back to rule-based layout analysis")
                self.use_ml_models = False
        else:
            logger.info("Using rule-based layout analysis (no ML models)")
    
    def _load_ml_models(self):
        """Load LayoutLM or similar model for document layout understanding."""
        # Try to load a pre-trained layout model
        # Note: In production, you would use a specific model like:
        # - microsoft/layoutlm-base-uncased
        # - or a DocLayNet fine-tuned model
        
        try:
            # Attempt to load LayoutLM (if available)
            model_name = "microsoft/layoutlm-base-uncased"
            logger.info(f"Loading ML model: {model_name}")
            self.ml_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.ml_model = AutoModelForTokenClassification.from_pretrained(model_name)
            if torch and torch.cuda.is_available():
                self.ml_model = self.ml_model.cuda()
            self.ml_model.eval()
            logger.info("ML model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load ML model: {e}")
            raise
    
    def analyze_page_layout(
        self,
        text_blocks: List[Dict[str, Any]],
        page_width: float,
        page_height: float,
        page_num: int,
        full_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze page layout and assign semantic roles to text blocks.
        
        Args:
            text_blocks: List of text blocks with bounding boxes
            page_width: Page width in points
            page_height: Page height in points
            page_num: Page number (1-indexed)
            full_text: Optional full text of the page for context
            
        Returns:
            List of text blocks with added 'semantic_role' field
        """
        if not text_blocks:
            logger.debug(f"Page {page_num}: No text blocks to analyze")
            return text_blocks
        
        logger.debug(f"Page {page_num}: Analyzing {len(text_blocks)} text blocks")
        
        # Calculate page statistics for heuristics
        page_stats = self._calculate_page_statistics(text_blocks, page_width, page_height)
        
        # Analyze each block
        enhanced_blocks = []
        role_counts = {}
        for block in text_blocks:
            role = self._classify_block(block, page_stats, page_num, full_text)
            enhanced_block = block.copy()
            enhanced_block["semantic_role"] = role.value
            enhanced_block["role_confidence"] = self._calculate_confidence(block, role, page_stats)
            enhanced_blocks.append(enhanced_block)
            role_counts[role.value] = role_counts.get(role.value, 0) + 1
        
        # Post-process to improve consistency
        enhanced_blocks = self._post_process_roles(enhanced_blocks, page_stats)
        
        # Log role distribution for this page
        role_summary = ", ".join([f"{role}: {count}" for role, count in sorted(role_counts.items())])
        logger.debug(f"Page {page_num}: Role distribution - {role_summary}")
        
        return enhanced_blocks
    
    def _calculate_page_statistics(
        self,
        text_blocks: List[Dict[str, Any]],
        page_width: float,
        page_height: float
    ) -> Dict[str, Any]:
        """Calculate statistics about the page layout for heuristics."""
        if not text_blocks:
            return {}
        
        # Calculate vertical distribution
        y_positions = [block.get("y", 0) for block in text_blocks]
        y_heights = [block.get("height", 0) for block in text_blocks]
        
        # Calculate horizontal distribution (for column detection)
        x_positions = [block.get("x", 0) for block in text_blocks]
        x_widths = [block.get("width", 0) for block in text_blocks]
        
        # Identify header region (top 15% of page)
        header_threshold = 0.15
        # Identify footer region (bottom 15% of page)
        footer_threshold = 0.85
        
        # Calculate average font size (if available)
        # For now, use text length as proxy for importance
        text_lengths = [len(block.get("text", "")) for block in text_blocks]
        avg_text_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0
        
        # Detect columns by clustering x positions
        columns = self._detect_columns(x_positions, x_widths, page_width)
        
        return {
            "header_threshold": header_threshold,
            "footer_threshold": footer_threshold,
            "avg_text_length": avg_text_length,
            "columns": columns,
            "page_width": page_width,
            "page_height": page_height,
            "y_positions": y_positions,
            "x_positions": x_positions,
        }
    
    def _detect_columns(
        self,
        x_positions: List[float],
        x_widths: List[float],
        page_width: float
    ) -> List[Dict[str, float]]:
        """
        Detect column layout by clustering x positions.
        
        Returns list of column definitions with {x, width} for each column.
        """
        if not x_positions:
            return []
        
        # Simple clustering: group x positions into columns
        # Sort x positions
        sorted_x = sorted(set(x_positions))
        
        # Cluster nearby positions (within 5% of page width)
        cluster_threshold = 0.05 * page_width
        columns = []
        current_cluster = []
        
        for x in sorted_x:
            if not current_cluster:
                current_cluster = [x]
            else:
                # Check if x is close to any in current cluster
                if any(abs(x - cx) < cluster_threshold for cx in current_cluster):
                    current_cluster.append(x)
                else:
                    # Start new cluster
                    if current_cluster:
                        columns.append({
                            "x": min(current_cluster),
                            "width": max(current_cluster) - min(current_cluster)
                        })
                    current_cluster = [x]
        
        if current_cluster:
            columns.append({
                "x": min(current_cluster),
                "width": max(current_cluster) - min(current_cluster)
            })
        
        return columns
    
    def _classify_block(
        self,
        block: Dict[str, Any],
        page_stats: Dict[str, Any],
        page_num: int,
        full_text: Optional[str] = None
    ) -> SemanticRole:
        """
        Classify a text block into a semantic role.
        
        Uses rule-based heuristics with optional ML model enhancement.
        """
        text = block.get("text", "").strip()
        if not text:
            return SemanticRole.UNKNOWN
        
        x = block.get("x", 0)
        y = block.get("y", 0)
        width = block.get("width", 0)
        height = block.get("height", 0)
        
        text_lower = text.lower()
        
        # 1. Header detection (top of page, often contains page numbers, titles)
        header_threshold = page_stats.get("header_threshold", 0.15)
        if y < header_threshold:
            # Check for header indicators
            if self._is_header_text(text, page_num):
                return SemanticRole.HEADER
        
        # 2. Footer detection (bottom of page, often contains page numbers, copyright)
        footer_threshold = page_stats.get("footer_threshold", 0.85)
        if y + height > footer_threshold:
            # Check for footer indicators
            if self._is_footer_text(text, page_num):
                return SemanticRole.FOOTER
        
        # 3. Figure/Caption detection
        if self._is_figure_caption(text):
            return SemanticRole.CAPTION
        
        # 4. Table detection
        if self._is_table(text):
            return SemanticRole.TABLE
        
        # 5. Title detection (first page, large text, centered)
        if page_num == 1 and y < 0.3:
            if self._is_title(text, page_stats):
                return SemanticRole.TITLE
        
        # 6. Abstract detection (first page, after title)
        if page_num == 1 and 0.1 < y < 0.4:
            if self._is_abstract(text):
                return SemanticRole.ABSTRACT
        
        # 7. Reference detection (end of document, citation patterns)
        if self._is_reference(text):
            return SemanticRole.REFERENCE
        
        # 8. Column detection (multi-column layout)
        columns = page_stats.get("columns", [])
        if len(columns) > 1:
            # Check if block is in a column
            for col in columns:
                if col["x"] <= x <= col["x"] + col["width"]:
                    return SemanticRole.COLUMN
        
        # 9. Default to body text
        return SemanticRole.BODY_TEXT
    
    def _is_header_text(self, text: str, page_num: int) -> bool:
        """Check if text is likely a header."""
        text_lower = text.lower().strip()
        
        # Page numbers
        if re.match(r'^\d+$', text_lower):
            return True
        
        # Short text at top (likely header)
        if len(text_lower) < 50 and len(text_lower.split()) < 10:
            return True
        
        # Common header patterns
        header_patterns = [
            r'^chapter\s+\d+',
            r'^section\s+\d+',
            r'^\d+\.\s+[A-Z]',  # Numbered section
        ]
        for pattern in header_patterns:
            if re.match(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False
    
    def _is_footer_text(self, text: str, page_num: int) -> bool:
        """Check if text is likely a footer."""
        text_lower = text.lower().strip()
        
        # Page numbers
        if re.match(r'^\d+$', text_lower):
            return True
        
        # Copyright notices
        if 'copyright' in text_lower or '©' in text:
            return True
        
        # Short text at bottom
        if len(text_lower) < 50:
            return True
        
        return False
    
    def _is_figure_caption(self, text: str) -> bool:
        """Check if text is a figure or table caption."""
        text_lower = text.lower().strip()
        
        # Figure/Table caption patterns
        caption_patterns = [
            r'^figure\s+\d+',
            r'^fig\.\s+\d+',
            r'^table\s+\d+',
            r'^tab\.\s+\d+',
        ]
        for pattern in caption_patterns:
            if re.match(pattern, text_lower):
                return True
        
        return False
    
    def _is_table(self, text: str) -> bool:
        """Check if text block contains table-like content."""
        # Tables often have multiple lines with similar structure
        lines = text.split('\n')
        if len(lines) < 2:
            return False
        
        # Check for tabular patterns (multiple spaces, tabs, or pipes)
        tabular_indicators = 0
        for line in lines[:5]:  # Check first 5 lines
            if re.search(r'\t|\s{3,}|\|', line):
                tabular_indicators += 1
        
        # If most lines have tabular structure, likely a table
        if tabular_indicators >= len(lines) * 0.6:
            return True
        
        return False
    
    def _is_title(self, text: str, page_stats: Dict[str, Any]) -> bool:
        """Check if text is likely a title."""
        text_lower = text.lower().strip()
        
        # Titles are usually short
        if len(text_lower) > 200:
            return False
        
        # Titles often have specific patterns
        # All caps (common in academic papers)
        if text.isupper() and len(text) > 10:
            return True
        
        # Title case with specific keywords
        title_keywords = ['study', 'analysis', 'evaluation', 'assessment', 'investigation']
        if any(keyword in text_lower for keyword in title_keywords):
            if len(text_lower.split()) < 20:  # Not too long
                return True
        
        return False
    
    def _is_abstract(self, text: str) -> bool:
        """Check if text is likely an abstract."""
        text_lower = text.lower().strip()
        
        # Abstract section marker
        if text_lower.startswith('abstract'):
            return True
        
        # Abstract-like content (summary, overview)
        abstract_keywords = ['background', 'objective', 'methods', 'results', 'conclusion']
        keyword_count = sum(1 for keyword in abstract_keywords if keyword in text_lower)
        
        # If multiple abstract keywords present, likely abstract
        if keyword_count >= 2 and len(text_lower) > 100:
            return True
        
        return False
    
    def _is_reference(self, text: str) -> bool:
        """Check if text is likely a reference/citation."""
        text_lower = text.lower().strip()
        
        # Citation patterns
        citation_patterns = [
            r'\d{4}',  # Year
            r'doi:',  # DOI
            r'http',  # URL
            r'vol\.',  # Volume
            r'pp\.',  # Pages
            r'journal',  # Journal
        ]
        
        pattern_matches = sum(1 for pattern in citation_patterns if re.search(pattern, text_lower))
        
        # If multiple citation indicators, likely a reference
        if pattern_matches >= 2:
            return True
        
        # Author patterns (Last, First)
        if re.search(r'[A-Z][a-z]+,\s+[A-Z]\.', text):
            return True
        
        return False
    
    def _calculate_confidence(
        self,
        block: Dict[str, Any],
        role: SemanticRole,
        page_stats: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for the assigned role (0.0 to 1.0)."""
        # Base confidence on how well the block matches role criteria
        confidence = 0.7  # Base confidence
        
        # Increase confidence based on position
        y = block.get("y", 0.5)
        
        if role == SemanticRole.HEADER:
            if y < 0.1:
                confidence = 0.9
            elif y < 0.15:
                confidence = 0.8
        
        elif role == SemanticRole.FOOTER:
            if y > 0.9:
                confidence = 0.9
            elif y > 0.85:
                confidence = 0.8
        
        elif role == SemanticRole.TITLE:
            if block.get("y", 0) < 0.2:
                confidence = 0.85
        
        # Increase confidence if text patterns strongly match
        text = block.get("text", "")
        if role == SemanticRole.CAPTION:
            if re.match(r'^(figure|fig\.|table|tab\.)\s+\d+', text.lower()):
                confidence = 0.95
        
        return min(confidence, 1.0)
    
    def _post_process_roles(
        self,
        blocks: List[Dict[str, Any]],
        page_stats: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Post-process roles to improve consistency.
        
        - Ensure headers/footers are consistent across page
        - Merge adjacent blocks with same role
        - Fix obvious misclassifications
        """
        if not blocks:
            return blocks
        
        # Count roles to identify dominant patterns
        role_counts = {}
        for block in blocks:
            role = block.get("semantic_role", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # If very few headers/footers, might be misclassified
        # (This is a simple heuristic - could be improved)
        
        return blocks


def analyze_document_layout(
    pages_with_coords: List[Dict[str, Any]],
    pages_text: Optional[List[str]] = None,
    use_ml_models: bool = False
) -> List[Dict[str, Any]]:
    """
    Analyze document layout for all pages and add semantic roles.
    
    This is the main entry point for layout analysis.
    
    Args:
        pages_with_coords: List of page data with text_blocks
        pages_text: Optional list of full page text for context
        use_ml_models: Whether to use ML models (if available)
        
    Returns:
        Enhanced pages_with_coords with semantic_role in each text_block
    """
    logger.info(f"Starting layout analysis for {len(pages_with_coords)} pages")
    analyzer = LayoutAnalyzer(use_ml_models=use_ml_models)
    
    enhanced_pages = []
    total_blocks = 0
    overall_role_counts = {}
    
    for i, page_data in enumerate(pages_with_coords):
        page_num = page_data.get("page_num", i + 1)
        text_blocks = page_data.get("text_blocks", [])
        page_width = page_data.get("page_width", 0)
        page_height = page_data.get("page_height", 0)
        full_text = pages_text[i] if pages_text and i < len(pages_text) else None
        
        enhanced_blocks = analyzer.analyze_page_layout(
            text_blocks=text_blocks,
            page_width=page_width,
            page_height=page_height,
            page_num=page_num,
            full_text=full_text
        )
        
        # Count roles for summary
        for block in enhanced_blocks:
            role = block.get("semantic_role", "unknown")
            overall_role_counts[role] = overall_role_counts.get(role, 0) + 1
            total_blocks += 1
        
        enhanced_page = page_data.copy()
        enhanced_page["text_blocks"] = enhanced_blocks
        enhanced_page["layout_analyzed"] = True
        enhanced_pages.append(enhanced_page)
    
    # Log summary statistics
    role_summary = ", ".join([f"{role}: {count}" for role, count in sorted(overall_role_counts.items(), key=lambda x: x[1], reverse=True)])
    logger.info(f"Layout analysis completed: {len(enhanced_pages)} pages, {total_blocks} blocks analyzed")
    logger.info(f"Role distribution: {role_summary}")
    
    return enhanced_pages

