import sys
import socket
import struct
import base64
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal
from flask import Flask, request, jsonify

app = Flask(__name__)
# Suppress noisy Flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

current_flask_thread = None

@app.route('/send', methods=['POST'])
def send_message():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Missing message'}), 400
    
    msg = data['message']
    if current_flask_thread:
        current_flask_thread.message_received.emit(msg)
    
    return jsonify({'status': 'ok'}), 200

class FlaskThread(QThread):
    message_received = pyqtSignal(str)

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        global current_flask_thread
        current_flask_thread = self

    def run(self):
        # Disable reloader so it doesn't break in a thread
        app.run(host=self.host, port=self.port, debug=False, use_reloader=False)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def encode_lobby_code(ip: str, port: int) -> str:
    ip_bytes = socket.inet_aton(ip)
    port_bytes = struct.pack('!H', port)
    combined = ip_bytes + port_bytes
    b32 = base64.b32encode(combined).decode('utf-8').replace('=', '')
    return b32

class HostApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DMS Host")
        self.resize(400, 300)

        # UI Setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.ip = get_local_ip()
        self.port = 8080
        self.lobby_code = encode_lobby_code(self.ip, self.port)

        info_label = QLabel(f"<b>Host IP:</b> {self.ip}:{self.port}")
        layout.addWidget(info_label)

        code_label = QLabel(f"<b>Lobby Code:</b> <span style='color: blue; font-size: 20px;'>{self.lobby_code}</span>")
        layout.addWidget(code_label)

        layout.addWidget(QLabel("<b>Received Messages:</b>"))
        self.messages_area = QTextEdit()
        self.messages_area.setReadOnly(True)
        layout.addWidget(self.messages_area)

        # Start Flask backend
        self.flask_thread = FlaskThread('0.0.0.0', self.port)
        self.flask_thread.message_received.connect(self.on_message_received)
        self.flask_thread.start()

    def on_message_received(self, msg):
        self.messages_area.append(f"Client: {msg}")

    def closeEvent(self, event):
        # Terminating threads abruptly is bad practice, but for this prototype it ensures clean exit
        self.flask_thread.terminate()
        super().closeEvent(event)

if __name__ == '__main__':
    qt_app = QApplication(sys.argv)
    window = HostApp()
    window.show()
    sys.exit(qt_app.exec_())
