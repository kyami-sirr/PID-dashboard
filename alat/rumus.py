from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QGridLayout, QLabel, QDoubleSpinBox, QPushButton, 
                             QFrame, QMessageBox)
from PyQt5.QtCore import Qt

class MetricCard(QFrame):
    def __init__(self, title, val_init):
        super().__init__()
        self.setStyleSheet("background-color: #1a1e26; border: 1px solid #28303f; border-radius: 6px;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("font-size: 10px; color: #94a3b8; font-weight: 600;")

        self.lbl_v = QLabel(val_init)
        self.lbl_v.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff; font-family: monospace;")
        self.lbl_v.setAlignment(Qt.AlignCenter)

        layout.addWidget(lbl_t)
        layout.addWidget(self.lbl_v)


class TabRumus(QWidget):
    def __init__(self, main_dashboard):
        super().__init__()
        self.main_dashboard = main_dashboard
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        box_style = """
            QGroupBox {
                color: #cbd5e1;
                font-weight: 600;
                font-size: 11px;
                border: 1px solid #1f242d;
                border-radius: 8px;
                margin-top: 6px;
                padding-top: 14px;
                background-color: #14171d;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                background-color: #14171d;
            }
        """

        input_style = """
            QDoubleSpinBox {
                background-color: #1a1e26;
                color: #ffffff;
                border: 1px solid #28303f;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 11px;
            }
            QDoubleSpinBox:focus {
                border-color: #475569;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 16px;
                background: #232936;
                border: none;
            }
        """

        btn_style = """
            QPushButton {
                background-color: #1a1e26;
                color: #ffffff;
                border: 1px solid #28303f;
                border-radius: 6px;
                font-weight: 600;
                font-size: 11px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #232936;
                border-color: #475569;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #0d0f12;
            }
        """

        self.setStyleSheet(input_style)

        # 1. INPUT PARAMETER ZIEGLER-NICHOLS
        grp_in = QGroupBox("AUTO TUNING PID (ZIEGLER-NICHOLS)")
        grp_in.setStyleSheet(box_style)
        gl = QGridLayout(grp_in)
        gl.setContentsMargins(12, 12, 12, 12)
        gl.setSpacing(10)

        lbl_ku = QLabel("Ku (Ultimate Gain):")
        lbl_ku.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.spn_ku = QDoubleSpinBox()
        self.spn_ku.setRange(0.01, 100.0)
        self.spn_ku.setSingleStep(0.1)
        self.spn_ku.setValue(2.5)

        lbl_tu = QLabel("Tu (Ultimate Period - detik):")
        lbl_tu.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.spn_tu = QDoubleSpinBox()
        self.spn_tu.setRange(0.01, 60.0)
        self.spn_tu.setSingleStep(0.1)
        self.spn_tu.setValue(0.8)

        btn_calc_zn = QPushButton("Hitung")
        btn_calc_zn.setMinimumHeight(34)
        btn_calc_zn.setStyleSheet(btn_style)
        btn_calc_zn.clicked.connect(self.calc_zn)

        gl.addWidget(lbl_ku, 0, 0)
        gl.addWidget(self.spn_ku, 0, 1)
        gl.addWidget(lbl_tu, 1, 0)
        gl.addWidget(self.spn_tu, 1, 1)
        gl.addWidget(btn_calc_zn, 2, 0, 1, 2)

        layout.addWidget(grp_in)

        # 2. HASIL KALKULASI (METRIC CARDS)
        grp_out = QGroupBox("HASIL KALKULASI PARAMETER")
        grp_out.setStyleSheet(box_style)
        out_layout = QHBoxLayout(grp_out)
        out_layout.setContentsMargins(12, 12, 12, 12)
        out_layout.setSpacing(10)

        self.card_kp = MetricCard("Kp (Proportional)", "-")
        self.card_ki = MetricCard("Ki (Integral)", "-")
        self.card_kd = MetricCard("Kd (Derivative)", "-")

        out_layout.addWidget(self.card_kp)
        out_layout.addWidget(self.card_ki)
        out_layout.addWidget(self.card_kd)

        layout.addWidget(grp_out)

        # 3. TOMBOL TERAPKAN PARAMETER
        btn_apply = QPushButton("Terapkan Parameter ke Dashboard & Hardware")
        btn_apply.setMinimumHeight(36)
        btn_apply.setStyleSheet(btn_style)
        btn_apply.clicked.connect(self.apply_to_dashboard)
        layout.addWidget(btn_apply)

        layout.addStretch()

    def calc_zn(self):
        ku = self.spn_ku.value()
        tu = self.spn_tu.value()
        self.calc_kp = 0.6 * ku
        self.calc_ki = 2.0 * self.calc_kp / tu
        self.calc_kd = self.calc_kp * tu / 8.0

        self.card_kp.lbl_v.setText(f"{self.calc_kp:.3f}")
        self.card_ki.lbl_v.setText(f"{self.calc_ki:.3f}")
        self.card_kd.lbl_v.setText(f"{self.calc_kd:.3f}")

    def apply_to_dashboard(self):
        if hasattr(self, 'calc_kp'):
            self.main_dashboard.is_updating_ui = True
            self.main_dashboard.panel_pid.spn_kp.setValue(self.calc_kp)
            self.main_dashboard.panel_pid.spn_ki.setValue(self.calc_ki)
            self.main_dashboard.panel_pid.spn_kd.setValue(self.calc_kd)
            self.main_dashboard.is_updating_ui = False

            self.main_dashboard.update_pid_from_spinbox()
            QMessageBox.information(
                self, "Berhasil", 
                f"Parameter PID berhasil dikirim ke Hardware:\nKp: {self.calc_kp:.3f} | Ki: {self.calc_ki:.3f} | Kd: {self.calc_kd:.3f}"
            )
        else:
            QMessageBox.warning(self, "Peringatan", "Hitung parameter PID terlebih dahulu sebelum menerapkan!")
