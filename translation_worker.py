from PySide6.QtCore import QObject, Signal, Slot


class TranslationWorker(QObject):
    finished = Signal(str, str)
    error = Signal(str)

    def __init__(self, engine, region):
        super().__init__()

        self.engine = engine
        self.region = region

    @Slot()
    def run(self):
        try:
            original_text, translated_text = (
                self.engine.translate_screen(self.region)
            )

            self.finished.emit(
                original_text,
                translated_text,
            )

        except Exception as error:
            self.error.emit(str(error))


