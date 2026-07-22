from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class TranslationRegion(QWidget):

    def __init__(self):
        super().__init__()

        self.drag_position = None

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

        self.show()

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
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = None
            event.accept()


