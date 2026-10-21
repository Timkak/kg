import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTabWidget, 
                             QSlider, QFileDialog, QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap

class Variant6App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа 2 - Вариант 6 (PyQt6)")
        self.resize(1000, 700)
        
        self.original_image = None
        self.processed_image = None
        
        self.initUI()

    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        top_layout = QHBoxLayout()
        btn_load = QPushButton("Загрузить изображение")
        btn_load.clicked.connect(self.load_image)
        
        btn_save = QPushButton("Сохранить результат")
        btn_save.clicked.connect(self.save_image)
        
        top_layout.addWidget(btn_load)
        top_layout.addWidget(btn_save)
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        img_layout = QHBoxLayout()
        
        self.lbl_orig = QLabel("Оригинал")
        self.lbl_orig.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_orig.setStyleSheet("border: 1px solid gray; background-color: #1e1e1e; color: white;")
        self.lbl_orig.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        img_layout.addWidget(self.lbl_orig)
        
        self.lbl_proc = QLabel("Результат")
        self.lbl_proc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_proc.setStyleSheet("border: 1px solid gray; background-color: #1e1e1e; color: white;")
        self.lbl_proc.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        img_layout.addWidget(self.lbl_proc)
        
        layout.addLayout(img_layout, stretch=1)
        
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        tab1 = QWidget()
        tab1_layout = QHBoxLayout(tab1)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 255)
        self.slider.setValue(127)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        
        btn_manual = QPushButton("Применить ручной порог")
        btn_manual.clicked.connect(self.apply_manual)
        
        btn_otsu = QPushButton("Авто-порог (Метод Оцу)")
        btn_otsu.clicked.connect(self.apply_otsu)
        
        tab1_layout.addWidget(QLabel("Ручной порог:"))
        tab1_layout.addWidget(self.slider)
        tab1_layout.addWidget(btn_manual)
        tab1_layout.addSpacing(40)
        tab1_layout.addWidget(btn_otsu)
        tab1_layout.addStretch()
        tabs.addTab(tab1, "1. Глобальная пороговая обработка")
        
        tab2 = QWidget()
        tab2_layout = QHBoxLayout(tab2)
        
        btn_linear = QPushButton("Линейное контрастирование")
        btn_linear.clicked.connect(self.linear_contrast)
        btn_neg = QPushButton("Негатив")
        btn_neg.clicked.connect(self.negative)
        btn_bright = QPushButton("Осветление (+50)")
        btn_bright.clicked.connect(self.brighten)
        
        tab2_layout.addWidget(btn_linear)
        tab2_layout.addWidget(btn_neg)
        tab2_layout.addWidget(btn_bright)
        tab2_layout.addStretch()
        tabs.addTab(tab2, "2. Поэлементные операции")

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_name:
            self.original_image = cv2.imread(file_name)
            self.processed_image = self.original_image.copy()
            self.update_images()

    def save_image(self):
        if self.processed_image is not None:
            file_name, _ = QFileDialog.getSaveFileName(self, "Сохранить", "", "PNG (*.png);;JPEG (*.jpg)")
            if file_name:
                cv2.imwrite(file_name, self.processed_image)
                QMessageBox.information(self, "Успех", "Изображение сохранено!")

    def update_images(self):
        self.display_image(self.original_image, self.lbl_orig)
        self.display_image(self.processed_image, self.lbl_proc)

    def display_image(self, img, label):
        if img is None: return
        
        # Проверка, чтобы не крашилось на нулевом размере
        if label.width() <= 0 or label.height() <= 0: return

        if len(img.shape) == 3:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            
        h, w, ch = img_rgb.shape
        bytes_per_line = ch * w
        
        qt_img = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        
        scaled_pixmap = pixmap.scaled(label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_images()

    def apply_manual(self):
        if self.original_image is None: return
        gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        val = self.slider.value()
        _, self.processed_image = cv2.threshold(gray, val, 255, cv2.THRESH_BINARY)
        self.update_images()

    def apply_otsu(self):
        if self.original_image is None: return
        gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        val, self.processed_image = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        self.update_images()
        print(f"[LOG] Метод Оцу выбрал порог: {val}")

    def linear_contrast(self):
        if self.original_image is None: return
        self.processed_image = cv2.normalize(self.original_image, None, 0, 255, cv2.NORM_MINMAX)
        self.update_images()

    def negative(self):
        if self.original_image is None: return
        self.processed_image = cv2.bitwise_not(self.original_image)
        self.update_images()

    def brighten(self):
        if self.original_image is None: return
        self.processed_image = cv2.convertScaleAbs(self.original_image, alpha=1.0, beta=50)
        self.update_images()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Variant6App()
    ex.show()
    sys.exit(app.exec())