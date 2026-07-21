from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QTextEdit,
    QVBoxLayout,
)

from engine import TranslationEngine

class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Game Translator")
        self.resize(600, 400)

        self.start_button = QPushButton("Start Translation")
        self.status_label = QLabel("Status: Ready")
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("Detected text will appear here.")

        layout = QVBoxLayout()
        layout.addWidget(self.start_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.result_text)
        self.setLayout(layout)

        self.engine = TranslationEngine()

        self.start_button.clicked.connect(self.start_translation)

    def start_translation(self):
        self.status_label.setText("Status: Translating screen...")

        translated_text = self.engine.translate_screen()

        self.result_text.setPlainText(translated_text)
        self.status_label.setText("Status: Complete")




















