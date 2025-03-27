from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt
import sys

class Window_Menu(QMainWindow):
    def __init__(self,manager):
        super().__init__()
        self.setWindowTitle("MENU")
        self.setFixedSize(400, 600)
        self.manager = manager

        # 背景色
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#303030"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # 中央ウィジェットとレイアウト
        central_widget = QWidget()
        layout = QVBoxLayout()

        # ボタン1
        button1 = QPushButton("Button 1")
        button1.clicked.connect(lambda: self.bt(1))
        button1.setStyleSheet("""
            QPushButton {
                background-color: #FFB6C1;
                color: white;
                font-size: 18px;
                padding: 12px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #FF69B4;
            }
        """)

        # ボタン2
        button2 = QPushButton("Button 2")
        button2.clicked.connect(lambda: print(2))
        button2.setStyleSheet("""
            QPushButton {
                background-color: #87CEFA;
                color: white;
                font-size: 18px;
                padding: 12px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #00BFFF;
            }
        """)

        layout.addWidget(button1)
        layout.addWidget(button2)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
    def bt(self,number):
        print("aaaaa")
        self.manager.push_loop()
