"""
Progress tracking system for real-time stage updates.

This module provides a progress tracker that allows the backend to emit
stage updates that the frontend can poll for real-time progress information.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ProcessingStage(Enum):
    """Enumeration of processing stages."""
    INITIALIZING = "initializing"
    CLASSIFYING = "classifying"
    AGENT_SELECTION = "agent_selection"
    PDF_PARSING = "pdf_parsing"
    LLM_ANALYSIS = "llm_analysis"
    TOOL_EXECUTION = "tool_execution"
    EVIDENCE_COLLECTION = "evidence_collection"
    SCORING = "scoring"
    COMPILING = "compiling"
    COMPLETE = "complete"
    ERROR = "error"


class ProgressTracker:
    """
    Tracks progress for analysis requests.
    
    Uses a simple in-memory store keyed by request ID.
    For production, this could be replaced with Redis or a database.
    """
    
    def __init__(self):
        self._progress_store: Dict[str, Dict[str, Any]] = {}
        self._cleanup_interval = 3600  # Clean up progress after 1 hour
    
    def create_tracker(self, request_id: Optional[str] = None) -> str:
        """
        Create a new progress tracker for a request.
        
        Args:
            request_id: Optional request ID. If not provided, generates a UUID.
            
        Returns:
            str: The request ID
        """
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        self._progress_store[request_id] = {
            "request_id": request_id,
            "stage": ProcessingStage.INITIALIZING.value,
            "stage_name": "Initializing",
            "progress": 0.0,
            "estimated_time_remaining": None,
            "estimated_total_time": None,
            "message": "Starting analysis...",
            "start_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
            "metadata": {}
        }
        
        logger.info(f"Created progress tracker for request: {request_id}")
        return request_id
    
    def update_stage(
        self,
        request_id: str,
        stage: ProcessingStage,
        message: Optional[str] = None,
        progress: Optional[float] = None,
        estimated_time_remaining: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Update the progress stage for a request.
        
        Args:
            request_id: The request ID
            stage: The current processing stage
            message: Optional message describing the current stage
            progress: Optional progress percentage (0-100)
            estimated_time_remaining: Optional estimated time remaining in seconds
            metadata: Optional additional metadata
        """
        if request_id not in self._progress_store:
            logger.warning(f"Progress tracker not found for request: {request_id}")
            return
        
        stage_names = {
            ProcessingStage.INITIALIZING: "Initializing",
            ProcessingStage.CLASSIFYING: "Classifying Query",
            ProcessingStage.AGENT_SELECTION: "Selecting Agent",
            ProcessingStage.PDF_PARSING: "Parsing PDF",
            ProcessingStage.LLM_ANALYSIS: "LLM Analysis",
            ProcessingStage.TOOL_EXECUTION: "Running Analysis Tools",
            ProcessingStage.EVIDENCE_COLLECTION: "Collecting Evidence",
            ProcessingStage.SCORING: "Calculating Scores",
            ProcessingStage.COMPILING: "Compiling Results",
            ProcessingStage.COMPLETE: "Complete",
            ProcessingStage.ERROR: "Error"
        }
        
        tracker = self._progress_store[request_id]
        tracker["stage"] = stage.value
        tracker["stage_name"] = stage_names.get(stage, stage.value)
        tracker["last_update"] = datetime.now().isoformat()
        
        if message:
            tracker["message"] = message
        if progress is not None:
            tracker["progress"] = min(100.0, max(0.0, progress))
        if estimated_time_remaining is not None:
            tracker["estimated_time_remaining"] = estimated_time_remaining
        if metadata:
            tracker["metadata"].update(metadata)
        
        logger.info(f"Progress update for {request_id}: {stage.value} - {message or stage_names.get(stage, '')}")
    
    def get_progress(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current progress for a request.
        
        Args:
            request_id: The request ID
            
        Returns:
            Optional[Dict[str, Any]]: Progress information or None if not found
        """
        return self._progress_store.get(request_id)
    
    def complete(self, request_id: str, success: bool = True, message: Optional[str] = None):
        """
        Mark a request as complete.
        
        Args:
            request_id: The request ID
            success: Whether the request completed successfully
            message: Optional completion message
        """
        if request_id not in self._progress_store:
            return
        
        tracker = self._progress_store[request_id]
        tracker["stage"] = ProcessingStage.COMPLETE.value if success else ProcessingStage.ERROR.value
        tracker["stage_name"] = "Complete" if success else "Error"
        tracker["progress"] = 100.0 if success else tracker.get("progress", 0.0)
        tracker["estimated_time_remaining"] = 0.0
        tracker["last_update"] = datetime.now().isoformat()
        
        if message:
            tracker["message"] = message
        
        # Calculate actual time taken
        start_time = datetime.fromisoformat(tracker["start_time"])
        end_time = datetime.now()
        actual_time = (end_time - start_time).total_seconds()
        tracker["actual_time_taken"] = actual_time
        
        logger.info(f"Request {request_id} completed in {actual_time:.2f}s")
    
    def cleanup(self, request_id: str):
        """Remove a progress tracker (cleanup)."""
        if request_id in self._progress_store:
            del self._progress_store[request_id]
            logger.debug(f"Cleaned up progress tracker for request: {request_id}")


# Global instance
_progress_tracker = ProgressTracker()


def get_progress_tracker() -> ProgressTracker:
    """Get the global progress tracker instance."""
    return _progress_tracker

