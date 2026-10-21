"""
Graph Visualizer — визуализация алгоритмов кратчайшего пути (Дейкстра, Беллман–Форд).

Зависимости:   pip install PySide6
Сборка в .exe: pyinstaller --noconfirm --onefile --windowed --name GraphVisualizer vizualizergraphof.py
(все иконки рисуются кодом, внешних файлов с ресурсами не требуется)
"""
import sys
import os
import math
import heapq
import random
import tempfile

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QComboBox, QFileDialog, QMessageBox, QTreeWidget,
    QTreeWidgetItem, QSlider, QSplitter, QFrame, QProgressBar, QButtonGroup,
    QTabWidget, QListWidget, QListWidgetItem, QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, QSize, QRect
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QFontMetrics, QPalette,
    QLinearGradient, QRadialGradient, QKeySequence, QShortcut, QPolygonF,
    QPixmap, QIcon
)

# ════════════════════════════════════════════════════════════════════
#  Тема
# ════════════════════════════════════════════════════════════════════
FONT_FAMILY = "Segoe UI"

THEME = {
    'bg': '#0d1117',
    'panel': '#12171f',
    'card': '#171d27',
    'card_hi': '#1f2734',
    'border': '#263041',
    'text': '#e8ecf3',
    'muted': '#8d97ab',
    'faint': '#566073',
    'accent': '#7c6cff',
    'accent_hi': '#9285ff',
    'accent2': '#22d3ee',
    'success': '#34d399',
    'danger': '#fb7185',
    'warning': '#fbbf24',
    'canvas': '#0a0d13',
    # состояния узлов
    'n_start': '#34d399',
    'n_end': '#fb7185',
    'n_current': '#fbbf24',
    'n_visited': '#818cf8',
    'n_path': '#2dd4bf',
    'n_idle': '#465267',
    'edge_idle': '#2f3a4e',
}


def fmt_num(value):
    """Красивый вывод чисел: 5 вместо 5.0, ∞ для бесконечности."""
    if value is None:
        return "—"
    if value == float('inf'):
        return "∞"
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.1f}"


def text_on(color):
    """Контрастный цвет текста для заливки."""
    c = QColor(color)
    lum = 0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()
    return QColor('#0b0e14') if lum > 150 else QColor('#ffffff')


def with_alpha(color, alpha):
    c = QColor(color)
    c.setAlpha(alpha)
    return c


# ════════════════════════════════════════════════════════════════════
#  Иконки, нарисованные кодом (никаких внешних файлов → .exe остаётся простым)
# ════════════════════════════════════════════════════════════════════
def make_icon(kind, color='#e8ecf3', size=20, disabled='#566073'):
    icon = QIcon()
    for mode, col in ((QIcon.Normal, color), (QIcon.Disabled, disabled)):
        pm = QPixmap(size * 2, size * 2)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.scale(2, 2)
        c = QColor(col)
        s = float(size)
        pen = QPen(c, 1.8)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)

        if kind == 'play':
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            p.drawPolygon(QPolygonF([QPointF(s * .34, s * .2), QPointF(s * .34, s * .8), QPointF(s * .8, s * .5)]))
        elif kind == 'pause':
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            p.drawRoundedRect(QRectF(s * .27, s * .2, s * .17, s * .6), 1.5, 1.5)
            p.drawRoundedRect(QRectF(s * .56, s * .2, s * .17, s * .6), 1.5, 1.5)
        elif kind == 'prev':
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            p.drawRoundedRect(QRectF(s * .22, s * .24, s * .11, s * .52), 1.2, 1.2)
            p.drawPolygon(QPolygonF([QPointF(s * .78, s * .24), QPointF(s * .78, s * .76), QPointF(s * .4, s * .5)]))
        elif kind == 'next':
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            p.drawRoundedRect(QRectF(s * .67, s * .24, s * .11, s * .52), 1.2, 1.2)
            p.drawPolygon(QPolygonF([QPointF(s * .22, s * .24), QPointF(s * .22, s * .76), QPointF(s * .6, s * .5)]))
        elif kind == 'reset':
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(s * .22, s * .22, s * .56, s * .56), 90 * 16, 270 * 16)
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            cx, cy, r = s * .5, s * .5, s * .28
            p.drawPolygon(QPolygonF([
                QPointF(cx + r, cy - s * .17),
                QPointF(cx + r - s * .14, cy + s * .05),
                QPointF(cx + r + s * .14, cy + s * .05)
            ]))
        elif kind == 'open':
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            poly = QPolygonF([
                QPointF(s * .14, s * .28), QPointF(s * .38, s * .28), QPointF(s * .47, s * .37),
                QPointF(s * .86, s * .37), QPointF(s * .86, s * .78), QPointF(s * .14, s * .78)
            ])
            p.drawPolygon(poly)
        elif kind == 'dice':
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(QRectF(s * .16, s * .16, s * .68, s * .68), s * .16, s * .16)
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            r = s * .06
            for fx, fy in ((.36, .36), (.64, .36), (.5, .5), (.36, .64), (.64, .64)):
                p.drawEllipse(QPointF(s * fx, s * fy), r, r)
        p.end()
        pm.setDevicePixelRatio(2.0)
        icon.addPixmap(pm, mode)
    return icon


def make_logo(size=36):
    pm = QPixmap(size * 2, size * 2)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(2, 2)
    s = float(size)
    grad = QLinearGradient(0, 0, s, s)
    grad.setColorAt(0, QColor(THEME['accent']))
    grad.setColorAt(1, QColor(THEME['accent2']))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(grad))
    p.drawRoundedRect(QRectF(0, 0, s, s), s * .28, s * .28)
    a, b, c = QPointF(s * .27, s * .68), QPointF(s * .5, s * .3), QPointF(s * .76, s * .64)
    pen = QPen(QColor(255, 255, 255, 210), s * .055)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.drawLine(a, b)
    p.drawLine(b, c)
    p.drawLine(a, c)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor('#ffffff'))
    for pt in (a, b, c):
        p.drawEllipse(pt, s * .085, s * .085)
    p.end()
    pm.setDevicePixelRatio(2.0)
    return pm


def ensure_arrow_png(color):
    """Стрелка выпадающего списка: QSS умеет брать картинки только из файла."""
    path = os.path.join(tempfile.gettempdir(), f"gv_arrow_{color.lstrip('#')}.png")
    if not os.path.exists(path):
        pm = QPixmap(24, 24)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(color), 2.6)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.drawPolyline(QPolygonF([QPointF(6, 9), QPointF(12, 15), QPointF(18, 9)]))
        p.end()
        pm.save(path, "PNG")
    return path.replace("\\", "/")


def build_stylesheet(T):
    arrow = ensure_arrow_png(T['muted'])
    return f"""
    QWidget {{
        color: {T['text']};
        font-family: "{FONT_FAMILY}", "Inter", "Roboto", "Helvetica Neue", Arial, sans-serif;
        font-size: 13px;
    }}
    QMainWindow, QDialog, QMessageBox {{ background: {T['bg']}; }}
    QToolTip {{
        background: {T['card_hi']}; color: {T['text']};
        border: 1px solid {T['border']}; padding: 5px 8px; border-radius: 6px;
    }}

    QFrame#topbar {{ background: {T['panel']}; border-bottom: 1px solid {T['border']}; }}
    QWidget#sidebar {{ background: {T['panel']}; border-left: 1px solid {T['border']}; }}
    QLabel#brand {{ font-size: 16px; font-weight: 700; }}
    QLabel#brandSub {{ color: {T['muted']}; font-size: 11px; }}
    QLabel#muted {{ color: {T['muted']}; font-size: 12px; }}
    QLabel#value {{ color: {T['text']}; font-size: 12px; font-weight: 600; }}
    QLabel#arrow {{ color: {T['faint']}; font-size: 16px; }}

    QFrame#card {{
        background: {T['card']}; border: 1px solid {T['border']}; border-radius: 12px;
    }}
    QLabel#cardTitle {{ color: {T['muted']}; font-size: 11px; font-weight: 700; }}

    QPushButton {{
        background: {T['card_hi']}; border: 1px solid {T['border']};
        border-radius: 9px; padding: 8px 14px; font-weight: 600;
    }}
    QPushButton:hover {{ border-color: {T['accent']}; background: #263044; }}
    QPushButton:pressed {{ background: {T['border']}; }}
    QPushButton:disabled {{ color: {T['faint']}; background: {T['card']}; }}
    QPushButton#primary {{
        background: {T['accent']}; border: 1px solid {T['accent']}; color: white;
    }}
    QPushButton#primary:hover {{ background: {T['accent_hi']}; border-color: {T['accent_hi']}; }}
    QPushButton#primary:pressed {{ background: #6556e6; }}
    QPushButton#iconbtn {{
        padding: 0; min-width: 38px; max-width: 38px; min-height: 38px; max-height: 38px;
        border-radius: 10px;
    }}
    QPushButton#playbtn {{
        padding: 0; min-width: 46px; max-width: 46px; min-height: 46px; max-height: 46px;
        border-radius: 23px; background: {T['accent']}; border: 1px solid {T['accent']};
    }}
    QPushButton#playbtn:hover {{ background: {T['accent_hi']}; border-color: {T['accent_hi']}; }}

    QFrame#segment {{
        background: {T['bg']}; border: 1px solid {T['border']}; border-radius: 11px;
    }}
    QPushButton#seg {{
        background: transparent; border: none; border-radius: 8px;
        padding: 7px 14px; color: {T['muted']}; font-weight: 600;
    }}
    QPushButton#seg:hover {{ color: {T['text']}; background: transparent; }}
    QPushButton#seg:checked {{ background: {T['accent']}; color: white; }}

    QComboBox {{
        background: {T['bg']}; border: 1px solid {T['border']}; border-radius: 9px;
        padding: 7px 10px; min-height: 18px;
    }}
    QComboBox:hover {{ border-color: {T['accent']}; }}
    QComboBox::drop-down {{ border: none; width: 26px; }}
    QComboBox::down-arrow {{ image: url("{arrow}"); width: 12px; height: 12px; }}
    QComboBox QAbstractItemView {{
        background: {T['card']}; border: 1px solid {T['border']}; border-radius: 8px;
        selection-background-color: {T['accent']}; selection-color: white; outline: 0; padding: 4px;
    }}

    QSlider::groove:horizontal {{ height: 6px; background: {T['bg']}; border-radius: 3px; }}
    QSlider::sub-page:horizontal {{
        border-radius: 3px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {T['accent']}, stop:1 {T['accent2']});
    }}
    QSlider::handle:horizontal {{
        background: white; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px;
        border: 3px solid {T['accent']};
    }}

    QProgressBar {{ background: {T['bg']}; border: none; border-radius: 4px; min-height: 8px; max-height: 8px; }}
    QProgressBar::chunk {{
        border-radius: 4px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {T['accent']}, stop:1 {T['accent2']});
    }}

    QTabWidget::pane {{
        border: 1px solid {T['border']}; border-radius: 12px; background: {T['card']}; top: -1px;
    }}
    QTabBar {{ background: transparent; }}
    QTabBar::tab {{
        background: transparent; color: {T['muted']}; padding: 9px 16px; margin-right: 2px;
        border-bottom: 2px solid transparent; font-weight: 600;
    }}
    QTabBar::tab:hover {{ color: {T['text']}; }}
    QTabBar::tab:selected {{ color: {T['text']}; border-bottom: 2px solid {T['accent']}; }}

    QTreeWidget, QListWidget {{
        background: transparent; border: none; outline: 0;
        alternate-background-color: rgba(255, 255, 255, 7);
    }}
    QTreeWidget::item {{ padding: 5px 4px; border: none; }}
    QListWidget::item {{ padding: 5px 8px; border: none; }}
    QTreeWidget::item:selected, QListWidget::item:selected {{
        background: rgba(124, 108, 255, 56); color: {T['text']};
    }}
    QHeaderView::section {{
        background: transparent; color: {T['muted']}; border: none;
        border-bottom: 1px solid {T['border']}; padding: 7px 8px; font-weight: 700; font-size: 11px;
    }}

    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {T['border']}; border-radius: 3px; min-height: 28px; }}
    QScrollBar::handle:vertical:hover {{ background: {T['faint']}; }}
    QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
    QScrollBar::handle:horizontal {{ background: {T['border']}; border-radius: 3px; min-width: 28px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

    QSplitter::handle {{ background: {T['border']}; }}
    QStatusBar {{ background: {T['panel']}; border-top: 1px solid {T['border']}; color: {T['muted']}; }}
    QStatusBar::item {{ border: none; }}
    QStatusBar QLabel {{ font-size: 12px; padding: 0 6px; }}

    QFrame#zoombar {{
        background: rgba(18, 23, 31, 235); border: 1px solid {T['border']}; border-radius: 11px;
    }}
    QPushButton#zoombtn {{
        background: transparent; border: none; border-radius: 8px;
        min-width: 30px; min-height: 30px; padding: 0 8px; font-size: 15px; font-weight: 600;
    }}
    QPushButton#zoombtn:hover {{ background: {T['card_hi']}; }}
    QLabel#zoomlabel {{ color: {T['muted']}; font-size: 12px; min-width: 44px; qproperty-alignment: AlignCenter; }}
    """


