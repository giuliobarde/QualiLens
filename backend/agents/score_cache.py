"""
Score Cache for QualiLens.

This module provides persistent caching of paper quality scores to ensure
consistency across multiple analyses of the same paper.
"""

import sqlite3
import hashlib
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class ScoreCache:
    """
    Persistent cache for paper quality scores using SQLite.
    Ensures consistent scoring for identical paper content.
    """

    # Cache version - increment when scoring logic changes to invalidate old caches
    # Version 1: Phase 1 - Basic deterministic scoring with stable hashing
    # Version 2: Phase 2 - Enhanced scoring with reproducibility, bias penalties, research gaps bonuses
    # Version 3: Phase 2 Revised - Weighted component scoring (60% methodology, 20% bias, 10% reproducibility, 10% research gaps)
    # Version 4: Temperature fix - Added temperature=0.0 to all analysis tools (bias, reproducibility, gaps, citation, statistical)
    # Version 5: Chain-of-Thought - Two-step reasoning for bias detection and research gap identification (brainstorm + verify)
    # Version 6: Enhanced Reproducibility - Multi-factor analysis with 8 weighted components (data, code, methods, materials, stats, prereg, docs, version)
    CACHE_VERSION = 6

    def __init__(self, db_path: str = None):
        """
        Initialize the score cache.

        Args:
            db_path: Path to SQLite database file. Defaults to 'score_cache.db' in current directory.
        """
        if db_path is None:
            # Default to backend directory
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(backend_dir, "score_cache.db")

        self.db_path = db_path
        self._initialize_db()
        logger.info(f"Score cache initialized at: {self.db_path}")

    def _initialize_db(self):
        """Initialize the SQLite database with required schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS score_cache (
                    content_hash TEXT PRIMARY KEY,
                    overall_score REAL NOT NULL,
                    score_breakdown TEXT NOT NULL,
                    field_detected TEXT,
                    cache_version INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_version
                ON score_cache(cache_version)
            """)

            conn.commit()
            conn.close()
            logger.info("Score cache database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize score cache database: {str(e)}")
            raise

    def _calculate_content_hash(self, content: str) -> str:
        """
        Calculate a stable SHA256 hash of paper content.

        Args:
            content: Paper content text

        Returns:
            Hex string of SHA256 hash
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def get_cached_score(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached score for given paper content.

        Args:
            content: Paper content text

        Returns:
            Dict with score data if cache hit, None if cache miss
        """
        try:
            content_hash = self._calculate_content_hash(content)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                """SELECT overall_score, score_breakdown, field_detected, created_at
                   FROM score_cache
                   WHERE content_hash = ? AND cache_version = ?""",
                (content_hash, self.CACHE_VERSION)
            )
            result = cursor.fetchone()

            if result:
                # Update last accessed timestamp
                conn.execute(
                    "UPDATE score_cache SET last_accessed = ? WHERE content_hash = ?",
                    (datetime.now().isoformat(), content_hash)
                )
                conn.commit()

                score_data = {
                    "overall_score": result[0],
                    "score_breakdown": json.loads(result[1]),
                    "field_detected": result[2],
                    "cached": True,
                    "cache_timestamp": result[3],
                    "content_hash": content_hash
                }
                logger.info(f"Cache HIT for content hash: {content_hash[:16]}...")
                conn.close()
                return score_data

            conn.close()
            logger.info(f"Cache MISS for content hash: {content_hash[:16]}...")
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve cached score: {str(e)}")
            return None

    def cache_score(self, content: str, score_data: Dict[str, Any]) -> bool:
        """
        Cache a score for given paper content.

        Args:
            content: Paper content text
            score_data: Dict containing:
                - overall_score: float
                - score_breakdown: dict with dimension scores
                - field_detected: str (optional)

        Returns:
            True if successfully cached, False otherwise
        """
        try:
            content_hash = self._calculate_content_hash(content)

            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """INSERT OR REPLACE INTO score_cache
                   (content_hash, overall_score, score_breakdown, field_detected, cache_version, created_at, last_accessed)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    content_hash,
                    score_data.get("overall_score", 0.0),
                    json.dumps(score_data.get("score_breakdown", {})),
                    score_data.get("field_detected", "unknown"),
                    self.CACHE_VERSION,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                )
            )
            conn.commit()
            conn.close()

            logger.info(f"Score cached successfully for hash: {content_hash[:16]}... (score: {score_data.get('overall_score', 0.0)})")
            return True

        except Exception as e:
            logger.error(f"Failed to cache score: {str(e)}")
            return False

    def clear_cache(self, older_than_days: int = None) -> int:
        """
        Clear cached scores.

        Args:
            older_than_days: If specified, only clear scores older than this many days.
                           If None, clear all scores for current cache version.

        Returns:
            Number of entries cleared
        """
        try:
            conn = sqlite3.connect(self.db_path)

            if older_than_days is not None:
                # Clear old entries
                cursor = conn.execute(
                    """DELETE FROM score_cache
                       WHERE julianday('now') - julianday(created_at) > ?""",
                    (older_than_days,)
                )
            else:
                # Clear all entries for current version
                cursor = conn.execute(
                    "DELETE FROM score_cache WHERE cache_version = ?",
                    (self.CACHE_VERSION,)
                )

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            logger.info(f"Cleared {deleted_count} entries from score cache")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")
            return 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.

        Returns:
            Dict with cache statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)

            # Total entries
            cursor = conn.execute("SELECT COUNT(*) FROM score_cache WHERE cache_version = ?", (self.CACHE_VERSION,))
            total_entries = cursor.fetchone()[0]

            # Average score
            cursor = conn.execute("SELECT AVG(overall_score) FROM score_cache WHERE cache_version = ?", (self.CACHE_VERSION,))
            avg_score = cursor.fetchone()[0] or 0.0

            # Oldest entry
            cursor = conn.execute("SELECT MIN(created_at) FROM score_cache WHERE cache_version = ?", (self.CACHE_VERSION,))
            oldest_entry = cursor.fetchone()[0]

            # Most recent entry
            cursor = conn.execute("SELECT MAX(created_at) FROM score_cache WHERE cache_version = ?", (self.CACHE_VERSION,))
            newest_entry = cursor.fetchone()[0]

            conn.close()

            return {
                "total_entries": total_entries,
                "average_score": round(avg_score, 2),
                "oldest_entry": oldest_entry,
                "newest_entry": newest_entry,
                "cache_version": self.CACHE_VERSION,
                "db_path": self.db_path
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {
                "error": str(e),
                "cache_version": self.CACHE_VERSION,
                "db_path": self.db_path
            }
