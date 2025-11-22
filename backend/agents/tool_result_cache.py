"""
Tool Result Cache for QualiLens.

This module provides persistent caching of tool analysis results to speed up
re-analysis of the same papers and reduce API costs.
"""

import sqlite3
import hashlib
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class ToolResultCache:
    """
    Persistent cache for tool analysis results using SQLite.
    Caches results from all analysis tools (bias, statistical, reproducibility, etc.)
    to enable fast re-analysis and reduce API costs.
    """

    # Cache version - increment when tool logic changes to invalidate old caches
    # Version 1: Initial implementation - caching for all tools
    CACHE_VERSION = 1

    def __init__(self, db_path: str = None):
        """
        Initialize the tool result cache.

        Args:
            db_path: Path to SQLite database file. Defaults to 'tool_result_cache.db' in backend directory.
        """
        if db_path is None:
            # Default to backend directory
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(backend_dir, "tool_result_cache.db")

        self.db_path = db_path
        self._initialize_db()
        logger.info(f"Tool result cache initialized at: {self.db_path}")

    def _initialize_db(self):
        """Initialize the SQLite database with required schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_result_cache (
                    cache_key TEXT PRIMARY KEY,
                    tool_name TEXT NOT NULL,
                    result_data TEXT NOT NULL,
                    cache_version INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tool_name
                ON tool_result_cache(tool_name, cache_version)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_version
                ON tool_result_cache(cache_version)
            """)

            conn.commit()
            conn.close()
            logger.info("Tool result cache database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize tool result cache database: {str(e)}")
            raise

    def _calculate_cache_key(self, tool_name: str, text_content: str, **kwargs) -> str:
        """
        Calculate a stable cache key for tool execution.
        
        Args:
            tool_name: Name of the tool
            text_content: Paper content text
            **kwargs: Additional parameters that affect the result
            
        Returns:
            Hex string of SHA256 hash
        """
        # Create a stable representation of the input
        key_parts = [
            tool_name,
            text_content,
            json.dumps(kwargs, sort_keys=True) if kwargs else ""
        ]
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode('utf-8')).hexdigest()

    def get_cached_result(self, tool_name: str, text_content: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached result for a tool execution.

        Args:
            tool_name: Name of the tool
            text_content: Paper content text
            **kwargs: Additional parameters that affect the result

        Returns:
            Dict with cached result if cache hit, None if cache miss
        """
        try:
            cache_key = self._calculate_cache_key(tool_name, text_content, **kwargs)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                """SELECT result_data, created_at
                   FROM tool_result_cache
                   WHERE cache_key = ? AND cache_version = ?""",
                (cache_key, self.CACHE_VERSION)
            )
            result = cursor.fetchone()

            if result:
                # Update last accessed timestamp
                conn.execute(
                    "UPDATE tool_result_cache SET last_accessed = ? WHERE cache_key = ?",
                    (datetime.now().isoformat(), cache_key)
                )
                conn.commit()

                result_data = json.loads(result[0])
                result_data["cached"] = True
                result_data["cache_timestamp"] = result[1]
                result_data["cache_key"] = cache_key
                
                logger.info(f"Cache HIT for tool: {tool_name} (key: {cache_key[:16]}...)")
                conn.close()
                return result_data

            conn.close()
            logger.debug(f"Cache MISS for tool: {tool_name} (key: {cache_key[:16]}...)")
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve cached result: {str(e)}")
            return None

    def cache_result(self, tool_name: str, text_content: str, result_data: Dict[str, Any], **kwargs) -> bool:
        """
        Cache a tool result.

        Args:
            tool_name: Name of the tool
            text_content: Paper content text
            result_data: Dict containing the tool result
            **kwargs: Additional parameters that affect the result

        Returns:
            True if successfully cached, False otherwise
        """
        try:
            cache_key = self._calculate_cache_key(tool_name, text_content, **kwargs)

            # Create a copy of result_data without cached metadata
            cache_data = {k: v for k, v in result_data.items() 
                         if k not in ["cached", "cache_timestamp", "cache_key"]}

            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """INSERT OR REPLACE INTO tool_result_cache
                   (cache_key, tool_name, result_data, cache_version, created_at, last_accessed)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    cache_key,
                    tool_name,
                    json.dumps(cache_data),
                    self.CACHE_VERSION,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                )
            )
            conn.commit()
            conn.close()

            logger.info(f"Tool result cached successfully: {tool_name} (key: {cache_key[:16]}...)")
            return True

        except Exception as e:
            logger.error(f"Failed to cache tool result: {str(e)}")
            return False

    def clear_cache(self, tool_name: str = None, older_than_days: int = None) -> int:
        """
        Clear cached tool results.

        Args:
            tool_name: If specified, only clear cache for this tool. If None, clear all.
            older_than_days: If specified, only clear results older than this many days.
                           If None, clear all results for current cache version.

        Returns:
            Number of entries cleared
        """
        try:
            conn = sqlite3.connect(self.db_path)

            if older_than_days is not None:
                if tool_name:
                    cursor = conn.execute(
                        """DELETE FROM tool_result_cache
                           WHERE tool_name = ? AND cache_version = ?
                           AND julianday('now') - julianday(created_at) > ?""",
                        (tool_name, self.CACHE_VERSION, older_than_days)
                    )
                else:
                    cursor = conn.execute(
                        """DELETE FROM tool_result_cache
                           WHERE cache_version = ?
                           AND julianday('now') - julianday(created_at) > ?""",
                        (self.CACHE_VERSION, older_than_days)
                    )
            else:
                if tool_name:
                    cursor = conn.execute(
                        "DELETE FROM tool_result_cache WHERE tool_name = ? AND cache_version = ?",
                        (tool_name, self.CACHE_VERSION)
                    )
                else:
                    cursor = conn.execute(
                        "DELETE FROM tool_result_cache WHERE cache_version = ?",
                        (self.CACHE_VERSION,)
                    )

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            logger.info(f"Cleared {deleted_count} entries from tool result cache")
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
            cursor = conn.execute("SELECT COUNT(*) FROM tool_result_cache WHERE cache_version = ?", (self.CACHE_VERSION,))
            total_entries = cursor.fetchone()[0]

            # Entries by tool
            cursor = conn.execute(
                """SELECT tool_name, COUNT(*) 
                   FROM tool_result_cache 
                   WHERE cache_version = ? 
                   GROUP BY tool_name""",
                (self.CACHE_VERSION,)
            )
            by_tool = {row[0]: row[1] for row in cursor.fetchall()}

            # Oldest entry
            cursor = conn.execute("SELECT MIN(created_at) FROM tool_result_cache WHERE cache_version = ?", (self.CACHE_VERSION,))
            oldest_entry = cursor.fetchone()[0]

            # Most recent entry
            cursor = conn.execute("SELECT MAX(created_at) FROM tool_result_cache WHERE cache_version = ?", (self.CACHE_VERSION,))
            newest_entry = cursor.fetchone()[0]

            conn.close()

            return {
                "total_entries": total_entries,
                "entries_by_tool": by_tool,
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

