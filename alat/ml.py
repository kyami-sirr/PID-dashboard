import json
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, 
    QPushButton, QGroupBox, QScrollArea, QLabel,
    QRadioButton, QButtonGroup, QApplication
)
from PyQt5.QtCore import pyqtSignal


class TabHideTools(QWidget):
    """
    Tab Pengaturan Visibilitas Fitur & Mode Tampilan.
    Latar belakang dijamin gelap netral tanpa box putih.
    """
    visibility_changed = pyqtSignal(dict)

    def __init__(self, parent=None, config_path="config_settings.json"):
        super().__init__(parent)
        self.config_path = config_path
        self.hidden_states = {}
        self.checkbox_map = {}
        self.load_config()
        self.init_ui()
        self.apply_dark_style()

    def apply_dark_style(self):
        """Menghilangkan background putih pada QScrollArea secara total."""
        self.setStyleSheet("""
            QWidget {
                background-color: #121419;
                color: #e0e0e0;
            }
            QScrollArea {
                border: none;
                background-color: #121419;
            }
            QScrollArea > QWidget > QWidget {
                background-color: #121419;
            }
            QGroupBox {
                border: 1px solid #2d3139;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: #a8b2c1;
                background-color: #1a1d24;
            }
            QLabel {
                color: #dcdfe6;
                background-color: transparent;
            }
            QCheckBox, QRadioButton {
                color: #dcdfe6;
                font-size: 13px;
                padding: 4px;
                background-color: transparent;
            }
            QPushButton {
                background-color: #1a1d24;
                color: #e0e0e0;
                border: 1px solid #3a3f4d;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #222630;
                border-color: #5c6370;
            }
        """)

    def load_config(self):
        """Memuat preferensi tersimpan dari JSON."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    self.hidden_states = data.get("visibility_settings", {})
            except Exception:
                self.hidden_states = {}

    def save_config(self):
        """Menyimpan preferensi ke JSON."""
        data = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data["visibility_settings"] = self.hidden_states
        try:
            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def get_main_dashboard(self):
        """Mencari instance ControlLabDashboard utama."""
        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, "panel_koneksi") or widget.__class__.__name__ == "ControlLabDashboard":
                return widget
        return None

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # 1. Selection Mode Tampilan Monitoring Respon
        group_view = QGroupBox("MODE TAMPILAN MONITORING KECEPATAN & POSISI")
        layout_view = QVBoxLayout()
        self.btn_group_view = QButtonGroup(self)

        self.radio_grafik = QRadioButton("Tampilan Grafik Respon (Plot Line)")
        self.radio_gauge_pos = QRadioButton("Tampilan Bulat Dial Posisi Sudut")
        self.radio_speedometer = QRadioButton("Tampilan Speedometer RPM (Jarum Analog + Digital)")

        self.btn_group_view.addButton(self.radio_grafik, 0)
        self.btn_group_view.addButton(self.radio_gauge_pos, 1)
        self.btn_group_view.addButton(self.radio_speedometer, 2)

        view_mode = self.hidden_states.get("monitoring_view_mode", 0)
        if view_mode == 1:
            self.radio_gauge_pos.setChecked(True)
        elif view_mode == 2:
            self.radio_speedometer.setChecked(True)
        else:
            self.radio_grafik.setChecked(True)

        self.radio_grafik.toggled.connect(self.on_view_mode_changed)
        self.radio_gauge_pos.toggled.connect(self.on_view_mode_changed)
        self.radio_speedometer.toggled.connect(self.on_view_mode_changed)

        layout_view.addWidget(self.radio_grafik)
        layout_view.addWidget(self.radio_gauge_pos)
        layout_view.addWidget(self.radio_speedometer)
        group_view.setLayout(layout_view)
        scroll_layout.addWidget(group_view)

        # 2. Daftar Komponen yang Dapat Dihide/Show
        self.elements = {
            "Metrik Angka Atas (Top Metric Cards)": [
                ("card_status", "Status Sistem / Mode"),
                ("card_sp", "Nilai Setpoint (SP)"),
                ("card_pv", "Process Variable (PV / RPM)"),
                ("card_pwm", "Sinyal Output PWM"),
                ("card_error", "Nilai Error Saat Ini"),
                ("card_overshoot", "Nilai Overshoot (%)"),
                ("card_risetime", "Nilai Rise Time (s)"),
                ("card_settling", "Nilai Settling Time (s)"),
                ("card_steady_error", "Steady State Error")
            ],
            "Daftar Mode Kontrol Presisi": [
                ("mode_off", "0. Off"),
                ("mode_openloop", "1. Open Loop"),
                ("mode_closeloop", "2. Close Loop"),
                ("mode_pid_speed", "3. PID Kecepatan"),
                ("mode_pid_pos", "4. PID Posisi"),
                ("mode_potensio", "5. Potensio")
            ],
            "Panel Utama Dashboard": [
                ("panel_koneksi", "Panel Koneksi Serial"),
                ("panel_pid", "Panel Parameter PID"),
                ("panel_grafik", "Panel Grafik Respon / Speedometer"),
                ("panel_skema", "Panel Skema Sistem"),
                ("panel_kartu", "Panel Metrics Atas")
            ],
            "Tombol Aksi Dashboard": [
                ("btn_export_csv", "Tombol Ekspor CSV"),
                ("btn_reset_graph", "Tombol Reset Grafik"),
                ("btn_emergency", "Tombol Emergency Stop"),
                ("chk_sim_mode", "Checkbox Mode Simulasi")
            ]
        }

        for group_name, items in self.elements.items():
            group = QGroupBox(group_name)
            group_layout = QVBoxLayout()
            for key, label in items:
                cb = QCheckBox(f"Tampilkan {label}")
                is_visible = self.hidden_states.get(key, True)
                cb.setChecked(is_visible)
                cb.toggled.connect(lambda checked, k=key: self.on_toggle(k, checked))
                self.checkbox_map[key] = cb
                group_layout.addWidget(cb)
            group.setLayout(group_layout)
            scroll_layout.addWidget(group)

        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Baris Tombol Aksi
        btn_layout = QHBoxLayout()
        btn_show_all = QPushButton("Tampilkan Semua Fitur")
        btn_show_all.clicked.connect(self.show_all)

        btn_layout.addWidget(btn_show_all)
        main_layout.addLayout(btn_layout)

    def on_view_mode_changed(self):
        """Mengalihkan mode monitoring (0 = Grafik, 1 = Dial Posisi, 2 = Speedometer RPM)."""
        if self.radio_gauge_pos.isChecked():
            mode_idx = 1
        elif self.radio_speedometer.isChecked():
            mode_idx = 2
        else:
            mode_idx = 0

        self.hidden_states["monitoring_view_mode"] = mode_idx
        self.save_config()

        dashboard = self.get_main_dashboard()
        if dashboard and hasattr(dashboard, "panel_grafik"):
            dashboard.panel_grafik.set_monitoring_mode(mode_idx)

    def on_toggle(self, key: str, is_visible: bool):
        """Menerapkan status visibilitas langsung ke dashboard utama."""
        self.hidden_states[key] = is_visible
        self.save_config()

        dashboard = self.get_main_dashboard()
        if not dashboard:
            return

        # 1. Kontrol Kartu Metrik Atas & Panel Dashboard
        target_widget = getattr(dashboard, key, None)
        if not target_widget and hasattr(dashboard, "panel_kartu"):
            target_widget = getattr(dashboard.panel_kartu, key, None)
        if not target_widget and hasattr(dashboard, "panel_grafik"):
            target_widget = getattr(dashboard.panel_grafik, key, None)
        if not target_widget and hasattr(dashboard, "panel_koneksi"):
            target_widget = getattr(dashboard.panel_koneksi, key, None)

        if target_widget and hasattr(target_widget, "setVisible"):
            target_widget.setVisible(is_visible)

        # 2. Kontrol Mode Kontrol Dropdown
        mode_mapping = {
            "mode_off": ["0. Off", "Off", "0. (Off)"],
            "mode_openloop": ["1. Open Loop", "Open Loop"],
            "mode_closeloop": ["2. Close Loop", "Close Loop"],
            "mode_pid_speed": ["3. PID Kecepatan", "PID Kecepatan"],
            "mode_pid_pos": ["4. PID Posisi", "PID Posisi"],
            "mode_potensio": ["5. Potensio", "Potensio", "Potensio Manual"]
        }

        if key in mode_mapping:
            self._update_mode_visibility(dashboard, mode_mapping[key], is_visible)

    def _update_mode_visibility(self, dashboard, mode_aliases: list, is_visible: bool):
        """Menambah/menghapus pilihan mode pada ComboBox."""
        combos = []
        if hasattr(dashboard, "combo_mode"):
            combos.append(dashboard.combo_mode)
        if hasattr(dashboard, "panel_pid") and hasattr(dashboard.panel_pid, "combo_mode"):
            combos.append(dashboard.panel_pid.combo_mode)

        for combo in combos:
            for alias in mode_aliases:
                idx = combo.findText(alias)
                if not is_visible and idx >= 0:
                    combo.removeItem(idx)
                elif is_visible and idx < 0:
                    combo.addItem(alias)

    def show_all(self):
        """Mencentang ulang semua fitur."""
        for cb in self.checkbox_map.values():
            cb.setChecked(True)


# Alias Kompatibilitas Impor
TabML = TabHideTools
TabMachineLearning = TabHideTools
