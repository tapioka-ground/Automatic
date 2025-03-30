import threading
import time
import subprocess
import re

class DfsAI():
    def __init__(self, android_class, single_manager):
        self.android = android_class
        self.manager = single_manager
        self.running = False  # 重複起動防止用フラグ

    def dfs_start(self):
        if self.running:
            print("⚠️ DFSはすでに実行中です")
            return

        self.running = True
        thread = threading.Thread(target=self._dfs_loop)
        thread.start()

    def _dfs_loop(self):
        print("🔍 DFS探索スレッド開始")
        visited_failed_hashes = set()  # ← 追加：失敗したハッシュを記録して無限ループ回避

        while self.running:
            time.sleep(0.5)
            found = False
            max_depth = self.android.max_depth

            # 通常の深いところから探索
            for depth in reversed(range(max_depth + 1)):
                hash_list = [h for h, d in self.android.depth_map.items() if d == depth]
                for hash_val in hash_list:
                    actions = self.android.transition_log.get(hash_val, [])
                    for i, action in enumerate(actions):#---------------------------------------------上下切り替え
                    #for i in reversed(range(len(actions))):
                        #action = actions[i]#----------------------
                        if not action.get("done"):
                            if self.android.current_hash != hash_val:
                                print(f"↩️ ハッシュ移動: {self.android.current_hash[:4]} → {hash_val[:4]}")
                                path = self.reachable_path_to(hash_val)
                                if not path:
                                    print("❌ ハッシュへのジャンプに失敗 (current_hash からのルートなし)")
                                    visited_failed_hashes.add(hash_val)  # ← 追加
                                    continue

                                for from_hash, index in path:
                                    print(f"➡️ {from_hash[:4]} → index[{index}] を実行")
                                    self.manager.loop_effect(index)
                                    time.sleep(1.0)

                                    if self.android.current_hash == hash_val:
                                        break

                            if self.android.current_hash == hash_val:
                                print(f"➡️ 未実行アクションを実行: index={i}, hash={hash_val[:4]}")
                                self.manager.loop_effect(i)
                                found = True
                                break
                    if found:
                        break
                if found:
                    break

            if not found:
                # 全探索失敗 → デプス+1の未探索に変更して探す
                print("🌀 全てのルート探索失敗 → デプスを浅くして再探索")
                for offset in range(1, max_depth + 1):
                    depth = max_depth - offset
                    hash_list = [h for h, d in self.android.depth_map.items() if d == depth and h not in visited_failed_hashes]
                    for hash_val in hash_list:
                        actions = self.android.transition_log.get(hash_val, [])
                        for i, action in enumerate(actions):
                            if not action.get("done"):
                                print(f"➡️ 例外探索: index={i}, hash={hash_val[:4]}（デプス {depth}）")
                                self.manager.loop_effect(i)
                                found = True
                                break
                        if found:
                            break
                    if found:
                        break

            if not found:
                print("✅ 全てのアクションを探索済み。DFS終了。")
                self.running = False
                break

            time.sleep(1.0)

    def reachable_path_to(self, target_hash):
        visited = set()

        def dfs(current, path):
            if current == target_hash:
                return path
            visited.add(current)

            actions = self.android.transition_log.get(current, [])
            for i, action in enumerate(actions):
                to = action.get("to")

                if isinstance(to, str) and to not in visited:
                    result = dfs(to, path + [(current, i)])
                    if result:
                        return result

                elif isinstance(to, dict):
                    for val, next_hash in to.items():
                        if next_hash not in visited:
                            result = dfs(next_hash, path + [(current, i)])
                            if result:
                                return result
            return None

        return dfs(self.android.current_hash, [])

    def back_index(self, mode, index, inputvalue):
        actions = self.android.transition_log[self.android.current_hash]
        action = actions[index]

        if mode == "input":
            print("🔙 バックトラッキング：inputモード")

            bounds = action["bounds"]
            x1, y1, x2, y2 = map(int, re.findall(r'\\d+', bounds))
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            print(f"⌨️ 入力復元: '{inputvalue}' at bounds={bounds}")
            subprocess.run(["adb", "shell", "input", "tap", str(center_x), str(center_y)])
            time.sleep(0.3)
            for _ in range(10):
                subprocess.run(["adb", "shell", "input", "keyevent", "67"])
                time.sleep(0.05)
            subprocess.run(["adb", "shell", "input", "text", inputvalue])
            time.sleep(0.2)
            subprocess.run(["adb", "shell", "input", "keyevent", "66"])
            time.sleep(1.5)

            xml_string = self.android.get_xml_tree()
            new_hash = self.android.hash_screen(xml_string)
            self.android.record_ui_state(xml_string)
            print(f"✅ バックトラッキングによる入力完了 → ハッシュ: {new_hash}")

        else:
            print("🔙 バックトラッキング：tapモード")
            self.manager.loop_effect(index)
