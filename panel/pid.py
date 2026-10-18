from PyQt5.QtWidgets import QGroupBox, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox, QDoubleSpinBox

class PanelPID(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("PARAMETER PID", parent)
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()

        self.spn_ppr = QSpinBox()
        self.spn_ppr.setRange(10, 10000)
        self.spn_ppr.setValue(188)
        self.btn_apply_ppr = QPushButton("Atur PPR")

        self.spn_kp = self.build_spinbox(0.85, 0.01, 0.0, 50.0, False)
        self.spn_ki = self.build_spinbox(0.00, 0.01, 0.0, 50.0, False)
        self.spn_kd = self.build_spinbox(0.12, 0.001, 0.0, 10.0, False)

        self.btn_save_preset = QPushButton("Simpan")
        self.btn_load_preset = QPushButton("Muat")

        layout.addWidget(QLabel("PPR Encoder:"), 0, 0)
        layout.addWidget(self.spn_ppr, 0, 1)
        layout.addWidget(self.btn_apply_ppr, 0, 2)
        layout.addWidget(QLabel("Kp:"), 1, 0)
        layout.addWidget(self.spn_kp, 1, 1, 1, 2)
        layout.addWidget(QLabel("Ki:"), 2, 0)
        layout.addWidget(self.spn_ki, 2, 1, 1, 2)
        layout.addWidget(QLabel("Kd:"), 3, 0)
        layout.addWidget(self.spn_kd, 3, 1, 1, 2)

        layout_preset = QHBoxLayout()
        layout_preset.addWidget(self.btn_save_preset)
        layout_preset.addWidget(self.btn_load_preset)
        layout.addLayout(layout_preset, 4, 0, 1, 3)

        self.setLayout(layout)

    def build_spinbox(self, val, step, min_v, max_v, enabled=True):
        spn = QDoubleSpinBox()
        spn.setRange(min_v, max_v)
        spn.setValue(val)
        spn.setSingleStep(step)
        spn.setDecimals(3)
        spn.setEnabled(enabled)
        return spn
