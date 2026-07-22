import ctypes

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QLabel


WDA_EXCLUDEFROMCAPTURE = 0x00000011
WDA_MONITOR = 0x00000001


def exclude_window_from_capture(widget):
    """让 Windows 截图和录屏忽略这个窗口。"""
    try:
        hwnd = int(widget.winId())
        user32 = ctypes.windll.user32

        user32.SetWindowDisplayAffinity.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
        ]
        user32.SetWindowDisplayAffinity.restype = ctypes.c_bool

        success = user32.SetWindowDisplayAffinity(
            ctypes.c_void_p(hwnd),
            WDA_EXCLUDEFROMCAPTURE,
        )

        if not success:
            # 兼容较旧的 Windows 版本
            user32.SetWindowDisplayAffinity(
                ctypes.c_void_p(hwnd),
                WDA_MONITOR,
            )

    except Exception as error:
        print("Could not exclude overlay from capture:", error)


class OverlayWindow(QLabel):
    def __init__(self):
        super().__init__()

        self.edit_mode = True

        # 字体自适应范围
        self.minimum_font_size = 12
        self.maximum_font_size = 48

        # 黑色半透明背景透明度
        self.background_opacity = 180

        # 文字四周留白
        self.text_padding = 10

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_ShowWithoutActivating,
            True,
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True,
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True,
        )

        # 背景由 paintEvent 绘制，所以 QLabel 自身保持透明
        self.setStyleSheet(
            """
            QLabel {
                background-color: transparent;
                color: white;
                border: none;
            }
            """
        )

        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setContentsMargins(
            self.text_padding,
            self.text_padding,
            self.text_padding,
            self.text_padding,
        )

        self.setText("Translation")
        self.resize(260, 120)

        self.update_font_size()

    def set_translation(self, text):
        text = text or ""

        if text == self.text():
            return

        self.setText(text)

        # 不再使用 adjustSize()
        # Overlay 的大小始终由 TranslationRegion 决定
        self.update_font_size()
        self.update()

    def update_font_size(self):
        """
        找出当前框中能够完整容纳译文的最大字号。
        """
        text = self.text().strip()

        if not text:
            return

        available_width = max(
            1,
            self.width() - self.text_padding * 2,
        )
        available_height = max(
            1,
            self.height() - self.text_padding * 2,
        )

        text_rect = QRect(
            0,
            0,
            available_width,
            available_height,
        )

        flags = (
            Qt.AlignmentFlag.AlignCenter
            | Qt.TextFlag.TextWordWrap
        )

        low = self.minimum_font_size
        high = self.maximum_font_size
        best_size = self.minimum_font_size

        while low <= high:
            test_size = (low + high) // 2

            font = QFont(self.font())
            font.setPixelSize(test_size)
            font.setBold(True)

            metrics = QFontMetrics(font)

            required_rect = metrics.boundingRect(
                text_rect,
                flags,
                text,
            )

            fits_width = (
                required_rect.width() <= available_width
            )
            fits_height = (
                required_rect.height() <= available_height
            )

            if fits_width and fits_height:
                best_size = test_size
                low = test_size + 1
            else:
                high = test_size - 1

        final_font = QFont(self.font())
        final_font.setPixelSize(best_size)
        final_font.setBold(True)

        self.setFont(final_font)

    def paintEvent(self, event):
        painter = QPainter(self)

        # 使用模式才显示黑色半透明背景
        if not self.edit_mode:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(
                QColor(
                    20,
                    20,
                    20,
                    self.background_opacity,
                )
            )

            # 使用普通矩形，不使用圆角
            painter.drawRect(self.rect())

        super().paintEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        # 选框尺寸变化时，重新计算字体大小
        self.update_font_size()

    def set_edit_mode(self, enabled):
        self.edit_mode = bool(enabled)
        self.update_font_size()
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        exclude_window_from_capture(self)


