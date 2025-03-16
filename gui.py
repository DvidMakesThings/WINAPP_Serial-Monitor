import serial.tools.list_ports
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QComboBox, QTextEdit,
    QLineEdit, QFileDialog, QLabel, QCheckBox, QHBoxLayout
)
from serial_comm import SerialComm
from file_handler import save_log

class SerialMonitorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Serial Monitor")
        self.setGeometry(100, 100, 700, 500)
        self.setStyleSheet("background-color: #222; color: white;")

        self.serial_comm = None
        self.port_map = {}

        # UI Components
        layout = QVBoxLayout()

        self.port_combo = QComboBox()
        self.refresh_ports()

        # Standard baud rates
        standard_baud_rates = [110, 300, 600, 1200, 2400, 4800, 9600, 14400, 19200,
                                38400, 57600, 115200, 128000, 256000]
        self.baud_combo = QComboBox()
        for baud in standard_baud_rates:
            self.baud_combo.addItem(str(baud))
        self.baud_combo.setCurrentText("115200")  # Default baud rate

        refresh_button = QPushButton("Refresh Ports")
        refresh_button.clicked.connect(self.refresh_ports)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)
        self.connect_button.setStyleSheet(self.get_button_style("green"))

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("background-color: #111; color: #0f0; font: 12px monospace;")

        # Clear & Save Buttons
        clear_button = QPushButton("Clear Terminal")
        clear_button.setFixedWidth(120)
        clear_button.setStyleSheet(self.get_button_style("green"))
        clear_button.clicked.connect(self.terminal.clear)

        save_button = QPushButton("Save Log")
        save_button.setFixedWidth(120)
        save_button.setStyleSheet(self.get_button_style("blue"))
        save_button.clicked.connect(self.handle_save_log)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Send")
        self.send_button.setFixedWidth(80)
        self.send_button.clicked.connect(self.send_message)

        self.auto_terminate = QCheckBox("Auto append \\r\\n")
        self.auto_terminate.setChecked(True)

        # Layout Configuration
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Port:"))
        control_layout.addWidget(self.port_combo)
        control_layout.addWidget(QLabel("Baud:"))
        control_layout.addWidget(self.baud_combo)
        control_layout.addWidget(refresh_button)
        control_layout.addWidget(self.connect_button)

        send_layout = QHBoxLayout()
        send_layout.addWidget(self.message_input)
        send_layout.addWidget(self.send_button)

        button_layout = QHBoxLayout()
        button_layout.addWidget(clear_button)
        button_layout.addWidget(save_button)

        layout.addLayout(control_layout)
        layout.addWidget(self.terminal)
        layout.addLayout(button_layout)
        layout.addLayout(send_layout)
        layout.addWidget(self.auto_terminate)

        self.setLayout(layout)

    def refresh_ports(self):
        """ Refresh the list of available COM ports with names. """
        self.port_combo.clear()
        self.port_map.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            desc = f"{port.device} - {port.description}"
            self.port_map[desc] = port.device
            self.port_combo.addItem(desc)

    def get_button_style(self, color):
        """ Returns the button style for a given color. """
        colors = {
            "green": "rgb(0, 150, 0)", "dark_green": "rgb(0, 100, 0)",
            "blue": "rgb(0, 100, 200)", "dark_blue": "rgb(0, 70, 150)",
            "red": "rgb(200, 0, 0)", "dark_red": "rgb(150, 0, 0)"
        }
        return f"""
            QPushButton {{
                background-color: {colors[color]};
                color: white;
                border-radius: 5px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {colors["dark_" + color]};
            }}
        """

    def toggle_connection(self):
        if self.serial_comm and self.serial_comm.running:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        selected_desc = self.port_combo.currentText()
        if not selected_desc:
            self.terminal.append("⚠ No port selected.")
            return
        port = self.port_map.get(selected_desc)
        baud = int(self.baud_combo.currentText())
        # Create the SerialComm instance with references to necessary GUI elements.
        self.serial_comm = SerialComm(
            self.port_combo, self.baud_combo, self.connect_button,
            self.terminal, self.port_map, self.get_button_style
        )
        if self.serial_comm.connect():
            self.connect_button.setText("Disconnect")
            self.connect_button.setStyleSheet(self.get_button_style("red"))
            self.port_combo.setEnabled(False)
            self.baud_combo.setEnabled(False)

    def disconnect_serial(self):
        if self.serial_comm:
            self.serial_comm.disconnect()
        self.connect_button.setText("Connect")
        self.connect_button.setStyleSheet(self.get_button_style("green"))
        self.port_combo.setEnabled(True)
        self.baud_combo.setEnabled(True)

    def send_message(self):
        if self.serial_comm and self.serial_comm.serial_port and self.serial_comm.serial_port.is_open:
            message = self.message_input.text()
            if self.auto_terminate.isChecked():
                message += "\r\n"
            self.serial_comm.send_message(message)
            self.message_input.clear()

    def handle_save_log(self):
        from PyQt6.QtWidgets import QFileDialog
        options = ["Text File (*.txt)", "Excel File (*.xls)"]
        file_dialog = QFileDialog.getSaveFileName(self, "Save Log", "", ";;".join(options))
        if file_dialog[0]:
            filename = file_dialog[0]
            log_text = self.terminal.toPlainText()
            save_log(log_text, filename)
            self.terminal.append(f"💾 Log saved to {filename}")
