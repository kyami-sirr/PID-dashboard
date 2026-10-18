from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt

def buat_kartu(title, init_val):
    frame = QFrame()
    frame.setStyleSheet("background-color: #14171d; border: 1px solid #1f242d; border-radius: 6px;")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(10, 10, 10, 10)
    
    lbl_t = QLabel(title)
    lbl_t.setStyleSheet("font-size: 9px; color: #64748b; font-weight: 700;")
    lbl_v = QLabel(init_val)
    lbl_v.setStyleSheet("font-size: 16px; font-weight: 600; color: #f1f5f9; font-family: monospace;")
    lbl_v.setAlignment(Qt.AlignCenter)
    
    layout.addWidget(lbl_t)
    layout.addWidget(lbl_v)
    frame.val_label = lbl_v
    return frame

class PanelKartu:
    def __init__(self):
        self.metrics_layout = QHBoxLayout()
        self.card_mode = buat_kartu("STATUS", "SIAP")
        self.card_target = buat_kartu("TARGET", "0.0")
        self.card_actual = buat_kartu("AKTUAL", "0.0")
        self.card_pwm = buat_kartu("PWM", "0")
        
        self.metrics_layout.addWidget(self.card_mode)
        self.metrics_layout.addWidget(self.card_target)
        self.metrics_layout.addWidget(self.card_actual)
        self.metrics_layout.addWidget(self.card_pwm)

        self.transient_layout = QHBoxLayout()
        self.card_overshoot = buat_kartu("OVERSHOOT", "0.0 %")
        self.card_risetime  = buat_kartu("RISE TIME", "0.00 s")
        self.card_settling  = buat_kartu("SETTLING", "0.00 s")
        self.card_ss_error  = buat_kartu("ERROR STEADY", "0.00")
        
        self.transient_layout.addWidget(self.card_overshoot)
        self.transient_layout.addWidget(self.card_risetime)
        self.transient_layout.addWidget(self.card_settling)
        self.transient_layout.addWidget(self.card_ss_error)
