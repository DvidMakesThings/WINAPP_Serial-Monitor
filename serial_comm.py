import serial
import threading

class SerialComm:
    def __init__(self, port_combo, baud_combo, connect_button, terminal, port_map, get_button_style):
        # References to GUI elements (passed from the GUI module)
        self.port_combo = port_combo
        self.baud_combo = baud_combo
        self.connect_button = connect_button
        self.terminal = terminal
        self.port_map = port_map
        self.get_button_style = get_button_style

        self.serial_port = None
        self.running = False
        self.serial_thread = None
        self.reconnect_thread = None

    def connect(self):
        selected_desc = self.port_combo.currentText()
        port = self.port_map.get(selected_desc, None)
        baud = int(self.baud_combo.currentText())  # Convert selected baud rate to integer

        if not port:
            self.terminal.append("⚠ No port selected.")
            return False

        try:
            self.serial_port = serial.Serial(port, baud, timeout=0.1)
            self.running = True
            self.connect_button.setText("Disconnect")
            self.connect_button.setStyleSheet(self.get_button_style("red"))
            self.terminal.append(f"✅ Connected to {port} @ {baud} baud")

            self.port_combo.setEnabled(False)
            self.baud_combo.setEnabled(False)

            self.serial_thread = threading.Thread(target=self.read_serial, daemon=True)
            self.serial_thread.start()
            return True
        except serial.SerialException:
            self.terminal.append(f"❌ Failed to connect to {port}. Retrying...")
            self.start_reconnect_thread()
            return False

    def disconnect(self):
        self.running = False
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None
        self.connect_button.setText("Connect")
        self.connect_button.setStyleSheet(self.get_button_style("green"))
        self.terminal.append("🔌 Disconnected.")

        # Re-enable COM port and baud rate selection when disconnected
        self.port_combo.setEnabled(True)
        self.baud_combo.setEnabled(True)

    def start_reconnect_thread(self):
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            return
        self.reconnect_thread = threading.Thread(target=self.reconnect_serial, daemon=True)
        self.reconnect_thread.start()

    def reconnect_serial(self):
        while not self.running:
            selected_desc = self.port_combo.currentText()
            port = self.port_map.get(selected_desc, None)
            baud = int(self.baud_combo.currentText())
            if port:
                try:
                    self.serial_port = serial.Serial(port, baud, timeout=0.1)
                    self.running = True
                    self.connect_button.setText("Disconnect")
                    self.connect_button.setStyleSheet(self.get_button_style("red"))
                    self.terminal.append(f"✅ Reconnected to {port}")

                    self.serial_thread = threading.Thread(target=self.read_serial, daemon=True)
                    self.serial_thread.start()
                    return
                except serial.SerialException:
                    pass  # Keep trying instantly

    def read_serial(self):
        while self.running and self.serial_port:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore')
                    if data:
                        # Use insertPlainText to preserve multiple \n characters
                        self.terminal.insertPlainText(data)
                        self.terminal.verticalScrollBar().setValue(self.terminal.verticalScrollBar().maximum())
            except serial.SerialException:
                self.terminal.append("⚠ Device disconnected. Reconnecting...")
                self.running = False
                self.start_reconnect_thread()
                break

    def send_message(self, message):
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(message.encode('utf-8'))
                self.terminal.append(f"➡ {message.strip()}")
            except serial.SerialException:
                self.terminal.append("⚠ Failed to send message.")
