import sys
import math
import heapq
import random
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QRadioButton, QGroupBox,
    QFileDialog, QMessageBox, QTreeWidget, QTreeWidgetItem,
    QSlider, QSplitter, QFrame, QProgressBar, QButtonGroup
)
from PySide6.QtCore import Qt, QTimer, QRect, QPointF
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPalette, QLinearGradient,
    QRadialGradient, QKeySequence, QShortcut, QPolygonF
)

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

    def get_current_state(self):
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

        return self.get_current_state("Инициализация: расстояния установлены в бесконечность, кроме стартовой вершины")

    def execute_step(self):
        if self.algorithm_finished or not self.queue:
            return None

        current_distance, self.current_node = heapq.heappop(self.queue)

        if self.current_node in self.visited:
            return self.get_current_state()

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

        if self.current_node == self.end_node or not self.queue:
            self.finalize_algorithm()

        description = f"Обрабатываем узел {self.current_node}"
        if updates:
            desc_updates = [f"{v}: {old:.1f}→{new:.1f}" for v, old, new in updates]
            description += f" | Обновления: {', '.join(desc_updates)}"

        return self.get_current_state(description)

    def finalize_algorithm(self):
        self.algorithm_finished = True
        self.current_node = None

        if self.end_node in self.previous and self.distances[self.end_node] != float('inf'):
            path = self.reconstruct_path(self.end_node)
            total_distance = self.distances[self.end_node]
            self.algorithm_result = f"Найден путь: {' -> '.join(path)} (длина: {total_distance})"
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
            'algorithm_result': self.algorithm_result
        }

class BellmanFordPlugin(ShortestPathAlgorithm):
    def __init__(self):
        super().__init__(
            name="Беллман-Форд",
            description="Алгоритм Беллмана-Форда для графов с отрицательными весами",
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

        if self.iteration < len(self.distances) - 1:
            if self.edge_index < len(self.edges):
                u, v, weight = self.edges[self.edge_index]
                self.current_node = u

                if self.distances[u] != float('inf') and self.distances[u] + weight < self.distances[v]:
                    old_dist = self.distances[v]
                    self.distances[v] = self.distances[u] + weight
                    self.previous[v] = u
                    self.changed = True

                    description = f"Итерация {self.iteration + 1}: {u}→{v} ({weight}) - {old_dist:.1f}→{self.distances[v]:.1f}"
                else:
                    description = f"Итерация {self.iteration + 1}: {u}→{v} ({weight}) - без изменений"

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
                    description = "Переход к проверке отрицательных циклов"

        else:
            if self.edge_index < len(self.edges):
                u, v, weight = self.edges[self.edge_index]
                self.current_node = u

                if self.distances[u] != float('inf') and self.distances[u] + weight < self.distances[v]:
                    self.algorithm_finished = True
                    self.algorithm_result = f"Обнаружен цикл отрицательного веса! {u}→{v} ({weight})"
                    description = f"ОШИБКА: {self.algorithm_result}"
                else:
                    description = f"Проверка циклов: {u}→{v} ({weight})"

                self.edge_index += 1
            else:
                self.algorithm_finished = True
                self.finalize_algorithm()
                description = "Алгоритм завершен"

        return self.get_current_state(description)

    def finalize_algorithm(self):
        if not self.algorithm_result:
            if self.end_node in self.previous and self.distances[self.end_node] != float('inf'):
                path = self.reconstruct_path(self.end_node)
                total_distance = self.distances[self.end_node]
                self.algorithm_result = f"Найден путь: {' -> '.join(path)} (длина: {total_distance})"
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
            'success': self.final_path is not None and "ОШИБКА" not in self.algorithm_result,
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
            'edge_index': self.edge_index
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

class GradientLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.gradient_pos = 0.0
        self.setMinimumHeight(40)

        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_gradient)
        self.animation_timer.start(50)

    def animate_gradient(self):
        self.gradient_pos = (self.gradient_pos + 0.02) % 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(max(0, self.gradient_pos - 0.5), QColor('#bb86fc'))
        gradient.setColorAt(self.gradient_pos, QColor('#03dac6'))
        gradient.setColorAt(min(1, self.gradient_pos + 0.5), QColor('#cf6679'))

        pen = QPen()
        pen.setBrush(QBrush(gradient))
        painter.setPen(pen)

        font = QFont("Segoe UI", 16, QFont.Bold)
        painter.setFont(font)

        painter.drawText(self.rect(), Qt.AlignCenter, self.text())

        painter.end()

