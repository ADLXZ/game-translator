from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class RegionSelector(QWidget):
    region_selected = Signal(dict)

    def __init__(self):
        super().__init__()

        self.start_point = None
        self.end_point = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )
        self.setCursor(Qt.CursorShape.CrossCursor)

        screen = self.screen()
        screen_geometry = screen.geometry()

        self.setGeometry(screen_geometry)
        self.show()
        self.activateWindow()
        self.raise_()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.toggle_auto_translation()
            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = (
                    event.globalPosition().toPoint()
                    - self.frameGeometry().topLeft()
            )

            event.accept()

    def mouseMoveEvent(self, event):
        if self.start_point is not None:
            self.end_point = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if (
                event.button() == Qt.MouseButton.LeftButton
                and self.start_point is not None
        ):
            self.end_point = event.position().toPoint()

            selected_rect = QRect(
                self.start_point,
                self.end_point,
            ).normalized()

            top_left_global = self.mapToGlobal(
                selected_rect.topLeft()
            )

            scale_factor = self.devicePixelRatioF()

            region = {
                "left": round(
                    top_left_global.x() * scale_factor
                ),
                "top": round(
                    top_left_global.y() * scale_factor
                ),
                "width": round(
                    selected_rect.width() * scale_factor
                ),
                "height": round(
                    selected_rect.height() * scale_factor
                ),
            }

            print("Scale factor:", scale_factor)
            print("Selected region:", region)

            self.region_selected.emit(region)
            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.fillRect(
            self.rect(),
            QColor(0, 0, 0, 120),
        )

        if self.start_point is None or self.end_point is None:
            return

        selected_rect = QRect(
            self.start_point,
            self.end_point,
        ).normalized()

        painter.setCompositionMode(
            QPainter.CompositionMode.CompositionMode_Clear
        )
        painter.fillRect(selected_rect, Qt.GlobalColor.transparent)

        painter.setCompositionMode(
            QPainter.CompositionMode.CompositionMode_SourceOver
        )

        pen = QPen(Qt.GlobalColor.red)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(selected_rect)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()














