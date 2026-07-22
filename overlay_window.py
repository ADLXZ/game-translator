import ctypes

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QLabel, QSizePolicy


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

        # 字体大小范围
        self.minimum_font_size = 16
        self.maximum_font_size = 26

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

        # QLabel 本身透明，背景由 paintEvent 绘制
        self.setStyleSheet(
            """
            QLabel {
                background-color: transparent;
                color: white;
                border: none;
            }
            """
        )

        # 自动换行
        self.setWordWrap(True)

        # 文字从左向右排列，垂直方向居中
        self.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        # 让 QLabel 使用整个窗口空间
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.setMinimumWidth(1)

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
        """更新翻译文本。"""
        text = text or ""

        if text == self.text():
            return

        self.setText(text)
        self.update_font_size()
        self.update()

    def update_font_size(self):
        """
        根据翻译框高度调整字体大小。

        不再使用根据文本内容不断放大字体的算法，
        避免中文文字一两个字一行。
        """
        available_height = max(
            1,
            self.height() - self.text_padding * 2,
        )

        # 翻译框越高，字体可以稍微变大
        font_size = available_height // 5

        # 限制字体范围，防止字体过大
        font_size = max(
            self.minimum_font_size,
            min(
                self.maximum_font_size,
                font_size,
            ),
        )

        font = QFont(self.font())
        font.setPixelSize(font_size)
        font.setBold(True)

        self.setFont(font)

    def paintEvent(self, event):
        """绘制半透明黑色背景和文字。"""
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

            painter.drawRect(self.rect())

        # 让 QLabel 正常绘制文字
        super().paintEvent(event)

    def resizeEvent(self, event):
        """翻译框尺寸改变时重新调整字体。"""
        super().resizeEvent(event)
        self.update_font_size()

    def set_edit_mode(self, enabled):
        """切换编辑模式和使用模式。"""
        self.edit_mode = bool(enabled)
        self.update_font_size()
        self.update()

    def showEvent(self, event):
        """窗口显示后设置为不被截图捕获。"""
        super().showEvent(event)
        exclude_window_from_capture(self)
