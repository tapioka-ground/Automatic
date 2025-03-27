import sys
from PySide6.QtWidgets import QApplication
from src.single_manager import App_Manager

print("[INFO] UIを起動します。")
app = QApplication(sys.argv)
main_manager = App_Manager()
sys.exit(app.exec())