# ════════════════════════════════════════════════════════════════════
#  Алгоритмы (плагины)
# ════════════════════════════════════════════════════════════════════
class ShortestPathAlgorithm:

    def __init__(self, name, description, supports_negative_weights=False):
        self.name = name
        self.description = description
        self.supports_negative_weights = supports_negative_weights

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def initialize(self, graph, start_node, positions, end_node=None):
        raise NotImplementedError

    def execute_step(self):
        raise NotImplementedError

    def is_finished(self):
        raise NotImplementedError

    def get_result(self):
        raise NotImplementedError

    def get_current_state(self, description=""):
        raise NotImplementedError


class DijkstraPlugin(ShortestPathAlgorithm):
    def __init__(self):
        super().__init__(
            name="Дейкстра",
            description="Алгоритм Дейкстры для поиска кратчайшего пути",
            supports_negative_weights=False
        )
        self.reset()

    def reset(self):
        self.distances = {}
        self.visited = set()
        self.previous = {}
        self.queue = []
        self.current_node = None
        self.final_path = None
        self.algorithm_finished = False
        self.algorithm_result = ""
        self.active_edges = []
        self.graph = None
        self.start_node = None
        self.end_node = None

    def initialize(self, graph, start_node, positions, end_node=None):
        self.reset()
        self.graph = graph
        self.start_node = start_node
        self.end_node = end_node

        self.distances = {node: float('inf') for node in positions}
        self.distances[start_node] = 0
        heapq.heappush(self.queue, (0, start_node))

        return self.get_current_state("Инициализация: расстояния = ∞, кроме стартовой вершины")

    def execute_step(self):
        if self.algorithm_finished or not self.queue:
            return None

        current_distance, self.current_node = heapq.heappop(self.queue)
        self.active_edges = []

        if self.current_node in self.visited:
            if not self.queue:
                self.finalize_algorithm()
            return self.get_current_state(f"Пропуск устаревшей записи {self.current_node}")

        self.visited.add(self.current_node)

        updates = []
        for neighbor, weight in self.graph.get(self.current_node, {}).items():
            if neighbor in self.visited:
                continue
            new_distance = current_distance + weight
            if new_distance < self.distances[neighbor]:
                old_distance = self.distances[neighbor]
                self.distances[neighbor] = new_distance
                self.previous[neighbor] = self.current_node
                heapq.heappush(self.queue, (new_distance, neighbor))
                updates.append((neighbor, old_distance, new_distance))
                self.active_edges.append((self.current_node, neighbor))

        description = f"Обрабатываем узел {self.current_node}"
        if updates:
            desc_updates = [f"{v}: {fmt_num(old)}→{fmt_num(new)}" for v, old, new in updates]
            description += f" · обновления: {', '.join(desc_updates)}"

        if self.current_node == self.end_node or not self.queue:
            self.finalize_algorithm()

        return self.get_current_state(description)

    def finalize_algorithm(self):
        self.algorithm_finished = True
        self.current_node = None

        if self.end_node in self.previous and self.distances[self.end_node] != float('inf'):
            path = self.reconstruct_path(self.end_node)
            total_distance = self.distances[self.end_node]
            self.algorithm_result = f"Найден путь: {' -> '.join(path)} (длина: {fmt_num(total_distance)})"
            self.final_path = path
        else:
            self.algorithm_result = f"Путь от {self.start_node} до {self.end_node} не найден"
            self.final_path = None

    def reconstruct_path(self, end_node):
        path = []
        current = end_node
        while current in self.previous:
            path.append(current)
            current = self.previous[current]
        path.append(self.start_node)
        return path[::-1]

    def is_finished(self):
        return self.algorithm_finished

    def get_result(self):
        return {
            'success': self.final_path is not None,
            'path': self.final_path,
            'distance': self.distances.get(self.end_node, float('inf')),
            'message': self.algorithm_result
        }

    def get_current_state(self, description=""):
        return {
            'description': description,
            'distances': self.distances.copy(),
            'visited': self.visited.copy(),
            'previous': self.previous.copy(),
            'current_node': self.current_node,
            'final_path': self.final_path.copy() if self.final_path else None,
            'algorithm_finished': self.algorithm_finished,
            'algorithm_result': self.algorithm_result,
            'active_edges': list(self.active_edges)
        }


class BellmanFordPlugin(ShortestPathAlgorithm):
    def __init__(self):
        super().__init__(
            name="Беллман–Форд",
            description="Алгоритм Беллмана–Форда для графов с отрицательными весами",
            supports_negative_weights=True
        )
        self.reset()

    def reset(self):
        self.distances = {}
        self.previous = {}
        self.current_node = None
        self.final_path = None
        self.algorithm_finished = False
        self.algorithm_result = ""
        self.iteration = 0
        self.edge_index = 0
        self.changed = False
        self.edges = []
        self.active_edges = []
        self.graph = None
        self.start_node = None
        self.end_node = None

    def initialize(self, graph, start_node, positions, end_node=None):
        self.reset()
        self.graph = graph
        self.start_node = start_node
        self.end_node = end_node

        self.distances = {node: float('inf') for node in positions}
        self.distances[start_node] = 0

        self.edges = []
        for u, neighbors in graph.items():
            for v, weight in neighbors.items():
                self.edges.append((u, v, weight))

        return self.get_current_state(f"Инициализация: |V| = {len(positions)}, |E| = {len(self.edges)}")

    def execute_step(self):
        if self.algorithm_finished:
            return None

        description = ""
        self.active_edges = []

        if self.iteration < len(self.distances) - 1:
            if self.edge_index < len(self.edges):
                u, v, weight = self.edges[self.edge_index]
                self.current_node = u
                self.active_edges = [(u, v)]

                if self.distances[u] != float('inf') and self.distances[u] + weight < self.distances[v]:
                    old_dist = self.distances[v]
                    self.distances[v] = self.distances[u] + weight
                    self.previous[v] = u
                    self.changed = True

                    description = (f"Итерация {self.iteration + 1}: {u}→{v} ({fmt_num(weight)}) · "
                                   f"{fmt_num(old_dist)}→{fmt_num(self.distances[v])}")
                else:
                    description = f"Итерация {self.iteration + 1}: {u}→{v} ({fmt_num(weight)}) · без изменений"

                self.edge_index += 1

            else:
                if self.changed:
                    self.iteration += 1
                    self.edge_index = 0
                    self.changed = False
                    self.current_node = None
                    description = f"Начало итерации {self.iteration + 1}"
                else:
                    self.iteration = len(self.distances) - 1
                    self.edge_index = 0
                    self.current_node = None
                    description = "Изменений нет — переход к проверке отрицательных циклов"

        else:
            if self.edge_index < len(self.edges):
                u, v, weight = self.edges[self.edge_index]
                self.current_node = u
                self.active_edges = [(u, v)]

                if self.distances[u] != float('inf') and self.distances[u] + weight < self.distances[v]:
                    self.algorithm_finished = True
                    self.algorithm_result = f"Обнаружен цикл отрицательного веса! {u}→{v} ({fmt_num(weight)})"
                    description = f"ОШИБКА: {self.algorithm_result}"
                else:
                    description = f"Проверка циклов: {u}→{v} ({fmt_num(weight)})"

                self.edge_index += 1
            else:
                self.algorithm_finished = True
                self.current_node = None
                self.finalize_algorithm()
                description = "Алгоритм завершён"

        return self.get_current_state(description)

    def finalize_algorithm(self):
        if not self.algorithm_result:
            if self.end_node in self.previous and self.distances[self.end_node] != float('inf'):
                path = self.reconstruct_path(self.end_node)
                total_distance = self.distances[self.end_node]
                self.algorithm_result = f"Найден путь: {' -> '.join(path)} (длина: {fmt_num(total_distance)})"
                self.final_path = path
            else:
                self.algorithm_result = f"Путь от {self.start_node} до {self.end_node} не найден"
                self.final_path = None

    def reconstruct_path(self, end_node):
        path = []
        current = end_node
        while current in self.previous:
            path.append(current)
            current = self.previous[current]
        path.append(self.start_node)
        return path[::-1]

    def is_finished(self):
        return self.algorithm_finished

    def get_result(self):
        return {
            'success': self.final_path is not None and "ОШИБКА" not in self.algorithm_result
                       and "отрицательн" not in self.algorithm_result,
            'path': self.final_path,
            'distance': self.distances.get(self.end_node, float('inf')),
            'message': self.algorithm_result
        }

    def get_current_state(self, description=""):
        return {
            'description': description,
            'distances': self.distances.copy(),
            'previous': self.previous.copy(),
            'current_node': self.current_node,
            'final_path': self.final_path.copy() if self.final_path else None,
            'algorithm_finished': self.algorithm_finished,
            'algorithm_result': self.algorithm_result,
            'iteration': self.iteration,
            'edge_index': self.edge_index,
            'active_edges': list(self.active_edges)
        }


class AlgorithmPluginManager:
    def __init__(self):
        self.plugins = {}
        self.current_plugin = None
        self.register_plugins()

    def register_plugins(self):
        self.plugins['dijkstra'] = DijkstraPlugin()
        self.plugins['bellman'] = BellmanFordPlugin()

    def get_plugin(self, name):
        return self.plugins.get(name)

    def get_available_plugins(self):
        return list(self.plugins.values())

    def set_current_plugin(self, plugin_name):
        self.current_plugin = self.get_plugin(plugin_name)
        return self.current_plugin


