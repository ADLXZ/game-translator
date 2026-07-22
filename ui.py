from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from engine import TranslationEngine
from translation_region import TranslationRegion


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.engine = TranslationEngine()
        self.translation_regions = []
        self.regions_in_edit_mode = True

        self.setWindowTitle(
            "Game Translator"
        )

        self.resize(
            380,
            400,
        )

        layout = QVBoxLayout(self)

        # =============================================
        # Translation service
        # =============================================

        self.provider_label = QLabel(
            "Translation Service"
        )

        self.provider_combo_box = QComboBox()

        self.provider_combo_box.addItem(
            "Google Translate",
            "google",
        )

        self.provider_combo_box.addItem(
            "Baidu Translate",
            "baidu",
        )

        self.provider_combo_box.currentIndexChanged.connect(
            self.change_translation_provider
        )

        layout.addWidget(
            self.provider_label
        )

        layout.addWidget(
            self.provider_combo_box
        )

        # =============================================
        # Baidu credentials panel
        # =============================================

        self.baidu_credentials_panel = QFrame()

        credentials_layout = QVBoxLayout(
            self.baidu_credentials_panel
        )

        self.baidu_help_label = QLabel(
            "Enter the APP ID and Secret Key from "
            "the Baidu Translate developer console."
        )

        self.baidu_help_label.setWordWrap(
            True
        )

        credentials_form = QFormLayout()

        self.baidu_app_id_input = QLineEdit()

        self.baidu_app_id_input.setPlaceholderText(
            "Enter Baidu APP ID"
        )

        self.baidu_secret_key_input = QLineEdit()

        self.baidu_secret_key_input.setPlaceholderText(
            "Enter Baidu Secret Key"
        )

        self.baidu_secret_key_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        credentials_form.addRow(
            "APP ID:",
            self.baidu_app_id_input,
        )

        credentials_form.addRow(
            "Secret Key:",
            self.baidu_secret_key_input,
        )

        self.save_baidu_button = QPushButton(
            "Save Baidu Credentials"
        )

        self.save_baidu_button.clicked.connect(
            self.save_baidu_credentials
        )

        credentials_layout.addWidget(
            self.baidu_help_label
        )

        credentials_layout.addLayout(
            credentials_form
        )

        credentials_layout.addWidget(
            self.save_baidu_button
        )

        # Google is the default, so keep this hidden initially.
        self.baidu_credentials_panel.hide()

        layout.addWidget(
            self.baidu_credentials_panel
        )

        # =============================================
        # Main controls
        # =============================================

        self.create_region_button = QPushButton(
            "Create Translation Region"
        )

        self.create_region_button.clicked.connect(
            self.create_translation_region
        )

        self.mode_button = QPushButton(
            "Enter Use Mode"
        )

        self.mode_button.clicked.connect(
            self.toggle_region_edit_mode
        )

        self.stop_all_button = QPushButton(
            "Stop All Auto Translation"
        )

        self.stop_all_button.clicked.connect(
            self.stop_all_auto_translation
        )

        layout.addWidget(
            self.create_region_button
        )

        layout.addWidget(
            self.mode_button
        )

        layout.addWidget(
            self.stop_all_button
        )

        # =============================================
        # Status
        # =============================================

        self.status_label = QLabel(
            "Translation Service: Google Translate"
        )

        self.status_label.setWordWrap(
            True
        )

        layout.addWidget(
            self.status_label
        )

        layout.addStretch()

    def create_translation_region(self):
        region = TranslationRegion(
            self.engine
        )

        region.closed.connect(
            self.remove_translation_region
        )

        region.show()

        region.set_edit_mode(
            self.regions_in_edit_mode
        )

        self.translation_regions.append(
            region
        )

    def remove_translation_region(
        self,
        region,
    ):
        if region in self.translation_regions:
            self.translation_regions.remove(
                region
            )

    def toggle_region_edit_mode(self):
        self.regions_in_edit_mode = (
            not self.regions_in_edit_mode
        )

        for region in list(
            self.translation_regions
        ):
            region.set_edit_mode(
                self.regions_in_edit_mode
            )

        self.mode_button.setText(
            "Enter Use Mode"
            if self.regions_in_edit_mode
            else "Enter Edit Mode"
        )

    def stop_all_auto_translation(self):
        stopped_count = 0

        for region in list(
            self.translation_regions
        ):
            if region.is_auto_translating:
                region.stop_auto_translation()
                stopped_count += 1

        if stopped_count == 0:
            self.status_label.setText(
                "No regions are currently using "
                "auto translation."
            )
            return

        region_word = (
            "region"
            if stopped_count == 1
            else "regions"
        )

        self.status_label.setText(
            "Stopped auto translation for "
            f"{stopped_count} {region_word}."
        )

    def change_translation_provider(
        self,
        _index,
    ):
        provider = (
            self.provider_combo_box.currentData()
        )

        provider_name = (
            self.provider_combo_box.currentText()
        )

        is_baidu = (
            provider == "baidu"
        )

        self.baidu_credentials_panel.setVisible(
            is_baidu
        )

        self.stop_all_auto_translation()

        try:
            self.engine.set_translation_provider(
                provider
            )

        except Exception as error:
            self.status_label.setText(
                "Failed to select "
                f"{provider_name}:\n{error}"
            )
            return

        for region in list(
            self.translation_regions
        ):
            region.last_original_text = ""

        if (
            is_baidu
            and not self.engine.text_translator
            .has_baidu_credentials()
        ):
            self.status_label.setText(
                "Baidu Translate selected. "
                "Enter your APP ID and Secret Key."
            )
            return

        self.status_label.setText(
            "Translation Service: "
            f"{provider_name}"
        )

    def save_baidu_credentials(self):
        app_id = (
            self.baidu_app_id_input
            .text()
            .strip()
        )

        secret_key = (
            self.baidu_secret_key_input
            .text()
            .strip()
        )

        try:
            self.engine.set_baidu_credentials(
                app_id,
                secret_key,
            )

        except Exception as error:
            self.status_label.setText(
                "Could not save Baidu credentials:\n"
                f"{error}"
            )
            return

        # Do not retain the visible secret after saving.
        self.baidu_secret_key_input.clear()

        self.status_label.setText(
            "Baidu credentials saved for this session."
        )

    def closeEvent(self, event):
        for region in list(
            self.translation_regions
        ):
            region.close()

        self.engine.shutdown()

        super().closeEvent(event)


