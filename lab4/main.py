import sys
import math
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QComboBox, 
                             QFileDialog, QMessageBox, QGroupBox, QSpinBox, 
                             QDoubleSpinBox, QSplitter, QTextEdit)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont

# ==============================================================================
# 1. Алгоритмы отсечения (Вариант 6)
# ==============================================================================

# Коды областей для алгоритма средней точки
INSIDE = 0  # 0000
LEFT   = 1  # 0001
RIGHT  = 2  # 0010
BOTTOM = 4  # 0100
TOP    = 8  # 1000

def compute_code(x, y, xmin, ymin, xmax, ymax):
    code = INSIDE
    if x < xmin:
        code |= LEFT
    elif x > xmax:
        code |= RIGHT
    if y < ymin:
        code |= BOTTOM
    elif y > ymax:
        code |= TOP
    return code

def midpoint_subdivision(p1, p2, xmin, ymin, xmax, ymax, eps=1e-3):
    """
    Часть 1: Алгоритм средней точки (двоичный поиск граничных точек пересечения).
    """
    x1, y1 = p1
    x2, y2 = p2
    c1 = compute_code(x1, y1, xmin, ymin, xmax, ymax)
    c2 = compute_code(x2, y2, xmin, ymin, xmax, ymax)

    # Полная видимость
    if (c1 | c2) == 0:
        return [(x1, y1), (x2, y2)]
    # Полная невидимость (оба с одной внешней стороны)
    if (c1 & c2) != 0:
        return None

    # Поиск первой точки пересечения (если p1 снаружи)
    p_start = p1
    if c1 != 0:
        A, B = p1, p2
        while math.hypot(B[0] - A[0], B[1] - A[1]) > eps:
            mid = ((A[0] + B[0]) / 2.0, (A[1] + B[1]) / 2.0)
            c_mid = compute_code(mid[0], mid[1], xmin, ymin, xmax, ymax)
            c_A = compute_code(A[0], A[1], xmin, ymin, xmax, ymax)
            if (c_A & c_mid) != 0:
                A = mid
            else:
                B = mid
        p_start = B

    # Поиск второй точки пересечения (если p2 снаружи)
    p_end = p2
    if c2 != 0:
        A, B = p2, p_start
        while math.hypot(B[0] - A[0], B[1] - A[1]) > eps:
            mid = ((A[0] + B[0]) / 2.0, (A[1] + B[1]) / 2.0)
            c_mid = compute_code(mid[0], mid[1], xmin, ymin, xmax, ymax)
            c_A = compute_code(A[0], A[1], xmin, ymin, xmax, ymax)
            if (c_A & c_mid) != 0:
                A = mid
            else:
                B = mid
        p_end = B

    # Проверка, что результирующие точки лежат в окне
    c_start = compute_code(p_start[0], p_start[1], xmin, ymin, xmax, ymax)
    c_end = compute_code(p_end[0], p_end[1], xmin, ymin, xmax, ymax)
    if c_start == 0 and c_end == 0:
        return [p_start, p_end]
    return None


def cyrus_beck(p1, p2, polygon):
    """
    Часть 2: Алгоритм Кируса-Бека (отсечение отрезка выпуклым многоугольником).
    polygon: список кортежей [(x0, y0), (x1, y1), ..., (xn-1, yn-1)] против часовой стрелки.
    """
    n = len(polygon)
    if n < 3:
        return None

    # Проверка ориентации полигона (гарантируем обход против часовой стрелки)
    area = 0.0
    for i in range(n):
        x_i, y_i = polygon[i]
        x_next, y_next = polygon[(i + 1) % n]
        area += (x_i * y_next - x_next * y_i)
    if area < 0:
        polygon = list(reversed(polygon))

    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    t_enter = 0.0
    t_leave = 1.0

    for i in range(n):
        v1 = polygon[i]
        v2 = polygon[(i + 1) % n]

        edge_x = v2[0] - v1[0]
        edge_y = v2[1] - v1[1]

        # Внутренняя нормаль для обхода против часовой стрелки: (-edge_y, edge_x)
        nx = -edge_y
        ny = edge_x

        # Вектор от вершины ребра к началу отрезка
        wx = p1[0] - v1[0]
        wy = p1[1] - v1[1]

        numerator = -(wx * nx + wy * ny)
        denominator = dx * nx + dy * ny

        if abs(denominator) < 1e-9:
            # Отрезок параллелен ребру
            if (wx * nx + wy * ny) < 0:
                # Начало отрезка лежит вне полуплоскости ребра
                return None
        else:
            t = numerator / denominator
            if denominator > 0:
                # Входящее пересечение
                if t > t_enter:
                    t_enter = t
            else:
                # Выходящее пересечение
                if t < t_leave:
                    t_leave = t

            if t_enter > t_leave:
                return None

    if t_enter <= t_leave:
        clipped_p1 = (p1[0] + t_enter * dx, p1[1] + t_enter * dy)
        clipped_p2 = (p1[0] + t_leave * dx, p1[1] + t_leave * dy)
        return [clipped_p1, clipped_p2]
    return None


