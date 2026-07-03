import sys
import socket
import struct
import base64
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, 
                             QPushButton, QVBoxLayout, QWidget, QMessageBox, QTextEdit)

def decode_lobby_code(code: str):
    code = code.upper().strip()
    padding_needed = (8 - len(code) % 8) % 8
    padded_code = code + ('=' * padding_needed)
    try:
        combined = base64.b32decode(padded_code.encode('utf-8'))
        if len(combined) != 6:
            return None, None
        ip = socket.inet_ntoa(combined[:4])
        port = struct.unpack('!H', combined[4:])[0]
        return ip, port
    except Exception:
        return None, None

class ClientApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DMS Client")
        self.resize(300, 250)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        layout.addWidget(QLabel("<b>Lobby Code:</b>"))
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter 10-char code from Host")
        layout.addWidget(self.code_input)

        layout.addWidget(QLabel("<b>Message:</b>"))
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        layout.addWidget(self.message_input)

        self.send_btn = QPushButton("Send Message")
        self.send_btn.clicked.connect(self.send_message)
        layout.addWidget(self.send_btn)

    def send_message(self):
        code = self.code_input.text()
        msg = self.message_input.toPlainText()

        if not code or not msg:
            QMessageBox.warning(self, "Error", "Please enter both a lobby code and a message.")
            return

        ip, port = decode_lobby_code(code)
        if not ip or not port:
            QMessageBox.critical(self, "Error", "Invalid Lobby Code.")
            return

        url = f"http://{ip}:{port}/send"
        
        try:
            self.send_btn.setEnabled(False)
            response = requests.post(url, json={'message': msg}, timeout=5)
            response.raise_for_status()
            
            QMessageBox.information(self, "Success", f"Message sent to {ip}:{port}!")
            self.message_input.clear()
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Connection Error", f"Could not connect to {ip}:{port}.\nError: {e}")
        finally:
            self.send_btn.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ClientApp()
    window.show()
    sys.exit(app.exec_())
