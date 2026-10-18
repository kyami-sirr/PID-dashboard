import serial
from PyQt5.QtCore import QThread, pyqtSignal

class SerialReaderThread(QThread):
    data_received = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, ser):
        super().__init__()
        self.ser = ser
        self.running = True

    def run(self):
        while self.running and self.ser and self.ser.is_open:
            try:
                line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    self.data_received.emit(line)
            except Exception:
                self.connection_lost.emit()
                break

    def stop(self):
        self.running = False
        self.wait()
