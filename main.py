import sys

from PySide6.QtWidgets import QApplication, QWidget


app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("Game Translator")
window.resize(600, 400)

window.show()

app.exec()


