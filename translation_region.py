
import ctypes
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

from overlay_window import OverlayWindow
from PySide6.QtCore import QRect
from translation_worker import TranslationWorker
from PySide6.QtGui import QPainter, QPen, QColor


WDA_EXCLUDEFROMCAPTURE = 0x00000011


def exclude_window_from_capture(widget):
    """让 Windows 截图和录屏忽略这个窗口。"""
    try:
        hwnd = int(widget.winId())

        result = ctypes.windll.user32.SetWindowDisplayAffinity(
            hwnd,
            WDA_EXCLUDEFROMCAPTURE,
        )

        if not result:
            print("Warning: failed to exclude window from capture")

    except Exception as error:
        print("Display affinity error:", error)




class TranslationRegion(QWidget):
    closed = Signal(object)

    def __init__(self, engine):
        super().__init__()

        self.engine = engine

        self.drag_position = None
        self.is_resizing = False
        self.resize_margin = 16
        self.minimum_region_width = 120
        self.minimum_region_height = 60
        self.close_button_size = 22
        self.drag_handle_width = 54
        self.drag_handle_height = 20

        self.edit_mode = True
        self.is_translating = False
        self.is_auto_translating = False
        self.last_original_text = ""

        # self.translation_thread = None
        # self.translation_worker = None

        self._request_id = 0
        self._pending_capture_region = None
        self._overlay_was_visible = False
        self._closing = False

        self.translation_timer = QTimer(self)
        self.translation_timer.setInterval(3000)
        self.translation_timer.timeout.connect(self.auto_translate_once)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.SizeAllCursor)

        self.resize(500, 160)
        self.move(300, 300)

        self.overlay = OverlayWindow()
        self.overlay.set_translation("Double-click the region to translate")

    def showEvent(self, event):
        super().showEvent(event)

        exclude_window_from_capture(self)

        if not self._closing and not self.is_translating:
            self.update_overlay_position()
            self.overlay.show()
            self.overlay.raise_()

    def get_drag_handle_rect(self):
        return QRect(
            (self.width() - self.drag_handle_width) // 2,
            self.height() - self.drag_handle_height - 3,
            self.drag_handle_width,
            self.drag_handle_height,
        )

    def get_drag_hit_rect(self):
        """真正用于点击检测，比视觉上的 Handle 大。"""
        rect = self.get_drag_handle_rect()

        return rect.adjusted(
            -300,  # 左
            -150,  # 上
            300,  # 右
            150,  # 下
        )

    def paintEvent(self, event):
        super().paintEvent(event)

        if not self.edit_mode:
            return

        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        normal_pink = QColor(255, 125, 180)
        active_pink = QColor(255, 70, 155)

        border_color = (
            active_pink
            if self.is_auto_translating
            else normal_pink
        )

        # 粉色选框
        painter.setPen(QPen(border_color, 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        painter.drawRect(
            self.rect().adjusted(1, 1, -2, -2)
        )

        # 左上角关闭按钮区域
        button_rect = QRect(
            4,
            3,
            self.close_button_size,
            self.close_button_size,
        )

        # 使用两条线绘制 ×，不再使用字体字符
        painter.setPen(
            QPen(
                border_color,
                2,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )

        close_center_x = button_rect.center().x()
        close_center_y = button_rect.center().y()
        close_radius = 5

        painter.drawLine(
            close_center_x - close_radius,
            close_center_y - close_radius,
            close_center_x + close_radius,
            close_center_y + close_radius,
        )

        painter.drawLine(
            close_center_x - close_radius,
            close_center_y + close_radius,
            close_center_x + close_radius,
            close_center_y - close_radius,
        )

        # 下方中间拖动手柄区域
        handle_rect = self.get_drag_hit_rect()

        # 暂时关闭抗锯齿，避免小点边缘出现浅色像素
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            False,
        )

        dot_size = 3
        horizontal_gap = 8
        vertical_gap = 6

        center_x = handle_rect.center().x()
        center_y = handle_rect.center().y()

        # 两行三列的小方点
        for row in (-1, 1):
            for column in (-1, 0, 1):
                dot_x = center_x + column * horizontal_gap
                dot_y = center_y + row * vertical_gap // 2

                painter.fillRect(
                    dot_x - dot_size // 2,
                    dot_y - dot_size // 2,
                    dot_size,
                    dot_size,
                    border_color,
                )

        # 重新开启抗锯齿，绘制右下角缩放线
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        painter.setPen(
            QPen(
                border_color,
                2,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )

        bottom_right_x = self.width() - 5
        bottom_right_y = self.height() - 5

        for offset in (0, 5, 10):
            painter.drawLine(
                bottom_right_x - 5 - offset,
                bottom_right_y,
                bottom_right_x,
                bottom_right_y - 5 - offset,
            )

    def mousePressEvent(self, event):
        if not self.edit_mode:
            event.ignore()
            return

        mouse_position = event.position().toPoint()

        button_rect = QRect(
            4,
            3,
            self.close_button_size,
            self.close_button_size,
        )

        # 关闭按钮
        if (
                event.button() == Qt.MouseButton.LeftButton
                and button_rect.contains(mouse_position)
        ):
            self.close()
            event.accept()
            return

        # 右键切换自动翻译
        if event.button() == Qt.MouseButton.RightButton:
            self.toggle_auto_translation()
            event.accept()
            return

        if event.button() != Qt.MouseButton.LeftButton:
            event.ignore()
            return

        # 右下角缩放
        if self.is_in_resize_area(event.position()):
            self.is_resizing = True
            self.drag_position = None
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)

        else:
            # 点住底部手柄或者框内其他位置都可以移动
            self.is_resizing = False
            self.drag_position = (
                    event.globalPosition().toPoint()
                    - self.frameGeometry().topLeft()
            )
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

        event.accept()

    def mouseMoveEvent(self, event):
        if not self.edit_mode:
            event.ignore()
            return

        if self.is_resizing:
            self.resize(
                max(
                    self.minimum_region_width,
                    round(event.position().x()),
                ),
                max(
                    self.minimum_region_height,
                    round(event.position().y()),
                ),
            )

            self.update_overlay_position()
            self.update()
            event.accept()
            return

        if (
                self.drag_position is not None
                and event.buttons() & Qt.MouseButton.LeftButton
        ):
            self.move(
                event.globalPosition().toPoint()
                - self.drag_position
            )

            self.update_overlay_position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        mouse_position = event.position().toPoint()

        if self.is_in_resize_area(event.position()):
            cursor = Qt.CursorShape.SizeFDiagCursor

        elif self.get_drag_hit_rect().contains(mouse_position):
            cursor = Qt.CursorShape.OpenHandCursor

        else:
            cursor = Qt.CursorShape.SizeAllCursor

        self.setCursor(cursor)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            event.ignore()
            return

        self.drag_position = None
        self.is_resizing = False

        mouse_position = event.position().toPoint()

        if self.is_in_resize_area(event.position()):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)

        elif self.get_drag_hit_rect().contains(mouse_position):
            self.setCursor(Qt.CursorShape.OpenHandCursor)

        else:
            self.setCursor(Qt.CursorShape.SizeAllCursor)

        self.update_overlay_position()
        event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.translate_once()
            event.accept()

    def moveEvent(self, event):
        super().moveEvent(event)
        if hasattr(self, "overlay") and not self.is_translating:
            self.update_overlay_position()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "overlay") and not self.is_translating:
            self.update_overlay_position()

    def update_overlay_position(self):
        if not hasattr(self, "overlay"):
            return

        global_position = self.mapToGlobal(self.rect().topLeft())

        self.overlay.setGeometry(
            global_position.x(),
            global_position.y(),
            self.width(),
            self.height(),
        )

        self.overlay.raise_()

    def get_capture_region(self):
        top_left_global = self.mapToGlobal(self.rect().topLeft())
        scale_factor = self.devicePixelRatioF()

        return {
            "left": round(top_left_global.x() * scale_factor),
            "top": round(top_left_global.y() * scale_factor),
            "width": round(self.width() * scale_factor),
            "height": round(self.height() * scale_factor),
        }

    def translate_once(self):
        if self.is_translating:
            return

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
        self.overlay.set_translation("Auto translation started...")
        self.update()
        self.auto_translate_once()

    def stop_auto_translation(self):
        self.translation_timer.stop()
        self.is_auto_translating = False

        self._request_id += 1

        self.overlay.set_translation("Auto translation stopped")
        self.update()

    def auto_translate_once(self):
        if not self.is_auto_translating or self.is_translating:
            return
        self.start_background_translation()

    def start_background_translation(self):
        if self.is_translating or self._closing:
            return

        self.is_translating = True
        self._request_id += 1
        request_id = self._request_id
        self._pending_capture_region = self.get_capture_region()
        self._overlay_was_visible = self.overlay.isVisible()

        QTimer.singleShot(
            0,
            lambda rid=request_id: self._capture_after_hidden(rid),
        )

    def _capture_after_hidden(self, request_id):
        if self._closing or request_id != self._request_id:
            self.is_translating = False
            return

        try:
            screenshot = self.engine.capture_screen(
                self._pending_capture_region
            )

        except Exception as error:
            self._restore_windows_after_capture()

            self.handle_translation_error(
                request_id,
                str(error),
            )

            self.is_translating = False
            return

        self._restore_windows_after_capture()

        try:
            original_text, translated_text = (
                self.engine.translate_screenshot(screenshot)
            )

            self.handle_translation_result(
                request_id,
                original_text,
                translated_text,
            )

        except Exception as error:
            self.handle_translation_error(
                request_id,
                str(error),
            )

        finally:
            self.is_translating = False

    def _restore_windows_after_capture(self):
        if self._closing:
            return

        self.update_overlay_position()

        if self.edit_mode:
            self.raise_()

        if self._overlay_was_visible:
            self.overlay.show()
            self.overlay.raise_()

    def _start_worker(self, request_id, screenshot):
        """
        暂时不使用 QThread 执行 EasyOCR。

        EasyOCR 底层依赖 PyTorch。在部分 Windows 环境中，
        从反复创建的 Qt 工作线程中运行 PyTorch，
        可能导致程序发生原生崩溃，而不是普通 Python 异常。
        """
        raise RuntimeError(
            "Translation worker is currently disabled."
        )

    def handle_translation_result(
            self,
            request_id,
            original_text,
            translated_text,
    ):
        if request_id != self._request_id or self._closing:
            return

        original_text = (original_text or "").strip()
        translated_text = (translated_text or "").strip()

        if not original_text:
            self.last_original_text = ""

            if not self.is_auto_translating:
                self.overlay.set_translation("No text detected")

            return

        if original_text == self.last_original_text:
            return

        self.last_original_text = original_text

        if translated_text:
            if translated_text != self.overlay.text():
                self.overlay.set_translation(translated_text)
        else:
            if not self.is_auto_translating:
                if self.overlay.text() != "":
                    self.overlay.set_translation("")

    def handle_translation_error(self, request_id, error_message):
        if request_id != self._request_id or self._closing:
            return

        print("Translation error:", error_message)
        self.overlay.set_translation(
            f"Translation failed:\n{error_message}"
        )

    # def cleanup_translation_thread(self):
    #     self.translation_worker = None
    #     self.translation_thread = None
    #     self.is_translating = False

    def is_in_resize_area(self, position):
        return (
            position.x() >= self.width() - self.resize_margin
            and position.y() >= self.height() - self.resize_margin
        )

    def set_edit_mode(self, enabled):
        self.edit_mode = bool(enabled)
        click_through = not self.edit_mode

        geometry = self.geometry()
        was_visible = self.isVisible()

        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            click_through,
        )
        self.setWindowFlag(
            Qt.WindowType.WindowTransparentForInput,
            click_through,
        )

        # Changing a top-level window flag can recreate the native window.
        # Restore its geometry and visibility afterwards.
        self.setGeometry(geometry)
        if was_visible:
            self.show()

        if self.edit_mode:
            self.raise_()

        self.update_overlay_position()
        self.update()
        self.overlay.set_edit_mode(enabled)

    def closeEvent(self, event):
        self._closing = True
        self._request_id += 1
        self.translation_timer.stop()
        self.overlay.close()
        self.closed.emit(self)
        super().closeEvent(event)
