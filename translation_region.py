from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

from overlay_window import OverlayWindow


class TranslationRegion(QWidget):

    def __init__(self, engine):
        super().__init__()

        self.engine = engine
        self.drag_position = None
        self.is_translating = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.setCursor(Qt.CursorShape.SizeAllCursor)

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

        pen = QPen(Qt.GlobalColor.red)
        pen.setWidth(2)

        painter.setPen(pen)
        painter.drawRect(
            self.rect().adjusted(1, 1, -2, -2)
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )

            event.accept()

    def mouseMoveEvent(self, event):
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

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = None
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

        self.is_translating = True
        self.overlay.set_translation("Translating...")

        region = self.get_capture_region()

        self.hide()
        QApplication.processEvents()

        try:
            translated_text = self.engine.translate_screen(
                region
            )

            if translated_text:
                self.overlay.set_translation(
                    translated_text
                )
            else:
                self.overlay.set_translation(
                    "No text detected"
                )

        except Exception as error:
            print("Translation error:", error)

            self.overlay.set_translation(
                f"Translation failed:\n{error}"
            )

        finally:
            self.show()
            self.raise_()
            self.update_overlay_position()
            self.is_translating = False


