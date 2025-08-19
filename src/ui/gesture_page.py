from __future__ import annotations
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false

from typing import Any, cast
import cv2
from PySide6 import QtCore, QtGui, QtWidgets
from .widgets import RippleButton
from .video_widget import VideoWidget

from src.core.background_initializer import BackgroundInitializer
from src.core.gesture_detector import GestureDetector


class GesturePage(QtWidgets.QWidget):
    backRequested = QtCore.Signal()

    def __init__(self) -> None:
        super().__init__()
        # Video card
        self.video_label = VideoWidget()
        self.video_label.setObjectName("video")
        self.video_label.setCornerRadius(20)
        vshadow = QtWidgets.QGraphicsDropShadowEffect(self.video_label)
        vshadow.setBlurRadius(24)
        vshadow.setOffset(0, 6)
        vshadow.setColor(QtGui.QColor(0, 0, 0, 140))
        self.video_label.setGraphicsEffect(vshadow)

        # Banner overlay (glass pill)
        self.overlay_banner = QtWidgets.QWidget()
        self.overlay_banner.setObjectName("overlayBanner")
        self.overlay_banner.setVisible(False)
        self.overlay_banner.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self._banner_h = 56
        self.overlay_banner.setMinimumHeight(self._banner_h)
        self.overlay_banner.setMaximumHeight(0)
        # Root layout: vertical layout per separare contenuto da progress bar
        banner_main_layout = QtWidgets.QVBoxLayout(self.overlay_banner)
        banner_main_layout.setContentsMargins(0, 0, 0, 0)
        banner_main_layout.setSpacing(0)
        
        # Top row: accent stripe + content
        top_row = QtWidgets.QWidget()
        banner_root = QtWidgets.QHBoxLayout(top_row)
        banner_root.setContentsMargins(0, 0, 0, 0)
        banner_root.setSpacing(0)
        
        # Accent stripe (3–4px), styled per-kind via QSS
        self.overlay_accent = QtWidgets.QWidget(top_row)
        self.overlay_accent.setObjectName("overlayAccent")
        self.overlay_accent.setFixedWidth(4)
        banner_root.addWidget(self.overlay_accent, 0)
        
        # Content area
        content_container = QtWidgets.QWidget(top_row)
        banner_vlayout = QtWidgets.QVBoxLayout(content_container)
        banner_vlayout.setContentsMargins(16, 8, 16, 8)
        banner_vlayout.setSpacing(6)
        content_row = QtWidgets.QWidget(content_container)
        banner_layout = QtWidgets.QHBoxLayout(content_row)
        banner_layout.setContentsMargins(0, 0, 0, 0)
        banner_layout.setSpacing(10)
        # Icon chip (circular, styled via QSS)
        self.overlay_icon = QtWidgets.QLabel("")
        self.overlay_icon.setObjectName("overlayIcon")
        self.overlay_icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.overlay_icon.setFixedSize(30, 30)
        # Text column: title + subtitle
        text_col = QtWidgets.QWidget(content_row)
        text_layout = QtWidgets.QVBoxLayout(text_col)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)
        self.overlay_title = QtWidgets.QLabel("")
        self.overlay_title.setObjectName("overlayTitle")
        self.overlay_title.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.overlay_title.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.overlay_subtitle = QtWidgets.QLabel("")
        self.overlay_subtitle.setObjectName("overlaySubtitle")
        self.overlay_subtitle.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.overlay_subtitle.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.overlay_subtitle.setVisible(False)  # Nascondi il subtitle dato che non lo usiamo più
        text_layout.addWidget(self.overlay_title)
        text_layout.addWidget(self.overlay_subtitle)
        banner_layout.addWidget(self.overlay_icon, 0)
        banner_layout.addWidget(text_col, 1)
        banner_vlayout.addWidget(content_row)
        
        # Aggiungi content container al top row
        banner_root.addWidget(content_container, 1)
        
        # Aggiungi top row al layout principale
        banner_main_layout.addWidget(top_row)
        
        # Progress bar che si estende su tutta la larghezza del banner
        self.overlay_progress = QtWidgets.QProgressBar()
        self.overlay_progress.setObjectName("overlayProgress")
        self.overlay_progress.setTextVisible(False)
        self.overlay_progress.setFixedHeight(4)
        self.overlay_progress.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        banner_main_layout.addWidget(self.overlay_progress)

        self._banner_wrapper = QtWidgets.QWidget()
        self._banner_wrapper.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        wrapper_layout = QtWidgets.QVBoxLayout(self._banner_wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(0)
        # Rimosso AlignHCenter - ora si estende per tutta la larghezza disponibile
        wrapper_layout.addWidget(self.overlay_banner)

        # Soft glow shadow (elevation 2–3)
        shadow = QtWidgets.QGraphicsDropShadowEffect(self.overlay_banner)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QtGui.QColor(0, 0, 0, 160))
        self.overlay_banner.setGraphicsEffect(shadow)

        # Timers and animations
        self.overlay_timer = QtCore.QTimer(self)
        self.overlay_timer.setSingleShot(True)
        self.overlay_timer.timeout.connect(self._hide_banner)
        self._progress_timer = QtCore.QTimer(self)
        self._progress_timer.timeout.connect(self._tick_progress)
        self._progress_total = 3000  # Aggiornato a 3 secondi
        self._progress_elapsed = 0
        self._banner_anim = QtCore.QPropertyAnimation(
            self.overlay_banner, b"maximumHeight", self
        )
        self._banner_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        self._banner_anim.setDuration(180)
        self._banner_hide_anim = QtCore.QPropertyAnimation(
            self.overlay_banner, b"maximumHeight", self
        )
        self._banner_hide_anim.setEasingCurve(QtCore.QEasingCurve.Type.InCubic)
        self._banner_hide_anim.setDuration(160)
        self._banner_hide_anim.finished.connect(
            lambda: self._set_banner_visible(False)
        )

        # Core components - lazy initialization via background loader
        self.capture = None  # Will be set by background initializer
        self.tracker = None  # Will be set by background initializer
        self.detector = GestureDetector()
        self.mirror = True
        
        # Background initialization
        self.bg_initializer = BackgroundInitializer()
        self.bg_initializer.handTrackerReady.connect(self._on_hand_tracker_ready)
        self.bg_initializer.videoCaptureReady.connect(self._on_video_capture_ready)
        self.bg_initializer.allComponentsReady.connect(self._on_all_components_ready)

        # Pre-initialization state
        self._is_preinitializing = False
        self._is_preinitialized = False
        self._components_ready = False
        self._gesture_detection_blocked = False  # Blocca rilevamento durante progress bar

        self._build()
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._on_tick)

    def _build(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        topbar = QtWidgets.QHBoxLayout()
        topbar.setContentsMargins(16, 16, 16, 16)
        topbar.setSpacing(16)  # Spazio tra bottone e banner
        
        back_btn = RippleButton("← Indietro", elevation=1)
        back_btn.clicked.connect(self.backRequested.emit)
        topbar.addWidget(back_btn, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        
        # Aggiungi il banner nel topbar invece che nell'overlay
        topbar.addWidget(self._banner_wrapper, 1)  # stretch per riempire lo spazio rimanente

        main_page = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(main_page)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addLayout(topbar)

        video_area = QtWidgets.QWidget(main_page)
        video_area.setObjectName("videoArea")
        video_area.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding
        )
        video_area_layout = QtWidgets.QVBoxLayout(video_area)
        video_area_layout.setContentsMargins(16, 8, 16, 16)
        video_area_layout.setSpacing(0)
        video_area_layout.addWidget(self.video_label)

        overlay_container = QtWidgets.QWidget(main_page)
        overlay_container.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_StyledBackground, True
        )
        overlay_container.setStyleSheet("background: transparent;")
        overlay_container.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        overlay_container.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding
        )
        overlay_layout = QtWidgets.QVBoxLayout(overlay_container)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)
        # Banner rimosso da qui - ora è nel topbar
        overlay_layout.addStretch(1)

        area = QtWidgets.QGridLayout()
        area.setContentsMargins(0, 0, 0, 0)
        area.setSpacing(0)
        area.addWidget(video_area, 0, 0)
        area.addWidget(overlay_container, 0, 0)
        area.setRowStretch(0, 1)
        area.setColumnStretch(0, 1)
        main_layout.addLayout(area)

        layout.addWidget(main_page)
        overlay_container.raise_()

    def _on_hand_tracker_ready(self, hand_tracker) -> None:
        """Called when HandTracker is ready from background initialization."""
        self.tracker = hand_tracker
        
    def _on_video_capture_ready(self, video_capture) -> None:
        """Called when VideoCaptureThread is ready from background initialization."""
        self.capture = video_capture
        
    def _on_all_components_ready(self) -> None:
        """Called when all components are ready."""
        self._components_ready = True
        # Auto-start pre-initialization once components are loaded
        self.preinitialize()

    def start(self) -> None:
        self._set_banner_visible(False)
        self.overlay_progress.setValue(0)
        
        # Check if components are ready
        if not self._components_ready or self.capture is None:
            # Components not ready, show loading state
            return
            
        # If already pre-initialized, start immediately
        if self._is_preinitialized:
            self.capture.start()  # Quick restart since camera is already initialized
            if not self._timer.isActive():
                self._timer.start(30)
        else:
            # Start normally (will be slower first time)
            self.capture.start()
            if not self._timer.isActive():
                self._timer.start(30)

    def preinitialize(self) -> None:
        """Pre-initialize camera and MediaPipe in background for instant startup."""
        if self._is_preinitializing or self._is_preinitialized or not self.capture or not self.tracker:
            return
            
        self._is_preinitializing = True
        # Start camera capture in background
        self.capture.start()
        
        # Pre-warm MediaPipe by processing a dummy frame
        QtCore.QTimer.singleShot(100, self._finish_preinitialize)
    
    def _finish_preinitialize(self) -> None:
        """Complete pre-initialization by warming up MediaPipe."""
        if not self.capture or not self.tracker:
            self._is_preinitializing = False
            return
            
        try:
            # Get a frame to warm up the pipeline
            frame = self.capture.read()
            if frame is not None:
                # Process once to initialize MediaPipe models
                self.tracker.process(frame)
            
            self._is_preinitialized = True
            self._is_preinitializing = False
            # Stop capture until user actually needs it
            self.capture.stop()
        except Exception:
            self._is_preinitializing = False

    def stop(self) -> None:
        if self._timer.isActive():
            self._timer.stop()
        if self.capture:
            self.capture.stop()
        self.video_label.clear()
        self.video_label.setText("")

    def _on_tick(self) -> None:
        if not self.capture or not self.tracker:
            return
            
        frame: Any = cast(Any, self.capture.read())
        if frame is None:
            return
        
        if self.mirror:
            frame = cv2.flip(frame, 1)  # type: ignore
            
        try:
            hands: Any = cast(Any, self.tracker.process(frame))
        except Exception:
            return
        drawn: Any = cast(Any, self.tracker.draw(frame, hands))
        self.video_label.show_frame(drawn)

        # Blocca rilevamento gesti durante la progress bar
        if self._gesture_detection_blocked:
            return

        event = self.detector.detect(hands)
        if event:
            if event.name == 'heart':
                self._show_overlay('Anche Topino ti ama tanto!', ms=3000, kind='heart')
            elif event.name == 'wave':
                self._show_overlay('Anche Topino ti saluta!', ms=3000, kind='wave')
            elif event.name == 'middle_finger':
                self._show_overlay('No, non essere cattiva con Topino! Topino ti vuole bene!', ms=3000, kind='middle_finger')

    def _set_banner_visible(self, visible: bool) -> None:
        self._banner_wrapper.setVisible(visible)
        self.overlay_banner.setVisible(visible)

    def _tick_progress(self) -> None:
        self._progress_elapsed += self._progress_timer.interval()
        progress_value = min(self._progress_elapsed, self._progress_total)
        self.overlay_progress.setValue(progress_value)
        
        if self._progress_elapsed >= self._progress_total:
            self._progress_timer.stop()
            self._gesture_detection_blocked = False  # Riabilita rilevamento gesti

    def _hide_banner(self) -> None:
        self._banner_hide_anim.stop()
        self._banner_hide_anim.setStartValue(self.overlay_banner.maximumHeight())
        self._banner_hide_anim.setEndValue(0)
        self._banner_hide_anim.start()

    def _show_overlay(self, text: str, ms: int = 3000, kind: str = 'info') -> None:
        # Blocca rilevamento gesti durante l'overlay
        self._gesture_detection_blocked = True
        
        # set kind on widgets and refresh style (for tinted glass and chip)
        self.overlay_banner.setProperty('kind', kind)
        self.overlay_progress.setProperty('kind', kind)
        self.overlay_icon.setProperty('kind', kind)
        self.overlay_accent.setProperty('kind', kind)
        for w in (self.overlay_banner, self.overlay_progress, self.overlay_icon, self.overlay_accent):
            w.style().unpolish(w)
            w.style().polish(w)

        # set texts and emoji chip
        if kind == 'heart':
            self.overlay_icon.setText('❤️')
            self.overlay_title.setText('Anche Topino ti ama tanto!')
            self.overlay_subtitle.setText('')  # Rimosso "Gesto: cuore"
        elif kind == 'wave':
            self.overlay_icon.setText('👋')
            self.overlay_title.setText('Anche Topino ti saluta!')
            self.overlay_subtitle.setText('')  # Rimosso "Gesto: saluto"
        elif kind == 'middle_finger':
            self.overlay_icon.setText('😡')  # Faccia arrabbiata e rossa
            self.overlay_title.setText('No, non essere cattiva con Topino! Topino ti vuole bene!')
            self.overlay_subtitle.setText('')
        else:
            self.overlay_icon.setText('')
            self.overlay_title.setText(text)
            self.overlay_subtitle.setText('')

        # progress - fisso a 3000ms (3 secondi)
        self._progress_total = 3000
        self._progress_elapsed = 0
        self.overlay_progress.setRange(0, 2000)
        self.overlay_progress.setValue(0)

        # animate show
        self._banner_anim.stop()
        self._set_banner_visible(True)
        self._banner_anim.setStartValue(self.overlay_banner.maximumHeight())
        self._banner_anim.setEndValue(self._banner_h)
        self._banner_anim.start()

        # timers - mantieni il timer di hiding al tempo specificato ma progress bar sempre 1.5s
        self.overlay_timer.start(ms)
        self._progress_timer.setInterval(30)
        self._progress_timer.start()
