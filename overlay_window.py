import ctypes
import re

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QTextOption
from PySide6.QtWidgets import (
    QWidget,
    QTextEdit,
    QSizePolicy,
    QAbstractItemView,
)


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
            user32.SetWindowDisplayAffinity(
                ctypes.c_void_p(hwnd),
                WDA_MONITOR,
            )

    except Exception as error:
        print("Could not exclude overlay from capture:", error)


class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.edit_mode = True
        self.translation_text = "Translation"

        # 字体大小范围
        self.minimum_font_size = 8
        self.maximum_font_size = 28
        self.current_font_size = 16

        # 背景透明度
        self.background_opacity = 180

        # 外层安全边距
        # 边距不要设置太大，否则会浪费右侧空间
        self.horizontal_padding = 8
        self.vertical_padding = 8

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

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.setMinimumSize(1, 1)

        # 创建专门负责文字排版的 QTextEdit
        self.text_edit = QTextEdit(self)

        self.text_edit.setReadOnly(True)
        self.text_edit.setUndoRedoEnabled(False)

        # 不允许文字被点击、选择或编辑
        self.text_edit.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
        )

        self.text_edit.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )

        self.text_edit.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True,
        )

        # 根据控件宽度自动换行
        self.text_edit.setLineWrapMode(
            QTextEdit.LineWrapMode.WidgetWidth
        )

        # 中文、英文都可以在需要时从字符中间换行
        self.text_edit.setWordWrapMode(
            QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere
        )

        # 禁止显示滚动条
        self.text_edit.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.text_edit.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # 清除 QTextEdit 默认边框和内部空白
        self.text_edit.setFrameStyle(
            QAbstractItemView.Shape.NoFrame
        )

        self.text_edit.setContentsMargins(0, 0, 0, 0)

        # QTextDocument 默认也有边距，需要清除
        self.text_edit.document().setDocumentMargin(1)

        self.text_edit.setStyleSheet(
            """
            QTextEdit {
                background: transparent;
                background-color: transparent;
                color: white;
                border: none;
                padding: 0px;
                margin: 0px;
                selection-background-color: transparent;
            }

            QTextEdit QScrollBar {
                width: 0px;
                height: 0px;
            }
            """
        )

        self.text_edit.setPlainText(
            self.translation_text
        )

        self.resize(500, 160)
        self.update_text_edit_geometry()

        # 等界面完成初始化后再计算字号
        QTimer.singleShot(
            0,
            self.update_font_size,
        )

    def text(self):
        """
        保留原先 QLabel.text() 风格的接口。

        项目中其他位置即使调用 overlay.text()，
        也不需要修改。
        """
        return self.translation_text

    def normalize_text(self, text):
        """
        清理 OCR 或翻译接口产生的不必要换行。

        单个换行通常只是 OCR 对原图的分行，
        会转换为空格，让文字自动使用整个翻译框宽度。

        两个及以上连续换行视为真正的段落。
        """
        if text is None:
            return ""

        text = str(text)

        # 统一换行符
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        # 去除每一行两端的空白
        lines = [
            line.strip()
            for line in text.split("\n")
        ]

        text = "\n".join(lines)

        # 临时保护真正的段落换行
        paragraph_marker = "\uE000"

        text = re.sub(
            r"\n\s*\n+",
            paragraph_marker,
            text,
        )

        # 普通单换行转换为空格
        text = text.replace("\n", " ")

        # 恢复段落
        text = text.replace(
            paragraph_marker,
            "\n\n",
        )

        # 合并多余空格
        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        # 清除段落周围的多余空格
        text = re.sub(
            r" *\n *",
            "\n",
            text,
        )

        return text.strip()

    def set_translation(self, text):
        """设置新的翻译文字。"""
        normalized_text = self.normalize_text(text)

        if normalized_text == self.translation_text:
            return

        self.translation_text = normalized_text

        self.text_edit.setPlainText(
            self.translation_text
        )

        # 文字改变后重新计算字号
        self.update_font_size()
        self.update()

    def create_font(self, pixel_size):
        """创建指定大小的中文字体。"""
        font = QFont()

        font.setFamilies(
            [
                "Microsoft YaHei UI",
                "Microsoft YaHei",
                "SimHei",
                "Arial",
            ]
        )

        font.setPixelSize(pixel_size)

        # 普通或中等粗细最不容易发生字形裁切
        font.setWeight(
            QFont.Weight.Normal
        )

        return font

    def update_text_edit_geometry(self):
        """
        让文字控件填满翻译窗口。

        只保留很小的安全边距，避免右侧空间被浪费。
        """
        text_x = self.horizontal_padding
        text_y = self.vertical_padding

        text_width = max(
            1,
            self.width()
            - self.horizontal_padding * 2,
        )

        text_height = max(
            1,
            self.height()
            - self.vertical_padding * 2,
        )

        self.text_edit.setGeometry(
            text_x,
            text_y,
            text_width,
            text_height,
        )

    def document_fits(self, font_size):
        """
        判断指定字号下的全部文字是否能够完整显示。

        同时检查宽度与高度，并预留安全空间，
        避免最后一行被窗口底部裁掉。
        """
        font = self.create_font(font_size)

        self.text_edit.setFont(font)
        self.text_edit.document().setDefaultFont(font)

        viewport_width = max(
            1,
            self.text_edit.viewport().width() - 2,
        )

        viewport_height = max(
            1,
            self.text_edit.viewport().height() - 2,
        )

        document = self.text_edit.document()

        # 明确告诉文档真实可用宽度
        document.setTextWidth(viewport_width)

        document_height = (
            document.documentLayout()
            .documentSize()
            .height()
        )

        # 额外预留 4 像素，避免字体下沿被裁切
        return document_height <= viewport_height - 4

    def update_font_size(self):
        """
        从最大字号开始寻找能够完整放下文字的字号。
        """
        if (
            self.width() <= 1
            or self.height() <= 1
            or self.text_edit.width() <= 1
            or self.text_edit.height() <= 1
        ):
            return

        chosen_size = self.minimum_font_size

        for font_size in range(
            self.maximum_font_size,
            self.minimum_font_size - 1,
            -1,
        ):
            if self.document_fits(font_size):
                chosen_size = font_size
                break

        self.current_font_size = chosen_size

        final_font = self.create_font(
            chosen_size
        )

        self.text_edit.setFont(final_font)
        self.text_edit.document().setDefaultFont(
            final_font
        )

        viewport_width = max(
            1,
            self.text_edit.viewport().width() - 2,
        )

        self.text_edit.document().setTextWidth(
            viewport_width
        )

        # 永远保持在文字顶部
        scroll_bar = (
            self.text_edit.verticalScrollBar()
        )

        scroll_bar.setValue(
            scroll_bar.minimum()
        )

        self.text_edit.viewport().update()

    def paintEvent(self, event):
        """绘制翻译框的半透明背景。"""
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        if not self.edit_mode:
            painter.setPen(
                Qt.PenStyle.NoPen
            )

            painter.setBrush(
                QColor(
                    20,
                    20,
                    20,
                    self.background_opacity,
                )
            )

            painter.drawRect(
                self.rect()
            )

        painter.end()

    def resizeEvent(self, event):
        """翻译框大小改变时重新排版。"""
        super().resizeEvent(event)

        self.update_text_edit_geometry()

        # 等 QTextEdit 的 viewport 尺寸更新完成后计算字号
        QTimer.singleShot(
            0,
            self.update_font_size,
        )

        self.update()

    def set_edit_mode(self, enabled):
        """切换编辑模式和翻译显示模式。"""
        self.edit_mode = bool(enabled)

        self.update_font_size()
        self.update()

    def showEvent(self, event):
        """窗口显示后排除截图并重新排版。"""
        super().showEvent(event)

        exclude_window_from_capture(self)

        QTimer.singleShot(
            0,
            self.update_font_size,
        )
