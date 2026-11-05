import sys
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QComboBox, 
                             QPushButton, QSlider, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QGroupBox, QMessageBox, QSplitter)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont

def step_by_step_line(x1, y1, x2, y2):
    """Пошаговый алгоритм (на основе y = kx + b или x = (y-b)/k)"""
    points = []
    dx = x2 - x1
    dy = y2 - y1
    
    if dx == 0 and dy == 0:
        return [(x1, y1)]
        
    if abs(dx) >= abs(dy):
        k = dy / dx
        b = y1 - k * x1
        step = 1 if x2 >= x1 else -1
        for x in range(x1, x2 + step, step):
            y = round(k * x + b)
            points.append((x, y))
    else:
        k = dx / dy
        b = x1 - k * y1
        step = 1 if y2 >= y1 else -1
        for y in range(y1, y2 + step, step):
            x = round(k * y + b)
            points.append((x, y))
    return points

def dda_line(x1, y1, x2, y2):
    """Алгоритм цифрового дифференциального анализатора (ЦДА)"""
    points = []
    dx = x2 - x1
    dy = y2 - y1
    steps = max(abs(dx), abs(dy))
    
    if steps == 0:
        return [(x1, y1)]
        
    x_inc = dx / steps
    y_inc = dy / steps
    
    x = float(x1)
    y = float(y1)
    for _ in range(steps + 1):
        points.append((round(x), round(y)))
        x += x_inc
        y += y_inc
    return points

def bresenham_line(x1, y1, x2, y2):
    """Целочисленный алгоритм Брезенхема для отрезка (все октанты)"""
    points = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    
    x, y = x1, y1
    while True:
        points.append((x, y))
        if x == x2 and y == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
    return points

def bresenham_circle(xc, yc, r):
    """Алгоритм Брезенхема для окружности (8-связная симметрия)"""
    if r < 0:
        return []
    if r == 0:
        return [(xc, yc)]
        
    points = set()
    x = 0
    y = r
    d = 3 - 2 * r
    
    def add_symmetric(cx, cy, px, py):
        for sx in (-1, 1):
            for sy in (-1, 1):
                points.add((cx + sx * px, cy + sy * py))
                points.add((cx + sx * py, cy + sy * px))

    add_symmetric(xc, yc, x, y)
    
    while x < y:
        x += 1
        if d < 0:
            d += 4 * x + 6
        else:
            y -= 1
            d += 4 * (x - y) + 10
        add_symmetric(xc, yc, x, y)
        
    return sorted(list(points))



class GridCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.scale = 25 
        self.pixels = []
        self.setMinimumSize(450, 450)

    def set_scale(self, new_scale):
        self.scale = max(5, min(new_scale, 60))
        self.update()

    def set_pixels(self, pixel_list):
        self.pixels = pixel_list
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        w = self.width()
        h = self.height()
        
        origin_x = w // 2
        origin_y = h // 2
        
        painter.fillRect(0, 0, w, h, QColor("#1e1e1e"))
        
        pen_grid = QPen(QColor("#333333"), 1, Qt.PenStyle.SolidLine)
        painter.setPen(pen_grid)
        
        start_x = origin_x % self.scale
        for x in range(start_x, w, self.scale):
            painter.drawLine(x, 0, x, h)
            
        start_y = origin_y % self.scale
        for y in range(start_y, h, self.scale):
            painter.drawLine(0, y, w, y)
            
        brush_pixel = QBrush(QColor("#00bcd4"))
        pen_pixel = QPen(QColor("#008ba3"), 1)
        painter.setBrush(brush_pixel)
        painter.setPen(pen_pixel)
        
        for px, py in self.pixels:
            screen_x = origin_x + px * self.scale
            screen_y = origin_y - (py + 1) * self.scale
            painter.drawRect(screen_x, screen_y, self.scale, self.scale)

        pen_axes = QPen(QColor("#ffffff"), 2)
        painter.setPen(pen_axes)
        painter.drawLine(0, origin_y, w, origin_y) 
        painter.drawLine(origin_x, 0, origin_x, h)  
        
        font = QFont("Monospace", 8)
        painter.setFont(font)
        painter.setPen(QColor("#aaaaaa"))
        
        step_labels = max(1, 40 // self.scale)
        for i in range(-50, 51, step_labels):
            if i == 0:
                continue
            sx = origin_x + i * self.scale
            if 0 <= sx <= w:
                painter.drawLine(sx, origin_y - 3, sx, origin_y + 3)
                painter.drawText(sx - 10, origin_y + 15, 20, 10, Qt.AlignmentFlag.AlignCenter, str(i))
                
        for j in range(-50, 51, step_labels):
            if j == 0:
                continue
            sy = origin_y - j * self.scale
            if 0 <= sy <= h:
                painter.drawLine(origin_x - 3, sy, origin_x + 3, sy)
                painter.drawText(origin_x + 6, sy - 5, 25, 10, Qt.AlignmentFlag.AlignLeft, str(j))
                
        painter.drawText(origin_x + 5, origin_y + 15, "0")



class Lab3App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа №3 — Базовые растровые алгоритмы")
        self.resize(1100, 750)
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        self.canvas = GridCanvas()
        splitter.addWidget(self.canvas)
        
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        splitter.addWidget(panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        
        group_algo = QGroupBox("Параметры растеризации")
        algo_layout = QVBoxLayout(group_algo)
        
        algo_layout.addWidget(QLabel("Алгоритм:"))
        self.algo_combo = QComboBox()
        self.algo_combo.addItems([
            "1. Пошаговый алгоритм (отрезок)",
            "2. Алгоритм ЦДА (отрезок)",
            "3. Алгоритм Брезенхема (отрезок)",
            "4. Алгоритм Брезенхема (окружность)"
        ])
        self.algo_combo.currentIndexChanged.connect(self.on_algo_changed)
        algo_layout.addWidget(self.algo_combo)
        
        self.lbl_p1 = QLabel("Начало отрезка (X1, Y1):")
        algo_layout.addWidget(self.lbl_p1)
        row_p1 = QHBoxLayout()
        self.input_x1 = QLineEdit("0")
        self.input_y1 = QLineEdit("0")
        row_p1.addWidget(QLabel("X1:")); row_p1.addWidget(self.input_x1)
        row_p1.addWidget(QLabel("Y1:")); row_p1.addWidget(self.input_y1)
        algo_layout.addLayout(row_p1)
        
        self.lbl_p2 = QLabel("Конец отрезка (X2, Y2):")
        algo_layout.addWidget(self.lbl_p2)
        row_p2 = QHBoxLayout()
        self.input_x2 = QLineEdit("12")
        self.input_y2 = QLineEdit("7")
        row_p2.addWidget(QLabel("X2:")); row_p2.addWidget(self.input_x2)
        row_p2.addWidget(QLabel("Y2:")); row_p2.addWidget(self.input_y2)
        algo_layout.addLayout(row_p2)
        
        btn_draw = QPushButton("Отрисовать")
        btn_draw.clicked.connect(self.draw_algorithm)
        algo_layout.addWidget(btn_draw)
        
        btn_clear = QPushButton("Очистить")
        btn_clear.clicked.connect(self.clear_canvas)
        algo_layout.addWidget(btn_clear)
        
        panel_layout.addWidget(group_algo)
        
        group_zoom = QGroupBox("Масштаб дискретной сетки")
        zoom_layout = QHBoxLayout(group_zoom)
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(8, 50)
        self.zoom_slider.setValue(25)
        self.zoom_slider.valueChanged.connect(self.canvas.set_scale)
        zoom_layout.addWidget(QLabel("Крупнее / Мельче:"))
        zoom_layout.addWidget(self.zoom_slider)
        panel_layout.addWidget(group_zoom)
        
        btn_bench = QPushButton("Запустить анализ времени (100 000 итераций)")
        btn_bench.clicked.connect(self.run_benchmark)
        panel_layout.addWidget(btn_bench)
        
        panel_layout.addWidget(QLabel("Трассировка вычислений пикселей:"))
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Шаг i", "X (растр)", "Y (растр)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        panel_layout.addWidget(self.table)

    def on_algo_changed(self, index):
        if index == 3:
            self.lbl_p1.setText("Центр окружности (Xc, Yc):")
            self.lbl_p2.setText("Радиус (R):")
            self.input_x2.setText("8")
            self.input_y2.setEnabled(False)
        else:
            self.lbl_p1.setText("Начало отрезка (X1, Y1):")
            self.lbl_p2.setText("Конец отрезка (X2, Y2):")
            self.input_y2.setEnabled(True)

    def draw_algorithm(self):
        try:
            x1 = int(self.input_x1.text())
            y1 = int(self.input_y1.text())
            algo_idx = self.algo_combo.currentIndex()
            
            if algo_idx == 3:
                r = int(self.input_x2.text())
                pixels = bresenham_circle(x1, y1, r)
            else:
                x2 = int(self.input_x2.text())
                y2 = int(self.input_y2.text())
                if algo_idx == 0:
                    pixels = step_by_step_line(x1, y1, x2, y2)
                elif algo_idx == 1:
                    pixels = dda_line(x1, y1, x2, y2)
                else:
                    pixels = bresenham_line(x1, y1, x2, y2)
            
            self.canvas.set_pixels(pixels)
            self.update_trace_table(pixels)
        except ValueError:
            QMessageBox.critical(self, "Ошибка", "Все координаты и радиус должны быть целыми числами!")

    def update_trace_table(self, pixels):
        self.table.setRowCount(len(pixels))
        for step, (px, py) in enumerate(pixels):
            self.table.setItem(step, 0, QTableWidgetItem(str(step + 1)))
            self.table.setItem(step, 1, QTableWidgetItem(str(px)))
            self.table.setItem(step, 2, QTableWidgetItem(str(py)))

    def clear_canvas(self):
        self.canvas.set_pixels([])
        self.table.setRowCount(0)

    def run_benchmark(self):
        n = 100000
        x1, y1, x2, y2 = 2, 3, 45, 38
        r = 30
        
        t0 = time.perf_counter()
        for _ in range(n):
            step_by_step_line(x1, y1, x2, y2)
        t_step = (time.perf_counter() - t0) * 1000 / n
        
        t0 = time.perf_counter()
        for _ in range(n):
            dda_line(x1, y1, x2, y2)
        t_dda = (time.perf_counter() - t0) * 1000 / n
        
        t0 = time.perf_counter()
        for _ in range(n):
            bresenham_line(x1, y1, x2, y2)
        t_bres = (time.perf_counter() - t0) * 1000 / n
        
        t0 = time.perf_counter()
        for _ in range(n):
            bresenham_circle(0, 0, r)
        t_circ = (time.perf_counter() - t0) * 1000 / n
        
        msg = (f"Результаты среднего времени выполнения (N={n:,}):\n\n"
               f"1. Пошаговый алгоритм: {t_step:.5f} мс\n"
               f"2. Алгоритм ЦДА: {t_dda:.5f} мс\n"
               f"3. Брезенхем (отрезок): {t_bres:.5f} мс\n"
               f"4. Брезенхем (окружность): {t_circ:.5f} мс\n\n")
        QMessageBox.information(self, "Анализ времени", msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Lab3App()
    window.show()
    sys.exit(app.exec())