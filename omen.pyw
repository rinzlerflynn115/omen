from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
import sys

from omen_gui import MainWindow

#main script functions
app = QApplication(sys.argv)
form = MainWindow()
form.setWindowFlags(Qt.Window)
form.show()
app.exec_()