from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QWidget
from PyQt5.QtCore import Qt

class PanelSkema(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("SKEMA KONTROL", parent)
        self.preset_btns = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.btn_mode_selector = QPushButton("0. (Off)")
        self.btn_mode_selector.setStyleSheet("""
            QPushButton {
                background-color: #1a1e26; color: #f1f5f9; border: 1px solid #28303f;
                border-radius: 6px; padding: 10px; font-weight: bold; font-size: 12px; text-align: left; padding-left: 14px;
            }
            QPushButton:hover { background-color: #232936; border-color: #3b475d; }
        """)

        self.lbl_target_info = QLabel("Referensi: 0")
        self.sld_target = QSlider(Qt.Horizontal)
        self.sld_target.setEnabled(False)

        self.preset_box = QHBoxLayout()
        for i in range(5):
            b = QPushButton("—")
            self.preset_box.addWidget(b)
            self.preset_btns.append(b)

        self.btn_zero = QPushButton("Reset Set Point 0°")
        self.btn_zero.setEnabled(False)

        layout.addWidget(QLabel("Pilih Mode:"))
        layout.addWidget(self.btn_mode_selector)

        self.container = QWidget()
        layout_dyn = QVBoxLayout(self.container)
        layout_dyn.setContentsMargins(0, 0, 0, 0)
        layout_dyn.setSpacing(6)

        layout_dyn.addWidget(self.lbl_target_info)
        layout_dyn.addWidget(self.sld_target)
        layout_dyn.addWidget(QLabel("Tombol Cepat:"))
        layout_dyn.addLayout(self.preset_box)
        layout_dyn.addWidget(self.btn_zero)

        layout.addWidget(self.container)
        self.setLayout(layout)
