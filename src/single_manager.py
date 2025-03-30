import sys
from src.main_menu import Window_Menu
from src.android_get import ADBManager
from src.graph import GraphWindow
from src.dfs_ai import DfsAI

class App_Manager():
    def __init__(self):
        self.window = Window_Menu(self)
        self.window.show()
        self.android = ADBManager()
        self.graph = GraphWindow(self.android)
        self.graph.show()
        self.dfsai = DfsAI(self.android,self)

    def create_entry_point(self):
        xml = self.android.get_xml_tree()
        self.android.record_ui_state(xml)
        self.graph.update_graph()

        # --- 初期画面のアクション一覧を表示 ---
        actions = self.android.transition_log[self.android.current_hash]
        print("\n=== 初期画面のUI要素一覧 ===")
        for i, action in enumerate(actions):
            print(f"[{i}] {action['mode']}: {action['label']}")

        # --- 押さないインデックスを選択させる ---
        try:
            skip_input = input("🚫 押さない要素の index をカンマ区切りで入力（例: 1,3）→ ")
            skip_indices = [int(idx.strip()) for idx in skip_input.split(",") if idx.strip().isdigit()]
        except Exception as e:
            print(f"⚠️ 入力エラー: {e}")
            skip_indices = []

        # --- 該当インデックスの done を True にする ---
        for i in skip_indices:
            if 0 <= i < len(actions):
                actions[i]["done"] = True
                print(f"✅ index={i} を探索済みに設定")

        print("🎬 初期設定完了。探索準備OK！")


    def dfs_loop_start(self,):
        self.dfsai.dfs_start()




    def loop_effect(self,index):#Dfsから受け取る
        xml = self.android.get_xml_tree()
        self.android.record_ui_state(xml)

        print("\n=== 実行可能なアクション一覧 ===")
        for i, action in enumerate(self.android.transition_log[self.android.current_hash]):
            status = "✅" if action.get("done") else "🟡"
            print(f"[{i}] {status} {action['mode']}: {action['label']}")

        try:
            self.android.tap_index(index)
            self.graph.update_graph()

        except Exception as e:
            print(f"⚠️ 入力エラー: {e}")







    def loot_test(self):#これテストような
        self.test_explore()

    def test_explore(self):
        xml = self.android.get_xml_tree()
        self.android.record_ui_state(xml)

        print("\n=== 実行可能なアクション一覧 ===")
        for i, action in enumerate(self.android.transition_log[self.android.current_hash]):
            status = "✅" if action.get("done") else "🟡"
            print(f"[{i}] {status} {action['mode']}: {action['label']}")

        try:
            index = int(input("➡ どのUI要素を試す？ indexを入力: "))
            self.android.tap_index(index)
            self.graph.update_graph()

        except Exception as e:
            print(f"⚠️ 入力エラー: {e}")
