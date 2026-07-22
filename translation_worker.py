import time

from PySide6.QtCore import QObject, Signal, Slot


class OCRWorker(QObject):
    """
    专门执行 OCR 的长期后台 Worker。

    这个 Worker 只负责：
    1. 接收截图
    2. 执行 OCR
    3. 返回识别出的原文

    它不会等待翻译网络请求。
    """

    finished = Signal(
        str,    # region_key
        int,    # request_id
        str,    # original_text
        float,  # ocr_ms
    )

    error = Signal(
        str,  # region_key
        int,  # request_id
        str,  # error_message
    )

    def __init__(self, ocr_function):
        super().__init__()
        self._ocr_function = ocr_function

    @Slot(str, int, object)
    def process(
        self,
        region_key,
        request_id,
        screenshot,
    ):
        started_at = time.perf_counter()

        try:
            original_text = self._ocr_function(
                screenshot
            )

            ocr_ms = (
                time.perf_counter() - started_at
            ) * 1000

            self.finished.emit(
                region_key,
                request_id,
                original_text or "",
                ocr_ms,
            )

        except Exception as error:
            self.error.emit(
                region_key,
                request_id,
                str(error),
            )


class TextTranslationWorker(QObject):
    """
    专门执行文本翻译网络请求的长期后台 Worker。

    normalized_text 是翻译任务的唯一键。
    多个区域识别出相同文字时，只翻译一次。
    """

    finished = Signal(
        str,    # normalized_text
        str,    # translated_text
        float,  # translation_ms
    )

    error = Signal(
        str,  # normalized_text
        str,  # error_message
    )

    def __init__(self, translation_function):
        super().__init__()
        self._translation_function = (
            translation_function
        )

    @Slot(str, str)
    def process(
        self,
        normalized_text,
        source_text,
    ):
        started_at = time.perf_counter()

        try:
            translated_text = (
                self._translation_function(
                    source_text
                )
            )

            translation_ms = (
                time.perf_counter() - started_at
            ) * 1000

            self.finished.emit(
                normalized_text,
                translated_text or "",
                translation_ms,
            )

        except Exception as error:
            self.error.emit(
                normalized_text,
                str(error),
            )


