import sys
from src.main_menu import Window_Menu
from src.android_get import ADBManager

class App_Manager():
    def __init__(self,):
        self.window = Window_Menu(self,)
        self.window.show()

        self.android = ADBManager()

    def push_loop(self,):
        print("ループ開始")
        self.android.loop_start()

    def save_start(self,):
        print("スタート保存")