# ════════════════════════════════════════════════════════════════════
#  Раскладка графа (силовая), чтобы загруженные/сгенерированные графы выглядели аккуратно
# ════════════════════════════════════════════════════════════════════
def compute_layout(nodes, graph, width=760.0, height=520.0, iterations=300):
    n = len(nodes)
    cx, cy = 400.0, 300.0
    if n == 0:
        return {}
    if n == 1:
        return {nodes[0]: (cx, cy)}

    rng = random.Random(1234)
    pos = {}
    for i, node in enumerate(nodes):
        ang = 2 * math.pi * i / n
        pos[node] = [cx + width * 0.35 * math.cos(ang) + rng.uniform(-8, 8),
                     cy + height * 0.35 * math.sin(ang) + rng.uniform(-8, 8)]

    edges = set()
    for u, nb in graph.items():
        for v in nb:
            if u != v and u in pos and v in pos:
                edges.add(tuple(sorted((u, v))))

    k = math.sqrt(width * height / n) * 0.75
    temp = width / 6.0
    for _ in range(iterations):
        disp = {nd: [0.0, 0.0] for nd in nodes}
        for i in range(n):
            ui = nodes[i]
            for j in range(i + 1, n):
                vj = nodes[j]
                dx = pos[ui][0] - pos[vj][0]
                dy = pos[ui][1] - pos[vj][1]
                d = math.hypot(dx, dy)
                if d < 0.01:
                    dx, dy, d = rng.uniform(-1, 1), rng.uniform(-1, 1), 1.0
                f = k * k / d
                fx, fy = dx / d * f, dy / d * f
                disp[ui][0] += fx
                disp[ui][1] += fy
                disp[vj][0] -= fx
                disp[vj][1] -= fy
        for u, v in edges:
            dx = pos[u][0] - pos[v][0]
            dy = pos[u][1] - pos[v][1]
            d = math.hypot(dx, dy) or 0.01
            f = d * d / k
            fx, fy = dx / d * f, dy / d * f
            disp[u][0] -= fx
            disp[u][1] -= fy
            disp[v][0] += fx
            disp[v][1] += fy
        for nd in nodes:
            disp[nd][0] -= (pos[nd][0] - cx) * 0.06
            disp[nd][1] -= (pos[nd][1] - cy) * 0.06
            dx, dy = disp[nd]
            d = math.hypot(dx, dy) or 0.01
            step = min(d, temp)
            pos[nd][0] = min(cx + width / 2, max(cx - width / 2, pos[nd][0] + dx / d * step))
            pos[nd][1] = min(cy + height / 2, max(cy - height / 2, pos[nd][1] + dy / d * step))
        temp *= 0.98
    return {nd: (pos[nd][0], pos[nd][1]) for nd in nodes}



# ════════════════════════════════════════════════════════════════════
#  Генераторы графов (логика сохранена из исходной версии)
# ════════════════════════════════════════════════════════════════════
class GraphGeneratorsMixin:
    def generate_connected_graph(self, all_nodes):
        complexity = self.complexity_combo.currentText()
        if complexity == "Лёгкий (4-6 узлов)":
            num_nodes = random.randint(4, 6)
        elif complexity == "Средний (6-9 узлов)":
            num_nodes = random.randint(6, 9)
        else:
            num_nodes = random.randint(9, 12)
        selected_nodes = all_nodes[:num_nodes]

        graph = {}

        for i in range(len(selected_nodes) - 1):
            u = selected_nodes[i]
            v = selected_nodes[i + 1]
            weight = random.randint(1, 10)
            self.add_edge_to_dict(graph, u, v, weight)

        num_extra_edges = random.randint(num_nodes, num_nodes + 3)
        for _ in range(num_extra_edges):
            u = random.choice(selected_nodes)
            v = random.choice(selected_nodes)
            if u != v and not self.has_edge_in_dict(graph, u, v):
                weight = random.randint(1, 10)
                if random.random() < 0.1:
                    weight = -random.randint(1, 3)
                self.add_edge_to_dict(graph, u, v, weight)

        return {
            'graph': graph,
            'nodes': selected_nodes,
            'name': 'Связный случайный граф'
        }

    def generate_complete_graph(self, all_nodes):
        complexity = self.complexity_combo.currentText()
        if complexity == "Лёгкий (4-6 узлов)":
            num_nodes = random.randint(3, 5)
        elif complexity == "Средний (6-9 узлов)":
            num_nodes = random.randint(5, 7)
        else:
            num_nodes = random.randint(6, 8)
        selected_nodes = all_nodes[:num_nodes]

        graph = {}

        for i in range(len(selected_nodes)):
            for j in range(i + 1, len(selected_nodes)):
                weight = random.randint(1, 10)
                if random.random() < 0.05:
                    weight = -random.randint(1, 2)
                self.add_edge_to_dict(graph, selected_nodes[i], selected_nodes[j], weight)

        return {
            'graph': graph,
            'nodes': selected_nodes,
            'name': 'Полный граф'
        }

    def generate_tree_graph(self, all_nodes):
        complexity = self.complexity_combo.currentText()
        if complexity == "Лёгкий (4-6 узлов)":
            num_nodes = random.randint(4, 6)
        elif complexity == "Средний (6-9 узлов)":
            num_nodes = random.randint(7, 9)
        else:
            num_nodes = random.randint(10, 12)
        selected_nodes = all_nodes[:num_nodes]
        random.shuffle(selected_nodes)

        graph = {}

        for i in range(1, len(selected_nodes)):
            parent_index = random.randint(0, i - 1)
            weight = random.randint(1, 15)
            if complexity == "Сложный (9-12 узлов)" and random.random() < 0.1:
                weight = -random.randint(1, 2)
            self.add_edge_to_dict(graph, selected_nodes[parent_index], selected_nodes[i], weight)

        return {
            'graph': graph,
            'nodes': selected_nodes,
            'name': 'Дерево'
        }

    def generate_grid_graph(self, all_nodes):
        complexity = self.complexity_combo.currentText()
        if complexity == "Лёгкий (4-6 узлов)":
            grid_size = 2
        elif complexity == "Средний (6-9 узлов)":
            grid_size = 3
        else:
            grid_size = 4

        num_nodes = min(grid_size * grid_size, len(all_nodes))
        grid_size = int(num_nodes ** 0.5)
        num_nodes = grid_size * grid_size
        selected_nodes = all_nodes[:num_nodes]

        graph = {}

        for i in range(grid_size):
            for j in range(grid_size):
                if i * grid_size + j >= num_nodes:
                    break
                current = selected_nodes[i * grid_size + j]

                if j < grid_size - 1 and i * grid_size + j + 1 < num_nodes:
                    right = selected_nodes[i * grid_size + j + 1]
                    weight = random.randint(1, 5)
                    self.add_edge_to_dict(graph, current, right, weight)

                if i < grid_size - 1 and (i + 1) * grid_size + j < num_nodes:
                    down = selected_nodes[(i + 1) * grid_size + j]
                    weight = random.randint(1, 5)
                    self.add_edge_to_dict(graph, current, down, weight)

        diagonal_chance = 0.2 if complexity == "Лёгкий (4-6 узлов)" else 0.4
        for i in range(grid_size - 1):
            for j in range(grid_size - 1):
                if i * grid_size + j >= num_nodes or i * grid_size + j + 1 >= num_nodes:
                    continue
                if (i + 1) * grid_size + j + 1 >= num_nodes:
                    continue

                if random.random() < diagonal_chance:
                    current = selected_nodes[i * grid_size + j]
                    diag = selected_nodes[(i + 1) * grid_size + j + 1]
                    weight = random.randint(5, 10)
                    if not self.has_edge_in_dict(graph, current, diag):
                        self.add_edge_to_dict(graph, current, diag, weight)

        return {
            'graph': graph,
            'nodes': selected_nodes,
            'name': 'Решёточный граф'
        }

    def generate_bipartite_graph(self, all_nodes):
        complexity = self.complexity_combo.currentText()
        if complexity == "Лёгкий (4-6 узлов)":
            set1_size = random.randint(2, 3)
            set2_size = random.randint(2, 3)
        elif complexity == "Средний (6-9 узлов)":
            set1_size = random.randint(3, 4)
            set2_size = random.randint(3, 5)
        else:
            set1_size = random.randint(4, 6)
            set2_size = random.randint(4, 6)

        set1 = all_nodes[:set1_size]
        set2 = all_nodes[set1_size:set1_size + set2_size]
        selected_nodes = set1 + set2

        graph = {}

        for u in set1:
            connections = random.randint(1, 3)
            if len(set2) < connections:
                connections = len(set2)
            if connections > 0:
                connected_nodes = random.sample(set2, connections)
                for v in connected_nodes:
                    weight = random.randint(1, 8)
                    if random.random() < 0.05:
                        weight = -random.randint(1, 2)
                    self.add_edge_to_dict(graph, u, v, weight)

        extra_chance = 0.15 if complexity == "Лёгкий (4-6 узлов)" else 0.25
        for u in set1:
            for v in set2:
                if not self.has_edge_in_dict(graph, u, v) and random.random() < extra_chance:
                    weight = random.randint(3, 12)
                    if complexity == "Сложный (9-12 узлов)" and random.random() < 0.1:
                        weight = -random.randint(1, 3)
                    self.add_edge_to_dict(graph, u, v, weight)

        return {
            'graph': graph,
            'nodes': selected_nodes,
            'name': 'Двудольный граф'
        }

    def generate_star_graph(self, all_nodes):
        center_node = 'A'
        complexity = self.complexity_combo.currentText()
        if complexity == "Лёгкий (4-6 узлов)":
            num_leaves = random.randint(3, 5)
        elif complexity == "Средний (6-9 узлов)":
            num_leaves = random.randint(5, 8)
        else:
            num_leaves = random.randint(8, 11)

        leaf_nodes = all_nodes[1:num_leaves + 1]
        selected_nodes = [center_node] + leaf_nodes

        graph = {}

        for leaf in leaf_nodes:
            weight = random.randint(1, 15)
            if complexity == "Сложный (9-12 узлов)" and random.random() < 0.1:
                weight = -random.randint(1, 3)
            self.add_edge_to_dict(graph, center_node, leaf, weight)

        leaf_connection_chance = 0.2 if complexity == "Лёгкий (4-6 узлов)" else 0.4
        for i in range(len(leaf_nodes)):
            for j in range(i + 1, len(leaf_nodes)):
                if random.random() < leaf_connection_chance:
                    weight = random.randint(5, 20)
                    if complexity == "Сложный (9-12 узлов)" and random.random() < 0.1:
                        weight = -random.randint(1, 2)
                    if not self.has_edge_in_dict(graph, leaf_nodes[i], leaf_nodes[j]):
                        self.add_edge_to_dict(graph, leaf_nodes[i], leaf_nodes[j], weight)

        return {
            'graph': graph,
            'nodes': selected_nodes,
            'name': 'Звёздчатый граф'
        }

    def add_edge_to_dict(self, graph, u, v, weight):
        if u not in graph:
            graph[u] = {}
        if v not in graph:
            graph[v] = {}
        graph[u][v] = weight
        if not self.directed:
            graph[v][u] = weight

    def has_edge_in_dict(self, graph, u, v):
        return u in graph and v in graph[u]


