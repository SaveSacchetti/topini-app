"""
Background initialization manager for heavy components.
Avoids blocking the UI thread during startup.
"""

from __future__ import annotations
import threading
import time
from typing import Optional, Callable, Any
from PySide6 import QtCore


class BackgroundInitializer(QtCore.QObject):
    """Manages background initialization of heavy components."""
    
    # Signals
    handTrackerReady = QtCore.Signal(object)  # HandTracker instance
    videoCaptureReady = QtCore.Signal(object)  # VideoCaptureThread instance
    allComponentsReady = QtCore.Signal()
    
    def __init__(self, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__(parent)
        self._hand_tracker: Optional[Any] = None
        self._video_capture: Optional[Any] = None
        self._is_initializing = False
        self._initialization_thread: Optional[threading.Thread] = None
    
    def start_initialization(self) -> None:
        """Start background initialization of components."""
        if self._is_initializing:
            return
            
        self._is_initializing = True
        self._initialization_thread = threading.Thread(
            target=self._initialize_components,
            daemon=True
        )
        self._initialization_thread.start()
    
    def _initialize_components(self) -> None:
        """Initialize components in background thread."""
        try:
            # Initialize HandTracker (heavy MediaPipe import)
            from src.core.hand_tracker import HandTracker
            self._hand_tracker = HandTracker()
            self.handTrackerReady.emit(self._hand_tracker)
            
            # Initialize VideoCaptureThread
            from src.core.video_capture import VideoCaptureThread
            self._video_capture = VideoCaptureThread()
            self.videoCaptureReady.emit(self._video_capture)
            
            # All components ready
            self.allComponentsReady.emit()
            
        except Exception as e:
            print(f"Background initialization error: {e}")
        finally:
            self._is_initializing = False
    
    def get_hand_tracker(self) -> Optional[Any]:
        """Get initialized HandTracker or None if not ready."""
        return self._hand_tracker
    
    def get_video_capture(self) -> Optional[Any]:
        """Get initialized VideoCaptureThread or None if not ready."""
        return self._video_capture
    
    def is_ready(self) -> bool:
        """Check if all components are ready."""
        return (self._hand_tracker is not None and 
                self._video_capture is not None)
