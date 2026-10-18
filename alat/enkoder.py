import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QGridLayout, QLabel, QPushButton, QTextEdit, QFrame, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont

class VisualEncoderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        self.angle = 0.0

    def set_angle(self, angle):
        self.angle = angle % 360.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        radius = min(w, h) / 2 - 20

        # Ring Luar
        painter.setBrush(QBrush(QColor("#14171d")))
        painter.setPen(QPen(QColor("#1f242d"), 2))
        painter.drawEllipse(int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2))

        # Ring Dalam
        inner_r = radius - 12
        painter.setBrush(QBrush(QColor("#0d0f12")))
        painter.setPen(QPen(QColor("#28303f"), 1))
        painter.drawEllipse(int(cx - inner_r), int(cy - inner_r), int(inner_r * 2), int(inner_r * 2))

        # Garis Skala Derajat
        for i in range(36):
            deg = i * 10
            rad = math.radians(deg - 90)
            is_major = (deg % 30 == 0)
            t_len = 10 if is_major else 5

            x1 = cx + inner_r * math.cos(rad)
            y1 = cy + inner_r * math.sin(rad)
            x2 = cx + (inner_r - t_len) * math.cos(rad)
            y2 = cy + (inner_r - t_len) * math.sin(rad)

            pen_color = QColor("#94a3b8") if is_major else QColor("#334155")
            painter.setPen(QPen(pen_color, 1.5 if is_major else 1))
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Label Kardinal (0°, 90°, 180°, 270°)
        painter.setPen(QColor("#94a3b8"))
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        labels = [(0, "0°"), (90, "90°"), (180, "180°"), (270, "270°")]
        for deg, txt in labels:
            rad = math.radians(deg - 90)
            lx = cx + (inner_r - 22) * math.cos(rad)
            ly = cy + (inner_r - 22) * math.sin(rad)
            painter.drawText(int(lx - 15), int(ly - 8), 30, 16, Qt.AlignCenter, txt)

        # Jarum Indikator Posisi (Putih Solid)
        angle_rad = math.radians(self.angle - 90)
        nx = cx + (inner_r - 10) * math.cos(angle_rad)
        ny = cy + (inner_r - 10) * math.sin(angle_rad)

        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.drawLine(int(cx), int(cy), int(nx), int(ny))

        # Pivot Tengah
        painter.setBrush(QBrush(QColor("#1a1e26")))
        painter.setPen(QPen(QColor("#ffffff"), 1.5))
        painter.drawEllipse(int(cx - 8), int(cy - 8), 16, 16)

        # Display Teks Sudut
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Monospace", 10, QFont.Bold))
        painter.drawText(int(cx - 40), int(cy + radius + 2), 80, 18, Qt.AlignCenter, f"{self.angle:.1f}°")


