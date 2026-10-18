from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QPushButton
from alat.mode import TabNamaMode
from alat.enkoder import TabEnkoder
from alat.perangkat import TabPerangkat
from alat.sinyal import TabSinyal
from alat.rumus import TabRumus
from alat.ml import TabML

class AdvancedToolsDialog(QDialog):
    def __init__(self, serial_conn, engine, main_dashboard):
        super().__init__(main_dashboard)
        self.ser = serial_conn
        self.engine = engine
        self.main_dashboard = main_dashboard

        self.setWindowTitle("Panel Pengaturan & Toolkit Sistem")
        self.resize(780, 580)
        self.apply_theme()
        self.init_ui()

    def apply_theme(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0d0f12;
            }
            QTabWidget::pane {
                border: 1px solid #1f242d;
                border-radius: 8px;
                background-color: #14171d;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #1a1e26;
                color: #94a3b8;
                border: 1px solid #1f242d;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
                font-size: 11px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #14171d;
                color: #ffffff;
                border-color: #475569;
                border-bottom: 2px solid #ffffff;
            }
            QTabBar::tab:hover:!selected {
                background-color: #232936;
                color: #ffffff;
            }
            QPushButton {
                background-color: #1a1e26;
                color: #ffffff;
                border: 1px solid #28303f;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #232936;
                border-color: #475569;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #0d0f12;
            }
            QLabel {
                color: #cbd5e1;
            }
        """)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        self.tabs = QTabWidget()

        self.tab_mode = TabNamaMode(self.main_dashboard)
        self.tab_enkoder = TabEnkoder(self.main_dashboard)
        self.tab_perangkat = TabPerangkat(self.main_dashboard)
        self.tab_sinyal = TabSinyal(self.main_dashboard)
        self.tab_rumus = TabRumus(self.main_dashboard)
        self.tab_ml = TabML(self.main_dashboard)

        self.tabs.addTab(self.tab_mode, "Custom Mode")
        self.tabs.addTab(self.tab_enkoder, "Kalibrasi Encoder")
        #self.tabs.addTab(self.tab_perangkat, "Cek Hardware")
        self.tabs.addTab(self.tab_sinyal, "Generator Sinyal")
        self.tabs.addTab(self.tab_rumus, "Tunning PID")
        #self.tabs.addTab(self.tab_ml, "ML Optimizer")

        main_layout.addWidget(self.tabs)

        btn_close = QPushButton("Tutup Panel")
        btn_close.clicked.connect(self.close)
        main_layout.addWidget(btn_close)

    def parse_diag_response(self, line):
        self.tab_perangkat.process_diag_response(line)

    def process_telemetry_calib(self, actual):
        self.tab_enkoder.update_live_angle(actual)

    def closeEvent(self, event):
        if hasattr(self.tab_ml, 'worker') and self.tab_ml.worker and self.tab_ml.worker.isRunning():
            self.tab_ml.worker.stop()
            self.tab_ml.worker.wait()
        event.accept()
