import json
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QLineEdit, QSpinBox, QPushButton, 
    QGroupBox, QMessageBox, QApplication, QListView, QFormLayout
)
from PyQt5.QtCore import Qt, pyqtSignal


class TabCustomMode(QWidget):
    mode_updated = pyqtSignal(dict)

    MODE_KEYS = {
        "Mode 0": "mode_off",
        "Mode 1": "mode_openloop",
        "Mode 2": "mode_closeloop",
        "Mode 3": "mode_pid_speed",
        "Mode 4": "mode_pid_pos",
        "Mode 5": "mode_potensio"
    }

    def __init__(self, parent=None, config_path="config_settings.json"):
        super().__init__(parent)
        self.config_path = config_path
        self.modes = {}
        self.visibility_settings = {}
        self.load_config()
        self.init_ui()
        self.apply_dark_style()

    def showEvent(self, event):
        """Otomatis memuat ulang data dari JSON setiap kali tab/dialog dibuka kembali."""
        super().showEvent(event)
        self.load_config()
        if hasattr(self, 'combo_mode'):
            self.on_mode_changed(self.combo_mode.currentText())

    def apply_dark_style(self):
        """Menerapkan tampilan Dark Theme seragam pada QComboBox dan Popup List."""
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #2d3139;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 14px;
                font-weight: bold;
                color: #a8b2c1;
            }
            QLabel {
                color: #dcdfe6;
                font-size: 12px;
            }
            QComboBox {
                background-color: #1a1d24;
                color: #e0e0e0;
                border: 1px solid #3a3f4d;
                border-radius: 4px;
                padding: 5px 8px;
                font-size: 13px;
            }
            QComboBox:focus {
                border: 1px solid #5c6370;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #14171d;
                color: #cbd5e1;
                selection-background-color: #1e2430;
                selection-color: #ffffff;
                border: 1px solid #28303f;
                outline: 0px;
                padding: 4px;
            }
            QLineEdit, QSpinBox {
                background-color: #1a1e26;
                color: #e0e0e0;
                border: 1px solid #3a3f4d;
                border-radius: 4px;
                padding: 5px 8px;
                font-size: 13px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 1px solid #5c6370;
                background-color: #222630;
            }
            QPushButton {
                background-color: #1a1e26;
                color: #e0e0e0;
                border: 1px solid #3a3f4d;
                border-radius: 4px;
                padding: 8px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #222630;
                border-color: #5c6370;
            }
        """)

    def load_config(self):
        """Memuat 6 slot mode bawaan dan status visibilitas tersimpan."""
        default_modes = {
            "Mode 0": {"name": "0. (Off)", "min": -255, "max": 255, "presets": [-255, -125, 0, 125, 255]},
            "Mode 1": {"name": "1. Open_Loop", "min": -255, "max": 255, "presets": [-255, -125, 0, 125, 255]},
            "Mode 2": {"name": "2. Close_Loop", "min": -1360, "max": 1360, "presets": [-1360, -680, 0, 680, 1360]},
            "Mode 3": {"name": "3. PID Kecepatan", "min": -1360, "max": 1360, "presets": [-1360, -680, 0, 680, 1360]},
            "Mode 4": {"name": "4. PID Posisi", "min": -180, "max": 180, "presets": [-180, -90, 0, 90, 180]},
            "Mode 5": {"name": "5. Potensio", "min": -180, "max": 180, "presets": [-180, -90, 0, 90, 180]}
        }
        
        loaded = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    loaded = data.get("custom_modes", {})
                    self.visibility_settings = data.get("visibility_settings", {})
            except Exception:
                loaded = {}
                self.visibility_settings = {}

        self.modes = {}
        for key, def_val in default_modes.items():
            if key in loaded and isinstance(loaded[key], dict):
                self.modes[key] = loaded[key]
            else:
                self.modes[key] = def_val

    def save_config_to_file(self):
        """Menyimpan konfigurasi mode & visibilitas tanpa menimpa data lain."""
        try:
            data = {}
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, "r") as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            data["custom_modes"] = self.modes
            data["visibility_settings"] = self.visibility_settings
            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Gagal menyimpan file konfigurasi: {e}")

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Group Utama Parameter Mode (Semua terintegrasi rapi)
        group_param = QGroupBox("PENGATURAN PARAMETER MODE")
        layout_param = QFormLayout(group_param)
        layout_param.setContentsMargins(14, 16, 14, 16)
        layout_param.setSpacing(12)
        layout_param.setLabelAlignment(Qt.AlignLeft)

        # 1. Pilih Mode Kontrol
        self.combo_mode = QComboBox()
        self.combo_mode.setView(QListView())
        self.combo_mode.addItems(["Mode 0", "Mode 1", "Mode 2", "Mode 3", "Mode 4", "Mode 5"])
        self.combo_mode.currentTextChanged.connect(self.on_mode_changed)
        layout_param.addRow("Pilih Mode Kontrol:", self.combo_mode)

        # 2. Nama Custom Mode
        self.txt_name = QLineEdit()
        layout_param.addRow("Nama Custom Mode:", self.txt_name)

        # 3. Batas Bawah (Min Slider)
        self.spin_min = QSpinBox()
        self.spin_min.setRange(-10000, 10000)
        layout_param.addRow("Batas Bawah (Min Slider):", self.spin_min)

        # 4. Batas Atas (Max Slider)
        self.spin_max = QSpinBox()
        self.spin_max.setRange(-10000, 10000)
        layout_param.addRow("Batas Atas (Max Slider):", self.spin_max)

        # 5. Preset Tombol Cepat (1-5)
        layout_preset = QHBoxLayout()
        layout_preset.setSpacing(8)
        self.preset_spins = []
        for _ in range(5):
            sb = QSpinBox()
            sb.setRange(-10000, 10000)
            self.preset_spins.append(sb)
            layout_preset.addWidget(sb)
        
        layout_param.addRow("Preset Tombol Cepat (1-5):", layout_preset)

        layout.addWidget(group_param)

        # Baris Tombol Aksi
        layout_buttons = QHBoxLayout()
        layout_buttons.setSpacing(10)

        self.btn_save = QPushButton("Simpan Konfigurasi Mode")
        self.btn_save.clicked.connect(self.save_mode)

        self.btn_hide = QPushButton("Sembunyikan Mode")
        self.btn_hide.setStyleSheet("""
            QPushButton {
                background-color: #8b1a1a;
                color: #ffffff;
                border: 1px solid #a82828;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #a82828;
            }
            QPushButton:pressed {
                background-color: #6e1010;
            }
        """)
        self.btn_hide.clicked.connect(self.toggle_hide_mode)

        layout_buttons.addWidget(self.btn_save, stretch=3)
        layout_buttons.addWidget(self.btn_hide, stretch=1)

        layout.addLayout(layout_buttons)

        self.on_mode_changed(self.combo_mode.currentText())

    def on_mode_changed(self, mode_key):
        """Menampilkan parameter dan status visibilitas mode terpilih."""
        if not mode_key or mode_key not in self.modes:
            return

        data = self.modes[mode_key]
        self.txt_name.setText(data.get("name", ""))
        self.spin_min.setValue(data.get("min", -255))
        self.spin_max.setValue(data.get("max", 255))
        presets = data.get("presets", [-255, -125, 0, 125, 255])
        for i in range(min(5, len(presets))):
            self.preset_spins[i].setValue(presets[i])

        vis_key = self.MODE_KEYS.get(mode_key, "mode_off")
        is_visible = self.visibility_settings.get(vis_key, True)

        self.update_ui_state(is_visible)

    def update_ui_state(self, is_visible: bool):
        """Mengubah UI menjadi abu-abu jika di-hide, tombol TETAP MERAH hanya teks berganti."""
        if is_visible:
            self.btn_hide.setText("Sembunyikan Mode")
            self.set_inputs_enabled(True)
        else:
            self.btn_hide.setText("Tampilkan Mode")
            self.set_inputs_enabled(False)

    def set_inputs_enabled(self, enabled: bool):
        """Mengaktifkan atau menonaktifkan input (menjadi abu-abu) saat di-hide."""
        self.txt_name.setEnabled(enabled)
        self.spin_min.setEnabled(enabled)
        self.spin_max.setEnabled(enabled)
        self.btn_save.setEnabled(enabled)
        for sb in self.preset_spins:
            sb.setEnabled(enabled)

        gray_style = """
            QLineEdit:disabled, QSpinBox:disabled {
                background-color: #12151a;
                color: #64748b;
                border: 1px solid #1f242d;
            }
        """
        self.txt_name.setStyleSheet(gray_style if not enabled else "")
        self.spin_min.setStyleSheet(gray_style if not enabled else "")
        self.spin_max.setStyleSheet(gray_style if not enabled else "")
        for sb in self.preset_spins:
            sb.setStyleSheet(gray_style if not enabled else "")

    def save_mode(self):
        """Menyimpan data mode aktif."""
        current_key = self.combo_mode.currentText()
        if not current_key:
            return

        self.modes[current_key] = {
            "name": self.txt_name.text().strip(),
            "min": self.spin_min.value(),
            "max": self.spin_max.value(),
            "presets": [sb.value() for sb in self.preset_spins]
        }

        self.save_config_to_file()
        self.mode_updated.emit(self.modes)
        QMessageBox.information(self, "Sukses", f"Konfigurasi '{current_key}' berhasil disimpan!")

    def toggle_hide_mode(self):
        """Mengubah status visibilitas mode antara Hide/Show."""
        current_key = self.combo_mode.currentText()
        if not current_key:
            return

        vis_key = self.MODE_KEYS.get(current_key, "mode_off")
        curr_vis = self.visibility_settings.get(vis_key, True)
        new_vis = not curr_vis

        self.visibility_settings[vis_key] = new_vis
        self.save_config_to_file()

        # Refresh dashboard utama
        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, "apply_saved_visibility"):
                widget.apply_saved_visibility()

        self.on_mode_changed(current_key)
        
        status_str = "ditampilkan kembali" if new_vis else "disembunyikan"
        QMessageBox.information(self, "Berhasil", f"'{current_key}' ({self.txt_name.text()}) berhasil {status_str}!")


TabNamaMode = TabCustomMode