class GraphCanvas(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setMinimumSize(800, 600)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        self.draw_grid(painter)

        if not self.parent.graph:
            painter.setPen(QColor(self.parent.current_theme['text']))
            painter.setFont(QFont("Arial", 16, QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter, "Граф не загружен\nНажмите 'Загрузить' или 'Случайный'")
            painter.end()
            return

        arrow_data = self.draw_edges(painter)
        self.draw_nodes(painter)
        if self.parent.directed:
            self.draw_arrows(painter, arrow_data)
        self.draw_legend(painter)

        painter.end()

    def draw_grid(self, painter):
        painter.fillRect(self.rect(), QColor(self.parent.current_theme['canvas_bg']))

        parallax_factor = 0.3
        offset_x = self.parent.pan_offset_x * parallax_factor
        offset_y = self.parent.pan_offset_y * parallax_factor

        grid_size = 50 * self.parent.zoom_level
        small_grid_size = 10 * self.parent.zoom_level

        pen_small = QPen(QColor(40, 40, 40, 30))
        pen_small.setWidth(1)
        painter.setPen(pen_small)

        start_x = (offset_x % small_grid_size) - small_grid_size
        for x in range(int(start_x), self.width(), max(1, int(small_grid_size))):
            painter.drawLine(x, 0, x, self.height())

        start_y = (offset_y % small_grid_size) - small_grid_size
        for y in range(int(start_y), self.height(), max(1, int(small_grid_size))):
            painter.drawLine(0, y, self.width(), y)

        pen_main = QPen(QColor(60, 60, 60, 50))
        pen_main.setWidth(1)
        painter.setPen(pen_main)

        start_x = (offset_x % grid_size) - grid_size
        for x in range(int(start_x), self.width(), max(1, int(grid_size))):
            painter.drawLine(x, 0, x, self.height())

        start_y = (offset_y % grid_size) - grid_size
        for y in range(int(start_y), self.height(), max(1, int(grid_size))):
            painter.drawLine(0, y, self.width(), y)

        center_x = int(self.width() // 2 + offset_x)
        center_y = int(self.height() // 2 + offset_y)

        pen_axis = QPen(QColor(80, 80, 80, 80))
        pen_axis.setWidth(2)
        painter.setPen(pen_axis)

        painter.drawLine(center_x, 0, center_x, self.height())
        painter.drawLine(0, center_y, self.width(), center_y)

    def draw_edges(self, painter):
        arrows = []
        for u, v, weight in self.parent.iter_unique_edges():
            if u in self.parent.positions and v in self.parent.positions:
                x1, y1 = self.parent.get_transformed_position(*self.parent.positions[u])
                x2, y2 = self.parent.get_transformed_position(*self.parent.positions[v])
                dx = x2 - x1
                dy = y2 - y1
                length = math.hypot(dx, dy)
                if length == 0:
                    continue
                end_x, end_y = x2, y2
                if self.parent.directed:
                    node_radius = self.parent.get_node_radius()
                    end_x = x2 - (dx / length) * node_radius
                    end_y = y2 - (dy / length) * node_radius

                pen = QPen()
                if weight < 0:
                    pen.setColor(QColor(self.parent.current_theme['danger']))
                    pen.setWidth(3)
                elif (self.parent.final_path and u in self.parent.final_path and
                      v in self.parent.final_path and
                      abs(self.parent.final_path.index(u) - self.parent.final_path.index(v)) == 1):
                    pen.setColor(QColor(self.parent.current_theme['success']))
                    pen.setWidth(4)
                else:
                    pen.setColor(QColor(self.parent.current_theme['text_secondary']))
                    pen.setWidth(2)

                painter.setPen(pen)
                painter.drawLine(int(x1), int(y1), int(end_x), int(end_y))

                if self.parent.directed:
                    arrows.append((x1, y1, end_x, end_y, QColor(pen.color())))
        return arrows

    def draw_arrows(self, painter, arrows):
        for x1, y1, end_x, end_y, color in arrows:
            self.draw_arrow_head(painter, x1, y1, end_x, end_y, color)

    def draw_arrow_head(self, painter, x1, y1, x2, y2, color):
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_length = max(12, 14 * self.parent.zoom_level)
        arrow_width = max(6, 8 * self.parent.zoom_level)

        point1 = QPointF(x2, y2)
        point2 = QPointF(
            x2 - arrow_length * math.cos(angle - math.pi / 8),
            y2 - arrow_length * math.sin(angle - math.pi / 8)
        )
        point3 = QPointF(
            x2 - arrow_length * math.cos(angle + math.pi / 8),
            y2 - arrow_length * math.sin(angle + math.pi / 8)
        )

        polygon = QPolygonF([point1, point2, point3])
        painter.setBrush(QColor(color))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(polygon)

    def draw_nodes(self, painter):
        for node, (orig_x, orig_y) in self.parent.positions.items():
            x, y = self.parent.get_transformed_position(orig_x, orig_y)

            color = self.parent.get_node_color(node)

            shadow_offset = 4 * self.parent.zoom_level
            painter.setBrush(QColor(0, 0, 0, 80))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(x - 15 + shadow_offset),
                              int(y - 15 + shadow_offset),
                              30, 30)

            radius = self.parent.get_node_radius()
            gradient = QRadialGradient(x, y, radius)
            gradient.setColorAt(0, QColor(color).lighter(150))
            gradient.setColorAt(0.7, QColor(color))
            gradient.setColorAt(1, QColor(color).darker(120))

            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(self.parent.current_theme['border']), 2))
            painter.drawEllipse(int(x - radius), int(y - radius), radius * 2, radius * 2)

            text_color = "white" if color in ["#4CAF50", "#F44336", "#bb86fc", "#4caf50", "#ffb74d"] else "black"
            painter.setPen(QColor(text_color))
            painter.setFont(QFont("Arial", max(8, int(12 * self.parent.zoom_level)), QFont.Bold))
            painter.drawText(int(x - radius), int(y - radius), radius * 2, radius * 2,
                           Qt.AlignCenter, node)

            if (node in self.parent.distances and self.parent.distances[node] != float('inf') and
                self.parent.zoom_level > 0.5):
                self.draw_node_distance(painter, x, y, node)

    def draw_node_distance(self, painter, x, y, node):
        dist_text = f"{self.parent.distances[node]:.1f}"

        text_rect = QRect(int(x + 25 * self.parent.zoom_level),
                         int(y - 35 * self.parent.zoom_level),
                         40, 20)
        painter.setBrush(QColor(30, 30, 30, 200))
        painter.setPen(QPen(QColor(self.parent.current_theme['border']), 1))
        painter.drawRoundedRect(text_rect, 5, 5)

        painter.setPen(QColor(self.parent.current_theme['accent']))
        painter.setFont(QFont("Arial", max(6, int(10 * self.parent.zoom_level)), QFont.Bold))
        painter.drawText(text_rect, Qt.AlignCenter, dist_text)

    def draw_legend(self, painter):
        legend_height = 240 if self.parent.directed else 200
        legend_bg_rect = QRect(15, 15, 220, legend_height)

        painter.setBrush(QColor(20, 20, 20, 180))
        painter.setPen(QPen(QColor(self.parent.current_theme['border']), 1))
        painter.drawRoundedRect(legend_bg_rect, 12, 12)

        inner_rect = legend_bg_rect.adjusted(8, 8, -8, -8)
        painter.setBrush(QColor(30, 30, 30, 150))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(inner_rect, 8, 8)

        legend_x, legend_y = 25, 30
        legend_items = [
            ("Текущий узел", self.parent.current_theme['warning']),
            ("Посещенный", self.parent.current_theme['accent']),
            ("Кратчайший путь", self.parent.current_theme['success']),
            ("Старт", "#4CAF50"),
            ("Финиш", "#F44336"),
            ("Не посещенный", self.parent.current_theme['text_secondary'])
        ]
        if self.parent.directed:
            legend_items.append(("Направление (стрелка)", self.parent.current_theme['text']))

        painter.setFont(QFont("Arial", 10, QFont.Bold))

        for text, color in legend_items:
            icon_size = 16
            painter.setBrush(QColor(0, 0, 0, 80))
            painter.setPen(Qt.NoPen)
            painter.drawRect(legend_x + 1, legend_y + 1, icon_size, icon_size)

            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(QPen(QColor(self.parent.current_theme['border']), 1))
            painter.drawRect(legend_x, legend_y, icon_size, icon_size)

            painter.setPen(QColor(self.parent.current_theme['text']))
            painter.drawText(legend_x + 25, legend_y + 12, text)
            legend_y += 28

        if hasattr(self.parent, 'start_node') and hasattr(self.parent, 'end_node'):
            info_bg_rect = QRect(15, legend_y + 15, 250, 100)

            painter.setBrush(QColor(20, 20, 20, 180))
            painter.setPen(QPen(QColor(self.parent.current_theme['border']), 1))
            painter.drawRoundedRect(info_bg_rect, 12, 12)

            inner_info_rect = info_bg_rect.adjusted(8, 8, -8, -8)
            painter.setBrush(QColor(30, 30, 30, 150))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(inner_info_rect, 8, 8)

            info_y = legend_y + 30

            painter.setFont(QFont("Arial", 11, QFont.Bold))
            painter.setPen(QColor(self.parent.current_theme['text']))
            painter.drawText(25, info_y, f"Алгоритм: {self.parent.current_algorithm.get_name() if self.parent.current_algorithm else 'Не выбран'}")
            painter.drawText(25, info_y + 25, f"Старт: {self.parent.start_node}, Конец: {self.parent.end_node}")

            if self.parent.algorithm_finished and self.parent.algorithm_result:
                result_color = self.parent.current_theme['success'] if "Найден путь" in self.parent.algorithm_result else self.parent.current_theme['danger']
                painter.setPen(QColor(result_color))
                result_text = self.parent.algorithm_result.split("(")[0] if "Найден путь" in self.parent.algorithm_result else self.parent.algorithm_result
                painter.drawText(25, info_y + 50, result_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            click_pos = event.position()
            x, y = click_pos.x(), click_pos.y()
            clicked_node = self.get_node_at_position(x, y)
            if clicked_node:
                if not self.parent.start_node:
                    self.parent.start_node = clicked_node
                elif not self.parent.end_node and clicked_node != self.parent.start_node:
                    self.parent.end_node = clicked_node
                    self.parent.restart()
                else:
                    self.parent.start_node = clicked_node
                    self.parent.end_node = None
                self.parent.update_selection_comboboxes()
                self.update()
                return

        if event.button() == Qt.MiddleButton:
            self.parent.is_panning = True
            self.parent.pan_start_x = event.position().x()
            self.parent.pan_start_y = event.position().y()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self.parent.is_panning:
            dx = event.position().x() - self.parent.pan_start_x
            dy = event.position().y() - self.parent.pan_start_y
            self.parent.pan_offset_x += dx
            self.parent.pan_offset_y += dy
            self.parent.pan_start_x = event.position().x()
            self.parent.pan_start_y = event.position().y()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.parent.is_panning = False
            self.setCursor(Qt.ArrowCursor)

    def get_node_at_position(self, x, y):
        for node, (orig_x, orig_y) in self.parent.positions.items():
            transformed_x, transformed_y = self.parent.get_transformed_position(orig_x, orig_y)
            radius = self.parent.get_node_radius()
            dx = x - transformed_x
            dy = y - transformed_y
            if dx * dx + dy * dy <= radius * radius:
                return node
        return None

    def keyPressEvent(self, event):
        self.parent.keyPressEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.parent.zoom_level *= 1.1
        else:
            self.parent.zoom_level /= 1.1

        self.parent.zoom_level = max(0.1, min(5.0, self.parent.zoom_level))
        self.update()

class ModernGraphVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Визуализация алгоритмов кратчайшего пути - Modern UI")
        self.setGeometry(100, 100, 1400, 900)

        self.dark_mode = True
        self.setup_themes()
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

        self.history = []
        self.current_history_index = -1
        self.pause = True

        self.animation_speed = 500
        self.zoom_level = 1.0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.is_panning = False

        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.auto_step)

        self.algorithm_manager = AlgorithmPluginManager()
        self.current_algorithm = None

        self.setup_ui()
        self.initialize_default_graph()
        self.initialize_algorithm()
        self.setup_shortcuts()

        self.activateWindow()
        self.raise_()
        QTimer.singleShot(100, lambda: self.canvas_widget.setFocus())

    def setup_themes(self):
        self.themes = {
            'dark': {
                'bg': '#1e1e1e',
                'bg_secondary': '#2d2d2d',
                'bg_tertiary': '#3d3d3d',
                'text': '#ffffff',
                'text_secondary': '#cccccc',
                'accent': '#bb86fc',
                'accent_secondary': '#03dac6',
                'danger': '#cf6679',
                'warning': '#ffb74d',
                'success': '#4caf50',
                'border': '#444444',
                'canvas_bg': '#121212'
            }
        }
        self.current_theme = self.themes['dark']

    def apply_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(self.current_theme['bg']))
        palette.setColor(QPalette.WindowText, QColor(self.current_theme['text']))
        palette.setColor(QPalette.Base, QColor(self.current_theme['bg_secondary']))
        palette.setColor(QPalette.AlternateBase, QColor(self.current_theme['bg_tertiary']))
        palette.setColor(QPalette.ToolTipBase, QColor(self.current_theme['bg']))
        palette.setColor(QPalette.ToolTipText, QColor(self.current_theme['text']))
        palette.setColor(QPalette.Text, QColor(self.current_theme['text']))
        palette.setColor(QPalette.Button, QColor(self.current_theme['bg_secondary']))
        palette.setColor(QPalette.ButtonText, QColor(self.current_theme['text']))
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(self.current_theme['accent']))
        palette.setColor(QPalette.Highlight, QColor(self.current_theme['accent']))
        palette.setColor(QPalette.HighlightedText, Qt.black)

        QApplication.setPalette(palette)

    def create_animated_header(self):
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 5, 0, 5)
        header_layout.setSpacing(2)

        title_label = GradientLabel("GRAPH VISUALIZER PRO", self)
        title_label.setAlignment(Qt.AlignCenter)

        subtitle_text = f"""
        <html>
        <head/>
        <body>
        <p style="color: {self.current_theme['text_secondary']}; font-size: 12px; margin: 0; padding: 0; text-align: center;">
        <span style="color: {self.current_theme['accent']}; font-weight: bold;">Дейкстра</span> •
        <span style="color: {self.current_theme['accent']}; font-weight: bold;">Беллман-Форд</span> •
        Визуализация графов • Анализ алгоритмов
        </p>
        </body>
        </html>
        """

        subtitle_label = QLabel()
        subtitle_label.setText(subtitle_text)
        subtitle_label.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)

        return header_widget

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        self.main_splitter = QSplitter(Qt.Vertical)
        layout.addWidget(self.main_splitter)

        self.top_panel = self.create_top_panel()
        self.main_splitter.addWidget(self.top_panel)

        main_area_widget = QWidget()
        main_area_layout = QHBoxLayout(main_area_widget)
        main_area_layout.setContentsMargins(0, 0, 0, 0)
        main_area_layout.setSpacing(0)

        content_splitter = QSplitter(Qt.Horizontal)

        self.canvas_widget = GraphCanvas(self)
        content_splitter.addWidget(self.canvas_widget)

        right_panel = self.create_right_panel()
        content_splitter.addWidget(right_panel)

        content_splitter.setSizes([1000, 400])
        main_area_layout.addWidget(content_splitter)

        self.main_splitter.addWidget(main_area_widget)

        self.main_splitter.setSizes([120, 780])
        self.main_splitter.setCollapsible(0, True)
        self.main_splitter.setCollapsible(1, False)

        self.create_status_bar()

    def create_top_panel(self):
        top_frame = QFrame()
        top_frame.setMinimumHeight(0)
        top_frame.setMaximumHeight(200)
        top_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.current_theme['bg_secondary']},
                    stop:1 {self.current_theme['bg']});
                border-bottom: 2px solid {self.current_theme['accent']};
                border-radius: 0px;
                padding: 8px;
            }}
        """)

        top_layout = QHBoxLayout(top_frame)
        top_layout.setSpacing(10)

        header_widget = self.create_animated_header()
        top_layout.addWidget(header_widget)

        top_layout.addStretch(1)

        graph_type_group = self.create_graph_type_group()
        top_layout.addWidget(graph_type_group)

        algo_group = QGroupBox("Выбор алгоритма")
        algo_group.setStyleSheet(f"""
            QGroupBox {{
                color: {self.current_theme['accent']};
                font-weight: bold;
                font-size: 11px;
                border: 1px solid {self.current_theme['border']};
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 6px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
            }}
        """)
        algo_layout = QHBoxLayout(algo_group)
        algo_layout.setSpacing(8)

        self.algorithm_group = QButtonGroup(self)

        self.dijkstra_radio = QRadioButton("Дейкстра")
        self.bellman_radio = QRadioButton("Беллман-Форд")
        self.dijkstra_radio.clicked.connect(self.on_algorithm_changed)
        self.bellman_radio.clicked.connect(self.on_algorithm_changed)

        self.auto_update_timer = QTimer()
        self.auto_update_timer.timeout.connect(self.auto_update_status)
        self.auto_update_timer.start(500)

        radio_style = f"""
            QRadioButton {{
                color: {self.current_theme['text']};
                font-weight: normal;
                font-size: 10px;
                padding: 3px 6px;
                border: 1px solid transparent;
                border-radius: 4px;
            }}
            QRadioButton:hover {{
                background: {self.current_theme['bg_tertiary']};
                border: 1px solid {self.current_theme['accent']};
            }}
            QRadioButton::indicator {{
                width: 12px;
                height: 12px;
            }}
            QRadioButton::indicator::unchecked {{
                border: 2px solid {self.current_theme['text_secondary']};
                border-radius: 6px;
                background: {self.current_theme['bg_tertiary']};
            }}
            QRadioButton::indicator::checked {{
                border: 2px solid {self.current_theme['accent']};
                border-radius: 6px;
                background: {self.current_theme['accent']};
            }}
        """

        self.dijkstra_radio.setStyleSheet(radio_style)
        self.bellman_radio.setStyleSheet(radio_style)

        self.algorithm_group.addButton(self.dijkstra_radio)
        self.algorithm_group.addButton(self.bellman_radio)

        algo_layout.addWidget(self.dijkstra_radio)
        algo_layout.addWidget(self.bellman_radio)
        top_layout.addWidget(algo_group)

        top_layout.addStretch(1)

        control_layout = QHBoxLayout()
        control_layout.setSpacing(6)

        self.step_back_btn = self.create_control_button("◀◀", "Назад", self.step_backward)
        self.step_forward_btn = self.create_control_button("▶▶", "Вперед", self.step_forward)
        self.pause_btn = self.create_control_button("▶", "Старт", self.toggle_pause)
        self.restart_btn = self.create_control_button("↺", "Сброс", self.restart)

        control_layout.addWidget(self.step_back_btn)
        control_layout.addWidget(self.step_forward_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.restart_btn)

        top_layout.addLayout(control_layout)

        top_layout.addStretch(1)

        file_layout = QHBoxLayout()
        file_layout.setSpacing(6)

        self.load_btn = self.create_styled_button("📁 Загрузить", self.load_graph_from_file)
        file_layout.addWidget(self.load_btn)

        top_layout.addLayout(file_layout)

        return top_frame

    def create_control_button(self, icon, tooltip, callback):
        btn = QPushButton(icon)
        btn.setToolTip(tooltip)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.current_theme['bg_tertiary']};
                border: 2px solid {self.current_theme['border']};
                border-radius: 6px;
                padding: 8px;
                color: {self.current_theme['text']};
                font-weight: bold;
                font-size: 14px;
                min-width: 40px;
                min-height: 32px;
            }}
            QPushButton:hover {{
                background: {self.current_theme['accent']};
                border: 2px solid {self.current_theme['accent_secondary']};
                color: {self.current_theme['bg']};
            }}
            QPushButton:pressed {{
                background: {self.current_theme['accent_secondary']};
                border: 2px solid {self.current_theme['accent']};
            }}
            QPushButton:disabled {{
                background: {self.current_theme['bg_secondary']};
                border: 2px solid {self.current_theme['text_secondary']};
                color: {self.current_theme['text_secondary']};
            }}
        """)
        btn.setFocusPolicy(Qt.NoFocus)
        btn.clicked.connect(callback)
        return btn

    def create_styled_button(self, text, callback):
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.current_theme['bg_tertiary']},
                    stop:1 {self.current_theme['bg_secondary']});
                border: 1px solid {self.current_theme['border']};
                border-radius: 5px;
                padding: 6px 10px;
                color: {self.current_theme['text']};
                font-weight: bold;
                font-size: 10px;
                min-width: 70px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.current_theme['accent']},
                    stop:1 {self.current_theme['accent_secondary']});
                border: 1px solid {self.current_theme['accent']};
                color: black;
            }}
            QPushButton:pressed {{
                background: {self.current_theme['accent_secondary']};
            }}
        """)
        btn.clicked.connect(callback)
        return btn

    def create_right_panel(self):
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(10)

        node_group = QGroupBox("Выбор узлов")
        node_group.setStyleSheet(self.get_groupbox_style())
        node_layout = QVBoxLayout(node_group)

        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Старт:"))
        self.start_combo = QComboBox()
        self.start_combo.setStyleSheet(self.get_combobox_style())
        self.start_combo.setFocusPolicy(Qt.NoFocus)
        self.start_combo.currentTextChanged.connect(self.on_node_selection_changed)
        start_layout.addWidget(self.start_combo)
        node_layout.addLayout(start_layout)

        end_layout = QHBoxLayout()
        end_layout.addWidget(QLabel("Конец:"))
        self.end_combo = QComboBox()
        self.end_combo.setStyleSheet(self.get_combobox_style())
        self.end_combo.setFocusPolicy(Qt.NoFocus)
        self.end_combo.currentTextChanged.connect(self.on_node_selection_changed)
        end_layout.addWidget(self.end_combo)
        node_layout.addLayout(end_layout)

        self.apply_btn = self.create_styled_button("Применить выбор", self.apply_selection)
        node_layout.addWidget(self.apply_btn)

        right_layout.addWidget(node_group)

        generation_group = QGroupBox("Генерация графа")
        generation_group.setStyleSheet(self.get_groupbox_style())
        generation_layout = QVBoxLayout(generation_group)

        self.graph_type_combo = QComboBox()
        self.graph_type_combo.setStyleSheet(self.get_combobox_style())
        self.graph_type_combo.setFocusPolicy(Qt.NoFocus)
        self.graph_type_combo.addItems([
            "Связный случайный",
            "Полный граф",
            "Дерево",
            "Решётка",
            "Двудольный",
            "Звёздчатый"
        ])
        generation_layout.addWidget(self.graph_type_combo)

        self.complexity_combo = QComboBox()
        self.complexity_combo.setStyleSheet(self.get_combobox_style())
        self.complexity_combo.setFocusPolicy(Qt.NoFocus)
        self.complexity_combo.addItems([
            "Лёгкий (4-6 узлов)",
            "Средний (6-9 узлов)",
            "Сложный (9-12 узлов)"
        ])
        self.complexity_combo.setCurrentText("Средний (6-9 узлов)")
        generation_layout.addWidget(self.complexity_combo)

        self.random_btn = self.create_styled_button("🎲 Генерировать", self.generate_random_graph)
        generation_layout.addWidget(self.random_btn)

        right_layout.addWidget(generation_group)

        speed_group = QGroupBox("Скорость анимации")
        speed_group.setStyleSheet(self.get_groupbox_style())
        speed_layout = QVBoxLayout(speed_group)
        speed_layout.setContentsMargins(10, 12, 10, 12)
        speed_layout.setSpacing(8)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(0, 5)
        self.speed_slider.setValue(2)
        self.speed_slider.valueChanged.connect(self.change_speed)
        self.speed_slider.setStyleSheet(self.get_slider_style())
        self.speed_slider.setMinimumHeight(25)
        speed_layout.addWidget(self.speed_slider)

        self.speed_label = QLabel("Средняя скорость")
        self.speed_label.setStyleSheet(f"color: {self.current_theme['text']}; font-size: 10px; padding: 3px;")
        speed_layout.addWidget(self.speed_label)

        right_layout.addWidget(speed_group)

        progress_group = QGroupBox("Прогресс выполнения")
        progress_group.setStyleSheet(self.get_groupbox_style())
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {self.current_theme['border']};
                border-radius: 4px;
                text-align: center;
                background: {self.current_theme['bg_secondary']};
                color: {self.current_theme['text']};
                font-weight: bold;
                height: 20px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.current_theme['accent']},
                    stop:1 {self.current_theme['accent_secondary']});
                border-radius: 2px;
            }}
        """)
        progress_layout.addWidget(self.progress_bar)

        right_layout.addWidget(progress_group)

        results_group = QGroupBox("Результаты")
        results_group.setStyleSheet(self.get_groupbox_style())
        results_layout = QVBoxLayout(results_group)

        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["Вершина", "Расстояние", "Путь"])
        self.results_tree.setStyleSheet(f"""
    QTreeWidget {{
        background: {self.current_theme['bg_secondary']};
        color: {self.current_theme['text']};
        border: 1px solid {self.current_theme['border']};
        border-radius: 4px;
        font-size: 14px;
        font-weight: normal;
    }}
    QTreeWidget::item {{
        padding: 8px;
        border-bottom: 1px solid {self.current_theme['border']};
        height: 22px;
    }}
    QTreeWidget::item:selected {{
        background: {self.current_theme['accent']};
        color: black;
    }}
    QHeaderView::section {{
        background: {self.current_theme['bg_tertiary']};
        color: {self.current_theme['text']};
        padding: 8px;
        border: 1px solid {self.current_theme['border']};
        font-weight: bold;
        font-size: 14px;
    }}
""")
        self.results_tree.setColumnWidth(0, 90)
        self.results_tree.setColumnWidth(1, 105)
        self.results_tree.setColumnWidth(2, 225)
        results_layout.addWidget(self.results_tree)

        right_layout.addWidget(results_group)

        weights_group = QGroupBox("Веса рёбер")
        weights_group.setStyleSheet(self.get_groupbox_style())
        weights_layout = QVBoxLayout(weights_group)

        self.weights_tree = QTreeWidget()
        self.weights_tree.setHeaderLabels(["Ребро", "Вес"])
        self.weights_tree.setStyleSheet(f"""
    QTreeWidget {{
        background: {self.current_theme['bg_secondary']};
        color: {self.current_theme['text']};
        border: 1px solid {self.current_theme['border']};
        border-radius: 4px;
        font-size: 14px;
        font-weight: normal;
    }}
    QTreeWidget::item {{
        padding: 8px;
        border-bottom: 1px solid {self.current_theme['border']};
        height: 22px;
    }}
    QTreeWidget::item:selected {{
        background: {self.current_theme['accent']};
        color: black;
    }}
    QHeaderView::section {{
        background: {self.current_theme['bg_tertiary']};
        color: {self.current_theme['text']};
        padding: 8px;
        border: 1px solid {self.current_theme['border']};
        font-weight: bold;
        font-size: 14px;
    }}
""")
        self.weights_tree.setColumnWidth(0, 120)
        self.weights_tree.setColumnWidth(1, 90)
        weights_layout.addWidget(self.weights_tree)

        right_layout.addWidget(weights_group)

        right_layout.addStretch()

        return right_widget

    def create_graph_type_group(self):
        group = QGroupBox("Тип графа")
        group.setStyleSheet(self.get_groupbox_style())
        layout = QHBoxLayout(group)
        layout.setSpacing(10)

        self.undirected_radio = QRadioButton("Неориентированный")
        self.directed_radio = QRadioButton("Ориентированный")
        self.undirected_radio.setChecked(not self.directed)
        self.directed_radio.setChecked(self.directed)

        radio_style = f"""
            QRadioButton {{
                color: {self.current_theme['text']};
                font-size: 12px;
                padding: 4px;
            }}
        """
        self.undirected_radio.setStyleSheet(radio_style)
        self.directed_radio.setStyleSheet(radio_style)

        self.undirected_radio.toggled.connect(self.on_graph_type_toggled)
        self.directed_radio.toggled.connect(self.on_graph_type_toggled)

        layout.addWidget(self.undirected_radio)
        layout.addWidget(self.directed_radio)
        layout.addStretch()

        return group

    def on_graph_type_toggled(self):
        new_directed = self.directed_radio.isChecked()
        if new_directed == self.directed:
            return
        self.directed = new_directed
        mode = "ориентированный" if self.directed else "неориентированный"
        self.status_label.setText(f"Тип графа: {mode}. Перезагрузите или сгенерируйте граф для применения.")
        self.update_weights_table()
        self.canvas_widget.update()

    def update_graph_type_controls(self):
        if hasattr(self, 'directed_radio'):
            self.directed_radio.blockSignals(True)
            self.undirected_radio.blockSignals(True)
            self.directed_radio.setChecked(self.directed)
            self.undirected_radio.setChecked(not self.directed)
            self.directed_radio.blockSignals(False)
            self.undirected_radio.blockSignals(False)

    def update_weights_table(self):
        self.weights_tree.clear()

        if not self.graph:
            return

        edge_symbol = "→" if self.directed else "-"
        for u, v, weight in self.iter_unique_edges():
            edge_text = f"{u} {edge_symbol} {v}"
            weight_text = str(weight)

            item = QTreeWidgetItem([edge_text, weight_text])

            if weight < 0:
                item.setBackground(1, QColor(self.current_theme['danger']))
                item.setForeground(1, QColor('white'))

            self.weights_tree.addTopLevelItem(item)

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

    def get_groupbox_style(self):
        return f"""
            QGroupBox {{
                color: {self.current_theme['accent']};
                font-weight: bold;
                font-size: 11px;
                border: 1px solid {self.current_theme['border']};
                border-radius: 5px;
                margin-top: 6px;
                padding-top: 6px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
            }}
        """

    def get_combobox_style(self):
        return f"""
            QComboBox {{
                background: {self.current_theme['bg_tertiary']};
                color: {self.current_theme['text']};
                border: 1px solid {self.current_theme['border']};
                border-radius: 3px;
                padding: 6px;
                min-width: 75px;
                font-size: 14px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 1px solid {self.current_theme['border']};
                padding: 3px;
            }}
            QComboBox QAbstractItemView {{
                background: {self.current_theme['bg_secondary']};
                color: {self.current_theme['text']};
                selection-background-color: {self.current_theme['accent']};
                font-size: 16px;
            }}
        """

    def setup_shortcuts(self):
        self.default_shortcuts = {
            'pause': Qt.Key_Space,
            'step_forward': Qt.Key_Right,
            'step_backward': Qt.Key_Left,
            'restart': Qt.Key_R,
            'fullscreen': Qt.Key_F,
            'increase_speed': Qt.Key_Minus,
            'decrease_speed': Qt.Key_Plus,
            'reset_view': Qt.Key_I,
            'generate_graph': Qt.Key_G,
            'load_graph': Qt.Key_L,
            'algorithm_1': Qt.Key_1,
            'algorithm_2': Qt.Key_2,
            'help': Qt.Key_H
        }

        self.shortcuts = self.default_shortcuts.copy()

        QShortcut(QKeySequence("Space"), self, self.toggle_pause)
        QShortcut(QKeySequence("Right"), self, self.step_forward)
        QShortcut(QKeySequence("Left"), self, self.step_backward)
        QShortcut(QKeySequence("R"), self, self.restart)
        QShortcut(QKeySequence("F"), self, self.toggle_fullscreen)
        QShortcut(QKeySequence("="), self, self.decrease_speed)
        QShortcut(QKeySequence("-"), self, self.increase_speed)
        QShortcut(QKeySequence("I"), self, self.reset_view)
        QShortcut(QKeySequence("G"), self, self.generate_random_graph)
        QShortcut(QKeySequence("L"), self, self.load_graph_from_file)
        QShortcut(QKeySequence("1"), self, lambda: self.set_algorithm(1))
        QShortcut(QKeySequence("2"), self, lambda: self.set_algorithm(2))
        QShortcut(QKeySequence("H"), self, self.show_shortcuts_help)
        QShortcut(QKeySequence("Escape"), self, lambda: self.showNormal() if self.isFullScreen() else None)

    def set_algorithm(self, algorithm_num):
        if algorithm_num == 1:
            self.dijkstra_radio.setChecked(True)
            self.restart()
        elif algorithm_num == 2:
            self.bellman_radio.setChecked(True)
            self.restart()

    def keyPressEvent(self, event):
        key = event.key()

        if key == self.shortcuts['pause']:
            self.toggle_pause()
            event.accept()
        elif key == self.shortcuts['step_forward']:
            self.step_forward()
            event.accept()
        elif key == self.shortcuts['step_backward']:
            self.step_backward()
            event.accept()
        elif key == self.shortcuts['restart']:
            self.restart()
            event.accept()
        elif key == self.shortcuts['fullscreen']:
            self.toggle_fullscreen()
            event.accept()
        elif key == Qt.Key_Plus or key == Qt.Key_Equal:
            self.decrease_speed()
            event.accept()
        elif key == Qt.Key_Minus:
            self.increase_speed()
            event.accept()
        elif key == self.shortcuts['reset_view']:
            self.reset_view()
            event.accept()
        elif key == self.shortcuts['generate_graph']:
            self.generate_random_graph()
            event.accept()
        elif key == self.shortcuts['load_graph']:
            self.load_graph_from_file()
            event.accept()
        elif key == self.shortcuts['algorithm_1']:
            self.dijkstra_radio.setChecked(True)
            self.restart()
            event.accept()
        elif key == self.shortcuts['algorithm_2']:
            self.bellman_radio.setChecked(True)
            self.restart()
            event.accept()
        elif key == self.shortcuts['help']:
            self.show_shortcuts_help()
            event.accept()
        elif key == Qt.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def increase_speed(self):
        current_value = self.speed_slider.value()
        if current_value < 5:
            self.speed_slider.setValue(current_value + 1)

    def decrease_speed(self):
        current_value = self.speed_slider.value()
        if current_value > 0:
            self.speed_slider.setValue(current_value - 1)

    def reset_view(self):
        self.zoom_level = 1.0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.canvas_widget.update()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def on_algorithm_changed(self, checked):
        if checked and self.sender() == self.dijkstra_radio and self.check_negative_weights():
            QMessageBox.warning(
                self, "Предупреждение",
                "Алгоритм Дейкстры не поддерживает отрицательные веса!\n"
                "Переключено на алгоритм Беллмана-Форда."
            )
            self.dijkstra_radio.setChecked(False)
            self.bellman_radio.setChecked(True)
            self.restart()
            return
        if checked:
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

    def auto_update_status(self):
        self.update_progress()
        self.update_results_table()
        self.canvas_widget.update()

    def show_shortcuts_help(self):
        shortcuts = {
            "Пробел": "Пауза/Старт анимации",
            "Стрелка →": "Шаг вперед",
            "Стрелка ←": "Шаг назад",
            "R": "Перезапуск алгоритма",
            "F": "Полноэкранный режим",
            "+/-": "Увеличить/уменьшить скорость",
            "I": "Сброс масштаба и позиции",
            "G": "Сгенерировать случайный граф",
            "L": "Загрузить граф из файла",
            "1/2": "Переключить алгоритм (Дейкстра/Беллман)",
            "H": "Эта справка"
        }

        help_text = "Горячие клавиши:\n\n" + "\n".join(
            f"{key}: {desc}" for key, desc in shortcuts.items()
        )

        QMessageBox.information(self, "Справка по клавишам", help_text)

    def get_slider_style(self):
        return f"""
            QSlider::groove:horizontal {{
                border: 1px solid {self.current_theme['border']};
                height: 6px;
                background: {self.current_theme['bg_tertiary']};
                border-radius: 3px;
                margin: 1px 0px;
            }}
            QSlider::handle:horizontal {{
                background: {self.current_theme['accent']};
                border: 2px solid {self.current_theme['accent_secondary']};
                width: 16px;
                height: 16px;
                margin: -6px 0px;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.current_theme['accent']},
                    stop:1 {self.current_theme['accent_secondary']});
                border-radius: 3px;
            }}
        """

    def create_status_bar(self):
        self.status_bar = self.statusBar()
        self.status_label = QLabel("Готов к работе. Загрузите граф или создайте случайный.")
        self.status_bar.addWidget(self.status_label)

        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background: {self.current_theme['bg_secondary']};
                color: {self.current_theme['text']};
                border-top: 1px solid {self.current_theme['border']};
                font-size: 10px;
            }}
        """)

    def get_node_color(self, node):
        if node == self.start_node:
            return "#4CAF50"
        if node == self.end_node:
            return "#F44336"
        if node == self.current_node:
            return self.current_theme['warning']
        if node in self.visited:
            return self.current_theme['accent']
        if self.final_path and node in self.final_path:
            return self.current_theme['success']
        return self.current_theme['text_secondary']

    def get_node_radius(self):
        return max(15, int(20 * self.zoom_level))

    def get_transformed_position(self, x, y):
        center_x, center_y = self.canvas_widget.width() // 2, self.canvas_widget.height() // 2
        transformed_x = center_x + (x - center_x + self.pan_offset_x) * self.zoom_level
        transformed_y = center_y + (y - center_y + self.pan_offset_y) * self.zoom_level
        return transformed_x, transformed_y

    def change_speed(self, value):
        speeds = ["Очень медленно", "Медленно", "Средняя", "Быстро", "Очень быстро", "Максимум"]
        delays = [2000, 1000, 500, 200, 50, 0]
        self.animation_speed = delays[value]
        self.speed_label.setText(f"{speeds[value]} ({delays[value]}мс/шаг)")

        if hasattr(self, 'animation_timer') and self.animation_timer.isActive():
            self.animation_timer.setInterval(self.animation_speed)

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

        inner_nodes = ['A', 'B', 'C', 'D', 'E', 'F']
        for i, node in enumerate(inner_nodes):
            angle = 2 * math.pi * i / len(inner_nodes)
            self.positions[node] = (
                center_x + 120 * math.cos(angle),
                center_y + 120 * math.sin(angle)
            )

        middle_nodes = ['G', 'H', 'I']
        for i, node in enumerate(middle_nodes):
            angle = 2 * math.pi * i / len(middle_nodes) - math.pi/6
            self.positions[node] = (
                center_x + 250 * math.cos(angle),
                center_y + 250 * math.sin(angle)
            )

        self.start_node = 'G'
        self.end_node = 'D'
        self.original_positions = self.positions.copy()
        self.update_selection_comboboxes()
        self.update_weights_table()

        self.dijkstra_radio.setChecked(not self.check_negative_weights())
        self.bellman_radio.setChecked(self.check_negative_weights())

    def update_selection_comboboxes(self):
        if self.positions:
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

                if upper_line.startswith('START'):
                    start_node = line.split()[1]
                    continue
                elif upper_line.startswith('END'):
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
                QMessageBox.critical(self, "Ошибка", "Файл не содержит корректных ребер графа")
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

            self.start_node = start_node if start_node else list(self.positions.keys())[0]
            self.end_node = end_node if end_node else list(self.positions.keys())[-1]

            self.original_positions = self.positions.copy()
            self.update_selection_comboboxes()

            has_negative = self.check_negative_weights()

            if has_negative and self.dijkstra_radio.isChecked():
                QMessageBox.warning(
                    self, "Предупреждение",
                    "Обнаружены отрицательные веса!\n"
                    "Алгоритм Дейкстры не работает с отрицательными весами.\n"
                    "Автоматически переключен на алгоритм Беллмана-Форда."
                )
                self.bellman_radio.setChecked(True)

            self.restart()
            self.update_weights_table()

            graph_type = "ориентированный" if self.directed else "неориентированный"
            message_text = (
                f"Граф загружен ({graph_type})!\n"
                f"Ребер: {self.get_edge_count()}\n"
                f"Узлов: {len(self.positions)}\n"
                f"Старт: {self.start_node}, Конец: {self.end_node}"
            )
            if has_negative:
                message_text += f"\n⚠️ Обнаружены отрицательные веса!"

            QMessageBox.information(self, "Успех", message_text)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл:\n{str(e)}")

    def calculate_positions(self, nodes=None):
        if nodes is None:
            nodes = list(self.get_all_nodes())
        self.positions = {}

        if not nodes:
            return

        center_x, center_y = 400, 300
        radius = min(350, 30 * len(nodes))

        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / len(nodes)
            self.positions[node] = (
                center_x + radius * math.cos(angle),
                center_y + radius * math.sin(angle)
            )

        self.original_positions = self.positions.copy()

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
        graph_name = generated['name']

        self.calculate_positions(selected_nodes)

        self.start_node = random.choice(selected_nodes)
        self.end_node = random.choice([n for n in selected_nodes if n != self.start_node])
        self.original_positions = self.positions.copy()
        self.update_selection_comboboxes()

        has_negative = self.check_negative_weights()
        if has_negative and self.dijkstra_radio.isChecked():
            self.bellman_radio.setChecked(True)

        self.restart()
        self.update_weights_table()

        is_directed = "ориентированный" if self.directed else "неориентированный"
        QMessageBox.information(self, f"Сгенерирован {graph_name}",
                               f"Тип: {graph_name} ({is_directed})\n"
                               f"Узлов: {len(selected_nodes)}\n"
                               f"Ребер: {self.get_edge_count()}\n"
                               f"Старт: {self.start_node}, Конец: {self.end_node}")

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

    def initialize_algorithm(self):
        self.history = []
        self.current_history_index = -1

        if self.dijkstra_radio.isChecked():
            self.current_algorithm = self.algorithm_manager.set_current_plugin('dijkstra')
        else:
            self.current_algorithm = self.algorithm_manager.set_current_plugin('bellman')

        if self.current_algorithm:
            initial_state = self.current_algorithm.initialize(
                self.graph, self.start_node, self.positions, self.end_node
            )
            self.apply_algorithm_state(initial_state)
            self.save_state("Инициализация алгоритма")

    def apply_algorithm_state(self, state):
        self.distances = state['distances']
        self.visited = state.get('visited', set())
        self.previous = state.get('previous', {})
        self.current_node = state.get('current_node')
        self.final_path = state.get('final_path')
        self.algorithm_finished = state.get('algorithm_finished', False)
        self.algorithm_result = state.get('algorithm_result', "")

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
            'description': description
        }
        self.history = self.history[:self.current_history_index + 1]
        self.history.append(state)
        self.current_history_index = len(self.history) - 1

    def step_forward(self):
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

        self.update_progress()
        self.update_results_table()
        self.canvas_widget.update()

    def step_backward(self):
        if self.current_history_index > 0:
            self.current_history_index -= 1
            self.restore_state()
            self.update_progress()
            self.update_results_table()
            self.canvas_widget.update()

    def restore_state(self):
        state = self.history[self.current_history_index]
        self.distances = state['distances'].copy()
        self.visited = state['visited'].copy()
        self.previous = state['previous'].copy()
        self.current_node = state['current_node']
        self.final_path = state['final_path'].copy() if state['final_path'] else None
        self.algorithm_finished = state['algorithm_finished']
        self.algorithm_result = state['algorithm_result']

    def toggle_pause(self):
        self.pause = not self.pause
        if not self.pause:
            self.pause_btn.setText("❚❚")
            self.pause_btn.setToolTip("Пауза")
            self.animation_timer.start(self.animation_speed)
        else:
            self.pause_btn.setText("▶")
            self.pause_btn.setToolTip("Старт")
            self.animation_timer.stop()

    def auto_step(self):
        if self.pause or self.algorithm_finished:
            self.animation_timer.stop()
            if self.algorithm_finished and not self.pause:
                self.pause = True
                self.pause_btn.setText("▶")
                self.pause_btn.setToolTip("Старт")
            return

        self.step_forward()

    def restart(self):
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()

        self.pause = True
        self.pause_btn.setText("▶")
        self.pause_btn.setToolTip("Старт")
        self.initialize_algorithm()
        self.update_progress()
        self.update_results_table()
        self.canvas_widget.update()
        self.status_label.setText("Алгоритм перезапущен. Нажмите 'Старт' для начала.")

    def update_progress(self):
        if not self.positions:
            self.progress_bar.setValue(0)
            return

        if self.algorithm_finished:
            self.progress_bar.setValue(100)
        elif self.current_algorithm and isinstance(self.current_algorithm, DijkstraPlugin):
            total_nodes = len(self.positions)
            visited_nodes = len(self.visited)
            progress = int((visited_nodes / total_nodes) * 100)
            self.progress_bar.setValue(progress)
        elif self.current_algorithm and isinstance(self.current_algorithm, BellmanFordPlugin):
            total_iterations = len(self.positions)
            if hasattr(self.current_algorithm, 'iteration'):
                iteration = self.current_algorithm.iteration
                if iteration < total_iterations - 1:
                    progress = int((iteration / (total_iterations - 1)) * 100)
                else:
                    total_edges = len(getattr(self.current_algorithm, 'edges', []))
                    if total_edges > 0:
                        edge_index = getattr(self.current_algorithm, 'edge_index', 0)
                        progress = 80 + int((edge_index / total_edges) * 20)
                    else:
                        progress = 100
                self.progress_bar.setValue(min(progress, 100))
            else:
                self.progress_bar.setValue(0)
        else:
            self.progress_bar.setValue(0)

    def update_results_table(self):
        self.results_tree.clear()

        if not hasattr(self, 'distances') or not self.distances:
            return

        for node in sorted(self.positions.keys()):
            distance = self.distances.get(node, float('inf'))
            distance_text = f"{distance:.1f}" if distance != float('inf') else "∞"

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
                path_text = " -> ".join(path)
            else:
                path_text = "-"

            item = QTreeWidgetItem([node, distance_text, path_text])
            self.results_tree.addTopLevelItem(item)

            if node == self.start_node:
                item.setBackground(0, QColor(self.current_theme['success']))
            elif node == self.end_node:
                item.setBackground(0, QColor(self.current_theme['danger']))
            elif node in self.visited:
                item.setBackground(0, QColor(self.current_theme['accent']))

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = ModernGraphVisualizer()
    window.show()
    window.setFocus()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