def qflags(*items):
    """Безопасное объединение флагов Qt (работает в разных версиях PySide6)."""
    result = 0
    for item in items:
        result |= int(getattr(item, 'value', item))
    return result


# ════════════════════════════════════════════════════════════════════
#  Холст графа
# ════════════════════════════════════════════════════════════════════
class GraphCanvas(QWidget):
    def __init__(self, app_window):
        super().__init__()
        self.app = app_window
        self.zoom = 1.0
        self.view_center = QPointF(400, 300)
        self.pulse = 0.0
        self.hover_node = None
        self.drag_node = None
        self.press_pos = None
        self.drag_moved = False
        self.panning = False
        self.pan_last = QPointF()
        self._bg_key = None
        self._bg_pixmap = None

        self.setMouseTracking(True)
        self.setMinimumSize(520, 420)
        self.setFocusPolicy(Qt.StrongFocus)

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._tick)
        self.anim_timer.start(33)

        self._build_zoombar()

    # ── панель масштаба ─────────────────────────────────────────────
    def _build_zoombar(self):
        self.zoombar = QFrame(self)
        self.zoombar.setObjectName("zoombar")
        lay = QHBoxLayout(self.zoombar)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(2)

        minus = QPushButton("−")
        plus = QPushButton("+")
        fit = QPushButton("Вписать")
        self.zoom_label = QLabel("100%")
        self.zoom_label.setObjectName("zoomlabel")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        for b, tip in ((minus, "Отдалить"), (plus, "Приблизить"), (fit, "Вписать граф в окно (I)")):
            b.setObjectName("zoombtn")
            b.setFocusPolicy(Qt.NoFocus)
            b.setCursor(Qt.PointingHandCursor)
            b.setToolTip(tip)
        minus.clicked.connect(lambda: self.zoom_by(1 / 1.2))
        plus.clicked.connect(lambda: self.zoom_by(1.2))
        fit.clicked.connect(self.fit_view)

        lay.addWidget(minus)
        lay.addWidget(self.zoom_label)
        lay.addWidget(plus)
        lay.addWidget(fit)
        self.zoombar.adjustSize()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.zoombar.adjustSize()
        self.zoombar.move(self.width() - self.zoombar.width() - 16,
                          self.height() - self.zoombar.height() - 16)

    def _tick(self):
        self.pulse += 0.14
        if self.app.current_node is not None or self.app.final_path:
            self.update()

    # ── преобразования координат ────────────────────────────────────
    def to_screen(self, pos):
        return QPointF(self.width() / 2 + (pos[0] - self.view_center.x()) * self.zoom,
                       self.height() / 2 + (pos[1] - self.view_center.y()) * self.zoom)

    def to_world(self, point):
        return QPointF((point.x() - self.width() / 2) / self.zoom + self.view_center.x(),
                       (point.y() - self.height() / 2) / self.zoom + self.view_center.y())

    def node_radius(self):
        return max(13.0, min(30.0, 21.0 * self.zoom))

    def set_zoom(self, value):
        self.zoom = max(0.2, min(4.0, value))
        self.zoom_label.setText(f"{int(round(self.zoom * 100))}%")

    def zoom_by(self, factor, anchor=None):
        if anchor is None:
            anchor = QPointF(self.width() / 2, self.height() / 2)
        before = self.to_world(anchor)
        self.set_zoom(self.zoom * factor)
        after = self.to_world(anchor)
        self.view_center += before - after
        self.update()

    def fit_view(self):
        pos = self.app.positions
        if not pos:
            return
        xs = [p[0] for p in pos.values()]
        ys = [p[1] for p in pos.values()]
        bw = max(max(xs) - min(xs), 1.0)
        bh = max(max(ys) - min(ys), 1.0)
        avail_w = max(self.width() - 180, 200)
        avail_h = max(self.height() - 200, 160)
        self.set_zoom(min(avail_w / bw, avail_h / bh, 1.8))
        self.view_center = QPointF((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2)
        self.update()

    def node_at(self, point):
        r = self.node_radius() + 2
        for node in reversed(list(self.app.positions.keys())):
            c = self.to_screen(self.app.positions[node])
            dx, dy = point.x() - c.x(), point.y() - c.y()
            if dx * dx + dy * dy <= r * r:
                return node
        return None

    # ── фон ─────────────────────────────────────────────────────────
    def _background(self):
        key = (self.width(), self.height(), round(self.zoom, 3),
               round(self.view_center.x(), 1), round(self.view_center.y(), 1))
        if key == self._bg_key and self._bg_pixmap is not None:
            return self._bg_pixmap

        dpr = self.devicePixelRatioF()
        w, h = self.width(), self.height()
        pm = QPixmap(max(1, int(w * dpr)), max(1, int(h * dpr)))
        pm.setDevicePixelRatio(dpr)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)

        grad = QRadialGradient(w / 2, h / 2, max(w, h) * 0.75)
        grad.setColorAt(0, QColor('#111722'))
        grad.setColorAt(1, QColor(THEME['canvas']))
        p.fillRect(0, 0, w, h, QBrush(grad))

        spacing = 30.0 * self.zoom
        while spacing < 18:
            spacing *= 2
        while spacing > 72:
            spacing /= 2
        ox = (w / 2 - self.view_center.x() * self.zoom) % spacing
        oy = (h / 2 - self.view_center.y() * self.zoom) % spacing
        pen = QPen(QColor(255, 255, 255, 30), 2.0)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        pts = []
        x = ox
        while x < w:
            y = oy
            while y < h:
                pts.append(QPointF(x, y))
                y += spacing
            x += spacing
        p.drawPoints(QPolygonF(pts))
        p.end()

        self._bg_key = key
        self._bg_pixmap = pm
        return pm

    # ── отрисовка ───────────────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        p.drawPixmap(0, 0, self._background())

        if not self.app.graph:
            self._draw_empty(p)
            p.end()
            return

        self.draw_edges(p)
        self.draw_nodes(p)
        self.draw_hud(p)
        self.draw_legend(p)
        p.end()

    def _font(self, px, bold=False):
        f = QFont(FONT_FAMILY)
        f.setPixelSize(int(px))
        f.setBold(bold)
        return f

    def _draw_empty(self, p):
        p.setPen(QColor(THEME['text']))
        p.setFont(self._font(20, True))
        p.drawText(self.rect().adjusted(0, -20, 0, 0), Qt.AlignCenter, "Граф не загружен")
        p.setPen(QColor(THEME['muted']))
        p.setFont(self._font(13))
        p.drawText(self.rect().adjusted(0, 40, 0, 0), Qt.AlignCenter,
                   "Нажмите «Загрузить» или «Сгенерировать граф»")

    def draw_edges(self, p):
        a = self.app
        r = self.node_radius()
        directed = a.directed
        path_edges = a.path_edge_set()
        tree_edges = {(prev, node) for node, prev in a.previous.items()}
        active = set(a.active_edges)
        z = max(0.7, min(1.3, self.zoom))
        pills = []

        for u, v, w in a.iter_unique_edges():
            if u not in a.positions or v not in a.positions:
                continue
            p1 = self.to_screen(a.positions[u])
            p2 = self.to_screen(a.positions[v])
            dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
            length = math.hypot(dx, dy)
            if length < 1:
                continue
            ux, uy = dx / length, dy / length
            nx, ny = -uy, ux

            off = 7.0 if (directed and a.has_edge(v, u)) else 0.0
            if directed:
                start = QPointF(p1.x() + ux * r + nx * off, p1.y() + uy * r + ny * off)
                end = QPointF(p2.x() - ux * r + nx * off, p2.y() - uy * r + ny * off)
            else:
                start, end = p1, p2

            key, rev = (u, v), (v, u)
            on_path = key in path_edges or (not directed and rev in path_edges)
            in_tree = key in tree_edges or (not directed and rev in tree_edges)
            is_active = key in active or (not directed and rev in active)

            if on_path:
                color, width, style = QColor(THEME['n_path']), 3.6 * z, Qt.SolidLine
            elif is_active:
                color, width, style = QColor(THEME['warning']), 3.0 * z, Qt.SolidLine
            elif w < 0:
                color, width, style = QColor(THEME['danger']), 2.2 * z, Qt.DashLine
            elif in_tree:
                color, width, style = QColor(THEME['n_visited']), 2.6 * z, Qt.SolidLine
            else:
                color, width, style = QColor(THEME['edge_idle']), 1.8 * z, Qt.SolidLine

            if on_path:
                glow = QPen(with_alpha(color, 55 + int(25 * math.sin(self.pulse))), width + 7)
                glow.setCapStyle(Qt.RoundCap)
                p.setPen(glow)
                p.drawLine(start, end)

            pen = QPen(color, width)
            pen.setStyle(style)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            p.drawLine(start, end)

            if directed:
                size = 11.0 * z
                tip = end
                base = QPointF(tip.x() - ux * size, tip.y() - uy * size)
                head = QPolygonF([
                    tip,
                    QPointF(base.x() + nx * size * 0.45, base.y() + ny * size * 0.45),
                    QPointF(base.x() - nx * size * 0.45, base.y() - ny * size * 0.45)
                ])
                p.setPen(Qt.NoPen)
                p.setBrush(color)
                p.drawPolygon(head)

            mid = QPointF((start.x() + end.x()) / 2, (start.y() + end.y()) / 2)
            pills.append((mid, w, color, on_path or is_active or w < 0))

        if self.zoom > 0.4:
            p.setFont(self._font(11, True))
            fm = QFontMetrics(p.font())
            for mid, w, color, highlight in pills:
                text = fmt_num(w)
                tw = fm.horizontalAdvance(text) + 12
                rect = QRectF(mid.x() - tw / 2, mid.y() - 10, tw, 20)
                p.setPen(QPen(with_alpha(color, 200 if highlight else 90), 1))
                p.setBrush(QColor(10, 13, 19, 238))
                p.drawRoundedRect(rect, 10, 10)
                p.setPen(color if highlight else QColor(THEME['muted']))
                p.drawText(rect, Qt.AlignCenter, text)

    def draw_nodes(self, p):
        a = self.app
        r = self.node_radius()
        for node, pos in a.positions.items():
            c = self.to_screen(pos)
            col = QColor(a.get_node_color(node))
            is_path = bool(a.final_path and node in a.final_path)

            if node == a.current_node or is_path:
                gr = r + 11 + 3.5 * math.sin(self.pulse + (0 if node == a.current_node else 1.5))
                g = QRadialGradient(c, gr)
                g.setColorAt(0.5, with_alpha(col, 140 if node == a.current_node else 90))
                g.setColorAt(1.0, with_alpha(col, 0))
                p.setPen(Qt.NoPen)
                p.setBrush(QBrush(g))
                p.drawEllipse(c, gr, gr)

            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 110))
            p.drawEllipse(QPointF(c.x(), c.y() + r * 0.2), r, r)

            g = QRadialGradient(c.x() - r * 0.35, c.y() - r * 0.4, r * 1.7)
            g.setColorAt(0.0, col.lighter(128))
            g.setColorAt(0.55, col)
            g.setColorAt(1.0, col.darker(135))
            ring = QColor(255, 255, 255, 230) if node == self.hover_node else col.lighter(150)
            p.setPen(QPen(ring, 2.4 if node == self.hover_node else 1.6))
            p.setBrush(QBrush(g))
            p.drawEllipse(c, r, r)

            size = r * 0.85
            f = self._font(size, True)
            fm = QFontMetrics(f)
            while fm.horizontalAdvance(node) > r * 1.7 and size > 7:
                size -= 1
                f = self._font(size, True)
                fm = QFontMetrics(f)
            p.setFont(f)
            p.setPen(text_on(col))
            p.drawText(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r), Qt.AlignCenter, node)

            if self.zoom > 0.45:
                d = a.distances.get(node, float('inf'))
                if d != float('inf'):
                    p.setFont(self._font(11, True))
                    fm = QFontMetrics(p.font())
                    text = fmt_num(d)
                    tw = fm.horizontalAdvance(text) + 14
                    rect = QRectF(c.x() - tw / 2, c.y() - r - 25, tw, 19)
                    p.setPen(QPen(with_alpha(THEME['accent2'], 150), 1))
                    p.setBrush(QColor(10, 13, 19, 238))
                    p.drawRoundedRect(rect, 9, 9)
                    p.setPen(QColor(THEME['accent2']))
                    p.drawText(rect, Qt.AlignCenter, text)

                tag = "СТАРТ" if node == a.start_node else ("ФИНИШ" if node == a.end_node else None)
                if tag:
                    p.setFont(self._font(9, True))
                    p.setPen(QColor(THEME['n_start'] if node == a.start_node else THEME['n_end']))
                    p.drawText(QRectF(c.x() - 40, c.y() + r + 3, 80, 14), Qt.AlignCenter, tag)

    # ── HUD ─────────────────────────────────────────────────────────
    def _panel(self, p, rect, radius=12):
        p.setPen(QPen(QColor(THEME['border']), 1))
        p.setBrush(QColor(18, 23, 31, 228))
        p.drawRoundedRect(rect, radius, radius)

    def draw_hud(self, p):
        a = self.app
        x, y, w = 16, 16, 310
        pad = 14
        algo = a.current_algorithm.get_name() if a.current_algorithm else "—"
        step = max(0, a.current_history_index)

        # текст статуса
        status_color = QColor(THEME['muted'])
        lines = []
        if a.algorithm_finished and a.current_algorithm:
            res = a.current_algorithm.get_result() if a.current_algorithm.is_finished() else None
            if res and res['success'] and res['path']:
                lines.append(("Путь найден", QColor(THEME['n_path']), True))
                lines.append((" → ".join(res['path']), QColor(THEME['text']), False))
                lines.append((f"Длина: {fmt_num(res['distance'])}", QColor(THEME['accent2']), True))
            else:
                msg = a.algorithm_result or "Путь не найден"
                lines.append((msg, QColor(THEME['danger']), True))
        else:
            if step == 0:
                lines.append(("Нажмите Пробел или ▶ для запуска", status_color, False))
            else:
                desc = a.history[a.current_history_index].get('description', '') if a.history else ''
                lines.append((desc, status_color, False))

        inner_w = w - 2 * pad
        body_h = 0
        measured = []
        for text, color, bold in lines:
            f = self._font(12, bold)
            fm = QFontMetrics(f)
            br = fm.boundingRect(QRect(0, 0, inner_w, 2000), qflags(Qt.TextWordWrap), text)
            measured.append((text, color, f, br.height()))
            body_h += br.height() + 4

        h = pad + 20 + 6 + 22 + 8 + body_h + pad - 4
        self._panel(p, QRectF(x, y, w, h))

        cy = y + pad
        p.setFont(self._font(14, True))
        p.setPen(QColor(THEME['text']))
        p.drawText(QRectF(x + pad, cy, inner_w, 20), Qt.AlignLeft | Qt.AlignVCenter, algo)
        p.setFont(self._font(11))
        p.setPen(QColor(THEME['muted']))
        p.drawText(QRectF(x + pad, cy, inner_w, 20), Qt.AlignRight | Qt.AlignVCenter, f"шаг {step}")

        cy += 26
        p.setFont(self._font(13, True))
        s_txt = a.start_node or "—"
        e_txt = a.end_node or "—"
        fm = QFontMetrics(p.font())
        cx = x + pad
        p.setPen(QColor(THEME['n_start']))
        p.drawText(QRectF(cx, cy, 200, 22), Qt.AlignLeft | Qt.AlignVCenter, s_txt)
        cx += fm.horizontalAdvance(s_txt) + 8
        p.setPen(QColor(THEME['faint']))
        p.drawText(QRectF(cx, cy, 30, 22), Qt.AlignLeft | Qt.AlignVCenter, "→")
        cx += fm.horizontalAdvance("→") + 8
        p.setPen(QColor(THEME['n_end']))
        p.drawText(QRectF(cx, cy, 200, 22), Qt.AlignLeft | Qt.AlignVCenter, e_txt)

        cy += 30
        for text, color, f, th in measured:
            p.setFont(f)
            p.setPen(color)
            p.drawText(QRectF(x + pad, cy, inner_w, th + 2), qflags(Qt.TextWordWrap, Qt.AlignLeft, Qt.AlignTop), text)
            cy += th + 4

    def draw_legend(self, p):
        items = [
            ("Старт", THEME['n_start']), ("Финиш", THEME['n_end']),
            ("Текущий", THEME['n_current']), ("Посещён", THEME['n_visited']),
            ("Путь", THEME['n_path']), ("Не посещён", THEME['n_idle'])
        ]
        f = self._font(12)
        fm = QFontMetrics(f)
        total = 18
        for text, _ in items:
            total += 10 + 6 + fm.horizontalAdvance(text) + 16
        h = 34
        x, y = 16, self.height() - h - 16
        if x + total > self.zoombar.x() - 10:
            return
        self._panel(p, QRectF(x, y, total, h), 17)
        p.setFont(f)
        cx = x + 16
        for text, color in items:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(color))
            p.drawEllipse(QPointF(cx + 5, y + h / 2), 5, 5)
            cx += 16
            p.setPen(QColor(THEME['muted']))
            tw = fm.horizontalAdvance(text)
            p.drawText(QRectF(cx, y, tw + 4, h), Qt.AlignLeft | Qt.AlignVCenter, text)
            cx += tw + 16

    # ── мышь ────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        pos = event.position()
        if event.button() == Qt.LeftButton:
            node = self.node_at(pos)
            if node:
                self.drag_node = node
                self.press_pos = pos
                self.drag_moved = False
            else:
                self.panning = True
                self.pan_last = pos
                self.setCursor(Qt.ClosedHandCursor)
        elif event.button() in (Qt.MiddleButton, Qt.RightButton):
            self.panning = True
            self.pan_last = pos
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        pos = event.position()
        if self.drag_node:
            if not self.drag_moved:
                d = pos - self.press_pos
                if math.hypot(d.x(), d.y()) > 4:
                    self.drag_moved = True
                    self.setCursor(Qt.ClosedHandCursor)
            if self.drag_moved:
                w = self.to_world(pos)
                self.app.positions[self.drag_node] = (w.x(), w.y())
                self.update()
        elif self.panning:
            d = pos - self.pan_last
            self.view_center -= QPointF(d.x() / self.zoom, d.y() / self.zoom)
            self.pan_last = pos
            self.update()
        else:
            node = self.node_at(pos)
            if node != self.hover_node:
                self.hover_node = node
                self.setCursor(Qt.PointingHandCursor if node else Qt.ArrowCursor)
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drag_node:
            node = self.drag_node
            moved = self.drag_moved
            self.drag_node = None
            self.drag_moved = False
            self.setCursor(Qt.PointingHandCursor)
            if not moved:
                shift = bool(event.modifiers() & Qt.ShiftModifier)
                self.app.handle_node_click(node, shift)
            self.update()
        if event.button() in (Qt.LeftButton, Qt.MiddleButton, Qt.RightButton) and self.panning:
            self.panning = False
            self.setCursor(Qt.PointingHandCursor if self.hover_node else Qt.ArrowCursor)

    def leaveEvent(self, event):
        if self.hover_node is not None:
            self.hover_node = None
            self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta == 0:
            return
        self.zoom_by(1.12 ** (delta / 120.0), event.position())


