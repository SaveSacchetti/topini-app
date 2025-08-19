from __future__ import annotations
from PySide6 import QtWidgets, QtCore
from .widgets import RippleButton
from .theme import APP_TITLE, APP_LOGO, APP_TAGLINE, CTA_TEXT


class HomePage(QtWidgets.QWidget):
    startRequested = QtCore.Signal()

    def __init__(self) -> None:
        super().__init__()
        self.cta = None  # Will be set in _build
        self._build()

    def _build(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(36)  # Aumentato +30%: da 28px

        # Logo con emoji dei topini
        logo = QtWidgets.QLabel(APP_LOGO)
        logo.setObjectName("logo")
        logo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        title = QtWidgets.QLabel(APP_TITLE)
        title.setObjectName("title")
        subtitle = QtWidgets.QLabel(APP_TAGLINE)
        subtitle.setObjectName("subtitle")

        self.cta = RippleButton(CTA_TEXT, elevation=2)
        self.cta.clicked.connect(self.startRequested.emit)

        # Aggiungi il logo come primo elemento
        layout.addWidget(logo, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(title, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(subtitle, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(42)  # Aumentato +30%: da 32px
        layout.addWidget(self.cta, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)
        
    def set_loading_state(self, loading: bool) -> None:
        """Set button loading state."""
        if self.cta:
            if loading:
                self.cta.setText("Caricamento componenti...")
                self.cta.setEnabled(False)
            else:
                self.cta.setText(CTA_TEXT)
                self.cta.setEnabled(True)
