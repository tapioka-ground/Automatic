import subprocess
import time
from pathlib import Path
from lxml import etree
import re

class ADBManager:
    def __init__(self):
        self.xml_path = Path("view.xml")
        self.input_history = {}  # {bounds_str: [入れた数値リスト]}
        self.numbers_to_try = ["0", "1", "99"]  # 任意の入力候補


    def get_xml_tree(self):
        subprocess.run(["adb", "shell", "uiautomator", "dump", "/sdcard/view.xml"], check=True)
        subprocess.run(["adb", "pull", "/sdcard/view.xml", str(self.xml_path)], check=True)

        with open(self.xml_path, "r", encoding="utf-8") as f:
            return f.read()

    def parse_bounds(self, bounds_str):
        # [x1,y1][x2,y2] を整数のリストに
        nums = list(map(int, re.findall(r"\d+", bounds_str)))
        x = (nums[0] + nums[2]) // 2
        y = (nums[1] + nums[3]) // 2
        return x, y

    def get_all_bounds(self):
        xml_string = self.get_xml_tree()
        tree = etree.fromstring(xml_string.encode('utf-8'))

        bounds_list = []
        for elem in tree.xpath("//node"):
            bounds = elem.attrib.get("bounds")
            class_name = elem.attrib.get("class")
            if bounds and class_name != "android.widget.EditText":
                bounds_list.append(bounds)
        return bounds_list

    def tap_by_bounds(self, bounds):
        x, y = self.parse_bounds(bounds)
        subprocess.run(["adb", "shell", "input", "tap", str(x), str(y)])

    def detect_bottom_sheet(self):
        # BottomSheetが定義されてれば class名で判定可
        xml_string = self.get_xml_tree()
        return "BottomSheet" in xml_string or "keyboard" in xml_string.lower()

    def input_number_sequence(self, bounds):
        if bounds not in self.input_history:
            self.input_history[bounds] = []

        for num in self.numbers_to_try:
            if num not in self.input_history[bounds]:
                subprocess.run(["adb", "shell", "input", "text", num])
                time.sleep(0.3)
                subprocess.run(["adb", "shell", "input", "keyevent", "66"])  # ENTER
                print(f"[INPUT] {bounds} に {num} を入力")
                self.input_history[bounds].append(num)
                break

    def run_test_loop(self):
        visited = set()

        while True:
            bounds_list = self.get_all_bounds()
            for bounds in bounds_list:
                if bounds in visited:
                    continue

                print(f"[TAP] タップする: {bounds}")
                self.tap_by_bounds(bounds)
                visited.add(bounds)
                time.sleep(1.0)

                if self.detect_bottom_sheet():
                    print("[DETECTED] BottomSheet detected!")
                    self.input_number_sequence(bounds)
                    time.sleep(1.0)

    def loop_start(self,):
        adb = ADBManager()
        adb.run_test_loop()
