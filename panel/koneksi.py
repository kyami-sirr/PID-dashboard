import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QCheckBox, QGroupBox
)
from PyQt5.QtCore import pyqtSignal


class PortLineEdit(QLineEdit):
    """QLineEdit bertema gelap netral dengan method kompatibilitas QComboBox untuk dashboard.py."""
    currentTextChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.textChanged.connect(self.currentTextChanged.emit)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet("""
            QLineEdit {
                background-color: #1a1d24;
                color: #e0e0e0;
                border: 1px solid #3a3f4d;
                border-radius: 4px;
                padding: 5px 8px;
                font-family: monospace;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #5c6370;
                background-color: #222630;
            }
            QLineEdit:disabled {
                background-color: #121419;
                color: #5c6370;
                border: 1px solid #282c34;
            }
        """)

    # Method kompatibilitas agar dashboard.py tidak crash
    def currentText(self) -> str:
        return self.text().strip()

    def setCurrentText(self, text: str):
        self.setText(text)

    def addItems(self, items: list):
        if items and not self.text().strip():
            self.setText(str(items[0]))

    def addItem(self, item: str):
        if item and not self.text().strip():
            self.setText(str(item))

    def count(self) -> int:
        return 1 if self.text().strip() else 0

    def setEditable(self, editable: bool):
        pass

    def setInsertPolicy(self, policy):
        pass


class PanelKoneksi(QGroupBox):
    connect_requested = pyqtSignal(str)
    disconnect_requested = pyqtSignal()
    simulation_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__("KONEKSI SERIAL", parent)
        self.is_connected = False
        self.init_ui()
        self.scan_ports()

    def init_ui(self):
        layout = QVBoxLayout()

        # Baris Port dan Tombol Pindai
        port_layout = QHBoxLayout()
        
        self.label_port = QLabel("Port:")
        
        # Input Port Khusus Ketik Manual (QLineEdit)
        self.combo_port = PortLineEdit()
        self.combo_ports = self.combo_port  # Alias kompatibilitas
        self.combo_port.setPlaceholderText("COM3 atau /dev/ttyUSB0")
        self.combo_port.currentTextChanged.connect(self._update_connect_button_text)

        # Tombol Rescan / Pindai
        self.btn_rescan = QPushButton("Pindai")
        self.btn_scan = self.btn_rescan  # Alias kompatibilitas
        self.btn_rescan.clicked.connect(self.scan_ports)

        port_layout.addWidget(self.label_port)
        port_layout.addWidget(self.combo_port, stretch=1)
        port_layout.addWidget(self.btn_rescan)

        # Label Deskripsi Perangkat
        self.lbl_device_info = QLabel("")
        self.lbl_device_info.setStyleSheet("color: #8a92a3; font-size: 11px;")

        # Tombol Hubungkan / Putuskan
        self.btn_auto_connect = QPushButton("Hubungkan")
        self.btn_connect = self.btn_auto_connect  # Alias kompatibilitas

        # Checkbox Mode Simulasi
        self.chk_sim_mode = QCheckBox("Mode Simulasi")
        self.chk_simulation = self.chk_sim_mode  # Alias kompatibilitas

        layout.addLayout(port_layout)
        layout.addWidget(self.lbl_device_info)
        layout.addWidget(self.btn_auto_connect)
        layout.addWidget(self.chk_sim_mode)

        self.setLayout(layout)

    def scan_ports(self):
        """Memindai port serial dan mengisi otomatis jika input port masih kosong."""
        current_text = self.get_selected_port()

        ports = serial.tools.list_ports.comports()
        scanned_ports = [port.device for port in ports]

        if scanned_ports:
            if not current_text:
                self.combo_port.setText(scanned_ports[0])
                if hasattr(ports[0], 'description'):
                    self.lbl_device_info.setText(ports[0].description)

        self._update_connect_button_text()

    def _update_connect_button_text(self):
        """Memperbarui label tombol sesuai port yang diketik/terdeteksi."""
        port = self.get_selected_port()
        if not self.is_connected:
            if port:
                self.btn_auto_connect.setText(f"Hubungkan ({port})")
            else:
                self.btn_auto_connect.setText("Hubungkan")

    def get_selected_port(self) -> str:
        """Mengambil teks port hasil ketikan manual."""
        return self.combo_port.text().strip()

    def set_connected_state(self, connected: bool):
        """Mengatur tampilan UI saat terhubung/terputus."""
        self.is_connected = connected
        if connected:
            port = self.get_selected_port()
            self.btn_auto_connect.setText(f"Putuskan ({port})")
            self.combo_port.setEnabled(False)
            self.btn_rescan.setEnabled(False)
        else:
            self.combo_port.setEnabled(True)
            self.btn_rescan.setEnabled(True)
            self._update_connect_button_text()
