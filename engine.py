from collections import OrderedDict
from threading import Lock
import hashlib
import time
import re

from PySide6.QtCore import (
    QObject,
    QThread,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtWidgets import QApplication

from ocr import OCRReader
from screenshot import ScreenCapture
from translator import TextTranslator
from translation_worker import TranslationWorker


class TranslationEngine(QObject):
    """
    所有翻译区域共享的翻译引擎。

    Scheduler 规则：
    1. Worker 同一时间只执行一个任务。
    2. 每个区域在等待队列中最多保留一个任务。
    3. 同一区域再次提交时，新任务覆盖旧任务。
    """

    translation_requested = Signal(
        str,
        int,
        object,
    )

    translation_finished = Signal(
        str,
        int,
        str,
        str,
    )

    translation_failed = Signal(
        str,
        int,
        str,
    )

    def __init__(self):
        super().__init__()

        self.screen_capture = ScreenCapture()
        self.ocr_reader = OCRReader()
        self.text_translator = TextTranslator()

        self._processing_lock = Lock()

        self._translation_cache = OrderedDict()
        self._cache_limit = 500
        # 保存每个区域最近一次完成 OCR 的规范化文本。
        self._last_ocr_text_by_region = {}

        self._is_shutting_down = False

        # 当前 Worker 正在处理的任务。
        # 格式：
        # (region_key, request_id)
        self._active_task = None

        # 等待任务。
        # key: region_key
        # value: (request_id, screenshot)
        #
        # OrderedDict 可以保留区域进入队列的顺序。
        self._pending_tasks = OrderedDict()

        self._worker_thread = QThread(self)

        self._worker = TranslationWorker(
            self.translate_screenshot_sync
        )
        self._worker.moveToThread(self._worker_thread)

        self.translation_requested.connect(
            self._worker.process
        )

        self._worker.finished.connect(
            self._handle_worker_finished
        )

        self._worker.error.connect(
            self._handle_worker_error
        )

        self._worker_thread.finished.connect(
            self._worker.deleteLater
        )

        self._worker_thread.start()

        app = QApplication.instance()

        if app is not None:
            app.aboutToQuit.connect(self.shutdown)

    def capture_screen(self, region):
        return self.screen_capture.capture(region)

    def submit_translation(
        self,
        region_key,
        request_id,
        screenshot,
    ):
        """
        向 Scheduler 提交翻译任务。

        Worker 空闲：
            立即执行。

        Worker 忙碌：
            放入等待队列。

        同一区域已经存在等待任务：
            使用新截图覆盖旧截图。
        """
        if self._is_shutting_down:
            return

        if self._active_task is None:
            self._dispatch_task(
                region_key,
                request_id,
                screenshot,
            )
            return

        # 覆盖这个区域之前尚未开始的旧任务。
        self._pending_tasks[region_key] = (
            request_id,
            screenshot,
        )

        # 将刚刚更新的区域移到队列末尾，
        # 保持不同区域之间相对公平。
        self._pending_tasks.move_to_end(region_key)

    def cancel_region(self, region_key):
        self._pending_tasks.pop(
            region_key,
            None,
        )

        self._last_ocr_text_by_region.pop(
            region_key,
            None,
        )

    def _dispatch_task(
        self,
        region_key,
        request_id,
        screenshot,
    ):
        if self._is_shutting_down:
            return

        self._active_task = (
            region_key,
            request_id,
        )

        self.translation_requested.emit(
            region_key,
            request_id,
            screenshot,
        )

    def _dispatch_next_task(self):
        if self._is_shutting_down:
            return

        if self._active_task is not None:
            return

        if not self._pending_tasks:
            return

        region_key, task = (
            self._pending_tasks.popitem(last=False)
        )

        request_id, screenshot = task

        self._dispatch_task(
            region_key,
            request_id,
            screenshot,
        )

    def _normalize_ocr_text(self, text):
        """
        清理 OCR 产生的不稳定空格和换行。

        只用于比较和缓存，不改变最终显示文本。
        """
        if not text:
            return ""

        normalized = text.strip()

        # 连续空白统一成一个空格。
        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        )

        # 清除部分标点前面不稳定的空格。
        normalized = re.sub(
            r"\s+([,.!?;:，。！？；：])",
            r"\1",
            normalized,
        )

        return normalized

    def translate_screenshot_sync(
            self,
            region_key,
            screenshot,
    ):
        """
        后台执行 OCR 和翻译。

        如果同一区域 OCR 得到的文字未变化，
        直接跳过翻译接口。
        """
        total_started_at = time.perf_counter()

        with self._processing_lock:
            ocr_started_at = time.perf_counter()

            original_text = self.ocr_reader.read_text(
                screenshot
            )

            ocr_ms = (
                             time.perf_counter() - ocr_started_at
                     ) * 1000

            if not original_text:
                self._last_ocr_text_by_region.pop(
                    region_key,
                    None,
                )

                total_ms = (
                                   time.perf_counter() - total_started_at
                           ) * 1000

                print(
                    "[PROFILE] "
                    f"OCR: {ocr_ms:.1f} ms | "
                    "Translate: skipped | "
                    f"Worker total: {total_ms:.1f} ms | "
                    "No text"
                )

                return "", ""

            normalized_text = self._normalize_ocr_text(
                original_text
            )

            previous_text = (
                self._last_ocr_text_by_region.get(
                    region_key
                )
            )

            if normalized_text == previous_text:
                total_ms = (
                                   time.perf_counter() - total_started_at
                           ) * 1000

                print(
                    "[PROFILE] "
                    f"OCR: {ocr_ms:.1f} ms | "
                    "Translate: skipped | "
                    f"Worker total: {total_ms:.1f} ms | "
                    "Unchanged OCR text"
                )

                # 返回原文字，但不再调用网络翻译。
                # 空翻译代表 Overlay 不需要更新。
                return original_text, ""

            self._last_ocr_text_by_region[
                region_key
            ] = normalized_text

            translation_started_at = time.perf_counter()

            cached_translation = (
                self._translation_cache.get(
                    normalized_text
                )
            )

            if cached_translation is not None:
                translated_text = cached_translation
                cache_hit = True

                self._translation_cache.move_to_end(
                    normalized_text
                )

            else:
                translated_text = (
                    self.text_translator.translate(
                        original_text
                    )
                )

                cache_hit = False

                self._translation_cache[
                    normalized_text
                ] = translated_text

                self._translation_cache.move_to_end(
                    normalized_text
                )

                while (
                        len(self._translation_cache)
                        > self._cache_limit
                ):
                    self._translation_cache.popitem(
                        last=False
                    )

            translation_ms = (
                                     time.perf_counter()
                                     - translation_started_at
                             ) * 1000

            total_ms = (
                               time.perf_counter() - total_started_at
                       ) * 1000

            cache_status = (
                "hit"
                if cache_hit
                else "miss"
            )

            print(
                "[PROFILE] "
                f"OCR: {ocr_ms:.1f} ms | "
                f"Translate: {translation_ms:.1f} ms | "
                f"Cache: {cache_status} | "
                f"Worker total: {total_ms:.1f} ms"
            )

            return original_text, translated_text

    def translate_screenshot(self, screenshot):
        """
        保留旧接口，避免其他代码调用时报错。
        """
        return self.translate_screenshot_sync(screenshot)

    def translate_screen(self, region):
        screenshot = self.capture_screen(region)
        return self.translate_screenshot_sync(screenshot)

    def _get_cached_translation(self, text):
        cached = self._translation_cache.get(text)

        if cached is not None:
            self._translation_cache.move_to_end(text)
            return cached

        translated = self.text_translator.translate(text)

        self._translation_cache[text] = translated
        self._translation_cache.move_to_end(text)

        while len(self._translation_cache) > self._cache_limit:
            self._translation_cache.popitem(last=False)

        return translated

    @Slot(str, int, str, str)
    def _handle_worker_finished(
        self,
        region_key,
        request_id,
        original_text,
        translated_text,
    ):
        if self._is_shutting_down:
            return

        # 清除当前任务后再向区域发送结果。
        self._active_task = None

        self.translation_finished.emit(
            region_key,
            request_id,
            original_text,
            translated_text,
        )

        # 等当前结果的 UI 回调完成后，再启动下一个任务。
        QTimer.singleShot(
            0,
            self._dispatch_next_task,
        )

    @Slot(str, int, str)
    def _handle_worker_error(
        self,
        region_key,
        request_id,
        error_message,
    ):
        if self._is_shutting_down:
            return

        self._active_task = None

        self.translation_failed.emit(
            region_key,
            request_id,
            error_message,
        )

        QTimer.singleShot(
            0,
            self._dispatch_next_task,
        )

    @Slot()
    def shutdown(self):
        if self._is_shutting_down:
            return

        self._is_shutting_down = True

        self._pending_tasks.clear()
        self._active_task = None

        if self._worker_thread.isRunning():
            self._worker_thread.quit()

            if not self._worker_thread.wait(5000):
                print(
                    "Warning: translation worker did not "
                    "stop within five seconds."
                )

    def fingerprint_screenshot(self, screenshot):
        """
        为截图生成一个快速指纹。

        支持常见截图类型：
        - PIL.Image
        - numpy.ndarray
        - bytes / bytearray
        """

        if screenshot is None:
            return None

        if isinstance(screenshot, (bytes, bytearray, memoryview)):
            raw_data = bytes(screenshot)

        elif hasattr(screenshot, "tobytes"):
            raw_data = screenshot.tobytes()

        else:
            raw_data = repr(screenshot).encode(
                "utf-8",
                errors="replace",
            )

        return hashlib.blake2b(
            raw_data,
            digest_size=8,
        ).hexdigest()




