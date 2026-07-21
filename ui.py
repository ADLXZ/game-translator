from PySide6.QtWidgets import QWidget


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Game Translator")
        self.resize(600, 400)


