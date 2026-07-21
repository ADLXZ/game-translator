from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
)

class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Game Translator")
        self.resize(600, 400)

        self.start_button = QPushButton("Start Translation")
        self.status_label = QLabel("Status: Ready")

        layout = QVBoxLayout()

        layout.addWidget(self.start_button)
        layout.addWidget(self.status_label)

        self.setLayout(layout)