# ==============================================================================
# 2. Холст отрисовки с масштабируемой системой координат
# ==============================================================================

class ClippingCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.scale = 20.0
        self.segments = []         # Исходные отрезки: [((x1, y1), (x2, y2)), ...]
        self.clipped_segments = [] # Отсеченные видимые части
        self.clip_rect = None      # (xmin, ymin, xmax, ymax)
        self.clip_poly = None      # [(x0, y0), ...]
        self.mode = "midpoint"     # "midpoint" или "cyrus_beck"
        self.setMinimumSize(500, 500)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w, h = self.width(), self.height()
        ox, oy = w // 2, h // 2

        # Фон
        painter.fillRect(0, 0, w, h, QColor("#1e1e1e"))

        # Сетка
        pen_grid = QPen(QColor("#2d2d2d"), 1)
        painter.setPen(pen_grid)
        step = int(self.scale)
        if step >= 5:
            start_x = ox % step
            for x in range(start_x, w, step):
                painter.drawLine(x, 0, x, h)
            start_y = oy % step
            for y in range(start_y, h, step):
                painter.drawLine(0, y, w, y)

        # Оси координат
        pen_axis = QPen(QColor("#777777"), 2)
        painter.setPen(pen_axis)
        painter.drawLine(0, oy, w, oy)
        painter.drawLine(ox, 0, ox, h)

        # Подписи и засечки на осях
        painter.setFont(QFont("Monospace", 8))
        painter.setPen(QColor("#888888"))
        label_step = max(1, int(50 / self.scale))
        for i in range(-50, 51, label_step):
            if i == 0:
                continue
            sx = int(ox + i * self.scale)
            sy = int(oy - i * self.scale)
            if 0 <= sx <= w:
                painter.drawLine(sx, oy - 3, sx, oy + 3)
                painter.drawText(sx - 10, oy + 15, 20, 10, Qt.AlignmentFlag.AlignCenter, str(i))
            if 0 <= sy <= h:
                painter.drawLine(ox - 3, sy, ox + 3, sy)
                painter.drawText(ox + 6, sy - 5, 25, 10, Qt.AlignmentFlag.AlignLeft, str(i))

        def to_screen(x, y):
            return QPointF(ox + x * self.scale, oy - y * self.scale)

        # 1. Отрисовка отсекающего окна / многоугольника (Желтый контур с полупрозрачной заливкой)
        if self.mode == "midpoint" and self.clip_rect:
            xmin, ymin, xmax, ymax = self.clip_rect
            p_lt = to_screen(xmin, ymax)
            p_rb = to_screen(xmax, ymin)
            rect_w = p_rb.x() - p_lt.x()
            rect_h = p_rb.y() - p_lt.y()

            painter.setPen(QPen(QColor("#ffb74d"), 2))
            painter.setBrush(QBrush(QColor(255, 183, 77, 30)))
            painter.drawRect(int(p_lt.x()), int(p_lt.y()), int(rect_w), int(rect_h))

        elif self.mode == "cyrus_beck" and self.clip_poly:
            poly_points = [to_screen(x, y) for x, y in self.clip_poly]
            painter.setPen(QPen(QColor("#ffb74d"), 2))
            painter.setBrush(QBrush(QColor(255, 183, 77, 30)))
            from PyQt6.QtGui import QPolygonF
            painter.drawPolygon(QPolygonF(poly_points))

        # 2. Исходные отрезки (Красные, полупрозрачные или пунктирные)
        pen_orig = QPen(QColor("#e57373"), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen_orig)
        for (x1, y1), (x2, y2) in self.segments:
            painter.drawLine(to_screen(x1, y1), to_screen(x2, y2))

        # 3. Видимые отсечённые части (Ярко-зелёные, толстая линия)
        pen_clipped = QPen(QColor("#00e676"), 3, Qt.PenStyle.SolidLine)
        painter.setPen(pen_clipped)
        for (x1, y1), (x2, y2) in self.clipped_segments:
            painter.drawLine(to_screen(x1, y1), to_screen(x2, y2))
            # Точки на концах видимого отрезка
            painter.setBrush(QBrush(QColor("#00e676")))
            painter.drawEllipse(to_screen(x1, y1), 3, 3)
            painter.drawEllipse(to_screen(x2, y2), 3, 3)