class TabEnkoder(QWidget):
    def __init__(self, main_dashboard):
        super().__init__()
        self.main_dashboard = main_dashboard
        self.is_recording = False
        self.start_angle = 0.0
        self.accumulated_angle = 0.0
        self.last_raw_angle = 0.0
        self.calculated_ppr = 0.0
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        left_box = QVBoxLayout()
        grp = QGroupBox("KALIBRASI PULSA ENCODER")
        gl = QGridLayout(grp)
        gl.setSpacing(10)

        gl.addWidget(QLabel("Status Perekaman:"), 0, 0)
        self.lbl_status = QLabel("STANBY")
        self.lbl_status.setStyleSheet("color: #94a3b8; font-weight: 600;")
        gl.addWidget(self.lbl_status, 0, 1)

        gl.addWidget(QLabel("Sudut Terbaca Hardware:"), 1, 0)
        self.lbl_live_deg = QLabel("0.0°")
        self.lbl_live_deg.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 13px; font-family: monospace;")
        gl.addWidget(self.lbl_live_deg, 1, 1)

        gl.addWidget(QLabel("Kalkulasi PPR Fisik:"), 2, 0)
        self.lbl_calc_ppr = QLabel("0 PPR")
        self.lbl_calc_ppr.setStyleSheet("color: #cbd5e1; font-weight: bold; font-size: 13px; font-family: monospace;")
        gl.addWidget(self.lbl_calc_ppr, 2, 1)

        btn_style = """
            QPushButton {
                background-color: #1a1e26;
                color: #cbd5e1;
                border: 1px solid #28303f;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #232936;
                border-color: #475569;
                color: #ffffff;
            }
        """

        self.btn_rec = QPushButton("Mulai")
        self.btn_rec.setStyleSheet(btn_style)
        self.btn_rec.clicked.connect(self.toggle_recording)
        gl.addWidget(self.btn_rec, 3, 0, 1, 2)

        self.btn_apply = QPushButton("Terapkan Hasil Kalibrasi")
        self.btn_apply.setStyleSheet(btn_style)
        self.btn_apply.clicked.connect(self.apply_calculated_ppr)
        gl.addWidget(self.btn_apply, 4, 0, 1, 2)

        left_box.addWidget(grp)

        self.txt_encoder_log = QTextEdit()
        self.txt_encoder_log.setStyleSheet("background-color: #0b0c0f; border: 1px solid #1f242d; border-radius: 6px; color: #94a3b8; font-family: monospace;")
        self.txt_encoder_log.setReadOnly(True)
        left_box.addWidget(self.txt_encoder_log)

        layout.addLayout(left_box, 6)

        right_card = QFrame()
        right_card.setStyleSheet("background-color: #14171d; border: 1px solid #1f242d; border-radius: 8px;")
        rc_layout = QVBoxLayout(right_card)
        rc_layout.setContentsMargins(12, 12, 12, 12)

        lbl_viz = QLabel("PUTAR MOTOR SECARA MANUAL")
        lbl_viz.setStyleSheet("color: #94a3b8; font-weight: 600; font-size: 11px;")
        lbl_viz.setAlignment(Qt.AlignCenter)
        rc_layout.addWidget(lbl_viz)

        self.encoder_dial = VisualEncoderWidget()
        rc_layout.addWidget(self.encoder_dial, 0, Qt.AlignCenter)

        layout.addWidget(right_card, 4)

    def toggle_recording(self):
        if not self.is_recording:
            self.is_recording = True
            self.accumulated_angle = 0.0
            self.start_angle = self.main_dashboard.actual_val
            self.last_raw_angle = self.start_angle
            self.lbl_status.setText("MEMINDAI ROTASI FISIK...")
            self.lbl_status.setStyleSheet("color: #ffffff; font-weight: bold;")
            self.btn_rec.setText("Selesai Rekam (Hitung PPR)")
            self.txt_encoder_log.append("Silakan putar motor manual 1 putaran penuh (360°)...")
        else:
            self.is_recording = False
            self.lbl_status.setText("REKAM SELESAI")
            self.lbl_status.setStyleSheet("color: #cbd5e1; font-weight: 600;")
            self.btn_rec.setText("Mulai")

            current_ppr = self.main_dashboard.panel_pid.spn_ppr.value()
            if abs(self.accumulated_angle) > 10.0:
                self.calculated_ppr = round(current_ppr * (abs(self.accumulated_angle) / 360.0))
                self.lbl_calc_ppr.setText(f"{int(self.calculated_ppr)} PPR")
                self.txt_encoder_log.append(f"[HASIL KALIBRASI] Total rotasi fisik: {self.accumulated_angle:.1f}°. Estimasi PPR Hardware: {int(self.calculated_ppr)} PPR.")
            else:
                self.txt_encoder_log.append("[PERINGATAN] Gerakan motor terlalu kecil untuk menghitung PPR.")

    def update_live_angle(self, actual_angle):
        self.encoder_dial.set_angle(actual_angle)
        self.lbl_live_deg.setText(f"{actual_angle:.1f}°")

        if self.is_recording:
            delta = actual_angle - self.last_raw_angle
            if delta > 180.0: delta -= 360.0
            elif delta < -180.0: delta += 360.0
            self.accumulated_angle += delta
            self.last_raw_angle = actual_angle
            self.txt_encoder_log.append(f"  └─ Delta Sudut Realtime: {self.accumulated_angle:.1f}°")

    def apply_calculated_ppr(self):
        if self.calculated_ppr > 0:
            self.main_dashboard.panel_pid.spn_ppr.setValue(int(self.calculated_ppr))
            self.main_dashboard.send_ppr()
            QMessageBox.information(self, "Berhasil", f"PPR Hardware berhasil diperbarui ke {int(self.calculated_ppr)} PPR!")
        else:
            QMessageBox.warning(self, "Peringatan", "Lakukan perekaman rotasi manual terlebih dahulu!")
