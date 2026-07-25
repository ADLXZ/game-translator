from collections import OrderedDict
import hashlib
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
from translation_worker import (
    OCRWorker,
    TextTranslationWorker,
)
from ocr_strategy import (
    RealtimeStrategy,
    ReadingStrategy,
    ScrollingStrategy,
)

class TranslationEngine(QObject):
    """
    所有翻译区域共享的双流水线翻译引擎。

    流程：

        Screenshot
            ↓
        OCR Worker
            ↓
        Translation Worker
            ↓
        TranslationRegion

    OCR 和网络翻译位于不同线程中，可以重叠执行。
    """

    ocr_requested = Signal(
        str,     # region_key
        int,     # request_id
        object,  # screenshot
    )

    text_translation_requested = Signal(
        str,  # normalized_text
        str,  # source_text
    )

    translation_finished = Signal(
        str,  # region_key
        int,  # request_id
        str,  # original_text
        str,  # translated_text
    )

    translation_failed = Signal(
        str,  # region_key
        int,  # request_id
        str,  # error_message
    )

    def __init__(self):
        super().__init__()

        self.screen_capture = ScreenCapture()
        self.ocr_reader = OCRReader()
        self.text_translator = TextTranslator()

        self._is_shutting_down = False

        # -------------------------------------------------
        # 翻译缓存
        # -------------------------------------------------

        self._translation_cache = OrderedDict()
        self._cache_limit = 500

        # 只保存已经成功处理过的 OCR 文本。
        #
        # key:
        #     region_key
        #
        # value:
        #     normalized_text
        self._last_successful_text_by_region = {}

        # -------------------------------------------------
        # OCR Scheduler
        # -------------------------------------------------

        # 当前 OCR 正在处理的任务：
        #
        # (region_key, request_id)
        self._active_ocr_task = None

        # 每个区域最多保留一个尚未开始的 OCR 任务。
        #
        # key:
        #     region_key
        #
        # value:
        #     (request_id, screenshot)
        self._pending_ocr_tasks = OrderedDict()

        # -------------------------------------------------
        # Reading Game Mode
        # -------------------------------------------------

        # Whether to delay translation until OCR text
        # stops changing.
        self._reading_mode = False

        # OCR text must remain unchanged for this long
        # before translation starts.
        self._reading_delay_ms = 1800

        # region_key -> latest OCR candidate
        self._reading_candidates = {}

        # region_key -> QTimer
        self._reading_timers = {}

        # -------------------------------------------------
        # Translation Scheduler
        # -------------------------------------------------

        # 当前正在进行网络翻译的规范化文本。
        self._active_translation_key = None

        # 尚未开始翻译的文本。
        #
        # key:
        #     normalized_text
        #
        # value:
        #     source_text
        self._pending_translation_tasks = (
            OrderedDict()
        )

        # 相同文本的等待者。
        #
        # key:
        #     normalized_text
        #
        # value:
        #     [
        #         (
        #             region_key,
        #             request_id,
        #             original_text,
        #         ),
        #     ]
        #
        # 多个区域识别出相同文字时，
        # 只发送一个翻译网络请求。
        self._translation_waiters = {}

        # -------------------------------------------------
        # OCR Thread
        # -------------------------------------------------

        self._ocr_thread = QThread(self)

        self._ocr_worker = OCRWorker(
            self.ocr_reader.read_text
        )

        self._ocr_worker.moveToThread(
            self._ocr_thread
        )

        self.ocr_requested.connect(
            self._ocr_worker.process
        )

        self._ocr_worker.finished.connect(
            self._handle_ocr_finished
        )

        self._ocr_worker.error.connect(
            self._handle_ocr_error
        )

        self._ocr_thread.finished.connect(
            self._ocr_worker.deleteLater
        )

        self._ocr_thread.start()

        self._ocr_strategy = RealtimeStrategy()

        # -------------------------------------------------
        # Translation Thread
        # -------------------------------------------------

        self._translation_thread = QThread(self)

        self._translation_worker = (
            TextTranslationWorker(
                self.text_translator.translate
            )
        )

        self._translation_worker.moveToThread(
            self._translation_thread
        )

        self.text_translation_requested.connect(
            self._translation_worker.process
        )

        self._translation_worker.finished.connect(
            self._handle_translation_finished
        )

        self._translation_worker.error.connect(
            self._handle_translation_error
        )

        self._translation_thread.finished.connect(
            self._translation_worker.deleteLater
        )

        self._translation_thread.start()

        app = QApplication.instance()

        if app is not None:
            app.aboutToQuit.connect(
                self.shutdown
            )

    def set_translation_provider(
            self,
            provider,
    ):
        if self._is_shutting_down:
            return

        normalized_provider = (
            str(provider)
            .strip()
            .lower()
        )

        if (
                normalized_provider
                == self.text_translator.provider
        ):
            return

        self.text_translator.set_provider(
            normalized_provider
        )

        self._translation_cache.clear()
        self._last_successful_text_by_region.clear()

        print(
            "Translation provider changed to:",
            normalized_provider,
        )

    # =====================================================
    # Public API
    # =====================================================

    def capture_screen(self, region):
        return self.screen_capture.capture(region)

    def submit_translation(
        self,
        region_key,
        request_id,
        screenshot,
    ):
        """
        向 OCR Scheduler 提交截图。

        OCR 空闲时立即执行。

        OCR 忙碌时：
        同一区域只保留最新截图。
        """
        if self._is_shutting_down:
            return

        if self._active_ocr_task is None:
            self._dispatch_ocr_task(
                region_key,
                request_id,
                screenshot,
            )
            return

        self._pending_ocr_tasks[region_key] = (
            request_id,
            screenshot,
        )

        # 更新过的区域移到队列末尾。
        self._pending_ocr_tasks.move_to_end(
            region_key
        )

    def cancel_region(self, region_key):
        """
        移除区域尚未开始的任务和等待结果。

        已经进入底层 OCR 或网络请求的操作不能强制中断，
        但结果返回后不会再发给已关闭的区域。
        """
        self._pending_ocr_tasks.pop(
            region_key,
            None,
        )

        self._last_successful_text_by_region.pop(
            region_key,
            None,
        )

        self._reading_candidates.pop(
            region_key,
            None,
        )

        reading_timer = self._reading_timers.pop(
            region_key,
            None,
        )

        if reading_timer is not None:
            reading_timer.stop()
            reading_timer.deleteLater()

        empty_translation_keys = []

        for normalized_text, waiters in (
            self._translation_waiters.items()
        ):
            remaining_waiters = [
                waiter
                for waiter in waiters
                if waiter[0] != region_key
            ]

            if remaining_waiters:
                self._translation_waiters[
                    normalized_text
                ] = remaining_waiters
            else:
                empty_translation_keys.append(
                    normalized_text
                )

        for normalized_text in (
            empty_translation_keys
        ):
            self._translation_waiters.pop(
                normalized_text,
                None,
            )

            # 当前已经开始的网络请求无法取消。
            if (
                normalized_text
                != self._active_translation_key
            ):
                self._pending_translation_tasks.pop(
                    normalized_text,
                    None,
                )

    # =====================================================
    # OCR Scheduler
    # =====================================================

    def _dispatch_ocr_task(
        self,
        region_key,
        request_id,
        screenshot,
    ):
        if self._is_shutting_down:
            return

        self._active_ocr_task = (
            region_key,
            request_id,
        )

        self.ocr_requested.emit(
            region_key,
            request_id,
            screenshot,
        )

    def _dispatch_next_ocr_task(self):
        if self._is_shutting_down:
            return

        if self._active_ocr_task is not None:
            return

        if not self._pending_ocr_tasks:
            return

        region_key, task = (
            self._pending_ocr_tasks.popitem(
                last=False
            )
        )

        request_id, screenshot = task

        self._dispatch_ocr_task(
            region_key,
            request_id,
            screenshot,
        )

    @Slot(str, int, str, float)
    def _handle_ocr_finished(
        self,
        region_key,
        request_id,
        original_text,
        ocr_ms,
    ):
        if self._is_shutting_down:
            return

        self._active_ocr_task = None

        original_text = (
            original_text or ""
        ).strip()

        print(
            "[PROFILE][OCR] "
            f"Region: {region_key[:6]} | "
            f"OCR: {ocr_ms:.1f} ms"
        )

        if not original_text:
            self._last_successful_text_by_region.pop(
                region_key,
                None,
            )

            self.translation_finished.emit(
                region_key,
                request_id,
                "",
                "",
            )

            QTimer.singleShot(
                0,
                self._dispatch_next_ocr_task,
            )
            return

        normalized_text = (
            self._normalize_ocr_text(
                original_text
            )
        )

        previous_successful_text = (
            self._last_successful_text_by_region.get(
                region_key
            )
        )

        # 画面发生变化，但 OCR 文字与上一次成功结果相同。
        if (
            normalized_text
            == previous_successful_text
        ):
            print(
                "[PROFILE][OCR] "
                f"Region: {region_key[:6]} | "
                "Translate: skipped | "
                "Unchanged OCR text"
            )

            self.translation_finished.emit(
                region_key,
                request_id,
                original_text,
                "",
            )

            QTimer.singleShot(
                0,
                self._dispatch_next_ocr_task,
            )
            return

        cache_key = (
            self.text_translator.provider,
            normalized_text,
        )

        cached_translation = (
            self._translation_cache.get(
                cache_key
            )
        )

        if cached_translation is not None:
            self._translation_cache.move_to_end(
                cache_key
            )

            self._last_successful_text_by_region[
                region_key
            ] = normalized_text

            print(
                "[PROFILE][Translate] "
                f"Region: {region_key[:6]} | "
                "Cache: hit"
            )

            self.translation_finished.emit(
                region_key,
                request_id,
                original_text,
                cached_translation,
            )

            QTimer.singleShot(
                0,
                self._dispatch_next_ocr_task,
            )
            return

        self._ocr_strategy.handle_ocr_result(
            self,
            region_key,
            request_id,
            normalized_text,
            original_text,
        )

        # 重点：
        # 不等待翻译完成，OCR 立即处理下一张图。
        QTimer.singleShot(
            0,
            self._dispatch_next_ocr_task,
        )

    @Slot(str, int, str)
    def _handle_ocr_error(
        self,
        region_key,
        request_id,
        error_message,
    ):
        if self._is_shutting_down:
            return

        self._active_ocr_task = None

        self.translation_failed.emit(
            region_key,
            request_id,
            f"OCR failed: {error_message}",
        )

        QTimer.singleShot(
            0,
            self._dispatch_next_ocr_task,
        )

    # =====================================================
    # Translation Scheduler
    # =====================================================
    def _schedule_reading_translation(
            self,
            normalized_text,
            source_text,
            region_key,
            request_id,
    ):
        self._reading_candidates[region_key] = (
            normalized_text,
            source_text,
            request_id,
        )

        timer = self._reading_timers.get(
            region_key
        )

        if timer is None:
            timer = QTimer(self)
            timer.setSingleShot(True)

            timer.timeout.connect(
                lambda key=region_key:
                self._commit_reading_translation(
                    key
                )
            )

            self._reading_timers[
                region_key
            ] = timer

        timer.start(
            self._reading_delay_ms
        )

    def _commit_reading_translation(
            self,
            region_key,
    ):
        candidate = self._reading_candidates.pop(
            region_key,
            None,
        )

        if candidate is None:
            return

        (
            normalized_text,
            source_text,
            request_id,
        ) = candidate

        self._queue_translation(
            normalized_text=normalized_text,
            source_text=source_text,
            region_key=region_key,
            request_id=request_id,
        )

    def _queue_translation(
        self,
        normalized_text,
        source_text,
        region_key,
        request_id,
    ):
        waiter = (
            region_key,
            request_id,
            source_text,
        )

        waiters = self._translation_waiters.setdefault(
            normalized_text,
            [],
        )

        waiters.append(waiter)

        # 相同文字已经正在翻译。
        if (
            normalized_text
            == self._active_translation_key
        ):
            print(
                "[PROFILE][Translate] "
                f"Region: {region_key[:6]} | "
                "Deduplicated: active request"
            )
            return

        # 相同文字已经在等待队列中。
        if (
            normalized_text
            in self._pending_translation_tasks
        ):
            print(
                "[PROFILE][Translate] "
                f"Region: {region_key[:6]} | "
                "Deduplicated: pending request"
            )
            return

        if self._active_translation_key is None:
            self._dispatch_translation_task(
                normalized_text,
                source_text,
            )
            return

        self._pending_translation_tasks[
            normalized_text
        ] = source_text

    def _dispatch_translation_task(
        self,
        normalized_text,
        source_text,
    ):
        if self._is_shutting_down:
            return

        self._active_translation_key = (
            normalized_text
        )

        self.text_translation_requested.emit(
            normalized_text,
            source_text,
        )

    def _dispatch_next_translation_task(self):
        if self._is_shutting_down:
            return

        if self._active_translation_key is not None:
            return

        if not self._pending_translation_tasks:
            return

        normalized_text, source_text = (
            self._pending_translation_tasks.popitem(
                last=False
            )
        )

        # 等待区域可能已经全部关闭。
        if not self._translation_waiters.get(
            normalized_text
        ):
            QTimer.singleShot(
                0,
                self._dispatch_next_translation_task,
            )
            return

        self._dispatch_translation_task(
            normalized_text,
            source_text,
        )

    @Slot(str, str, float)
    def _handle_translation_finished(
        self,
        normalized_text,
        translated_text,
        translation_ms,
    ):
        if self._is_shutting_down:
            return

        self._active_translation_key = None

        translated_text = (
            translated_text or ""
        ).strip()

        print(
            "[PROFILE][Translate] "
            f"Translate: {translation_ms:.1f} ms | "
            "Cache: miss"
        )

        self._store_cached_translation(
            normalized_text,
            translated_text,
        )

        waiters = self._translation_waiters.pop(
            normalized_text,
            [],
        )

        for (
            region_key,
            request_id,
            original_text,
        ) in waiters:
            self._last_successful_text_by_region[
                region_key
            ] = normalized_text

            self.translation_finished.emit(
                region_key,
                request_id,
                original_text,
                translated_text,
            )

        QTimer.singleShot(
            0,
            self._dispatch_next_translation_task,
        )

    @Slot(str, str)
    def _handle_translation_error(
        self,
        normalized_text,
        error_message,
    ):
        if self._is_shutting_down:
            return

        self._active_translation_key = None

        waiters = self._translation_waiters.pop(
            normalized_text,
            [],
        )

        # 翻译失败时不记录 last successful text，
        # 下次遇到相同文字仍然可以重新尝试。
        for (
            region_key,
            request_id,
            _original_text,
        ) in waiters:
            self.translation_failed.emit(
                region_key,
                request_id,
                f"Translation failed: {error_message}",
            )

        QTimer.singleShot(
            0,
            self._dispatch_next_translation_task,
        )

    # =====================================================
    # Helpers
    # =====================================================

    def _normalize_ocr_text(self, text):
        if not text:
            return ""

        normalized = text.strip()

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        )

        normalized = re.sub(
            r"\s+([,.!?;:，。！？；：])",
            r"\1",
            normalized,
        )

        return normalized

    def _store_cached_translation(
            self,
            normalized_text,
            translated_text,
    ):
        cache_key = (
            self.text_translator.provider,
            normalized_text,
        )

        self._translation_cache[
            cache_key
        ] = translated_text

        self._translation_cache.move_to_end(
            cache_key
        )

        while (
                len(self._translation_cache)
                > self._cache_limit
        ):
            self._translation_cache.popitem(
                last=False
            )

    def fingerprint_screenshot(self, screenshot):
        """
        为截图生成快速指纹。
        """
        if screenshot is None:
            return None

        if isinstance(
            screenshot,
            (
                bytes,
                bytearray,
                memoryview,
            ),
        ):
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

    # =====================================================
    # Shutdown
    # =====================================================

    @Slot()
    def shutdown(self):
        if self._is_shutting_down:
            return

        self._is_shutting_down = True

        self._pending_ocr_tasks.clear()
        self._pending_translation_tasks.clear()
        self._translation_waiters.clear()

        self._active_ocr_task = None
        self._active_translation_key = None

        threads = (
            (
                "OCR",
                self._ocr_thread,
            ),
            (
                "translation",
                self._translation_thread,
            ),
        )

        for thread_name, thread in threads:
            if not thread.isRunning():
                continue

            thread.quit()

            if not thread.wait(5000):
                print(
                    f"Warning: {thread_name} worker "
                    "did not stop within five seconds."
                )

    def set_baidu_credentials(
            self,
            app_id,
            secret_key,
    ):
        """
        Update the Baidu credentials used by the
        shared translation worker.
        """
        if self._is_shutting_down:
            return

        self.text_translator.set_baidu_credentials(
            app_id,
            secret_key,
        )

        # Credentials may belong to a different Baidu account,
        # so old Baidu translation results must not be reused.
        self._translation_cache.clear()
        self._last_successful_text_by_region.clear()

        print(
            "Baidu Translate credentials updated."
        )

    def set_openai_configuration(
            self,
            api_key,
            model="gpt-5-mini",
            style="Natural",
    ):
        if self._is_shutting_down:
            return

        self.text_translator.set_openai_configuration(
            api_key=api_key,
            model=model,
            style=style,
        )

        self._translation_cache.clear()
        self._last_successful_text_by_region.clear()

        print(
            "OpenAI configuration updated."
        )

    def set_reading_mode(
            self,
            enabled,
    ):
        self._reading_mode = bool(enabled)

        if not enabled:
            for timer in self._reading_timers.values():
                timer.stop()

            self._reading_candidates.clear()

        print(
            "Reading Game Mode:",
            "enabled" if enabled else "disabled",
        )

    def set_reading_delay(
            self,
            delay_ms,
    ):
        self._reading_delay_ms = max(
            100,
            int(delay_ms),
        )

        print(
            "Reading delay:",
            self._reading_delay_ms,
            "ms",
        )

    def set_ocr_mode(self, mode: str):
        normalized_mode = str(mode).strip().lower()

        # 切换模式时，停止 Reading 模式遗留的计时器。
        for timer in self._reading_timers.values():
            timer.stop()

        self._reading_candidates.clear()

        if normalized_mode == "realtime":
            self._ocr_strategy = RealtimeStrategy()
            self._reading_mode = False

        elif normalized_mode == "reading":
            self._ocr_strategy = ReadingStrategy()
            self._reading_mode = True

        elif normalized_mode == "scrolling":
            self._ocr_strategy = ScrollingStrategy()
            self._reading_mode = False

        else:
            raise ValueError(
                f"Unknown OCR mode: {mode}"
            )

        print(
            "OCR mode changed to:",
            normalized_mode,
        )
























