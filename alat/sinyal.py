import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QGridLayout, QLabel, QComboBox, QDoubleSpinBox, 
    QPushButton, QMessageBox, QListView
)
from PyQt5.QtCore import Qt, QTimer


class TabSinyal(QWidget):
    def __init__(self, main_dashboard):
        super().__init__()
        self.main_dashboard = main_dashboard
        self.is_running = False
        self.time_counter = 0.0
        
        # Timer untuk streaming sinyal dinamik ke hardware secara real-time
        self.signal_timer = QTimer(self)
        self.signal_timer.setInterval(50)  # Update setiap 50 ms (20 Hz)
        self.signal_timer.timeout.connect(self.process_signal_step)

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
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
            QComboBox, QDoubleSpinBox {
                background-color: #1a1e26;
                color: #ffffff;
                border: 1px solid #28303f;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 11px;
            }
            QComboBox:focus, QDoubleSpinBox:focus {
                border-color: #475569;
            }
            QComboBox::drop-down { border: none; width: 20px; }
            /* Styling Popup Dropdown Item List - Dark Theme Seragam */
            QComboBox QAbstractItemView {
                background-color: #14171d;
                color: #cbd5e1;
                selection-background-color: #1e2430;
                selection-color: #ffffff;
                border: 1px solid #28303f;
                outline: 0px;
                padding: 4px;
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

        left_box = QVBoxLayout()
        grp = QGroupBox("KONFIGURASI SINYAL")
        grp.setStyleSheet(box_style)
        gl = QGridLayout(grp)
        gl.setContentsMargins(12, 12, 12, 12)
        gl.setSpacing(10)

        lbl_type = QLabel("Bentuk Sinyal:")
        lbl_type.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.combo_sig_type = QComboBox()
        # Pasang QListView agar Qt mematuhi CSS Dark Theme pada popup list
        self.combo_sig_type.setView(QListView())
        self.combo_sig_type.addItems(["Sine Wave", "Square Wave", "Step Input"])
        self.combo_sig_type.currentIndexChanged.connect(self.update_preview)

        lbl_amp = QLabel("Amplitudo:")
        lbl_amp.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.spn_sig_amp = QDoubleSpinBox()
        self.spn_sig_amp.setRange(-1360, 1360)
        self.spn_sig_amp.setValue(300)
        self.spn_sig_amp.valueChanged.connect(self.update_preview)

        lbl_freq = QLabel("Frekuensi (Hz):")
        lbl_freq.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.spn_sig_freq = QDoubleSpinBox()
        self.spn_sig_freq.setRange(0.05, 5.0)
        self.spn_sig_freq.setSingleStep(0.05)
        self.spn_sig_freq.setValue(0.2)
        self.spn_sig_freq.valueChanged.connect(self.update_preview)

        self.btn_toggle_sig = QPushButton("Mulai")
        self.btn_toggle_sig.setMinimumHeight(34)
        self.btn_toggle_sig.setStyleSheet(btn_style)
        self.btn_toggle_sig.clicked.connect(self.toggle_signal_generator)

        gl.addWidget(lbl_type, 0, 0)
        gl.addWidget(self.combo_sig_type, 0, 1)
        gl.addWidget(lbl_amp, 1, 0)
        gl.addWidget(self.spn_sig_amp, 1, 1)
        gl.addWidget(lbl_freq, 2, 0)
        gl.addWidget(self.spn_sig_freq, 2, 1)
        gl.addWidget(self.btn_toggle_sig, 3, 0, 1, 2)

        left_box.addWidget(grp)
        left_box.addStretch()

        layout.addLayout(left_box, 4)

        grp_plot = QGroupBox("BENTUK GELOMBANG")
        grp_plot.setStyleSheet(box_style)
        plot_layout = QVBoxLayout(grp_plot)
        plot_layout.setContentsMargins(12, 12, 12, 12)

        # Mengunci warna PlotWidget agar tidak terpengaruh stylesheet parent
        self.plot_preview = pg.PlotWidget()
        self.plot_preview.setStyleSheet("background-color: #0b0c0f; border: 1px solid #1f242d; border-radius: 6px;")
        self.plot_preview.setBackground("#0b0c0f")
        self.plot_preview.getPlotItem().getViewBox().setBackgroundColor("#0b0c0f")
        self.plot_preview.showGrid(x=True, y=True, alpha=0.15)
        
        # Atur warna sumbu agar terlihat jelas pada background gelap
        self.plot_preview.getAxis('bottom').setPen(pg.mkPen(color='#475569'))
        self.plot_preview.getAxis('left').setPen(pg.mkPen(color='#475569'))
        self.plot_preview.getAxis('bottom').setTextPen(pg.mkPen(color='#94a3b8'))
        self.plot_preview.getAxis('left').setTextPen(pg.mkPen(color='#94a3b8'))

        self.curve_preview = self.plot_preview.plot(pen=pg.mkPen(color="#ffffff", width=1.8))
        self.cursor_point = self.plot_preview.plot(pen=None, symbol='o', symbolSize=8, symbolBrush='#ffffff')

        plot_layout.addWidget(self.plot_preview)

        layout.addWidget(grp_plot, 6)
        self.update_preview()

    def update_preview(self):
        amp = self.spn_sig_amp.value()
        freq = self.spn_sig_freq.value()
        stype = self.combo_sig_type.currentText()
        
        t = np.linspace(0, 5, 250)

        if stype == "Step Input":
            y = np.ones_like(t) * amp
        elif stype == "Square Wave":
            y = amp * np.sign(np.sin(2 * np.pi * freq * t))
        else:
            y = amp * np.sin(2 * np.pi * freq * t)

        self.curve_preview.setData(t, y)

    def toggle_signal_generator(self):
        if not self.is_running:
            mode = self.main_dashboard.engine.current_mode
            if mode == 0:
                QMessageBox.warning(self, "Peringatan", "Mode Kontrol saat ini sedang OFF (Mode 0). Aktifkan mode di dashboard terlebih dahulu!")
                return

            self.is_running = True
            self.time_counter = 0.0
            self.signal_timer.start()
            self.btn_toggle_sig.setText("Stop Generator Sinyal Live")
            self.btn_toggle_sig.setStyleSheet("""
                QPushButton {
                    background-color: #232936;
                    color: #ffffff;
                    border: 1px solid #ffffff;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 8px 12px;
                }
            """)
            self.main_dashboard.log(f"[GENERATOR SINYAL] Memulai streaming sinyal live pada Mode {mode}")
        else:
            self.stop_generator()

    def stop_generator(self):
        self.is_running = False
        self.signal_timer.stop()
        self.btn_toggle_sig.setText("Start Generator Sinyal Live")
        self.btn_toggle_sig.setStyleSheet("""
            QPushButton {
                background-color: #1a1e26;
                color: #ffffff;
                border: 1px solid #28303f;
                border-radius: 6px;
                font-weight: 600;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #232936;
                border-color: #475569;
            }
        """)
        self.cursor_point.setData([], [])

    def process_signal_step(self):
        if not self.is_running:
            return

        mode = self.main_dashboard.engine.current_mode
        if mode == 0:
            self.stop_generator()
            QMessageBox.warning(self, "Terhenti", "Mode kontrol diubah ke OFF. Generator sinyal dihentikan.")
            return

        amp = self.spn_sig_amp.value()
        freq = self.spn_sig_freq.value()
        stype = self.combo_sig_type.currentText()

        self.time_counter += 0.05  # Increment waktu interval

        if stype == "Step Input":
            val = amp
        elif stype == "Square Wave":
            val = amp * np.sign(np.sin(2 * np.pi * freq * self.time_counter))
        else:
            val = amp * np.sin(2 * np.pi * freq * self.time_counter)

        # Update titik posisi pada grafik preview
        t_mod = self.time_counter % 5.0
        self.cursor_point.setData([t_mod], [val])

        # Kirim nilai sinyal aktual secara continue ke hardware dan UI dashboard
        self.main_dashboard.panel_skema.sld_target.blockSignals(True)
        self.main_dashboard.panel_skema.sld_target.setValue(int(val))
        self.main_dashboard.panel_skema.sld_target.blockSignals(False)

        self.main_dashboard.engine.setpoint = float(val)
        self.main_dashboard.update_target_label(val)
        self.main_dashboard.send_command(f"M:{mode}:{val:.1f}")

    def hideEvent(self, event):
        self.stop_generator()
        super().hideEvent(event)
