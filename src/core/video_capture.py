from __future__ import annotations
import threading
import time
from typing import Optional, Any

import cv2


class VideoCaptureThread:
    def __init__(self, device_index: int = 0, fps: int = 30):
        self.device_index = device_index
        self.fps = fps
        self.cap: Optional[cv2.VideoCapture] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
        self._latest_frame: Optional[Any] = None

    def start(self):
        # ensure clean state
        self.stop()
        self._latest_frame = None
        self.cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            # fallback
            self.cap = cv2.VideoCapture(self.device_index)
        if not self.cap or not self.cap.isOpened():
            return
        
        # Try to get higher resolution if camera supports it
        # Test common resolutions in order of preference
        resolutions = [
            (1920, 1080),  # Full HD 16:9
            (1280, 720),   # HD 16:9  
            (1024, 768),   # XGA 4:3
            (800, 600),    # SVGA 4:3
            (640, 480)     # VGA 4:3 (fallback)
        ]
        
        for width, height in resolutions:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if actual_w == width and actual_h == height:
                break
        
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        # warm-up: leggi e scarta qualche frame per stabilizzare l'esposizione
        for _ in range(5):
            ok, frame = self.cap.read()
            if ok:
                with self._lock:
                    self._latest_frame = frame
            time.sleep(0.02)

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        interval = 1.0 / max(1, self.fps)
        # breve pausa prima del loop
        time.sleep(0.01)
        while self._running and self.cap and self.cap.isOpened():
            ok, frame = self.cap.read()
            if ok:
                with self._lock:
                    self._latest_frame = frame
            time.sleep(interval * 0.5)

    def read(self) -> Optional[Any]:
        with self._lock:
            if self._latest_frame is None:
                return None
            return self._latest_frame.copy()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
        if self.cap:
            try:
                self.cap.release()
            finally:
                self.cap = None
        # clear stale frame so UI doesn't keep showing last image
        with self._lock:
            self._latest_frame = None
