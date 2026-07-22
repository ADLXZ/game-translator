from PySide6.QtCore import QObject, Signal, Slot


class TranslationWorker(QObject):
    finished = Signal(int, str, str)
    error = Signal(int, str)

    def __init__(self, request_id, engine, screenshot):
        super().__init__()
        self.request_id = request_id
        self.engine = engine
        self.screenshot = screenshot

    @Slot()
    def run(self):
        try:
            original_text, translated_text = self.engine.translate_screenshot(
                self.screenshot
            )
            self.finished.emit(
                self.request_id,
                original_text,
                translated_text,
            )
        except Exception as error:
            self.error.emit(self.request_id, str(error))
