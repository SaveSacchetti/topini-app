from __future__ import annotations
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false

from typing import Optional, Any
import cv2
from PySide6 import QtCore, QtGui, QtWidgets


class VideoWidget(QtWidgets.QLabel):
    """Widget for displaying video frames with 16:9 aspect ratio that fills available space."""
    
    def __init__(self) -> None:
        super().__init__()
        # Expand to fill available space while maintaining 16:9
        self.setMinimumSize(480, 270)  # Minimum 16:9 size
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self._radius: int = 0
        self._pixmap: Optional[QtGui.QPixmap] = None
        self._render_size: QtCore.QSize = QtCore.QSize(1280, 720)  # Default HD 16:9 size

    def setCornerRadius(self, radius: int) -> None:
        self._radius = max(0, int(radius))
        self.update()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Maintain camera's native aspect ratio when widget is resized."""
        super().resizeEvent(event)
        # Use camera's actual aspect ratio (now 16:9 HD)
        new_size = event.size()
        width = new_size.width()
        height = new_size.height()
        
        # Calculate the optimal size maintaining 16:9 (camera actual ratio)
        camera_ratio = 16.0 / 9.0  # 1280x720 = 16:9
        current_ratio = width / height if height > 0 else camera_ratio
        
        if current_ratio > camera_ratio:
            # Too wide, limit by height (letterbox left/right)
            optimal_width = int(height * camera_ratio)
            optimal_height = height
        else:
            # Too tall, limit by width (letterbox top/bottom)
            optimal_width = width
            optimal_height = int(width / camera_ratio)
        
        # Store the optimal rendering size for 16:9
        self._render_size = QtCore.QSize(optimal_width, optimal_height)

    def show_frame(self, frame_bgr: Any) -> None:
        if frame_bgr is None:
            return
        
        # Convert frame to RGB without cropping (preserve all content)
        rgb: Any = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)  # type: ignore
        h, w = rgb.shape[:2]
        qimg: QtGui.QImage = QtGui.QImage(rgb.data, w, h, 3 * w, QtGui.QImage.Format.Format_RGB888)  # type: ignore
        
        # Scale maintaining aspect ratio (no cropping, may add letterbox)
        render_w = self._render_size.width()
        render_h = self._render_size.height()
        self._pixmap = QtGui.QPixmap.fromImage(qimg).scaled(
            render_w, render_h,
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,  # Preserve original content
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        self.update()

    def paintEvent(self, arg__1: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        
        # Fill background with black (for letterbox effect)
        widget_rect = self.rect()
        painter.fillRect(widget_rect, QtGui.QColor(0, 0, 0))
        
        if self._pixmap:
            # Center the video maintaining its aspect ratio
            pixmap_w = self._pixmap.width()
            pixmap_h = self._pixmap.height()
            
            x = (widget_rect.width() - pixmap_w) // 2
            y = (widget_rect.height() - pixmap_h) // 2
            video_rect = QtCore.QRect(x, y, pixmap_w, pixmap_h)
            
            # Apply rounded corners to the entire widget area
            if self._radius > 0:
                path = QtGui.QPainterPath()
                path.addRoundedRect(QtCore.QRectF(widget_rect), float(self._radius), float(self._radius))
                painter.setClipPath(path)
            
            # Draw video centered (may have letterbox bars)
            painter.drawPixmap(video_rect, self._pixmap)
        else:
            QtWidgets.QLabel.paintEvent(self, arg__1)
