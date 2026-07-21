from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
)
from screenshot import ScreenCapture

class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Game Translator")
        self.resize(600, 400)

        self.start_button = QPushButton("Start Translation")
        self.status_label = QLabel("Status: Ready")

        layout = QVBoxLayout()

        layout.addWidget(self.start_button)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        self.screen_capture = ScreenCapture()

        self.start_button.clicked.connect(self.start_translation)

    def start_translation(self):
        self.screen_capture.capture()












