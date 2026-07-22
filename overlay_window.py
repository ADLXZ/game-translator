from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

class OverlayWindow(QLabel):

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setStyleSheet("""
            background-color: rgba(30,30,30,180);
            color: white;
            border:2px solid #55AAFF;
            border-radius:8px;
            padding:8px;
            font-size:14px;
        """)

        self.setWordWrap(True)

        self.setText("Translation")

        self.resize(260,120)

        self.show()

    def set_translation(self, text):
        self.setText(text)




