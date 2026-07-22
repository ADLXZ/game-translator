from PySide6.QtCore import QObject, Signal, Slot


class TranslationWorker(QObject):
    """
    长期存在的共享翻译 Worker。
    """

    finished = Signal(str, int, str, str)
    error = Signal(str, int, str)

    def __init__(self, process_function):
        super().__init__()
        self._process_function = process_function

    @Slot(str, int, object)
    def process(
        self,
        region_key,
        request_id,
        screenshot,
    ):
        try:
            original_text, translated_text = (
                self._process_function(
                    region_key,
                    screenshot,
                )
            )

            self.finished.emit(
                region_key,
                request_id,
                original_text,
                translated_text,
            )

        except Exception as error:
            self.error.emit(
                region_key,
                request_id,
                str(error),
            )


