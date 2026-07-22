from PySide6.QtCore import QRect, Qt, QThread, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

from overlay_window import OverlayWindow
from translation_worker import TranslationWorker


class TranslationRegion(QWidget):

    def __init__(self, engine):
        super().__init__()

        self.engine = engine
        self.drag_position = None
        self.is_resizing = False
        self.resize_margin = 16
        self.minimum_region_width = 120
        self.minimum_region_height = 60
        self.is_translating = False
        self.last_original_text = ""
        self.is_auto_translating = False

        self.translation_thread = None
        self.translation_worker = None

        self.translation_timer = QTimer(self)
        self.translation_timer.setInterval(2000)
        self.translation_timer.timeout.connect(
            self.auto_translate_once
        )

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.setMouseTracking(True)

        self.resize(500, 160)
        self.move(300, 300)

        self.overlay = OverlayWindow()
        self.overlay.set_translation(
            "Double-click the region to translate"
        )

        self.show()
        self.update_overlay_position()

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.fillRect(
            self.rect(),
            QColor(0, 0, 0, 40),
        )

        if self.is_auto_translating:
            pen = QPen(Qt.GlobalColor.green)
        else:
            pen = QPen(Qt.GlobalColor.red)

        pen.setWidth(2)

        painter.setPen(pen)
        painter.drawRect(
            self.rect().adjusted(1, 1, -2, -2)
        )

        handle_size = 12

        handle_rect = QRect(
            self.width() - handle_size - 2,
            self.height() - handle_size - 2,
            handle_size,
            handle_size,
        )

        painter.fillRect(
            handle_rect,
            pen.color(),
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.toggle_auto_translation()
            event.accept()
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        if self.is_in_resize_area(event.position()):
            self.is_resizing = True
            self.drag_position = None

            self.setCursor(
                Qt.CursorShape.SizeFDiagCursor
            )
        else:
            self.is_resizing = False

            self.drag_position = (
                    event.globalPosition().toPoint()
                    - self.frameGeometry().topLeft()
            )

            self.setCursor(
                Qt.CursorShape.SizeAllCursor
            )

        event.accept()

    def mouseMoveEvent(self, event):
        if self.is_resizing:
            new_width = max(
                self.minimum_region_width,
                round(event.position().x()),
            )

            new_height = max(
                self.minimum_region_height,
                round(event.position().y()),
            )

            self.resize(
                new_width,
                new_height,
            )

            self.update_overlay_position()
            self.update()

            event.accept()
            return

        if (
                self.drag_position is not None
                and event.buttons() & Qt.MouseButton.LeftButton
        ):
            new_position = (
                    event.globalPosition().toPoint()
                    - self.drag_position
            )

            self.move(new_position)
            self.update_overlay_position()

            event.accept()
            return

        if self.is_in_resize_area(event.position()):
            self.setCursor(
                Qt.CursorShape.SizeFDiagCursor
            )
        else:
            self.setCursor(
                Qt.CursorShape.SizeAllCursor
            )

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        self.drag_position = None
        self.is_resizing = False

        if self.is_in_resize_area(event.position()):
            self.setCursor(
                Qt.CursorShape.SizeFDiagCursor
            )
        else:
            self.setCursor(
                Qt.CursorShape.SizeAllCursor
            )

        self.update_overlay_position()
        event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.translate_once()
            event.accept()

    def update_overlay_position(self):
        gap = 20

        self.overlay.move(
            self.x() + self.width() + gap,
            self.y()
        )

    def get_capture_region(self):
        top_left_global = self.mapToGlobal(
            self.rect().topLeft()
        )

        scale_factor = self.devicePixelRatioF()

        return {
            "left": round(
                top_left_global.x() * scale_factor
            ),
            "top": round(
                top_left_global.y() * scale_factor
            ),
            "width": round(
                self.width() * scale_factor
            ),
            "height": round(
                self.height() * scale_factor
            ),
        }

    def translate_once(self):
        if self.is_translating:
            return

        self.overlay.set_translation(
            "Translating..."
        )

        self.start_background_translation()

    def toggle_auto_translation(self):
        if self.is_auto_translating:
            self.stop_auto_translation()
        else:
            self.start_auto_translation()

    def start_auto_translation(self):
        self.is_auto_translating = True
        self.last_original_text = ""

        self.translation_timer.start()

        self.overlay.set_translation(
            "Auto translation started..."
        )

        self.update()
        self.auto_translate_once()

    def stop_auto_translation(self):
        print("Stopping auto translation")

        self.translation_timer.stop()
        self.is_auto_translating = False

        self.overlay.set_translation(
            "Auto translation stopped"
        )

        self.update()

    def auto_translate_once(self):
        if not self.is_auto_translating:
            return

        if self.is_translating:
            return

        self.start_background_translation()

    def start_background_translation(self):
        if self.is_translating:
            return

        self.is_translating = True

        region = self.get_capture_region()

        try:
            self.hide()
            QApplication.processEvents()

            screenshot = self.engine.capture_screen(
                region
            )

        except Exception as error:
            self.handle_translation_error(str(error))
            self.is_translating = False
            return

        finally:
            self.show()
            self.raise_()
            self.update_overlay_position()

        self.translation_thread = QThread()

        self.translation_worker = TranslationWorker(
            self.engine,
            screenshot,
        )

        self.translation_worker.moveToThread(
            self.translation_thread
        )

        self.translation_thread.started.connect(
            self.translation_worker.run
        )

        self.translation_worker.finished.connect(
            self.handle_translation_result
        )

        self.translation_worker.error.connect(
            self.handle_translation_error
        )

        self.translation_worker.finished.connect(
            self.translation_thread.quit
        )

        self.translation_worker.error.connect(
            self.translation_thread.quit
        )

        self.translation_thread.finished.connect(
            self.cleanup_translation_thread
        )

        self.translation_thread.start()

    def handle_translation_result(
            self,
            original_text,
            translated_text,
    ):
        if not original_text:
            if not self.is_auto_translating:
                self.overlay.set_translation(
                    "No text detected"
                )
            return

        if original_text == self.last_original_text:
            return

        self.last_original_text = original_text

        if translated_text:
            self.overlay.set_translation(
                translated_text
            )

    def handle_translation_error(self, error_message):
        print("Translation error:", error_message)

        self.overlay.set_translation(
            f"Translation failed:\n{error_message}"
        )

    def cleanup_translation_thread(self):
        self.translation_worker = None
        self.translation_thread = None
        self.is_translating = False

    def is_in_resize_area(self, position):
        return (
                position.x() >= self.width() - self.resize_margin
                and position.y() >= self.height() - self.resize_margin
        )