# ════════════════════════════════════════════════════════════════════
#  Главное окно
# ════════════════════════════════════════════════════════════════════
class ModernGraphVisualizer(GraphGeneratorsMixin, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Graph Visualizer — алгоритмы кратчайшего пути")
        self.resize(1440, 900)
        self.setMinimumSize(1180, 720)
        self.setWindowIcon(QIcon(make_logo(64)))

        self.current_theme = THEME
        self.apply_theme()

        self.graph = {}
        self.directed = False
        self.positions = {}
        self.original_positions = {}
        self.start_node = None
        self.end_node = None

        self.distances = {}
        self.visited = set()
        self.previous = {}
        self.current_node = None
        self.final_path = None
        self.algorithm_finished = False
        self.algorithm_result = ""
        self.active_edges = []
        self.iteration = 0
        self.edge_index = 0

        self.history = []
        self.current_history_index = -1
        self.pause = True
        self.animation_speed = 500
        self._first_show = True

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.auto_step)

        self.algorithm_manager = AlgorithmPluginManager()
        self.current_algorithm = None

        self.setup_ui()
        self.initialize_default_graph()
        self.initialize_algorithm()
        self.setup_shortcuts()
        self.update_all()

    # ── тема ────────────────────────────────────────────────────────
    def apply_theme(self):
        T = self.current_theme
        pal = QPalette()
        pal.setColor(QPalette.Window, QColor(T['bg']))
        pal.setColor(QPalette.WindowText, QColor(T['text']))
        pal.setColor(QPalette.Base, QColor(T['card']))
        pal.setColor(QPalette.AlternateBase, QColor(T['card_hi']))
        pal.setColor(QPalette.ToolTipBase, QColor(T['card_hi']))
        pal.setColor(QPalette.ToolTipText, QColor(T['text']))
        pal.setColor(QPalette.Text, QColor(T['text']))
        pal.setColor(QPalette.Button, QColor(T['card_hi']))
        pal.setColor(QPalette.ButtonText, QColor(T['text']))
        pal.setColor(QPalette.BrightText, Qt.red)
        pal.setColor(QPalette.Link, QColor(T['accent']))
        pal.setColor(QPalette.Highlight, QColor(T['accent']))
        pal.setColor(QPalette.HighlightedText, Qt.white)
        QApplication.setPalette(pal)
        QApplication.instance().setStyleSheet(build_stylesheet(T))

    # ── построение интерфейса ───────────────────────────────────────
    def setup_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self.create_top_bar())

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        self.canvas_widget = GraphCanvas(self)
        splitter.addWidget(self.canvas_widget)
        splitter.addWidget(self.create_sidebar())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setSizes([1000, 420])
        root.addWidget(splitter, 1)

        self.setCentralWidget(central)
        self.create_status_bar()

    def make_card(self, title):
        card = QFrame()
        card.setObjectName("card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 14)
        lay.setSpacing(10)
        label = QLabel(title.upper())
        label.setObjectName("cardTitle")
        lay.addWidget(label)
        return card, lay

    def make_segment(self, buttons):
        frame = QFrame()
        frame.setObjectName("segment")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(3, 3, 3, 3)
        lay.setSpacing(2)
        group = QButtonGroup(frame)
        group.setExclusive(True)
        for b in buttons:
            b.setObjectName("seg")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setFocusPolicy(Qt.NoFocus)
            group.addButton(b)
            lay.addWidget(b)
        frame._group = group
        return frame

    def make_icon_button(self, kind, tooltip, callback, object_name="iconbtn", icon_color=None, size=20):
        btn = QPushButton()
        btn.setObjectName(object_name)
        btn.setIcon(make_icon(kind, icon_color or THEME['text'], size))
        btn.setIconSize(QSize(size, size))
        btn.setToolTip(tooltip)
        btn.setFocusPolicy(Qt.NoFocus)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(callback)
        return btn

    def create_top_bar(self):
        bar = QFrame()
        bar.setObjectName("topbar")
        bar.setFixedHeight(70)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(18, 0, 18, 0)
        lay.setSpacing(14)

        # бренд
        logo = QLabel()
        logo.setPixmap(make_logo(38))
        logo.setFixedSize(38, 38)
        lay.addWidget(logo)
        brand = QVBoxLayout()
        brand.setSpacing(0)
        title = QLabel("Graph Visualizer")
        title.setObjectName("brand")
        sub = QLabel("Алгоритмы кратчайшего пути")
        sub.setObjectName("brandSub")
        brand.addStretch()
        brand.addWidget(title)
        brand.addWidget(sub)
        brand.addStretch()
        lay.addLayout(brand)
        lay.addStretch(1)

        # выбор алгоритма
        self.dijkstra_radio = QPushButton("Дейкстра")
        self.bellman_radio = QPushButton("Беллман–Форд")
        lay.addWidget(self.make_segment([self.dijkstra_radio, self.bellman_radio]))
        self.dijkstra_radio.clicked.connect(lambda: self.on_algorithm_changed('dijkstra'))
        self.bellman_radio.clicked.connect(lambda: self.on_algorithm_changed('bellman'))
        lay.addSpacing(10)

        # управление воспроизведением
        self.step_back_btn = self.make_icon_button('prev', "Шаг назад (←)", self.step_backward)
        self.pause_btn = self.make_icon_button('play', "Старт (Пробел)", self.toggle_pause,
                                               object_name="playbtn", icon_color="#ffffff", size=22)
        self.step_forward_btn = self.make_icon_button('next', "Шаг вперёд (→)", self.step_forward)
        self.restart_btn = self.make_icon_button('reset', "Сбросить (R)", self.restart)
        for b in (self.step_back_btn, self.pause_btn, self.step_forward_btn, self.restart_btn):
            lay.addWidget(b)
        lay.addStretch(1)

        # файл / справка
        self.load_btn = QPushButton("  Загрузить граф")
        self.load_btn.setIcon(make_icon('open', THEME['text'], 18))
        self.load_btn.setIconSize(QSize(18, 18))
        self.load_btn.setCursor(Qt.PointingHandCursor)
        self.load_btn.setFocusPolicy(Qt.NoFocus)
        self.load_btn.setToolTip("Загрузить граф из .txt файла (L)")
        self.load_btn.clicked.connect(self.load_graph_from_file)
        lay.addWidget(self.load_btn)

        help_btn = QPushButton("?")
        help_btn.setObjectName("iconbtn")
        help_btn.setToolTip("Справка и горячие клавиши (H)")
        help_btn.setFocusPolicy(Qt.NoFocus)
        help_btn.setCursor(Qt.PointingHandCursor)
        help_btn.clicked.connect(self.show_shortcuts_help)
        lay.addWidget(help_btn)

        return bar

    def create_sidebar(self):
        side = QWidget()
        side.setObjectName("sidebar")
        side.setMinimumWidth(390)
        side.setMaximumWidth(520)
        lay = QVBoxLayout(side)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(12)

        # — маршрут —
        card, cl = self.make_card("Маршрут")
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)
        lbl_s = QLabel("Старт")
        lbl_s.setObjectName("muted")
        lbl_e = QLabel("Финиш")
        lbl_e.setObjectName("muted")
        self.start_combo = QComboBox()
        self.end_combo = QComboBox()
        for combo in (self.start_combo, self.end_combo):
            combo.setFocusPolicy(Qt.NoFocus)
            combo.currentTextChanged.connect(self.on_node_selection_changed)
        arrow = QLabel("→")
        arrow.setObjectName("arrow")
        arrow.setAlignment(Qt.AlignCenter)
        grid.addWidget(lbl_s, 0, 0)
        grid.addWidget(lbl_e, 0, 2)
        grid.addWidget(self.start_combo, 1, 0)
        grid.addWidget(arrow, 1, 1)
        grid.addWidget(self.end_combo, 1, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(2, 1)
        cl.addLayout(grid)
        hint = QLabel("Или кликните по узлам на холсте. Shift+клик — задать финиш.")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        cl.addWidget(hint)
        lay.addWidget(card)

        # — воспроизведение —
        card, cl = self.make_card("Воспроизведение")
        row = QHBoxLayout()
        lbl = QLabel("Прогресс")
        lbl.setObjectName("muted")
        self.progress_label = QLabel("шаг 0 · 0%")
        self.progress_label.setObjectName("value")
        self.progress_label.setAlignment(Qt.AlignRight)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(self.progress_label)
        cl.addLayout(row)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        cl.addWidget(self.progress_bar)

        row = QHBoxLayout()
        lbl = QLabel("Скорость")
        lbl.setObjectName("muted")
        self.speed_label = QLabel("")
        self.speed_label.setObjectName("value")
        self.speed_label.setAlignment(Qt.AlignRight)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(self.speed_label)
        cl.addLayout(row)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(0, 5)
        self.speed_slider.setValue(2)
        self.speed_slider.setFocusPolicy(Qt.NoFocus)
        self.speed_slider.valueChanged.connect(self.change_speed)
        cl.addWidget(self.speed_slider)
        self.change_speed(2)
        lay.addWidget(card)

        # — граф / генератор —
        card, cl = self.make_card("Граф")
        self.undirected_radio = QPushButton("Неориентированный")
        self.directed_radio = QPushButton("Ориентированный")
        seg = self.make_segment([self.undirected_radio, self.directed_radio])
        for b in (self.undirected_radio, self.directed_radio):
            b.setStyleSheet("padding: 7px 8px;")
        self.undirected_radio.setChecked(not self.directed)
        self.directed_radio.setChecked(self.directed)
        self.directed_radio.toggled.connect(self.on_graph_type_toggled)
        cl.addWidget(seg)

        self.graph_type_combo = QComboBox()
        self.graph_type_combo.setFocusPolicy(Qt.NoFocus)
        self.graph_type_combo.addItems([
            "Связный случайный", "Полный граф", "Дерево",
            "Решётка", "Двудольный", "Звёздчатый"
        ])
        self.complexity_combo = QComboBox()
        self.complexity_combo.setFocusPolicy(Qt.NoFocus)
        self.complexity_combo.addItems([
            "Лёгкий (4-6 узлов)", "Средний (6-9 узлов)", "Сложный (9-12 узлов)"
        ])
        self.complexity_combo.setCurrentText("Средний (6-9 узлов)")
        combos = QHBoxLayout()
        combos.setSpacing(8)
        combos.addWidget(self.graph_type_combo, 1)
        combos.addWidget(self.complexity_combo, 1)
        cl.addLayout(combos)

        self.random_btn = QPushButton("  Сгенерировать граф")
        self.random_btn.setObjectName("primary")
        self.random_btn.setIcon(make_icon('dice', '#ffffff', 18))
        self.random_btn.setIconSize(QSize(18, 18))
        self.random_btn.setCursor(Qt.PointingHandCursor)
        self.random_btn.setFocusPolicy(Qt.NoFocus)
        self.random_btn.setToolTip("Сгенерировать случайный граф (G)")
        self.random_btn.clicked.connect(self.generate_random_graph)
        cl.addWidget(self.random_btn)
        lay.addWidget(card)

        # — вкладки с данными —
        self.tabs = QTabWidget()
        self.tabs.setFocusPolicy(Qt.NoFocus)

        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["Вершина", "Расстояние", "Путь"])
        self.weights_tree = QTreeWidget()
        self.weights_tree.setHeaderLabels(["Ребро", "Вес"])
        for tree in (self.results_tree, self.weights_tree):
            tree.setRootIsDecorated(False)
            tree.setAlternatingRowColors(True)
            tree.setUniformRowHeights(True)
            tree.setFocusPolicy(Qt.NoFocus)
            tree.setSelectionMode(QAbstractItemView.NoSelection)
        self.results_tree.setColumnWidth(0, 80)
        self.results_tree.setColumnWidth(1, 100)
        self.weights_tree.setColumnWidth(0, 160)

        self.log_list = QListWidget()
        self.log_list.setAlternatingRowColors(True)
        self.log_list.setFocusPolicy(Qt.NoFocus)
        self.log_list.setWordWrap(True)
        self.log_list.setSelectionMode(QAbstractItemView.NoSelection)

        self.tabs.addTab(self.results_tree, "Результаты")
        self.tabs.addTab(self.weights_tree, "Рёбра")
        self.tabs.addTab(self.log_list, "Журнал шагов")
        self.tabs.setMinimumHeight(220)
        lay.addWidget(self.tabs, 1)

        return side

    def create_status_bar(self):
        self.status_bar = self.statusBar()
        self.status_bar.setSizeGripEnabled(False)
        self.status_label = QLabel("Готов к работе. Загрузите граф или сгенерируйте случайный.")
        self.status_bar.addWidget(self.status_label, 1)
        self.graph_info_label = QLabel("")
        self.status_bar.addPermanentWidget(self.graph_info_label)

    def notify(self, text, kind="info"):
        colors = {
            'info': THEME['muted'], 'success': THEME['success'],
            'warning': THEME['warning'], 'error': THEME['danger']
        }
        self.status_label.setStyleSheet(f"color: {colors.get(kind, THEME['muted'])};")
        self.status_label.setText(text)

    def showEvent(self, event):
        super().showEvent(event)
        if self._first_show:
            self._first_show = False
            QTimer.singleShot(60, self.canvas_widget.fit_view)

    # ── тип графа ───────────────────────────────────────────────────
    def on_graph_type_toggled(self, checked=None):
        new_directed = self.directed_radio.isChecked()
        if new_directed == self.directed:
            return
        self.directed = new_directed
        if not self.directed:
            for u in list(self.graph.keys()):
                for v, w in list(self.graph[u].items()):
                    self.graph.setdefault(v, {}).setdefault(u, w)
            self.notify("Граф стал неориентированным: недостающие обратные рёбра добавлены.", "info")
        else:
            self.notify("Граф стал ориентированным. Рёбра пока двусторонние — сгенерируйте граф заново "
                        "или загрузите файл с DIRECTED.", "info")
        self.refresh_graph_views()
        if self.start_node and self.end_node:
            self.restart()
        else:
            self.canvas_widget.update()

    def update_graph_type_controls(self):
        for b in (self.directed_radio, self.undirected_radio):
            b.blockSignals(True)
        self.directed_radio.setChecked(self.directed)
        self.undirected_radio.setChecked(not self.directed)
        for b in (self.directed_radio, self.undirected_radio):
            b.blockSignals(False)

    # ── таблицы ─────────────────────────────────────────────────────
    def refresh_graph_views(self):
        self.update_weights_table()
        kind = "ориентированный" if self.directed else "неориентированный"
        self.graph_info_label.setText(
            f"{len(self.positions)} узлов · {self.get_edge_count()} рёбер · {kind}")

    def update_weights_table(self):
        self.weights_tree.clear()
        if not self.graph:
            return
        symbol = "→" if self.directed else "—"
        for u, v, weight in self.iter_unique_edges():
            item = QTreeWidgetItem([f"{u}  {symbol}  {v}", fmt_num(weight)])
            item.setTextAlignment(1, Qt.AlignCenter)
            if weight < 0:
                item.setForeground(0, QColor(THEME['danger']))
                item.setForeground(1, QColor(THEME['danger']))
            self.weights_tree.addTopLevelItem(item)

    def update_results_table(self):
        self.results_tree.clear()
        if not self.distances:
            return

        path_nodes = set(self.final_path) if self.final_path else set()
        for node in sorted(self.positions.keys()):
            distance = self.distances.get(node, float('inf'))
            distance_text = fmt_num(distance)

            path = []
            current = node
            max_steps = len(self.positions)
            while current != self.start_node and current in self.previous and max_steps > 0:
                path.append(current)
                current = self.previous[current]
                max_steps -= 1

            if max_steps > 0 and current == self.start_node:
                path.append(self.start_node)
                path.reverse()
                path_text = " → ".join(path)
            else:
                path_text = "—"

            item = QTreeWidgetItem([node, distance_text, path_text])
            item.setTextAlignment(1, Qt.AlignCenter)

            if node == self.start_node:
                color = THEME['n_start']
            elif node == self.end_node:
                color = THEME['n_end']
            elif node in path_nodes:
                color = THEME['n_path']
            elif node in self.visited:
                color = THEME['n_visited']
            else:
                color = THEME['muted']
            f = item.font(0)
            f.setBold(node in (self.start_node, self.end_node) or node in path_nodes)
            for col in range(3):
                item.setForeground(col, QColor(color if col != 1 or distance != float('inf') else THEME['faint']))
                item.setFont(col, f)
            self.results_tree.addTopLevelItem(item)

    def update_log(self):
        n = self.current_history_index + 1
        while self.log_list.count() > n:
            self.log_list.takeItem(self.log_list.count() - 1)
        while self.log_list.count() < n:
            i = self.log_list.count()
            desc = self.history[i].get('description', '') or 'Шаг алгоритма'
            item = QListWidgetItem(f"{i:>3}   {desc}")
            if "ОШИБКА" in desc:
                item.setForeground(QColor(THEME['danger']))
            elif "завершён" in desc:
                item.setForeground(QColor(THEME['success']))
            self.log_list.addItem(item)
        if n > 0:
            self.log_list.scrollToBottom()

    def update_progress(self):
        value = 0
        alg = self.current_algorithm
        if not self.positions or not alg:
            value = 0
        elif self.algorithm_finished:
            value = 100
        elif isinstance(alg, DijkstraPlugin):
            value = int(len(self.visited) / max(1, len(self.positions)) * 100)
        elif isinstance(alg, BellmanFordPlugin):
            total = len(self.positions)
            if self.iteration < total - 1:
                value = int(80 * self.iteration / max(1, total - 1))
            else:
                total_edges = len(alg.edges)
                value = 80 + (int(20 * self.edge_index / total_edges) if total_edges else 20)
        value = max(0, min(100, value))
        self.progress_bar.setValue(value)
        self.progress_label.setText(f"шаг {max(0, self.current_history_index)} · {value}%")

    def update_all(self):
        self.update_progress()
        self.update_results_table()
        self.update_log()
        self.canvas_widget.update()

    # ── горячие клавиши ─────────────────────────────────────────────
    def setup_shortcuts(self):
        bindings = [
            ("Space", self.toggle_pause),
            ("Right", self.step_forward),
            ("Left", self.step_backward),
            ("R", self.restart),
            ("F", self.toggle_fullscreen),
            ("=", self.faster),
            ("+", self.faster),
            ("-", self.slower),
            ("I", self.reset_view),
            ("G", self.generate_random_graph),
            ("L", self.load_graph_from_file),
            ("1", lambda: self.set_algorithm(1)),
            ("2", lambda: self.set_algorithm(2)),
            ("H", self.show_shortcuts_help),
            ("Escape", lambda: self.showNormal() if self.isFullScreen() else None),
        ]
        self._shortcuts = []
        for seq, handler in bindings:
            sc = QShortcut(QKeySequence(seq), self)
            sc.activated.connect(handler)
            self._shortcuts.append(sc)

    def set_algorithm(self, algorithm_num):
        if algorithm_num == 1:
            self.on_algorithm_changed('dijkstra', force=True)
        else:
            self.on_algorithm_changed('bellman', force=True)

    def faster(self):
        self.speed_slider.setValue(min(5, self.speed_slider.value() + 1))

    def slower(self):
        self.speed_slider.setValue(max(0, self.speed_slider.value() - 1))

    def reset_view(self):
        self.canvas_widget.fit_view()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def show_shortcuts_help(self):
        rows = [
            ("Пробел", "Старт / пауза"), ("← / →", "Шаг назад / вперёд"),
            ("R", "Перезапуск алгоритма"), ("+ / −", "Быстрее / медленнее"),
            ("1 / 2", "Дейкстра / Беллман–Форд"), ("G", "Сгенерировать граф"),
            ("L", "Загрузить граф из файла"), ("I", "Вписать граф в окно"),
            ("F", "Полный экран"), ("H", "Эта справка"),
        ]
        mouse = [
            ("Клик по узлу", "Выбор старта / финиша"), ("Shift + клик", "Задать финиш"),
            ("Перетаскивание узла", "Переместить узел"), ("Колесо мыши", "Масштаб к курсору"),
            ("ПКМ / СКМ / фон", "Сдвиг холста"),
        ]

        def table(items):
            return "".join(
                f"<tr><td style='padding:3px 18px 3px 0; color:{THEME['accent_hi']}; font-weight:600;'>{k}</td>"
                f"<td style='padding:3px 0;'>{v}</td></tr>" for k, v in items)

        html = (
            f"<h3 style='margin:0 0 6px 0;'>Клавиатура</h3><table>{table(rows)}</table>"
            f"<h3 style='margin:14px 0 6px 0;'>Мышь</h3><table>{table(mouse)}</table>"
            f"<h3 style='margin:14px 0 6px 0;'>Формат файла графа (.txt)</h3>"
            f"<pre style='margin:0; color:{THEME['muted']};'>"
            "# комментарий\nDIRECTED        (или UNDIRECTED)\nSTART A\nEND D\n"
            "A B 4           (вершина вершина вес)\nB C -2</pre>"
        )
        box = QMessageBox(self)
        box.setWindowTitle("Справка")
        box.setTextFormat(Qt.RichText)
        box.setText(html)
        box.exec()

    # ── выбор алгоритма и узлов ─────────────────────────────────────
    def on_algorithm_changed(self, key, force=False):
        if key == 'dijkstra' and self.check_negative_weights():
            QMessageBox.warning(
                self, "Предупреждение",
                "Алгоритм Дейкстры не поддерживает отрицательные веса!\n"
                "Переключено на алгоритм Беллмана–Форда."
            )
            self.bellman_radio.setChecked(True)
        elif force:
            (self.dijkstra_radio if key == 'dijkstra' else self.bellman_radio).setChecked(True)
        self.restart()

    def on_node_selection_changed(self, text):
        start_text = self.start_combo.currentText()
        end_text = self.end_combo.currentText()
        if not start_text or not end_text:
            return
        if start_text == self.start_node and end_text == self.end_node:
            return
        if start_text == end_text:
            return
        self.apply_selection()

    def handle_node_click(self, node, shift=False):
        if shift and self.start_node and node != self.start_node:
            self.end_node = node
            self.update_selection_comboboxes()
            self.restart()
            return
        if not self.start_node:
            self.start_node = node
        elif not self.end_node and node != self.start_node:
            self.end_node = node
            self.update_selection_comboboxes()
            self.restart()
            return
        else:
            self.start_node = node
            self.end_node = None
            self.notify(f"Старт: {node}. Теперь выберите конечный узел.", "info")
        self.update_selection_comboboxes()
        self.canvas_widget.update()

    def update_selection_comboboxes(self):
        if not self.positions:
            return
        nodes = list(self.positions.keys())
        self.start_combo.blockSignals(True)
        self.end_combo.blockSignals(True)
        self.start_combo.clear()
        self.end_combo.clear()
        self.start_combo.addItems(nodes)
        self.end_combo.addItems(nodes)
        if self.start_node:
            self.start_combo.setCurrentText(self.start_node)
        if self.end_node:
            self.end_combo.setCurrentText(self.end_node)
        self.start_combo.blockSignals(False)
        self.end_combo.blockSignals(False)

    def apply_selection(self):
        start = self.start_combo.currentText()
        end = self.end_combo.currentText()
        if not start or not end:
            QMessageBox.warning(self, "Предупреждение", "Выберите начальную и конечную точки")
            return
        if start == end:
            QMessageBox.warning(self, "Предупреждение", "Начальная и конечная точки не могут совпадать")
            return
        self.start_node = start
        self.end_node = end
        self.restart()

    def check_negative_weights(self):
        for neighbors in self.graph.values():
            for weight in neighbors.values():
                if weight < 0:
                    return True
        return False

    def get_node_color(self, node):
        if node == self.start_node:
            return THEME['n_start']
        if node == self.end_node:
            return THEME['n_end']
        if node == self.current_node:
            return THEME['n_current']
        if self.final_path and node in self.final_path:
            return THEME['n_path']
        if node in self.visited:
            return THEME['n_visited']
        return THEME['n_idle']

    def path_edge_set(self):
        edges = set()
        if self.final_path:
            for a, b in zip(self.final_path, self.final_path[1:]):
                edges.add((a, b))
        return edges

    def change_speed(self, value):
        names = ["Очень медленно", "Медленно", "Средняя", "Быстро", "Очень быстро", "Максимум"]
        delays = [2000, 1000, 500, 200, 50, 0]
        self.animation_speed = delays[value]
        self.speed_label.setText(f"{names[value]} · {delays[value]} мс/шаг")
        if hasattr(self, 'animation_timer') and self.animation_timer.isActive():
            self.animation_timer.setInterval(self.animation_speed)

    # ── граф: данные ────────────────────────────────────────────────
    def iter_unique_edges(self):
        if self.directed:
            for u, neighbors in self.graph.items():
                for v, weight in neighbors.items():
                    yield u, v, weight
            return

        seen = set()
        for u, neighbors in self.graph.items():
            for v, weight in neighbors.items():
                edge_key = tuple(sorted((u, v)))
                if edge_key in seen:
                    continue
                seen.add(edge_key)
                yield u, v, weight

    def add_edge(self, u, v, weight, bidirectional=None):
        if bidirectional is None:
            bidirectional = not self.directed
        self.graph.setdefault(u, {})
        self.graph.setdefault(v, {})
        self.graph[u][v] = weight
        if bidirectional:
            self.graph[v][u] = weight

    def has_edge(self, u, v):
        return u in self.graph and v in self.graph[u]

    def get_all_nodes(self):
        nodes = set(self.graph.keys())
        for neighbors in self.graph.values():
            nodes.update(neighbors.keys())
        return nodes

    def get_edge_count(self):
        return sum(1 for _ in self.iter_unique_edges())

    def initialize_default_graph(self):
        edges = [
            ('A', 'B', 4), ('B', 'C', 3), ('C', 'D', 5),
            ('D', 'E', 2), ('E', 'F', 6), ('F', 'A', 4),
            ('B', 'E', 7), ('C', 'F', 3), ('A', 'D', 8),
            ('G', 'A', 2), ('G', 'B', 5), ('H', 'C', 4),
            ('H', 'D', 3), ('I', 'E', 6), ('I', 'F', 2),
            ('G', 'H', 8), ('H', 'I', 5), ('I', 'G', 7),
        ]

        self.graph = {}
        for u, v, weight in edges:
            self.add_edge(u, v, weight)

        center_x, center_y = 400, 300
        self.positions = {}
        inner_nodes = ['A', 'B', 'C', 'D', 'E', 'F']
        for i, node in enumerate(inner_nodes):
            angle = 2 * math.pi * i / len(inner_nodes)
            self.positions[node] = (center_x + 120 * math.cos(angle), center_y + 120 * math.sin(angle))

        middle_nodes = ['G', 'H', 'I']
        for i, node in enumerate(middle_nodes):
            angle = 2 * math.pi * i / len(middle_nodes) - math.pi / 6
            self.positions[node] = (center_x + 250 * math.cos(angle), center_y + 250 * math.sin(angle))

        self.start_node = 'G'
        self.end_node = 'D'
        self.original_positions = dict(self.positions)
        self.update_selection_comboboxes()
        self.refresh_graph_views()

        negative = self.check_negative_weights()
        self.dijkstra_radio.setChecked(not negative)
        self.bellman_radio.setChecked(negative)

    def calculate_positions(self, nodes=None):
        if nodes is None:
            nodes = sorted(self.get_all_nodes())
        self.positions = compute_layout(list(nodes), self.graph)
        self.original_positions = dict(self.positions)

    # ── загрузка из файла ───────────────────────────────────────────
    def load_graph_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл с графом", "",
            "Текстовые файлы (*.txt);;Все файлы (*)"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            edges = []
            start_node = None
            end_node = None
            file_directed = None

            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                upper_line = line.upper()
                if upper_line == 'DIRECTED':
                    file_directed = True
                    continue
                elif upper_line == 'UNDIRECTED':
                    file_directed = False
                    continue

                if upper_line.startswith('START') and len(line.split()) == 2:
                    start_node = line.split()[1]
                    continue
                elif upper_line.startswith('END') and len(line.split()) == 2:
                    end_node = line.split()[1]
                    continue

                parts = line.split()
                if len(parts) >= 3:
                    u, v = parts[0], parts[1]
                    try:
                        weight = float(parts[2])
                        edges.append((u, v, weight))
                    except ValueError:
                        print(f"Ошибка в весе ребра: {line}")

            if not edges:
                QMessageBox.critical(self, "Ошибка", "Файл не содержит корректных рёбер графа")
                return

            if file_directed is not None:
                self.directed = file_directed
                self.update_graph_type_controls()

            self.graph = {}
            for u, v, weight in edges:
                self.add_edge(u, v, weight)

            if start_node:
                self.graph.setdefault(start_node, {})
            if end_node:
                self.graph.setdefault(end_node, {})

            self.calculate_positions()

            keys = list(self.positions.keys())
            self.start_node = start_node if start_node else keys[0]
            self.end_node = end_node if end_node else keys[-1]
            self.update_selection_comboboxes()

            has_negative = self.check_negative_weights()
            if has_negative and self.dijkstra_radio.isChecked():
                QMessageBox.warning(
                    self, "Предупреждение",
                    "Обнаружены отрицательные веса!\n"
                    "Алгоритм Дейкстры с ними не работает — выбран алгоритм Беллмана–Форда."
                )
                self.bellman_radio.setChecked(True)

            self.refresh_graph_views()
            self.restart()
            self.canvas_widget.fit_view()

            kind = "ориентированный" if self.directed else "неориентированный"
            msg = (f"Граф загружен ({kind}): {len(self.positions)} узлов, "
                   f"{self.get_edge_count()} рёбер. Старт {self.start_node}, финиш {self.end_node}.")
            if has_negative:
                msg += "  ⚠ Есть отрицательные веса."
            self.notify(msg, "warning" if has_negative else "success")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл:\n{str(e)}")

    # ── случайная генерация ─────────────────────────────────────────
    def generate_random_graph(self):
        graph_type = self.graph_type_combo.currentText()
        all_nodes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O']

        if graph_type == "Связный случайный":
            generated = self.generate_connected_graph(all_nodes)
        elif graph_type == "Полный граф":
            generated = self.generate_complete_graph(all_nodes)
        elif graph_type == "Дерево":
            generated = self.generate_tree_graph(all_nodes)
        elif graph_type == "Решётка":
            generated = self.generate_grid_graph(all_nodes)
        elif graph_type == "Двудольный":
            generated = self.generate_bipartite_graph(all_nodes)
        elif graph_type == "Звёздчатый":
            generated = self.generate_star_graph(all_nodes)
        else:
            generated = self.generate_connected_graph(all_nodes)

        self.graph = generated['graph']
        selected_nodes = generated['nodes']

        self.calculate_positions(sorted(selected_nodes))

        self.start_node = random.choice(selected_nodes)
        self.end_node = random.choice([n for n in selected_nodes if n != self.start_node])
        self.update_selection_comboboxes()

        has_negative = self.check_negative_weights()
        if has_negative and self.dijkstra_radio.isChecked():
            self.bellman_radio.setChecked(True)

        self.refresh_graph_views()
        self.restart()
        self.canvas_widget.fit_view()

        kind = "ориентированный" if self.directed else "неориентированный"
        msg = (f"Сгенерирован: {generated['name']} ({kind}) · {len(selected_nodes)} узлов · "
               f"{self.get_edge_count()} рёбер · {self.start_node} → {self.end_node}")
        if has_negative:
            msg += "  ⚠ есть отрицательные веса — выбран Беллман–Форд"
        self.notify(msg, "warning" if has_negative else "success")

    # ── ядро: шаги алгоритма ────────────────────────────────────────
    def initialize_algorithm(self):
        self.history = []
        self.current_history_index = -1

        if self.dijkstra_radio.isChecked():
            self.current_algorithm = self.algorithm_manager.set_current_plugin('dijkstra')
        else:
            self.current_algorithm = self.algorithm_manager.set_current_plugin('bellman')

        if self.current_algorithm and self.graph and self.start_node in self.positions:
            initial_state = self.current_algorithm.initialize(
                self.graph, self.start_node, self.positions, self.end_node
            )
            self.apply_algorithm_state(initial_state)
            self.save_state(initial_state.get('description') or "Инициализация алгоритма")

    def apply_algorithm_state(self, state):
        self.distances = state['distances']
        if 'visited' in state:
            self.visited = state['visited']
        else:
            self.visited = {n for n, d in state['distances'].items() if d != float('inf')}
        self.previous = state.get('previous', {})
        self.current_node = state.get('current_node')
        self.final_path = state.get('final_path')
        self.algorithm_finished = state.get('algorithm_finished', False)
        self.algorithm_result = state.get('algorithm_result', "")
        self.active_edges = state.get('active_edges', [])
        self.iteration = state.get('iteration', 0)
        self.edge_index = state.get('edge_index', 0)

        if self.algorithm_finished and self.current_algorithm:
            result = self.current_algorithm.get_result()
            self.algorithm_result = result['message']

    def save_state(self, description=""):
        state = {
            'distances': self.distances.copy(),
            'visited': self.visited.copy(),
            'previous': self.previous.copy(),
            'current_node': self.current_node,
            'final_path': self.final_path.copy() if self.final_path else None,
            'algorithm_finished': self.algorithm_finished,
            'algorithm_result': self.algorithm_result,
            'active_edges': list(self.active_edges),
            'iteration': self.iteration,
            'edge_index': self.edge_index,
            'description': description
        }
        self.history = self.history[:self.current_history_index + 1]
        self.history.append(state)
        self.current_history_index = len(self.history) - 1

    def restore_state(self):
        state = self.history[self.current_history_index]
        self.distances = state['distances'].copy()
        self.visited = state['visited'].copy()
        self.previous = state['previous'].copy()
        self.current_node = state['current_node']
        self.final_path = state['final_path'].copy() if state['final_path'] else None
        self.algorithm_finished = state['algorithm_finished']
        self.algorithm_result = state['algorithm_result']
        self.active_edges = list(state['active_edges'])
        self.iteration = state['iteration']
        self.edge_index = state['edge_index']

    def step_forward(self):
        if not self.history:
            return
        if self.current_history_index < len(self.history) - 1:
            self.current_history_index += 1
            self.restore_state()
        else:
            if self.algorithm_finished:
                return
            if self.current_algorithm:
                state = self.current_algorithm.execute_step()
                if state:
                    self.apply_algorithm_state(state)
                    self.save_state(state.get('description', 'Шаг алгоритма'))
        self.update_all()

    def step_backward(self):
        if self.current_history_index > 0:
            self.current_history_index -= 1
            self.restore_state()
            self.update_all()

    def set_play_state(self, playing):
        if playing:
            self.pause_btn.setIcon(make_icon('pause', '#ffffff', 22))
            self.pause_btn.setToolTip("Пауза (Пробел)")
        else:
            self.pause_btn.setIcon(make_icon('play', '#ffffff', 22))
            self.pause_btn.setToolTip("Старт (Пробел)")

    def toggle_pause(self):
        if self.pause and self.algorithm_finished and self.current_history_index == len(self.history) - 1:
            self.restart()
        self.pause = not self.pause
        if not self.pause:
            self.set_play_state(True)
            self.animation_timer.start(self.animation_speed)
        else:
            self.set_play_state(False)
            self.animation_timer.stop()

    def auto_step(self):
        if self.pause or self.algorithm_finished:
            self.animation_timer.stop()
            if self.algorithm_finished and not self.pause:
                self.pause = True
                self.set_play_state(False)
            return
        self.step_forward()
        if self.algorithm_finished:
            self.animation_timer.stop()
            self.pause = True
            self.set_play_state(False)
            self.notify(self.algorithm_result or "Алгоритм завершён.",
                        "success" if self.final_path else "error")

    def restart(self):
        self.animation_timer.stop()
        self.pause = True
        self.set_play_state(False)
        self.initialize_algorithm()
        self.update_all()
        self.notify("Алгоритм перезапущен. Нажмите ▶ или Пробел для начала.", "info")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont(FONT_FAMILY, 10))
    window = ModernGraphVisualizer()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
