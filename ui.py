from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from engine import TranslationEngine
from translation_region import TranslationRegion


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.engine = TranslationEngine()
        self.translation_regions = []
        self.regions_in_edit_mode = True

        self.setWindowTitle("Game Translator")
        self.resize(320, 180)

        layout = QVBoxLayout(self)

        self.create_region_button = QPushButton("创建翻译区域")
        self.create_region_button.clicked.connect(
            self.create_translation_region
        )

        self.mode_button = QPushButton("进入使用模式")
        self.mode_button.clicked.connect(
            self.toggle_region_edit_mode
        )

        layout.addWidget(self.create_region_button)
        layout.addWidget(self.mode_button)

    def create_translation_region(self):
        region = TranslationRegion(self.engine)
        region.closed.connect(self.remove_translation_region)
        region.show()
        region.set_edit_mode(self.regions_in_edit_mode)
        self.translation_regions.append(region)

    def remove_translation_region(self, region):
        if region in self.translation_regions:
            self.translation_regions.remove(region)

    def toggle_region_edit_mode(self):
        self.regions_in_edit_mode = not self.regions_in_edit_mode

        for region in list(self.translation_regions):
            region.set_edit_mode(self.regions_in_edit_mode)

        self.mode_button.setText(
            "进入使用模式"
            if self.regions_in_edit_mode
            else "进入编辑模式"
        )

    def closeEvent(self, event):
        for region in list(self.translation_regions):
            region.close()
        super().closeEvent(event)
