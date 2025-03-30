from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel,QHBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import networkx as nx
from PySide6.QtGui import QPixmap
from collections import defaultdict

class GraphWindow(QMainWindow):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.setWindowTitle("探索グラフ")
        self.setGeometry(100, 100, 1200, 800)  # 横幅ちょい拡張

        self.canvas = FigureCanvas(plt.Figure())

        # スクショラベル（右側に配置）
        self.screenshot_label = QLabel()
        self.screenshot_label.setFixedSize(300, 600)  # 横300・縦600

        # --- レイアウト構築（グラフ左・スクショ右） ---
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.canvas)
        h_layout.addWidget(self.screenshot_label)

        container = QWidget()
        container.setLayout(h_layout)
        self.setCentralWidget(container)

        self.update_graph()

    def update_graph(self):
        G = nx.MultiDiGraph()

        # --- グラフ構築 ---
        for hash_key, actions in self.manager.transition_log.items():
            G.add_node(hash_key)
            for action in actions:
                if action["to"]:
                    if isinstance(action["to"], dict):
                        for val, dest_hash in action["to"].items():
                            G.add_edge(hash_key, dest_hash, label=f"input:{val}")
                    else:
                        G.add_edge(hash_key, action["to"], label=action["mode"])

        fig = self.canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        # --- デプスごとのグルーピング ---
        depth_groups = defaultdict(list)
        for node in G.nodes:
            depth = self.manager.depth_map.get(node, 0)
            depth_groups[depth].append(node)

        # --- ノード座標の配置 ---
        pos = {}
        for depth, nodes_at_depth in sorted(depth_groups.items()):
            for i, node in enumerate(nodes_at_depth):
                pos[node] = (i, -depth)  # Y軸は深さ、X軸は横並び

        # --- ラベル＆ノード色 ---
        labels = {node: f"{node[:4]}" for node in G.nodes}
        node_colors = ["red" if node == self.manager.current_hash else "skyblue" for node in G.nodes]

        # --- ノード・エッジ描画 ---
        nx.draw(G, pos, with_labels=True, labels=labels,
                node_color=node_colors, ax=ax,
                node_size=1500, font_size=8)

        edge_labels = {(u, v): d["label"] for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax, font_size=7)

        # --- 深さラベル（左端に縦整列） ---
                # --- 深さラベル（左端に縦整列） ---
        max_depth = max(depth_groups.keys(), default=0)
        for depth in range(max_depth + 1):
            y = -depth
            ax.annotate(f"D{depth}", xy=(-1.5, y),
                        fontsize=10, fontweight='bold',
                        ha='right', va='center',
                        color='black', annotation_clip=False)

        # --- 表示範囲を手動調整 ---
        max_width = max((len(v) for v in depth_groups.values()), default=5)
        ax.set_xlim(-2, max_width + 1)       # 左に余白、右も確保
        ax.set_ylim(-max_depth - 1, 1)       # 下に余白、上は0〜

        # --- レイアウト強制調整 ---
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.05)

        self.canvas.draw()


        ax.set_xlim(left=-2)  # 左側に余白作成（ラベルが切れないように）

        fig.tight_layout()
        self.canvas.draw()

        # --- スクショ表示 ---
        if self.manager.current_hash in self.manager.screenshot_map:
            path = self.manager.screenshot_map[self.manager.current_hash]
            pixmap = QPixmap(path)
            self.screenshot_label.setPixmap(pixmap.scaledToWidth(300))
            # --- ノードの座標を保存しておく（後でクリック判定に使う）
            self._node_positions = pos
            # --- クリックイベントの登録（初回だけなら __init__ でもOK）
            self.canvas.mpl_connect("button_press_event", self.on_node_click)


    def on_node_click(self, event):
        if not event.inaxes:
            return

        click_x, click_y = event.xdata, event.ydata
        threshold = 0.5  # ノードにどれくらい近ければ「クリック」とみなすか

        for node, (x, y) in self._node_positions.items():
            if abs(click_x - x) < threshold and abs(click_y - y) < threshold:
                print(f"🖱️ ノードクリック検出: {node}")
                # スクショがあれば表示
                if node in self.manager.screenshot_map:
                    pixmap = QPixmap(self.manager.screenshot_map[node])
                    self.screenshot_label.setPixmap(pixmap.scaledToWidth(300))
                return

