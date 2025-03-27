from PySide6.QtWidgets import  QMainWindow
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt
import sys

class Window_Menu(QMainWindow):
    def __init__(self,):
        super().__init__()
        self.setWindowTitle("MENU")
        self.setFixedSize(400,600)

        background_color = QPalette()
        background_color.setColor(QPalette.Window, QColor("#303030"))
        self.setPalette(background_color)
        self.setAutoFillBackground(True)

        
