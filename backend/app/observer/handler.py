"""
This module defines the event handler for the watchdog observer.
The `PipelineEventHandler` class contains the logic that executes when
a file system event (specifically, the creation of a 'complete' file)
is detected in the monitored directory.
"""

import logging
import os
import time
import threading
from watchdog.events import FileSystemEventHandler
from app.pipeline import run_all  # Import the main pipeline runner function.
from app.core.config import settings

class PipelineEventHandler(FileSystemEventHandler):
    """
    Handles file system events in the trigger directory. When the 'complete'
    file is created, it triggers the data processing pipeline.
    
    Uses a threading lock to prevent concurrent pipeline execution.
    """
    def __init__(self):
        """Initializes the handler, logger, and pipeline lock."""
        self.logger = logging.getLogger(__name__)
        self.pipeline_lock = threading.Lock()
        self.logger.info("PipelineEventHandler initialized with thread safety")

    def on_created(self, event):
        """
        This method is called by the watchdog observer when a new file or
        directory is created in the monitored path.
        
        Uses a non-blocking lock to prevent concurrent pipeline execution.
        """
        # First, ignore events that are for directory creation. We only care about files.
        if event.is_directory:
            return

        # Check if the name of the created file is exactly "complete".
        # This is our specific trigger file.
        if os.path.basename(event.src_path) == "complete":
            self.logger.info(f"--- Trigger file detected: {event.src_path} ---")
            
            # Try to acquire the pipeline lock (non-blocking)
            # If another pipeline is running, this will return False immediately
            if not self.pipeline_lock.acquire(blocking=False):
                self.logger.warning(
                    "Pipeline is already running. Skipping this trigger. "
                    "The trigger file will be cleaned up and the next upload will create a new trigger."
                )
                # Clean up this trigger file since we're not processing it
                try:
                    os.remove(event.src_path)
                    self.logger.info(f"Cleaned up duplicate trigger file: {event.src_path}")
                except Exception as e:
                    self.logger.error(f"Failed to remove duplicate trigger file: {e}")
                return
            
            # Lock acquired - proceed with pipeline execution
            try:
                # Wait a short moment to ensure file write is complete
                time.sleep(0.5)
                
                # --- Runs ETL -> MBA -> PED -> NLP -> Holt-Winters ---
                self.logger.info("Starting pipeline execution (lock acquired)...")
                run_all.execute_pipeline()
                self.logger.info("--- Pipeline execution finished successfully. ---")
                
            except Exception as e:
                # If the pipeline fails for any reason, log the error.
                self.logger.error(f"Pipeline execution failed: {e}")
                
            finally:
                # CRITICAL: Release the lock so future pipelines can run
                self.pipeline_lock.release()
                self.logger.info("Pipeline lock released")
                
                # CRITICAL STEP: Always attempt to remove the trigger file,
                # whether the pipeline succeeded or failed. This "resets" the
                # system, allowing it to be triggered again by a future upload.
                try:
                    os.remove(event.src_path)
                    self.logger.info(f"Cleaned up trigger file: {event.src_path}")
                except Exception as e:
                    self.logger.error(f"Failed to remove trigger file: {e}")

    def on_modified(self, event):
        """
        This method is called when a file is modified. We don't need to act on
        modifications for this workflow, so it's left empty.
        """
        pass
