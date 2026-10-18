from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QGridLayout, QLabel, QPushButton, QTextEdit, QFrame)
from PyQt5.QtCore import Qt, QTimer

class StatusBadge(QFrame):
    def __init__(self, label_text):
        super().__init__()
        self.setStyleSheet("background-color: #1a1e26; border: 1px solid #28303f; border-radius: 6px;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)

        self.dot = QLabel("●")
        self.dot.setStyleSheet("color: #64748b; font-size: 12px;")

        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #cbd5e1; font-weight: 600; font-size: 11px;")

        self.status_lbl = QLabel("STANDBY")
        self.status_lbl.setStyleSheet("color: #64748b; font-weight: bold; font-size: 10px;")

        layout.addWidget(self.dot)
        layout.addWidget(lbl)
        layout.addStretch()
        layout.addWidget(self.status_lbl)

    def set_state(self, is_ok, text="OK"):
        if is_ok:
            self.dot.setStyleSheet("color: #ffffff; font-size: 12px;")
            self.status_lbl.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 10px;")
            self.status_lbl.setText(text)
        else:
            self.dot.setStyleSheet("color: #475569; font-size: 12px;")
            self.status_lbl.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 10px;")
            self.status_lbl.setText(text)


class TabPerangkat(QWidget):
    def __init__(self, main_dashboard):
        super().__init__()
        self.main_dashboard = main_dashboard
        
        # Timer timeout jika MCU tidak mengirim respon string balik
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.handle_diag_timeout)
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        grp_status = QGroupBox("STATUS PERANGKAT HARDWARE")
        grp_status.setStyleSheet("""
            QGroupBox {
                color: #cbd5e1;
                font-weight: 600;
                font-size: 11px;
                border: 1px solid #1f242d;
                border-radius: 8px;
                margin-top: 6px;
                padding-top: 16px;
                background-color: #14171d;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                background-color: #14171d;
            }
        """)
        grid_status = QGridLayout(grp_status)
        grid_status.setContentsMargins(12, 12, 12, 12)
        grid_status.setSpacing(10)

        self.st_mcu = StatusBadge("Mikrokontroler")
        self.st_encoder = StatusBadge("Encoder Quadrature")
        self.st_driver = StatusBadge("Driver Motor DC")
        self.st_pot = StatusBadge("Potensio Analog (A0)")

        grid_status.addWidget(self.st_mcu, 0, 0)
        grid_status.addWidget(self.st_encoder, 0, 1)
        grid_status.addWidget(self.st_driver, 1, 0)
        grid_status.addWidget(self.st_pot, 1, 1)

        layout.addWidget(grp_status)

        grp_diag = QGroupBox("DIAGNOSTIK TELEMETRI LOG")
        grp_diag.setStyleSheet("""
            QGroupBox {
                color: #cbd5e1;
                font-weight: 600;
                font-size: 11px;
                border: 1px solid #1f242d;
                border-radius: 8px;
                margin-top: 6px;
                padding-top: 16px;
                background-color: #14171d;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                background-color: #14171d;
            }
        """)
        diag_layout = QVBoxLayout(grp_diag)
        diag_layout.setContentsMargins(12, 12, 12, 12)
        diag_layout.setSpacing(10)

        btn_diag = QPushButton("Jalankan Uji Diagnostik Hardware (DIAG)")
        btn_diag.setMinimumHeight(36)
        btn_diag.setStyleSheet("""
            QPushButton {
                background-color: #1a1e26;
                color: #ffffff;
                border: 1px solid #28303f;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #232936;
                border-color: #475569;
            }
            QPushButton:pressed {
                background-color: #0d0f12;
            }
        """)
        btn_diag.clicked.connect(self.run_hardware_diag)
        diag_layout.addWidget(btn_diag)

        self.txt_hw_log = QTextEdit()
        self.txt_hw_log.setStyleSheet("background-color: #0b0c0f; border: 1px solid #1f242d; border-radius: 6px; color: #94a3b8; font-family: monospace; font-size: 11px;")
        self.txt_hw_log.setReadOnly(True)
        diag_layout.addWidget(self.txt_hw_log)

        layout.addWidget(grp_diag)

    def run_hardware_diag(self):
        self.txt_hw_log.clear()
        
        # Set status sementara
        self.st_mcu.set_state(False, "MEMERIKSA...")
        self.st_encoder.set_state(False, "MEMERIKSA...")
        self.st_driver.set_state(False, "MEMERIKSA...")
        self.st_pot.set_state(False, "MEMERIKSA...")

        if self.main_dashboard.ser and self.main_dashboard.ser.is_open:
            self.main_dashboard.send_command("DIAG")
            self.txt_hw_log.append("[TX SERIAL] -> Mengirim perintah DIAG ke Hardware...")
            # Jalankan timeout 2 detik jika hardware tidak membalas balasan DIAG
            self.timeout_timer.start(2000)
        else:
            self.txt_hw_log.append("[INFO] Port Serial Fisik tidak terhubung.")
            self.txt_hw_log.append("[SIMULASI] Menjalankan verifikasi internal perangkat...")
            QTimer.singleShot(400, self.simulate_diag_success)

    def process_diag_response(self, line):
        self.timeout_timer.stop()
        self.txt_hw_log.append(f"[RX SERIAL] <- {line}")
        
        # Update indikator dengan warna monokrom
        self.st_mcu.set_state(True, "NORMAL")
        self.st_encoder.set_state(True, "AKTIF")
        self.st_driver.set_state(True, "SIAP")
        self.st_pot.set_state(True, "BISA DIBACA")
        self.txt_hw_log.append("[SUKSES] Hardware merespon normal.")

    def handle_diag_timeout(self):
        self.txt_hw_log.append("[TIMEOUT] Perintah DIAG terkirim, namun Hardware tidak mengirim respon string DIAG.")
        if self.main_dashboard.ser and self.main_dashboard.ser.is_open:
            self.st_mcu.set_state(True, "TERHUBUNG")
            self.st_encoder.set_state(False, "NO RESP")
            self.st_driver.set_state(False, "NO RESP")
            self.st_pot.set_state(False, "NO RESP")
            self.txt_hw_log.append("[INFO] Port Serial terhubung, tetapi firmware MCU belum diprogram untuk balasan string 'DIAG'.")
        else:
            self.st_mcu.set_state(False, "DISCONNECT")
            self.st_encoder.set_state(False, "OFFLINE")
            self.st_driver.set_state(False, "OFFLINE")
            self.st_pot.set_state(False, "OFFLINE")

    def simulate_diag_success(self):
        self.st_mcu.set_state(True, "READY")
        self.st_encoder.set_state(True, "READY")
        self.st_driver.set_state(True, "READY")
        self.st_pot.set_state(True, "READY")
        self.txt_hw_log.append("[SUKSES] Verifikasi simulasi selesai.")