# ==============================================================================
# 3. Главное окно приложения
# ==============================================================================

class Lab4App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа №4 — Вариант 6 (Отсечение отрезков)")
        self.resize(1150, 750)
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Холст
        self.canvas = ClippingCanvas()
        splitter.addWidget(self.canvas)

        # Панель управления
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        splitter.addWidget(panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        # Выбор режима/алгоритма
        group_mode = QGroupBox("Режим алгоритма (Вариант 6)")
        mode_layout = QVBoxLayout(group_mode)
        self.combo_mode = QComboBox()
        self.combo_mode.addItems([
            "Часть 1: Алгоритм средней точки (окно)",
            "Часть 2: Кирус-Бек (выпуклый многоугольник)"
        ])
        self.combo_mode.currentIndexChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.combo_mode)
        panel_layout.addWidget(group_mode)

        # Ввод/загрузка данных
        group_data = QGroupBox("Управление данными")
        data_layout = QVBoxLayout(group_data)

        btn_load = QPushButton("Загрузить из файла (формат задания)")
        btn_load.clicked.connect(self.load_from_file)
        data_layout.addWidget(btn_load)

        btn_random = QPushButton("Сгенерировать случайные отрезки")
        btn_random.clicked.connect(self.generate_random_segments)
        data_layout.addWidget(btn_random)

        btn_clip = QPushButton("Выполнить отсечение")
        btn_clip.setStyleSheet("font-weight: bold; background-color: #2e7d32; color: white;")
        btn_clip.clicked.connect(self.run_clipping)
        data_layout.addWidget(btn_clip)

        btn_clear = QPushButton("Очистить всё")
        btn_clear.clicked.connect(self.clear_all)
        data_layout.addWidget(btn_clear)

        panel_layout.addWidget(group_data)

        # Масштабирование
        group_zoom = QGroupBox("Масштаб системы координат")
        zoom_layout = QHBoxLayout(group_zoom)
        self.spin_zoom = QDoubleSpinBox()
        self.spin_zoom.setRange(5.0, 60.0)
        self.spin_zoom.setValue(20.0)
        self.spin_zoom.setSingleStep(2.0)
        self.spin_zoom.valueChanged.connect(self.on_zoom_changed)
        zoom_layout.addWidget(QLabel("Масштаб (px/ед):"))
        zoom_layout.addWidget(self.spin_zoom)
        panel_layout.addWidget(group_zoom)

        # Лог работы
        panel_layout.addWidget(QLabel("Протокол отсечения:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        panel_layout.addWidget(self.log_text)

        # Начальные данные по умолчанию
        self.reset_defaults()

    def reset_defaults(self):
        # Дефолтное прямоугольное окно: [-6, -4, 6, 4]
        self.canvas.clip_rect = (-6.0, -4.0, 6.0, 4.0)
        # Дефолтный выпуклый многоугольник (правильный шестиугольник)
        r = 6.0
        poly = []
        for i in range(6):
            angle = i * (2 * math.pi / 6)
            poly.append((round(r * math.cos(angle), 2), round(r * math.sin(angle), 2)))
        self.canvas.clip_poly = poly

        # Набор демонстрационных отрезков
        self.canvas.segments = [
            ((-9.0, -2.0), (9.0, 3.0)),    # Пересекает насквозь
            ((-2.0, -2.0), (3.0, 2.0)),    # Полностью внутри
            ((8.0, 2.0), (10.0, 7.0)),     # Полностью снаружи
            ((-7.0, -6.0), (-3.0, 5.0)),   # Входит в одно ребро
            ((0.0, -7.0), (0.0, 7.0))      # Вертикальный
        ]
        self.run_clipping()

    def on_mode_changed(self, index):
        self.canvas.mode = "midpoint" if index == 0 else "cyrus_beck"
        self.run_clipping()

    def on_zoom_changed(self, val):
        self.canvas.scale = val
        self.canvas.update()

    def generate_random_segments(self):
        self.canvas.segments.clear()
        for _ in range(8):
            x1 = round(random.uniform(-11.0, 11.0), 1)
            y1 = round(random.uniform(-9.0, 9.0), 1)
            x2 = round(random.uniform(-11.0, 11.0), 1)
            y2 = round(random.uniform(-9.0, 9.0), 1)
            self.canvas.segments.append(((x1, y1), (x2, y2)))
        self.run_clipping()

    def load_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл с отрезками", "", "Text Files (*.txt);;All Files (*)"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

            # Формат из методички:
            # Строка 0: n
            # Строки 1..n: x1 y1 x2 y2
            # Строка n+1: xmin ymin xmax ymax
            n = int(lines[0].split()[0])
            parsed_segments = []
            for i in range(1, n + 1):
                parts = list(map(float, lines[i].split()))
                parsed_segments.append(((parts[0], parts[1]), (parts[2], parts[3])))

            rect_parts = list(map(float, lines[n + 1].split()))
            xmin, ymin, xmax, ymax = rect_parts[0], rect_parts[1], rect_parts[2], rect_parts[3]

            self.canvas.segments = parsed_segments
            self.canvas.clip_rect = (xmin, ymin, xmax, ymax)
            self.log_text.append(f"Успешно загружено {n} отрезков и окно [{xmin}, {ymin}, {xmax}, {ymax}]")
            self.run_clipping()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки", f"Не удалось прочитать файл:\n{str(e)}")

    def run_clipping(self):
        self.canvas.clipped_segments.clear()
        self.log_text.clear()

        algo_name = "Алгоритм средней точки" if self.canvas.mode == "midpoint" else "Алгоритм Кируса-Бека"
        self.log_text.append(f"=== {algo_name} ===")
        self.log_text.append(f"Всего отрезков: {len(self.canvas.segments)}\n")

        visible_count = 0
        for idx, (p1, p2) in enumerate(self.canvas.segments, 1):
            if self.canvas.mode == "midpoint":
                xmin, ymin, xmax, ymax = self.canvas.clip_rect
                clipped = midpoint_subdivision(p1, p2, xmin, ymin, xmax, ymax)
            else:
                clipped = cyrus_beck(p1, p2, self.canvas.clip_poly)

            if clipped:
                visible_count += 1
                self.canvas.clipped_segments.append(clipped)
                (cx1, cy1), (cx2, cy2) = clipped
                self.log_text.append(
                    f"Отрезок #{idx}: ({p1[0]:.1f}, {p1[1]:.1f}) -> ({p2[0]:.1f}, {p2[1]:.1f})\n"
                    f"  Видимая часть: ({cx1:.2f}, {cy1:.2f}) -> ({cx2:.2f}, {cy2:.2f})"
                )
            else:
                self.log_text.append(
                    f"Отрезок #{idx}: ({p1[0]:.1f}, {p1[1]:.1f}) -> ({p2[0]:.1f}, {p2[1]:.1f})\n"
                    f"  Полностью отсечён (вне окна)"
                )

        self.log_text.append(f"\nИтог: видимых отрезков: {visible_count} из {len(self.canvas.segments)}")
        self.canvas.update()

    def clear_all(self):
        self.canvas.segments.clear()
        self.canvas.clipped_segments.clear()
        self.log_text.clear()
        self.canvas.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Lab4App()
    win.show()
    sys.exit(app.exec())