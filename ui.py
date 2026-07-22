from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QTextEdit,
    QVBoxLayout,
)

from engine import TranslationEngine
from region_selector import RegionSelector

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
        self.select_region_button = QPushButton("Select Region")

        layout = QVBoxLayout()
        layout.addWidget(self.select_region_button)
        layout.addWidget(self.start_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.result_text)
        self.setLayout(layout)

        self.selected_region = None
        self.region_selector = None
        self.select_region_button.clicked.connect(self.open_region_selector)

        self.engine = TranslationEngine()

        self.start_button.clicked.connect(self.start_translation)

    def start_translation(self):
        if self.selected_region is None:
            self.status_label.setText(
                "Status: Please select a region first"
            )
            return

        self.status_label.setText("Status: Translating screen...")

        translated_text = self.engine.translate_screen(
            self.selected_region
        )

        self.result_text.setPlainText(translated_text)
        self.status_label.setText("Status: Complete")

    def open_region_selector(self):
        self.status_label.setText("Status: Select a region...")

        self.region_selector = RegionSelector()
        self.region_selector.region_selected.connect(
            self.save_selected_region
        )

    def save_selected_region(self, region):
        self.selected_region = region

        self.status_label.setText(
            "Status: Region selected "
            f"({region['width']} × {region['height']})"
        )

        print("Selected region:", region)

























