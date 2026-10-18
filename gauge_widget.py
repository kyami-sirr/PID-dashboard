import math
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QColor, QFont


class AngleGaugeWidget(QWidget):
    def __init__(self, show_text=True, parent=None):
        super().__init__(parent)
        self.target_angle = 0.0
        self.actual_angle = 0.0
        self.draw_actual = 0.0
        self.draw_target = 0.0
        self.show_text = show_text

    def set_angles(self, target, actual):
        # Langsung set nilai mentah dari Arduino tanpa interpolasi animasi LERP
        self.target_angle = float(target)
        self.actual_angle = float(actual)
        self.draw_actual = float(actual)
        self.draw_target = float(target)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        size = min(w, h) - 20
        cx, cy = w / 2, h / 2
        radius = size / 2

        # Ring Latar Depan & Dial Gauge
        painter.setPen(QPen(QColor("#28303f"), 2))
        painter.setBrush(QColor("#14171d"))
        painter.drawEllipse(int(cx - radius), int(cy - radius), int(size), int(size))

        # Skala Ticks Derajat
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        for deg in range(0, 360, 30):
            rad = math.radians(deg - 90)
            x1 = cx + (radius - 14) * math.cos(rad)
            y1 = cy + (radius - 14) * math.sin(rad)
            x2 = cx + (radius - 4) * math.cos(rad)
            y2 = cy + (radius - 4) * math.sin(rad)
            painter.setPen(QPen(QColor("#3d495d"), 2))
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

            val = deg if deg <= 180 else deg - 360
            lx = cx + (radius - 28) * math.cos(rad)
            ly = cy + (radius - 28) * math.sin(rad)
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(int(lx - 20), int(ly - 10), 40, 20, Qt.AlignCenter, str(val))

        # Jarum Target (Garis Putus-Putus Cyan)
        if self.show_text:
            t_rad = math.radians(self.draw_target - 90)
            tx = cx + (radius - 20) * math.cos(t_rad)
            ty = cy + (radius - 20) * math.sin(t_rad)
            painter.setPen(QPen(QColor("#64748b"), 2, Qt.DashLine))
            painter.drawLine(int(cx), int(cy), int(tx), int(ty))

        # Jarum Posisi Aktual Mentah dari Arduino
        a_rad = math.radians(self.draw_actual - 90)
        ax = cx + (radius - 10) * math.cos(a_rad)
        ay = cy + (radius - 10) * math.sin(a_rad)
        painter.setPen(QPen(QColor("#f1f5f9"), 3))
        painter.drawLine(int(cx), int(cy), int(ax), int(ay))

        # Titik Tengah Gauge
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#f1f5f9"))
        painter.drawEllipse(int(cx - 6), int(cy - 6), 12, 12)

        # Teks Indikator Real-time
        if self.show_text:
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(int(cx - 100), int(cy - 55), 200, 20, Qt.AlignCenter, f"TARGET: {self.target_angle:.1f}°")

            painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
            painter.setPen(QColor("#f1f5f9"))
            painter.drawText(int(cx - 120), int(cy + 40), 240, 25, Qt.AlignCenter, f"ACTUAL: {self.actual_angle:.1f}°")
