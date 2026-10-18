import sys
import os
import time
import json
import csv
import random
import hmac
import hashlib
from collections import deque

import serial
import serial.tools.list_ports

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QMessageBox, QMenu, QAction, QFileDialog, QPushButton,
    QDialog, QLabel, QLineEdit
)
from PyQt5.QtCore import QTimer, QPoint, Qt

from controller import PIDEngine
from serial_worker import SerialReaderThread

from panel.koneksi import PanelKoneksi
from panel.skema import PanelSkema
from panel.pid import PanelPID
from panel.kartu import PanelKartu
from panel.grafik import PanelGrafik
from alat.dialog import AdvancedToolsDialog
from alat.mode import TabCustomMode


SECRET_KEY = b"yasir123

def get_challenge_response(challenge_code: str) -> str:
    h = hmac.new(SECRET_KEY, challenge_code.encode('utf-8'), hashlib.sha256)
    return str(int(h.hexdigest(), 16) % 1000000).zfill(6)


class ChallengePasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Autentikasi Super User")
        self.setFixedWidth(400)
        self.challenge_code = str(random.randint(100000, 999999))
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #14171d;
                border: 1px solid #1f242d;
                border-radius: 8px;
            }
            QLabel {
                color: #cbd5e1;
                font-size: 11px;
                font-weight: 600;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit {
                background-color: #1a1e26;
                color: #ffffff;
                border: 1px solid #28303f;
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #475569;
            }
            QPushButton {
                background-color: #1a1e26;
                color: #cbd5e1;
                border: 1px solid #28303f;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #232936;
                border-color: #475569;
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        lbl_info = QLabel("Kirim Kode Request di bawah ke Yasir untuk mendapatkan Izin:")
        
        req_box = QHBoxLayout()
        lbl_req_title = QLabel("Kode Request Kamu:")
        self.lbl_req_code = QLabel(self.challenge_code)
        self.lbl_req_code.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 800; font-family: monospace;")
        req_box.addWidget(lbl_req_title)
        req_box.addWidget(self.lbl_req_code)
        req_box.addStretch()

        self.inp_pass = QLineEdit()
        self.inp_pass.setEchoMode(QLineEdit.Password)
        self.inp_pass.setPlaceholderText("Masukan Kode Yang di Berikan Yasir ke Sini!!")

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_ok = QPushButton("Verifikasi")
        self.btn_cancel = QPushButton("Batal")
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)

        layout.addWidget(lbl_info)
        layout.addLayout(req_box)
        layout.addWidget(self.inp_pass)
        layout.addLayout(btn_layout)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        self.inp_pass.returnPressed.connect(self.accept)

    def get_input(self):
        return self.inp_pass.text().strip()


class ControlLabDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Panel Kontrol Motor DC")
        self.resize(1240, 780)

        self.is_initializing = True

        self.engine = PIDEngine()
        self.ser = None
        self.reader_thread = None
        self.detected_port = None
        self.tools_dialog = None

        self.actual_val = 0.0
        self.current_pwm = 0
        self.max_measured_rpm = 1360

        self.user_role = "user"
        self.is_otp_session = False
        self.pressed_keys = set()

        self.mode_custom_names = {
            0: "0. (Off)",
            1: "1. Open_Loop",
            2: "2. Close_Loop",
            3: "3. PID Kecepatan",
            4: "4. PID Posisi",
            5: "5. Potensio"
        }

        self.custom_configs = {
            1: {"min": -1350, "max": 1360, "presets": [-1360, -500, 0, 500, 1360]},
            2: {"min": -1360, "max": 1360, "presets": [-1360, -680, 0, 680, 1360]},
            3: {"min": -1360, "max": 1360, "presets": [-1360, -680, 0, 680, 1360]},
            4: {"min": -180, "max": 180, "presets": [-180, -90, 0, 90, 180]},
            5: {"min": -180, "max": 180, "presets": [-180, -90, 0, 90, 180]}
        }

        self.step_start_time = None
        self.last_sp = 0.0
        self.peak_val = 0.0
        self.rise_time_start = None
        self.rise_time = 0.0
        self.settling_time = 0.0
        self.calc_active = False
        self.is_updating_ui = False

        self.max_pts = 300
        self.buf_time = deque(maxlen=self.max_pts)
        self.buf_sp = deque(maxlen=self.max_pts)
        self.buf_pv = deque(maxlen=self.max_pts)
        self.buf_pwm = deque(maxlen=self.max_pts)
        self.start_record_time = time.time()

        self.sim_timer = QTimer()
        self.sim_timer.setInterval(50)
        self.sim_timer.timeout.connect(self.run_internal_simulation)

        self.apply_unified_theme()
        self.init_ui()
        self.load_settings_from_file()

        self.is_initializing = False

        self.apply_role_permissions()
        self.apply_saved_visibility()

        role_val = getattr(self.user_role, 'value', self.user_role)
        role_str = str(role_val).lower()

        if "super" in role_str or "admin" in role_str:
            if hasattr(self, 'txt_log'):
                self.txt_log.clear()
            msg = "Halloooo, selamat menggunakan dashboard premium nya teman"
        else:
            msg = "hafe fun guys pake dashboard nya"

        self.log(f"[AUTH] {msg}")

        self.auto_detect_and_bind_port()

    def prompt_switch_to_super(self):
        dlg = ChallengePasswordDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            user_input = dlg.get_input()
            expected_response = get_challenge_response(dlg.challenge_code)

            if user_input == "dinosaurus":
                self.user_role = "super"
                self.is_otp_session = False
                self.save_settings_to_file()
                self.apply_role_permissions()
                msg = QMessageBox(self)
                msg.setWindowTitle("Berhasil")
                msg.setText("Akses ditingkatkan ke Super User (Permanen)!")
                msg.setStyleSheet("background-color: #14171d; color: #ffffff;")
                msg.exec_()
                self.log("[AUTH] Peran ditingkatkan menjadi Super User (Permanen).")
            elif user_input == expected_response:
                self.user_role = "super"
                self.is_otp_session = True
                self.save_settings_to_file()
                self.apply_role_permissions()
                msg = QMessageBox(self)
                msg.setWindowTitle("Berhasil")
                msg.setText("Akses ditingkatkan ke Super User!")
                msg.setStyleSheet("background-color: #14171d; color: #ffffff;")
                msg.exec_()
                self.log("[AUTH] Peran ditingkatkan menjadi Super User (Dynamic OTP Verified).")
            else:
                msg = QMessageBox(self)
                msg.setWindowTitle("Gagal")
                msg.setText("Password Salah!")
                msg.setIcon(QMessageBox.Warning)
                msg.setStyleSheet("background-color: #14171d; color: #ffffff;")
                msg.exec_()

    def apply_role_permissions(self):
        is_super = (self.user_role == "super")
        if hasattr(self.panel_grafik, 'btn_sandwich'):
            self.panel_grafik.btn_sandwich.setVisible(is_super)

    def keyPressEvent(self, event):
        self.pressed_keys.add(event.key())
        ctrl_pressed = bool({Qt.Key_Control} & self.pressed_keys) or bool(event.modifiers() & Qt.ControlModifier)
        
        if ctrl_pressed and Qt.Key_Y in self.pressed_keys and Qt.Key_S in self.pressed_keys and Qt.Key_R in self.pressed_keys:
            self.pressed_keys.clear()
            self.prompt_switch_to_super()
            
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        self.pressed_keys.discard(event.key())
        super().keyReleaseEvent(event)

    def save_settings_to_file(self):
        if getattr(self, 'is_initializing', False):
            return

        saved_role = "user" if self.is_otp_session else self.user_role

        existing_data = {}
        if os.path.exists("config_settings.json"):
            try:
                with open("config_settings.json", "r") as f:
                    existing_data = json.load(f)
            except Exception:
                existing_data = {}

        if "custom_modes" not in existing_data:
            existing_data["custom_modes"] = {}

        for idx in range(6):
            mode_key = f"Mode {idx}"
            if mode_key not in existing_data["custom_modes"]:
                existing_data["custom_modes"][mode_key] = {}
            
            existing_data["custom_modes"][mode_key]["name"] = self.mode_custom_names.get(idx, f"Mode {idx}")
            if idx in self.custom_configs:
                existing_data["custom_modes"][mode_key]["min"] = self.custom_configs[idx]["min"]
                existing_data["custom_modes"][mode_key]["max"] = self.custom_configs[idx]["max"]
                existing_data["custom_modes"][mode_key]["presets"] = self.custom_configs[idx]["presets"]

        existing_data["ppr"] = self.panel_pid.spn_ppr.value()
        existing_data["kp"] = self.panel_pid.spn_kp.value()
        existing_data["ki"] = self.panel_pid.spn_ki.value()
        existing_data["kd"] = self.panel_pid.spn_kd.value()
        existing_data["last_role"] = saved_role

        try:
            with open("config_settings.json", "w") as f:
                json.dump(existing_data, f, indent=4)
        except Exception as e:
            print(f"Gagal menyimpan pengaturan otomatis: {e}")

    def load_settings_from_file(self):
        if os.path.exists("config_settings.json"):
            try:
                with open("config_settings.json", "r") as f:
                    data = json.load(f)

                custom_modes = data.get("custom_modes", {})
                if custom_modes:
                    key_map = {"Mode 0": 0, "Mode 1": 1, "Mode 2": 2, "Mode 3": 3, "Mode 4": 4, "Mode 5": 5}
                    for k, v in custom_modes.items():
                        idx = key_map.get(k, int(k) if str(k).isdigit() else None)
                        if idx is not None and isinstance(v, dict):
                            self.mode_custom_names[idx] = v.get("name", f"Mode {idx}")
                            self.custom_configs[idx] = {
                                "min": v.get("min", -1360),
                                "max": v.get("max", 1360),
                                "presets": v.get("presets", [-1360, -125, 0, 125, 1360])
                            }
                elif "mode_names" in data:
                    self.mode_custom_names = {int(k): v for k, v in data["mode_names"].items()}
                    if "custom_configs" in data:
                        self.custom_configs = {int(k): v for k, v in data["custom_configs"].items()}

                self.is_updating_ui = True
                if "ppr" in data: self.panel_pid.spn_ppr.setValue(data["ppr"])
                if "kp" in data: self.panel_pid.spn_kp.setValue(data["kp"])
                if "ki" in data: self.panel_pid.spn_ki.setValue(data["ki"])
                if "kd" in data: self.panel_pid.spn_kd.setValue(data["kd"])
                self.is_updating_ui = False

                if "last_role" in data:
                    self.user_role = data["last_role"]

            except Exception as e:
                self.is_updating_ui = False
                print(f"Gagal memuat pengaturan otomatis: {e}")

        if hasattr(self, 'engine'):
            self.update_preset_buttons(self.engine.current_mode)

    def reload_custom_configs(self):
        """Memuat ulang konfigurasi kustom dari file JSON seketika saat disimpan."""
        if os.path.exists("config_settings.json"):
            try:
                with open("config_settings.json", "r") as f:
                    data = json.load(f)
                    custom_modes = data.get("custom_modes", {})
                    key_map = {"Mode 0": 0, "Mode 1": 1, "Mode 2": 2, "Mode 3": 3, "Mode 4": 4, "Mode 5": 5}
                    for k, v in custom_modes.items():
                        idx = key_map.get(k)
                        if idx is not None and isinstance(v, dict):
                            self.mode_custom_names[idx] = v.get("name", f"Mode {idx}")
                            self.custom_configs[idx] = {
                                "min": v.get("min", -255),
                                "max": v.get("max", 255),
                                "presets": v.get("presets", [-255, -125, 0, 125, 255])
                            }
            except Exception as e:
                print(f"Gagal reload custom config: {e}")

        self.update_preset_buttons(self.engine.current_mode)
        self.set_active_mode(self.engine.current_mode)

    def apply_unified_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0d0f12; }
            QWidget { color: #cbd5e1; font-family: 'Segoe UI', Roboto, sans-serif; font-size: 12px; }
            QGroupBox { border: 1px solid #1f242d; border-radius: 8px; margin-top: 10px; font-weight: 600; font-size: 11px; color: #94a3b8; padding-top: 12px; background-color: #14171d; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 8px; background-color: #14171d; color: #94a3b8; }
            QDoubleSpinBox, QSpinBox { background-color: #1a1e26; border: 1px solid #28303f; border-radius: 6px; padding: 4px 6px; color: #f1f5f9; font-weight: 500; }
            QDoubleSpinBox:disabled, QSpinBox:disabled { background-color: #12151a; color: #475569; border-color: #191e26; }
            QPushButton { background-color: #1a1e26; color: #cbd5e1; border: 1px solid #28303f; border-radius: 6px; padding: 6px 12px; font-weight: 600; }
            QPushButton:hover { background-color: #232936; border-color: #3b475d; }
            QTextEdit { background-color: #0b0c0f; border: 1px solid #1f242d; border-radius: 6px; color: #64748b; font-family: monospace; font-size: 11px; }
            QCheckBox { color: #94a3b8; spacing: 6px; }
            QMenu { background-color: #14171d; border: 1px solid #28303f; border-radius: 6px; padding: 6px; }
            QMenu::item { background-color: transparent; color: #cbd5e1; padding: 8px 24px; border-radius: 4px; font-weight: 600; margin: 2px 0px; }
            QMenu::item:selected { background-color: #1e2430; color: #ffffff; border: 1px solid #475569; }
        """)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(14, 14, 14, 14)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)

        self.panel_koneksi = PanelKoneksi()
        self.panel_koneksi.btn_auto_connect.clicked.connect(self.toggle_connection)
        self.panel_koneksi.btn_rescan.clicked.connect(self.auto_detect_and_bind_port)
        self.panel_koneksi.chk_sim_mode.stateChanged.connect(self.toggle_sim_mode)
        left_layout.addWidget(self.panel_koneksi)

        self.panel_skema = PanelSkema()
        self.setup_mode_popup_menu()
        self.panel_skema.sld_target.valueChanged.connect(self.slider_moved)
        for i, b in enumerate(self.panel_skema.preset_btns):
            b.clicked.connect(lambda ch, idx=i: self.on_preset_clicked(idx))
        self.panel_skema.btn_zero.clicked.connect(self.calibrate_zero)
        left_layout.addWidget(self.panel_skema)

        self.panel_pid = PanelPID()
        self.panel_pid.btn_apply_ppr.clicked.connect(self.send_ppr)
        self.panel_pid.spn_kp.valueChanged.connect(self.update_pid_from_spinbox)
        self.panel_pid.spn_ki.valueChanged.connect(self.update_pid_from_spinbox)
        self.panel_pid.spn_kd.valueChanged.connect(self.update_pid_from_spinbox)
        self.panel_pid.btn_save_preset.clicked.connect(self.save_preset_json)
        self.panel_pid.btn_load_preset.clicked.connect(self.load_preset_json)
        left_layout.addWidget(self.panel_pid)

        self.btn_estop = QPushButton("EMERGENCY (STOP)")
        self.btn_estop.setStyleSheet("background-color: #1a1e26; border: 1px solid #3d2228; color: #cbd5e1; font-weight: 700; padding: 10px;")
        self.btn_estop.clicked.connect(self.emergency_stop)
        left_layout.addWidget(self.btn_estop)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        left_layout.addWidget(self.txt_log, 1)

        main_layout.addLayout(left_layout, 32)

        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)

        self.panel_kartu = PanelKartu()
        right_layout.addLayout(self.panel_kartu.metrics_layout)
        right_layout.addLayout(self.panel_kartu.transient_layout)

        self.panel_grafik = PanelGrafik()
        self.panel_grafik.chk_unlock_pid.stateChanged.connect(self.toggle_pid_unlock)
        self.panel_grafik.btn_export_csv.clicked.connect(self.export_csv_data)
        self.panel_grafik.btn_sandwich.clicked.connect(self.open_advanced_tools)
        self.panel_grafik.btn_reset_view.clicked.connect(self.reset_graph_view)
        right_layout.addLayout(self.panel_grafik)

        main_layout.addLayout(right_layout, 68)
        self.set_active_mode(0)

    def setup_mode_popup_menu(self):
        self.mode_menu = QMenu(self)
        try:
            self.panel_skema.btn_mode_selector.clicked.disconnect()
        except Exception:
            pass
        self.panel_skema.btn_mode_selector.clicked.connect(self.show_mode_popup)

    def show_mode_popup(self):
        self.mode_menu.clear()
        self.mode_menu.setStyleSheet("""
            QMenu {
                background-color: #14171d;
                border: 1px solid #28303f;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                background-color: transparent;
                color: #cbd5e1;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #1e2430;
                color: #ffffff;
                border: 1px solid #475569;
            }
        """)

        hidden_states = {}
        if os.path.exists("config_settings.json"):
            try:
                with open("config_settings.json", "r") as f:
                    data = json.load(f)
                    hidden_states = data.get("visibility_settings", {})
            except Exception:
                hidden_states = {}

        mode_vis_map = {
            0: hidden_states.get("mode_off", True),
            1: hidden_states.get("mode_openloop", True),
            2: hidden_states.get("mode_closeloop", True),
            3: hidden_states.get("mode_pid_speed", True),
            4: hidden_states.get("mode_pid_pos", True),
            5: hidden_states.get("mode_potensio", True),
        }

        for idx in range(6):
            if mode_vis_map.get(idx, True):
                title = self.mode_custom_names.get(idx, f"Mode {idx}")
                action = QAction(title, self)
                action.triggered.connect(lambda checked, m=idx: self.set_active_mode(m))
                self.mode_menu.addAction(action)

        pos = self.panel_skema.btn_mode_selector.mapToGlobal(
            QPoint(0, self.panel_skema.btn_mode_selector.height() + 4)
        )
        self.mode_menu.exec_(pos)

    def apply_saved_visibility(self):
        if os.path.exists("config_settings.json"):
            try:
                with open("config_settings.json", "r") as f:
                    data = json.load(f)
                    hidden_states = data.get("visibility_settings", {})

                view_mode = hidden_states.get("monitoring_view_mode", 0)
                if hasattr(self, "panel_grafik") and hasattr(self.panel_grafik, "set_monitoring_mode"):
                    self.panel_grafik.set_monitoring_mode(view_mode)

                for key, is_visible in hidden_states.items():
                    target = getattr(self, key, None)
                    if not target and hasattr(self, "panel_kartu"):
                        target = getattr(self.panel_kartu, key, None)
                    if not target and hasattr(self, "panel_grafik"):
                        target = getattr(self.panel_grafik, key, None)
                    if not target and hasattr(self, "panel_koneksi"):
                        target = getattr(self.panel_koneksi, key, None)

                    if target and hasattr(target, "setVisible"):
                        target.setVisible(is_visible)
            except Exception as e:
                self.log(f"[CONFIG] Gagal memuat visibilitas: {e}")

    def emergency_stop(self):
        self.set_active_mode(0)
        self.panel_skema.sld_target.blockSignals(True)
        self.panel_skema.sld_target.setValue(0)
        self.panel_skema.sld_target.blockSignals(False)
        self.engine.setpoint = 0.0
        self.send_command("M:0:0")
        self.log("[EMERGENCY STOP] Motor dihentikan paksa.")

    def parse_telemetry(self, line):
        try:
            if line.startswith("DIAG:"):
                if self.tools_dialog and self.tools_dialog.isVisible():
                    self.tools_dialog.parse_diag_response(line)
                return

            parts = line.split(',')
            if len(parts) >= 4:
                mode = int(parts[0])
                target = float(parts[1])
                actual = float(parts[2])
                pwm = int(parts[3])

                self.actual_val = actual
                self.current_pwm = pwm
                self.engine.current_mode = mode
                self.engine.setpoint = target

                unit = "°" if mode in (4, 5, 0) else " rpm"
                if hasattr(self.panel_kartu, 'card_target') and hasattr(self.panel_kartu.card_target, 'val_label'):
                    self.panel_kartu.card_target.val_label.setText(f"{target:.1f}{unit}")
                if hasattr(self.panel_kartu, 'card_actual') and hasattr(self.panel_kartu.card_actual, 'val_label'):
                    self.panel_kartu.card_actual.val_label.setText(f"{actual:.1f}{unit}")
                if hasattr(self.panel_kartu, 'card_pwm') and hasattr(self.panel_kartu.card_pwm, 'val_label'):
                    self.panel_kartu.card_pwm.val_label.setText(str(pwm))

                self.update_telemetry_ui(mode, target, actual, pwm)
                if self.tools_dialog and self.tools_dialog.isVisible():
                    self.tools_dialog.process_telemetry_calib(actual)
            else:
                self.log(f"[RAW]: {line}")
        except (ValueError, IndexError):
            self.log(f"[ERR]: {line}")

    def export_csv_data(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Simpan Data CSV", "", "CSV Files (*.csv)")
        if filename:
            try:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Waktu_s", "Target", "Aktual", "PWM"])
                    for t, sp, pv, pwm in zip(self.buf_time, self.buf_sp, self.buf_pv, self.buf_pwm):
                        writer.writerow([f"{t:.3f}", sp, pv, pwm])
                self.log(f"Data berhasil diekspor ke {filename}")
            except Exception as e:
                self.log(f"Gagal ekspor: {e}")

    def update_pid_from_spinbox(self):
        if self.is_updating_ui:
            return
        kp = self.panel_pid.spn_kp.value()
        ki = self.panel_pid.spn_ki.value()
        kd = self.panel_pid.spn_kd.value()
        mode = self.engine.current_mode
        self.engine.set_pid_gains(mode, kp, ki, kd)
        
        ptype = 'P' if mode in (4, 5) else 'S'
        self.send_command(f"P:{ptype}:{kp:.3f}:{ki:.3f}:{kd:.3f}")
        self.save_settings_to_file()

    def send_ppr(self):
        ppr_val = float(self.panel_pid.spn_ppr.value())
        self.engine.ppr = ppr_val
        self.send_command(f"K:{ppr_val}")
        self.log(f"PPR diatur ke: {ppr_val}")
        self.save_settings_to_file()

    def save_preset_json(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Simpan Konfigurasi", "", "JSON Files (*.json)")
        if filename:
            data = {"ppr": self.panel_pid.spn_ppr.value(), "kp": self.panel_pid.spn_kp.value(), "ki": self.panel_pid.spn_ki.value(), "kd": self.panel_pid.spn_kd.value()}
            try:
                with open(filename, "w") as f:
                    json.dump(data, f, indent=4)
                self.log(f"Konfigurasi disimpan ke {filename}")
            except Exception as e:
                self.log(f"Gagal simpan: {e}")

    def load_preset_json(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Muat Konfigurasi", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, "r") as f:
                    data = json.load(f)
                self.is_updating_ui = True
                if "ppr" in data: self.panel_pid.spn_ppr.setValue(data["ppr"]); self.send_ppr()
                if "kp" in data: self.panel_pid.spn_kp.setValue(data["kp"])
                if "ki" in data: self.panel_pid.spn_ki.setValue(data["ki"])
                if "kd" in data: self.panel_pid.spn_kd.setValue(data["kd"])
                self.is_updating_ui = False
                self.update_pid_from_spinbox()
                self.log(f"Konfigurasi dimuat dari {filename}")
            except Exception as e:
                self.is_updating_ui = False
                self.log(f"Gagal memuat: {e}")

    def set_active_mode(self, idx):
        title = self.mode_custom_names.get(idx, f"Mode {idx}")
        self.panel_skema.btn_mode_selector.setText(title)
        self.change_mode(idx)

    def toggle_pid_unlock(self, state):
        unlocked = (state == 2)
        self.panel_pid.spn_kp.setEnabled(unlocked)
        self.panel_pid.spn_ki.setEnabled(unlocked)
        self.panel_pid.spn_kd.setEnabled(unlocked)

    def open_advanced_tools(self):
        if self.user_role != "super":
            msg = QMessageBox(self)
            msg.setWindowTitle("Akses Ditolak")
            msg.setText("Fitur Advanced Tools hanya untuk Super User!")
            msg.setIcon(QMessageBox.Warning)
            msg.setStyleSheet("background-color: #14171d; color: #ffffff;")
            msg.exec_()
            return
        
        if self.tools_dialog is None or not self.tools_dialog.isVisible():
            self.tools_dialog = AdvancedToolsDialog(self.ser, self.engine, self)
            
            # Cari instance TabCustomMode dalam dialog dan hubungkan sinyal simpan
            for child in self.tools_dialog.findChildren(TabCustomMode):
                child.mode_updated.connect(lambda _: self.reload_custom_configs())

            # Hubungkan juga event penutupan dialog
            self.tools_dialog.finished.connect(lambda: self.reload_custom_configs())
            self.tools_dialog.show()
        else:
            self.tools_dialog.raise_()
            self.tools_dialog.activateWindow()

    def auto_detect_and_bind_port(self):
        detected = None
        for p in serial.tools.list_ports.comports():
            desc, hwid = (p.description or "").lower(), (p.hwid or "").lower()
            if any(k in desc or k in hwid for k in ["ch340", "cp210", "ftdi", "arduino", "usb", "acm", "tty"]):
                detected = p.device
                break
        if not detected and serial.tools.list_ports.comports():
            detected = serial.tools.list_ports.comports()[0].device

        if detected:
            self.detected_port = detected
            self.panel_koneksi.lbl_device_info.setText(detected)
            self.panel_koneksi.btn_auto_connect.setEnabled(True)
            self.panel_koneksi.btn_auto_connect.setText(f"Hubungkan ({detected})")
        else:
            self.detected_port = None
            self.panel_koneksi.lbl_device_info.setText("Tidak Ada Port")
            self.panel_koneksi.btn_auto_connect.setEnabled(False)

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.disconnect_serial()
        else:
            if not self.detected_port:
                self.auto_detect_and_bind_port()
                if not self.detected_port:
                    return
            try:
                self.ser = serial.Serial(self.detected_port, 115200, timeout=1)
                self.ser.dtr = True
                self.ser.reset_input_buffer()

                self.reader_thread = SerialReaderThread(self.ser)
                self.reader_thread.data_received.connect(self.parse_telemetry)
                self.reader_thread.connection_lost.connect(self.disconnect_serial)
                self.reader_thread.start()

                self.panel_koneksi.btn_auto_connect.setText(f"Putus ({self.detected_port})")
                self.panel_koneksi.chk_sim_mode.setChecked(False)
                self.log(f"Terhubung ke {self.detected_port}")

                QTimer.singleShot(1500, self.sync_initial_state)
            except Exception as e:
                self.log(f"Gagal hubungkan: {e}")

    def sync_initial_state(self):
        if self.ser and self.ser.is_open:
            self.send_command(f"M:{self.engine.current_mode}:{self.engine.setpoint}")
            self.update_pid_from_spinbox()
            self.log("Status disinkronkan ke mikrokontroler.")

    def disconnect_serial(self):
        if self.reader_thread:
            self.reader_thread.stop()
            self.reader_thread = None
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None
        self.panel_koneksi.btn_auto_connect.setText("Hubungkan")
        self.log("Koneksi diputus.")

    def reset_graph_view(self):
        if len(self.buf_time) > 0:
            cur_t = self.buf_time[-1]
            if hasattr(self.panel_grafik, 'plot_graph'):
                self.panel_grafik.plot_graph.setXRange(max(0, cur_t - 10), cur_t + 0.5, padding=0)
            if hasattr(self.panel_grafik, 'pwm_graph'):
                self.panel_grafik.pwm_graph.setXRange(max(0, cur_t - 10), cur_t + 0.5, padding=0)

    def send_command(self, cmd):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write((cmd + "\n").encode("utf-8"))
            except Exception as e:
                self.log(f"Kesalahan pengiriman: {e}")

    def apply_mode_configurations(self, idx):
        if idx not in self.custom_configs:
            return
        cfg = self.custom_configs[idx]
        mn = int(cfg["min"])
        mx = int(cfg["max"])
        prs = cfg["presets"]

        self.panel_skema.sld_target.setRange(mn, mx)
        labels = [f"{p:g}" for p in prs]
        for i in range(5):
            self.panel_skema.preset_btns[i].setText(labels[i])
            self.panel_skema.preset_btns[i].setEnabled(True)
            self.panel_skema.preset_btns[i].show()
        self.custom_preset_values = prs

    def update_preset_buttons(self, mode_idx):
        self.apply_mode_configurations(mode_idx)
        if mode_idx in (4, 5):
            self.panel_skema.btn_zero.setEnabled(True)
            self.panel_skema.btn_zero.show()
        else:
            self.panel_skema.btn_zero.hide()

    def on_preset_clicked(self, idx):
        if hasattr(self, 'custom_preset_values') and len(self.custom_preset_values) == 5:
            target = self.custom_preset_values[idx]
        else:
            target = 0

        self.panel_skema.sld_target.blockSignals(True)
        self.panel_skema.sld_target.setValue(int(target))
        self.panel_skema.sld_target.blockSignals(False)
        self.engine.setpoint = float(target)
        self.update_target_label(target)
        self.send_command(f"M:{self.engine.current_mode}:{target}")
        self.trigger_step_change(self.engine.setpoint)

    def change_mode(self, idx):
        self.engine.current_mode = idx
        self.reset_transient_analytics()
        self.update_preset_buttons(idx)
        self.send_command("RST_STALL")
        
        if hasattr(self.panel_grafik, 'stacked_view'):
            if idx in (4, 5):
                self.panel_grafik.stacked_view.setCurrentIndex(1)
            else:
                self.panel_grafik.stacked_view.setCurrentIndex(0)

        self.is_updating_ui = True
        if idx in (2, 3):
            self.panel_pid.spn_kp.setValue(0.45); self.panel_pid.spn_ki.setValue(0.12); self.panel_pid.spn_kd.setValue(0.002)
        elif idx in (4, 5):
            self.panel_pid.spn_kp.setValue(0.85); self.panel_pid.spn_ki.setValue(0.00); self.panel_pid.spn_kd.setValue(0.12)
        self.is_updating_ui = False

        if idx == 0:
            self.panel_skema.container.hide()
            self.send_command("M:0:0")
        else:
            self.panel_skema.container.show()
            self.panel_skema.sld_target.setEnabled(idx != 5)
            self.send_command(f"M:{idx}:0")

        self.update_pid_from_spinbox()

    def update_target_label(self, val):
        if self.engine.current_mode == 1:
            self.panel_skema.lbl_target_info.setText(f"Duty PWM: {val}")
        elif self.engine.current_mode in (2, 3):
            self.panel_skema.lbl_target_info.setText(f"Target Kecepatan: {val} RPM")
        elif self.engine.current_mode == 4:
            self.panel_skema.lbl_target_info.setText(f"Target Posisi: {val}°")
        elif self.engine.current_mode == 5:
            self.panel_skema.lbl_target_info.setText("Mode Potensio (A0)")
        else:
            self.panel_skema.lbl_target_info.setText("Referensi: 0")

    def calibrate_zero(self):
        if self.engine.current_mode not in (4, 5):
            return
        self.panel_skema.sld_target.blockSignals(True)
        self.panel_skema.sld_target.setValue(0)
        self.panel_skema.sld_target.blockSignals(False)
        self.engine.setpoint = 0.0
        self.update_target_label(0)
        self.send_command("Z")
        self.log("Titik nol berhasil dikalibrasi ulang.")

    def slider_moved(self, value):
        val = float(value)
        self.engine.setpoint = val
        self.update_target_label(val)
        
        if hasattr(self.panel_grafik, 'gauge_widget'):
            self.panel_grafik.gauge_widget.set_angles(val, self.actual_val)

        self.send_command(f"M:{self.engine.current_mode}:{val:.1f}")

    def trigger_step_change(self, new_sp):
        if abs(new_sp - self.last_sp) > 5.0 and self.engine.current_mode in (2, 3, 4, 5):
            self.step_start_time = time.time()
            self.peak_val = 0.0
            self.rise_time_start = None
            self.rise_time = 0.0
            self.settling_time = 0.0
            self.calc_active = True
            self.last_sp = new_sp

    def reset_transient_analytics(self):
        self.calc_active = False
        if hasattr(self.panel_kartu, 'card_overshoot') and hasattr(self.panel_kartu.card_overshoot, 'val_label'):
            self.panel_kartu.card_overshoot.val_label.setText("0.0 %")
        if hasattr(self.panel_kartu, 'card_risetime') and hasattr(self.panel_kartu.card_risetime, 'val_label'):
            self.panel_kartu.card_risetime.val_label.setText("0.00 s")
        if hasattr(self.panel_kartu, 'card_settling') and hasattr(self.panel_kartu.card_settling, 'val_label'):
            self.panel_kartu.card_settling.val_label.setText("0.00 s")
        if hasattr(self.panel_kartu, 'card_ss_error') and hasattr(self.panel_kartu.card_ss_error, 'val_label'):
            self.panel_kartu.card_ss_error.val_label.setText("0.00")

    def update_transient_analytics(self, sp, pv):
        if not self.calc_active or sp == 0:
            return
        elapsed = time.time() - self.step_start_time
        if abs(pv) > abs(self.peak_val):
            self.peak_val = pv
        if abs(self.peak_val) > abs(sp):
            overshoot = ((abs(self.peak_val) - abs(sp)) / abs(sp)) * 100.0
            if hasattr(self.panel_kartu, 'card_overshoot') and hasattr(self.panel_kartu.card_overshoot, 'val_label'):
                self.panel_kartu.card_overshoot.val_label.setText(f"{overshoot:.1f} %")

        if self.rise_time_start is None and abs(pv) >= (0.1 * abs(sp)):
            self.rise_time_start = elapsed
        if self.rise_time == 0.0 and self.rise_time_start is not None and abs(pv) >= (0.9 * abs(sp)):
            self.rise_time = elapsed - self.rise_time_start
            if hasattr(self.panel_kartu, 'card_risetime') and hasattr(self.panel_kartu.card_risetime, 'val_label'):
                self.panel_kartu.card_risetime.val_label.setText(f"{self.rise_time:.2f} s")

        if abs(sp - pv) <= (0.05 * abs(sp)):
            if self.settling_time == 0.0 and elapsed > 0.3:
                self.settling_time = elapsed
                if hasattr(self.panel_kartu, 'card_settling') and hasattr(self.panel_kartu.card_settling, 'val_label'):
                    self.panel_kartu.card_settling.val_label.setText(f"{self.settling_time:.2f} s")
        else:
            self.settling_time = 0.0

        ss_err = abs(sp - pv)
        if hasattr(self.panel_kartu, 'card_ss_error') and hasattr(self.panel_kartu.card_ss_error, 'val_label'):
            self.panel_kartu.card_ss_error.val_label.setText(f"{ss_err:.2f}")

    def update_telemetry_ui(self, mode, target, actual, pwm):
        mode_names = ["BERHENTI", "MANUAL", "KONTROL", "PID KEC", "PID POS", "POTENSIO"]
        if hasattr(self.panel_kartu, 'card_mode') and hasattr(self.panel_kartu.card_mode, 'val_label'):
            self.panel_kartu.card_mode.val_label.setText(mode_names[mode] if mode < len(mode_names) else "JALAN")

        cur_t = time.time() - self.start_record_time

        self.buf_time.append(cur_t)
        self.buf_sp.append(target)
        self.buf_pv.append(actual)
        self.buf_pwm.append(pwm)

        if hasattr(self.panel_grafik, 'update_data'):
            self.panel_grafik.update_data(list(self.buf_time), list(self.buf_sp), list(self.buf_pv))
        else:
            if hasattr(self.panel_grafik, 'curve_target'):
                self.panel_grafik.curve_target.setData(list(self.buf_time), list(self.buf_sp))
            if hasattr(self.panel_grafik, 'curve_actual'):
                self.panel_grafik.curve_actual.setData(list(self.buf_time), list(self.buf_pv))
            if hasattr(self.panel_grafik, 'curve_pwm'):
                self.panel_grafik.curve_pwm.setData(list(self.buf_time), list(self.buf_pwm))

            window_sec = 10.0
            x_min = max(0.0, cur_t - window_sec)
            x_max = max(window_sec, cur_t + 0.5)

            if hasattr(self.panel_grafik, 'plot_graph'):
                self.panel_grafik.plot_graph.setXRange(x_min, x_max, padding=0)
            if hasattr(self.panel_grafik, 'pwm_graph'):
                self.panel_grafik.pwm_graph.setXRange(x_min, x_max, padding=0)

        if mode in (4, 5, 0) and hasattr(self.panel_grafik, 'gauge_widget'):
            if hasattr(self.panel_grafik.gauge_widget, 'set_angles'):
                self.panel_grafik.gauge_widget.set_angles(target, actual)

        self.update_transient_analytics(target, actual)

    def toggle_sim_mode(self, state):
        if state == 2:
            if self.ser and self.ser.is_open:
                self.disconnect_serial()
            self.sim_timer.start()
            self.log("[SIM] Mode Simulasi Fisika Motor DC Diaktifkan.")
        else:
            self.sim_timer.stop()
            self.log("[SIM] Mode Simulasi Dihentikan.")

    def run_internal_simulation(self):
        val_aktual = self.engine.setpoint
        self.actual_val = val_aktual
        self.update_telemetry_ui(self.engine.current_mode, self.engine.setpoint, val_aktual, 100)

    def log(self, text):
        self.txt_log.append(text)

    def closeEvent(self, event):
        self.save_settings_to_file()
        self.disconnect_serial()
        self.sim_timer.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ControlLabDashboard()
    window.show()
    sys.exit(app.exec_())
