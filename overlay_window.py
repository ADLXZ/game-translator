from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import (
    QColor,
    QPainter,
)
import ctypes

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
            print("Warning: failed to exclude overlay from capture")

    except Exception as error:
        print("Overlay display affinity error:", error)



class OverlayWindow(QLabel):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.setStyleSheet(
            """
            QLabel {
                background-color: rgba(30, 30, 30, 180);
                color: white;
                border: 2px solid #55AAFF;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
            }
            """
        )
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("Translation")
        self.resize(260, 120)
        self.edit_mode = True

        self.setStyleSheet("""
        QLabel{
            color:white;
            font-size:22px;
            font-weight:bold;
            padding:10px;
            background:transparent;
        }
        """)

    def set_translation(self, text):

        if text == self.text():
            return

        self.setText(text)

        self.adjustSize()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self.edit_mode:
            painter.setBrush(
                QColor(20, 20, 20, 180)
            )

            painter.setPen(Qt.PenStyle.NoPen)

            painter.drawRoundedRect(
                self.rect(),
                12,
                12,
            )

        super().paintEvent(event)

    def set_edit_mode(self, enabled):
        self.edit_mode = enabled
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        exclude_window_from_capture(self)

    def exclude_from_screen_capture(self):
        """
        让 Windows 截图 API 忽略该窗口。


        Overlay 仍然正常显示在屏幕上，
        但截图中不会出现它，因此不需要 hide/show。
        """
        try:
            hwnd = int(self.winId())

            user32 = ctypes.windll.user32

            user32.SetWindowDisplayAffinity.argtypes = [
                ctypes.c_void_p,
                ctypes.c_uint,
            ]
            user32.SetWindowDisplayAffinity.restype = ctypes.c_bool

            # Windows 10 2004 及以上：
            # 窗口在截图中完全不可见。
            WDA_EXCLUDEFROMCAPTURE = 0x00000011

            success = user32.SetWindowDisplayAffinity(
                ctypes.c_void_p(hwnd),
                WDA_EXCLUDEFROMCAPTURE,
            )

            if not success:
                # 较旧 Windows 的兼容模式。
                WDA_MONITOR = 0x00000001

                user32.SetWindowDisplayAffinity(
                    ctypes.c_void_p(hwnd),
                    WDA_MONITOR,
                )


        except Exception as error:
            print("Could not exclude overlay from capture:", error)










