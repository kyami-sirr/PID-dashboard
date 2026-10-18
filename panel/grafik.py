import pyqtgraph as pg
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QStackedWidget, QWidget
from PyQt5.QtCore import Qt

try:
    from gauge_widget import AngleGaugeWidget
except ImportError:
    class AngleGaugeWidget(QWidget):
        def set_angles(self, target, actual):
            pass

class PanelGrafik(QVBoxLayout):
    def __init__(self, parent=None):
        super().__init__()
        self.setSpacing(10)
        self.init_ui()

    def init_ui(self):
        # Matikan Antialias untuk mencegah freeze saat zoom dekat pada sinyal berosilasi
        pg.setConfigOptions(antialias=False, useOpenGL=False)

        plot_toolbar = QHBoxLayout()
        plot_title = QLabel("GRAFIK RESPON SISTEM")
        plot_title.setStyleSheet("color: #cbd5e1; font-weight: 700; font-size: 11px;")

        self.chk_unlock_pid = QCheckBox("Buka Kunci PID")
        self.chk_unlock_pid.setStyleSheet("color: #94a3b8; font-weight: 600; margin-right: 6px;")

        btn_style = """
            QPushButton {
                background-color: #1a1e26;
                color: #cbd5e1;
                border: 1px solid #28303f;
                border-radius: 6px;
                padding: 4px 10px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #232936;
                border-color: #475569;
                color: #ffffff;
            }
        """

        self.btn_export_csv = QPushButton("Ekspor CSV")
        self.btn_export_csv.setStyleSheet(btn_style)

        self.btn_sandwich = QPushButton("Pengaturan")
        self.btn_sandwich.setStyleSheet(btn_style)

        self.btn_reset_view = QPushButton("Reset Grafik")
        self.btn_reset_view.setStyleSheet(btn_style)

        plot_toolbar.addWidget(plot_title)
        plot_toolbar.addStretch()
        plot_toolbar.addWidget(self.chk_unlock_pid)
        plot_toolbar.addWidget(self.btn_export_csv)
        plot_toolbar.addWidget(self.btn_sandwich)
        plot_toolbar.addWidget(self.btn_reset_view)
        self.addLayout(plot_toolbar)

        self.stacked_view = QStackedWidget()

        # 1. GRAFIK UTAMA RESPON SISTEM
        self.plot_graph = pg.PlotWidget()
        self.plot_graph.setStyleSheet("background-color: #0d0f12; border: 1px solid #1f242d; border-radius: 6px;")
        self.plot_graph.setBackground("#0d0f12")
        self.plot_graph.showGrid(x=True, y=True, alpha=0.15)
        
        # Penguncian warna sumbu (monokrom)
        self.plot_graph.getAxis('bottom').setPen(pg.mkPen(color='#475569'))
        self.plot_graph.getAxis('left').setPen(pg.mkPen(color='#475569'))
        self.plot_graph.getAxis('bottom').setTextPen(pg.mkPen(color='#94a3b8'))
        self.plot_graph.getAxis('left').setTextPen(pg.mkPen(color='#94a3b8'))

        # Optimization Flags: Mencegah lag/freeze saat zoom dekat
        self.curve_target = self.plot_graph.plot(
            pen=pg.mkPen(color="#94a3b8", width=1.5, style=Qt.DashLine),
            clipToView=True,
            autoDownsample=True,
            downsampleMethod='peak'
        )
        self.curve_actual = self.plot_graph.plot(
            pen=pg.mkPen(color="#ffffff", width=1.8),
            clipToView=True,
            autoDownsample=True,
            downsampleMethod='peak'
        )
        
        self.plot_graph.setDownsampling(ds=True, auto=True, mode='peak')
        self.plot_graph.setClipToView(True)

        self.stacked_view.addWidget(self.plot_graph)

        # 2. INDIKATOR GAUGE (ANGLE GAUGE WIDGET)
        try:
            self.gauge_widget = AngleGaugeWidget(show_text=True)
        except TypeError:
            self.gauge_widget = AngleGaugeWidget()
        self.stacked_view.addWidget(self.gauge_widget)

        # 3. GRAFIK AKTUATOR (PWM)
        self.pwm_graph = pg.PlotWidget(title="AKTUATOR (PWM)")
        self.pwm_graph.setStyleSheet("background-color: #0d0f12; border: 1px solid #1f242d; border-radius: 6px;")
        self.pwm_graph.setBackground("#0d0f12")
        self.pwm_graph.setMaximumHeight(130)
        self.pwm_graph.showGrid(x=True, y=True, alpha=0.15)
        
        self.pwm_graph.getAxis('bottom').setPen(pg.mkPen(color='#475569'))
        self.pwm_graph.getAxis('left').setPen(pg.mkPen(color='#475569'))
        self.pwm_graph.getAxis('bottom').setTextPen(pg.mkPen(color='#94a3b8'))
        self.pwm_graph.getAxis('left').setTextPen(pg.mkPen(color='#94a3b8'))

        self.curve_pwm = self.pwm_graph.plot(
            pen=pg.mkPen(color="#cbd5e1", width=1.2),
            clipToView=True,
            autoDownsample=True,
            downsampleMethod='peak'
        )
        self.pwm_graph.setDownsampling(ds=True, auto=True, mode='peak')
        self.pwm_graph.setClipToView(True)

        self.addWidget(self.stacked_view, 7)
        self.addWidget(self.pwm_graph, 3)
