from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QSpinBox,
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
            420,
            520,
        )


        self.main_layout = QVBoxLayout(self)


        # =============================================
        # Translation provider
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


        self.provider_combo_box.addItem(
            "OpenAI",
            "openai",
        )


        self.main_layout.addWidget(
            self.provider_label
        )


        self.main_layout.addWidget(
            self.provider_combo_box
        )

        # =============================================
        # Provider configuration panels
        # =============================================


        self.provider_settings_stack = QStackedWidget()


        self.google_panel = self._create_google_panel()
        self.baidu_panel = self._create_baidu_panel()
        self.openai_panel = self._create_openai_panel()


        self.provider_settings_stack.addWidget(
            self.google_panel
        )


        self.provider_settings_stack.addWidget(
            self.baidu_panel
        )


        self.provider_settings_stack.addWidget(
            self.openai_panel
        )


        self.main_layout.addWidget(
            self.provider_settings_stack
        )


        self.provider_combo_box.currentIndexChanged.connect(
            self.change_translation_provider
        )



        # =============================================
        # OCR Mode
        # =============================================

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        self.main_layout.addWidget(separator)

        self.ocr_mode_label = QLabel(
            "OCR Mode"
        )

        self.main_layout.addWidget(
            self.ocr_mode_label
        )

        self.ocr_mode_combo_box = QComboBox()

        self.ocr_mode_combo_box.addItem(
            "Realtime",
            "realtime",
        )

        self.ocr_mode_combo_box.addItem(
            "Reading Game",
            "reading",
        )

        self.ocr_mode_combo_box.addItem(
            "Scrolling Text",
            "scrolling",
        )

        self.main_layout.addWidget(
            self.ocr_mode_combo_box
        )

        self.ocr_mode_combo_box.currentIndexChanged.connect(
            self.change_ocr_mode
        )

        self.ocr_settings_stack = QStackedWidget()

        self.realtime_panel = self._create_realtime_panel()
        self.reading_panel = self._create_reading_panel()
        self.scrolling_panel = self._create_scrolling_panel()

        self.ocr_settings_stack.addWidget(
            self.realtime_panel
        )

        self.ocr_settings_stack.addWidget(
            self.reading_panel
        )

        self.ocr_settings_stack.addWidget(
            self.scrolling_panel
        )

        self.main_layout.addWidget(
            self.ocr_settings_stack
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


        self.main_layout.addWidget(
            self.create_region_button
        )


        self.main_layout.addWidget(
            self.mode_button
        )


        self.main_layout.addWidget(
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


        self.main_layout.addWidget(
            self.status_label
        )


        self.main_layout.addStretch()


        # Ensure the initial panel and provider match.
        self.provider_settings_stack.setCurrentIndex(0)

        self.engine.set_translation_provider(
            "google"
        )

        self.provider_settings_stack.setCurrentIndex(
            0
        )

        self.engine.set_ocr_mode(
            "realtime"
        )

        self.ocr_settings_stack.setCurrentIndex(
            0
        )

        self.update_status()

    # =================================================
    # Provider panels
    # =================================================


    def _create_google_panel(self):
        panel = QFrame()


        layout = QVBoxLayout(panel)


        help_label = QLabel(
            "Google Translate does not require "
            "additional configuration."
        )


        help_label.setWordWrap(
            True
        )


        layout.addWidget(
            help_label
        )


        return panel


    def _create_baidu_panel(self):
        panel = QFrame()


        layout = QVBoxLayout(panel)


        help_label = QLabel(
            "Enter the APP ID and Secret Key from "
            "the Baidu Translate developer console."
        )


        help_label.setWordWrap(
            True
        )


        form = QFormLayout()


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


        form.addRow(
            "APP ID:",
            self.baidu_app_id_input,
        )


        form.addRow(
            "Secret Key:",
            self.baidu_secret_key_input,
        )


        self.save_baidu_button = QPushButton(
            "Save Baidu Credentials"
        )


        self.save_baidu_button.clicked.connect(
            self.save_baidu_credentials
        )


        layout.addWidget(
            help_label
        )


        layout.addLayout(
            form
        )


        layout.addWidget(
            self.save_baidu_button
        )


        return panel


    def _create_openai_panel(self):
        panel = QFrame()


        layout = QVBoxLayout(panel)


        help_label = QLabel(
            "Enter your OpenAI API key and choose "
            "the translation model and style."
        )


        help_label.setWordWrap(
            True
        )


        form = QFormLayout()


        # ---------------------------------------------
        # API key
        # ---------------------------------------------


        self.openai_api_key_input = QLineEdit()


        self.openai_api_key_input.setPlaceholderText(
            "Enter OpenAI API Key"
        )


        self.openai_api_key_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )


        # ---------------------------------------------
        # Model
        # ---------------------------------------------


        self.openai_model_combo_box = QComboBox()


        self.openai_model_combo_box.setEditable(
            True
        )


        self.openai_model_combo_box.addItem(
            "gpt-5-mini"
        )


        self.openai_model_combo_box.setCurrentText(
            "gpt-5-mini"
        )


        # ---------------------------------------------
        # Style
        # ---------------------------------------------


        self.openai_style_combo_box = QComboBox()


        self.openai_style_combo_box.addItems(
            [
                "Natural",
                "Visual Novel",
                "Casual Dialogue",
                "Fantasy RPG",
                "Literal",
                "Formal",
            ]
        )


        self.openai_style_combo_box.setCurrentText(
            "Natural"
        )


        form.addRow(
            "API Key:",
            self.openai_api_key_input,
        )


        form.addRow(
            "Model:",
            self.openai_model_combo_box,
        )


        form.addRow(
            "Style:",
            self.openai_style_combo_box,
        )


        self.save_openai_button = QPushButton(
            "Save OpenAI Configuration"
        )


        self.save_openai_button.clicked.connect(
            self.save_openai_configuration
        )


        layout.addWidget(
            help_label
        )


        layout.addLayout(
            form
        )


        layout.addWidget(
            self.save_openai_button
        )


        return panel


    # =================================================
    # Translation regions
    # =================================================


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


    # =================================================
    # Provider selection
    # =================================================


    def change_translation_provider(
        self,
        index,
    ):
        provider = (
            self.provider_combo_box.currentData()
        )


        provider_name = (
            self.provider_combo_box.currentText()
        )


        # The provider order matches the QStackedWidget:
        #
        # 0 = Google
        # 1 = Baidu
        # 2 = OpenAI
        self.provider_settings_stack.setCurrentIndex(
            index
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


        # Force every region to translate the next OCR result
        # again after the provider changes.
        for region in list(
            self.translation_regions
        ):
            region.last_original_text = ""


        if provider == "baidu":
            if not (
                self.engine.text_translator
                .has_baidu_credentials()
            ):
                self.status_label.setText(
                    "Baidu Translate selected. "
                    "Enter your APP ID and Secret Key."
                )
                return


        if provider == "openai":
            if not (
                self.engine.text_translator
                .has_openai_configuration()
            ):
                self.status_label.setText(
                    "OpenAI selected. "
                    "Enter your API key and save "
                    "the configuration."
                )
                return


        self.update_status()




    # =================================================
    # Baidu configuration
    # =================================================


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


        if not app_id:
            self.status_label.setText(
                "Please enter your Baidu APP ID."
            )
            return


        if not secret_key:
            self.status_label.setText(
                "Please enter your Baidu Secret Key."
            )
            return


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


    # =================================================
    # OpenAI configuration
    # =================================================


    def save_openai_configuration(self):
        api_key = (
            self.openai_api_key_input
            .text()
            .strip()
        )


        model = (
            self.openai_model_combo_box
            .currentText()
            .strip()
        )


        style = (
            self.openai_style_combo_box
            .currentText()
            .strip()
        )


        if not api_key:
            self.status_label.setText(
                "Please enter your OpenAI API key."
            )
            return


        if not model:
            self.status_label.setText(
                "Please enter an OpenAI model."
            )
            return


        if not style:
            self.status_label.setText(
                "Please select a translation style."
            )
            return


        try:
            self.engine.set_openai_configuration(
                api_key=api_key,
                model=model,
                style=style,
            )


        except Exception as error:
            self.status_label.setText(
                "Could not save OpenAI configuration:\n"
                f"{error}"
            )
            return


        # Do not leave the API key visible in the UI.
        self.openai_api_key_input.clear()


        self.status_label.setText(
            "OpenAI configuration saved for this session.\n"
            f"Model: {model} | Style: {style}"
        )


    # =================================================
    # Shutdown
    # =================================================


    def closeEvent(self, event):
        for region in list(
            self.translation_regions
        ):
            region.close()


        self.engine.shutdown()


        super().closeEvent(event)

    def change_ocr_mode(self, index):

        mode = self.ocr_mode_combo_box.currentData()

        self.engine.set_ocr_mode(mode)

        self.ocr_settings_stack.setCurrentIndex(index)

        self.update_status()

    def update_status(self):

        self.status_label.setText(

            f"Translation: "
            f"{self.provider_combo_box.currentText()}\n"

            f"OCR Mode: "
            f"{self.ocr_mode_combo_box.currentText()}"

        )

    def _create_realtime_panel(self):

        panel = QFrame()

        layout = QVBoxLayout(panel)

        label = QLabel(
            "No additional settings."
        )

        layout.addWidget(label)

        layout.addStretch()

        return panel

    def _create_reading_panel(self):

        panel = QFrame()

        layout = QVBoxLayout(panel)

        form = QFormLayout()

        self.reading_delay_spinbox = QSpinBox()

        self.reading_delay_spinbox.setRange(
            100,
            10000,
        )

        self.reading_delay_spinbox.setValue(
            1800,
        )

        self.reading_delay_spinbox.setSuffix(
            " ms"
        )

        self.reading_delay_spinbox.valueChanged.connect(
            self.engine.set_reading_delay
        )

        form.addRow(
            "Stable Delay:",
            self.reading_delay_spinbox,
        )

        layout.addLayout(form)

        return panel

    def _create_scrolling_panel(self):

        panel = QFrame()

        layout = QVBoxLayout(panel)

        layout.addWidget(
            QLabel(
                "Scrolling mode is under development."
            )
        )

        layout.addStretch()

        return panel


































