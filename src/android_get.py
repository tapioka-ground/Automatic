import subprocess
import time
from pathlib import Path
from lxml import etree
import re
import hashlib
from collections import defaultdict
import os
import xml.etree.ElementTree as ET

class ADBManager:

    def __init__(self):
        self.xml_path = Path("view.xml")
        self.input_history = {}  # {bounds_str: [入れた数値リスト]}
        self.numbers_to_try = ["-10","-1", "0","1", "10"]  # 任意の入力候補
        self.xml_hash = ""
        self.visited_hashes = set()
        self.action_log = {}
        self.depth_map = {}  # {hash: depth}
        self.screenshot_map = {}  # {hash: "screenshots/xxxx.png"}



        self.transition_log = defaultdict(list)  # {hash: [action_dicts]}
        self.stack = []  # 探索のための履歴スタック
        self.loop_counter = defaultdict(int)
        self.start_hash = None
        self.current_hash = ""
        self.current_depth = 0
        self.max_depth = 0

    def get_xml_tree(self):#現在の画面をプルするADBで
        subprocess.run(["adb", "shell", "uiautomator", "dump"], capture_output=True, text=True)
        subprocess.run(["adb", "pull", "/sdcard/window_dump.xml", "./window_dump.xml"], capture_output=True)
        with open("window_dump.xml", "r", encoding="utf-8") as f:
            return f.read()

    def hash_screen(self, xml_string):
        tree = etree.fromstring(xml_string.encode("utf-8"))
        for elem in tree.xpath("//node"):
            if "text" in elem.attrib:
                elem.attrib["text"] = ""
        cleaned_xml = etree.tostring(tree, encoding="utf-8", method="xml").decode("utf-8")
        return hashlib.sha256(cleaned_xml.encode("utf-8")).hexdigest()


    def reject_xml_tree(self, xml_string):
        tree = etree.fromstring(xml_string.encode('utf-8'))
        selectable_nodes = []

        for elem in tree.xpath("//node"):
            class_name = elem.attrib.get("class", "")
            clickable = elem.attrib.get("clickable", "false")
            enabled = elem.attrib.get("enabled", "false")
            text = elem.attrib.get("text", "")
            content_desc = elem.attrib.get("content-desc", "")
            resource_id = elem.attrib.get("resource-id", "")

            # 🚫 無視フィルター
            if (class_name == "android.widget.EditText" and "検索CDまたは" in text):
                #print(f"🚫 無視対象: class={class_name}, text='{text}'")
                continue

            #print(f"[解析] class={class_name}, clickable={clickable}, enabled={enabled}, text='{text}', desc='{content_desc}'")

            # ✅ 入力欄
            if "edittext" in class_name.lower():
                selectable_nodes.append(("input", elem))
                #print("→ ✅ 入力欄として追加")

            # ✅ ViewGroup タップ
            elif class_name == "android.view.ViewGroup" and clickable == "true":
                selectable_nodes.append(("tap", elem))
                #print("→ ✅ ViewGroup (タップ可能) として追加")

            # ✅ 一般タップ可能要素
            elif class_name not in ["android.widget.LinearLayout", "android.widget.FrameLayout"]:
                if clickable == "true" and enabled == "true" and (text.strip() or content_desc.strip()):
                    selectable_nodes.append(("tap", elem))
                    #print("→ ✅ 一般タップ要素として追加")

            # ✅ テキストオプション
            if class_name == "android.widget.TextView" and resource_id == "android:id/text1":
                selectable_nodes.append(("text_option", elem))
                #print("→ ✅ テキストオプションとして追加")

        print(f"👉 最終的に抽出されたUI要素数: {len(selectable_nodes)}個")

        def bounds_key(e):
            bounds = e[1].attrib.get("bounds", "")
            nums = list(map(int, re.findall(r"\d+", bounds)))
            return (nums[1], nums[0]) if len(nums) == 4 else (9999, 9999)

        selectable_nodes.sort(key=bounds_key)
        return selectable_nodes





    def record_ui_state(self, xml_string): #今のやつをレコードする！
        self.current_hash = self.hash_screen(xml_string)#現在地設定。
        if self.current_hash in self.transition_log:

            self.current_depth = self.depth_map[self.current_hash]
            print(f"今の深さ{self.current_depth}")
            return

        selectable_nodes = self.reject_xml_tree(xml_string)#新しいハッシュなら初めて要素を保存する
        self.current_depth += 1
        self.depth_map[self.current_hash] = self.current_depth
        if self.max_depth < self.current_depth:#これで最大階層更新ここだけ限定
            self.max_depth = self.current_depth

        print(f"今の深さ{self.current_depth}")

        screenshot_dir = Path("screenshots")#新しいハッシュならスクショも紐付けるよ
        screenshot_dir.mkdir(exist_ok=True)
        screenshot_path = screenshot_dir / f"{self.current_hash}.png"

        subprocess.run(["adb", "shell", "screencap", "-p", "/sdcard/tmp_screen.png"])
        subprocess.run(["adb", "pull", "/sdcard/tmp_screen.png", str(screenshot_path)])

        # スクショ登録
        self.screenshot_map[self.current_hash] = screenshot_path.as_posix()
        self.transition_log[self.current_hash] = []



        for i, (mode, elem) in enumerate(selectable_nodes):
            bounds = elem.attrib.get("bounds", "")
            label = elem.attrib.get("text", "") or elem.attrib.get("content-desc", "") or ""
            self.transition_log[self.current_hash].append({
                "index": i,
                "mode": mode,
                "label": label,
                "bounds": bounds,
                "to": None,
                "done": False,
            })







    def tap_index(self, input_index):
        if self.current_hash not in self.transition_log:
            print("⚠️ current_hash が transition_log に存在しません")
            return

        actions = self.transition_log[self.current_hash]
        if input_index < 0 or input_index >= len(actions):
            print("⚠️ 無効な input_index")
            return

        action = actions[input_index]
        if action["mode"] == "input":
            print("インプット")
            self.input_index(action)
            return

        if action["mode"] not in ["tap", "text_option"]:
            print(f"⚠️ mode が 'tap' ではないため無視: {action['mode']}")
            return

        bounds = action["bounds"]
        x1, y1, x2, y2 = map(int, re.findall(r'\d+', bounds))
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        print(f"📲 タップ中: index={input_index}, label='{action['label']}', bounds={bounds}")
        subprocess.run(["adb", "shell", "input", "tap", str(center_x), str(center_y)])
        time.sleep(2.0)  # 画面遷移を待つ
        # 新しい画面のハッシュを取得
        xml_string = self.get_xml_tree()
        new_hash = self.hash_screen(xml_string)
        # 新しい画面の UI を記録（必要なら）

        # アクションに遷移先を記録
        action["to"] = new_hash
        action["done"] = True
        self.record_ui_state(xml_string)

        print(f"✅ アクション実行完了: 遷移先ハッシュ = {new_hash}")





    def input_index(self, action):
        if action["mode"] != "input":
            print(f"⚠️ mode が 'input' ではありません: {action['mode']}")
            return

        bounds = action["bounds"]
        x1, y1, x2, y2 = map(int, re.findall(r'\d+', bounds))
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        if "tried_values" not in action:
            action["tried_values"] = []
        if "to" not in action or action["to"] is None:
            action["to"] = {}


        # ✅ 未試行の入力を1つだけ選ぶ
        next_input = None
        for val in self.numbers_to_try:
            if val not in action["tried_values"]:
                next_input = val
                break

        if not next_input:
            action["done"] = True
            print("✅ 全ての入力値を試行完了。done = True")
            return

        print(f"⌨️ 入力中: '{next_input}' at bounds={bounds}")
        subprocess.run(["adb", "shell", "input", "tap", str(center_x), str(center_y)])
        time.sleep(0.3)

        subprocess.run(["adb", "shell", "input", "keyevent", "KEYCODE_MOVE_END"])  # Endへ
        time.sleep(0.1)
        subprocess.run(["adb", "shell", "input", "keyevent", "KEYCODE_SHIFT_LEFT"])  # Shift押す
        time.sleep(0.1)
        subprocess.run(["adb", "shell", "input", "keyevent", "KEYCODE_MOVE_HOME"])  # Homeへ（Shift押しながらで全選択）
        time.sleep(0.1)
        subprocess.run(["adb", "shell", "input", "keyevent", "KEYCODE_DEL"])  # 削除
        time.sleep(0.3)

        subprocess.run(["adb", "shell", "input", "text", next_input])
        time.sleep(0.2)
        subprocess.run(["adb", "shell", "input", "keyevent", "66"])  # Enter
        time.sleep(1.5)

        xml_string = self.get_xml_tree()
        new_hash = self.hash_screen(xml_string)


        action["to"][next_input] = new_hash
        action["tried_values"].append(next_input)
        print(f"✅ 入力 '{next_input}' による遷移先: {new_hash}")
        self.record_ui_state(xml_string)

        # 次回呼ばれたときにまた次の値を試す仕組みに
        if set(action["tried_values"]) >= set(self.numbers_to_try):
            action["done"] = True
            print("✅ 全ての入力値を試行完了。done = True")




























