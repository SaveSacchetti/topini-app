from __future__ import annotations
import sys
import os
# Allow running this file directly (python src/main.py) by ensuring project root is on sys.path
if __package__ is None and __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from PySide6 import QtWidgets, QtGui, QtCore

from src.ui.home_page import HomePage
from src.ui.gesture_page import GesturePage
from src.ui.theme import STYLE_SHEET, APP_TITLE


def create_app_icon() -> QtGui.QIcon:
    """Carica l'icona dell'app dal file personalizzato."""
    # Percorso relativo all'icona personalizzata
    icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "app_icon.png")
    
    if os.path.exists(icon_path):
        # Carica l'icona dal file
        icon = QtGui.QIcon(icon_path)
        # Aggiungi dimensioni multiple per migliorare la qualità
        pixmap = QtGui.QPixmap(icon_path)
        if not pixmap.isNull():
            # Crea versioni scalate per diverse dimensioni
            icon.addPixmap(pixmap.scaled(16, 16, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation))
            icon.addPixmap(pixmap.scaled(32, 32, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation))
            icon.addPixmap(pixmap.scaled(64, 64, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation))
        return icon
    else:
        # Fallback: crea un'icona con emoji se il file non esiste
        pixmap = QtGui.QPixmap(64, 64)
        pixmap.fill(QtGui.QColor(255, 100, 150))  # Sfondo rosa
        
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        
        # Disegna un rettangolo arrotondato rosa
        painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 100, 150)))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 64, 64, 12, 12)
        
        font = QtGui.QFont()
        font.setPointSize(16)
        painter.setFont(font)
        painter.setPen(QtGui.QColor(255, 255, 255))
        
        # Disegna i due topini e il cuore
        painter.drawText(8, 8, 20, 20, QtCore.Qt.AlignmentFlag.AlignCenter, "🐭")
        painter.drawText(36, 8, 20, 20, QtCore.Qt.AlignmentFlag.AlignCenter, "🐭")
        painter.drawText(22, 35, 20, 20, QtCore.Qt.AlignmentFlag.AlignCenter, "💕")
        
        painter.end()
        
        return QtGui.QIcon(pixmap)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setWindowIcon(create_app_icon())  # Imposta l'icona dell'app
        self.resize(1100, 700)

        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home = HomePage()
        self.gesture = GesturePage()

        self.stack.addWidget(self.home)
        self.stack.addWidget(self.gesture)

        self.home.startRequested.connect(self._go_gesture)
        self.gesture.backRequested.connect(self._go_home)
        
        # Connect background initialization signals
        self.gesture.bg_initializer.allComponentsReady.connect(self._on_components_ready)

        self.setStyleSheet(STYLE_SHEET)
        
        # Start background initialization immediately for faster startup
        self.home.set_loading_state(True)  # Disable button until components are ready
        self.gesture.bg_initializer.start_initialization()

    def _go_gesture(self):
        self.stack.setCurrentWidget(self.gesture)
        self.gesture.start()

    def _go_home(self):
        self.gesture.stop()
        self.stack.setCurrentWidget(self.home)
        
    def _on_components_ready(self):
        """Called when all background components are ready."""
        self.home.set_loading_state(False)  # Enable button

    def closeEvent(self, event: QtGui.QCloseEvent):
        # make sure we stop capture if window is closed while on gesture page
        try:
            self.gesture.stop()
        except Exception:
            pass
        return super().closeEvent(event)


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
