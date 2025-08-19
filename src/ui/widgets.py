from __future__ import annotations

from typing import Optional
from PySide6 import QtCore, QtGui, QtWidgets


def apply_elevation(widget: QtWidgets.QWidget, level: int = 1) -> None:
    """Apply a soft drop shadow to simulate elevation.
    Levels: 1 (low), 2 (medium), 3 (high)
    """
    blur = {1: 8, 2: 16, 3: 24}.get(level, 8)
    offset_y = {1: 2, 2: 3, 3: 6}.get(level, 2)
    alpha = {1: 120, 2: 150, 3: 170}.get(level, 120)
    effect = QtWidgets.QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, offset_y)
    effect.setColor(QtGui.QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(effect)


class RippleButton(QtWidgets.QPushButton):
    """QPushButton with a simple material-like ripple on click."""

    def __init__(self, text: str = "", parent: Optional[QtWidgets.QWidget] = None, elevation: int = 1) -> None:
        super().__init__(text, parent)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        self._ripple_active: bool = False
        self._r_center: QtCore.QPointF = QtCore.QPointF(0, 0)
        self._r_radius: float = 0.0
        self._r_opacity: float = 0.0

        self._radius_anim = QtCore.QVariantAnimation(self)
        self._radius_anim.valueChanged.connect(self._on_radius_changed)
        self._opacity_anim = QtCore.QVariantAnimation(self)
        self._opacity_anim.valueChanged.connect(self._on_opacity_changed)
        self._group = QtCore.QParallelAnimationGroup(self)
        self._group.addAnimation(self._radius_anim)
        self._group.addAnimation(self._opacity_anim)
        self._group.finished.connect(self._on_anim_finished)

        apply_elevation(self, elevation)

    def _on_radius_changed(self, val: object) -> None:
        try:
            self._r_radius = float(val)  # type: ignore[arg-type]
        except Exception:
            self._r_radius = 0.0
        self.update()

    def _on_opacity_changed(self, val: object) -> None:
        try:
            self._r_opacity = float(val)  # type: ignore[arg-type]
        except Exception:
            self._r_opacity = 0.0
        self.update()

    def _on_anim_finished(self) -> None:
        self._ripple_active = False
        self.update()

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        self._start_ripple(e.position())
        QtWidgets.QPushButton.mousePressEvent(self, e)

    def _start_ripple(self, pos: QtCore.QPointF) -> None:
        self._r_center = QtCore.QPointF(pos)
        r = self.rect()
        corners = [QtCore.QPointF(r.topLeft()), QtCore.QPointF(r.topRight()), QtCore.QPointF(r.bottomLeft()), QtCore.QPointF(r.bottomRight())]
        max_dist = 0.0
        for c in corners:
            d = c - self._r_center
            dist = (d.x() ** 2 + d.y() ** 2) ** 0.5
            if dist > max_dist:
                max_dist = dist
        self._radius_anim.stop()
        self._opacity_anim.stop()
        self._group.stop()
        self._radius_anim.setStartValue(0.0)
        self._radius_anim.setEndValue(max_dist)
        self._radius_anim.setDuration(300)
        self._radius_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        self._opacity_anim.setStartValue(0.28)
        self._opacity_anim.setEndValue(0.0)
        self._opacity_anim.setDuration(380)
        self._opacity_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        self._ripple_active = True
        self._group.start()

    def paintEvent(self, arg__1: QtGui.QPaintEvent) -> None:
        QtWidgets.QPushButton.paintEvent(self, arg__1)
        if not self._ripple_active:
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        color = QtGui.QColor(255, 255, 255)
        color.setAlphaF(max(0.0, min(1.0, self._r_opacity)))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(self._r_center, self._r_radius, self._r_radius)
