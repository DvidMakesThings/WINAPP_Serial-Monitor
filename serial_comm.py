import threading
import time
from datetime import datetime
import tkinter as tk
import traceback

import serial

class SerialComm:
    def __init__(self, port_combo, baud_combo, connect_button, terminal, port_map, get_button_style, data_processor=None):
        # References to GUI elements (passed from the GUI module)
        self.port_combo = port_combo
        self.baud_combo = baud_combo
        self.connect_button = connect_button
        self.terminal = terminal
        self.port_map = port_map
        self.get_button_style = get_button_style
        self.data_processor = data_processor

        self.serial_port = None
        self.running = False
        self.serial_thread = None
        self.reconnect_thread = None
        self.last_port = None
        self.last_baud = None

    def connect(self, port, baud):
        if not port:
            self.terminal.after(0,
                lambda: self.append_to_terminal("⚠ No port selected.\n"))
            return False

        try:
            self.serial_port = serial.Serial(port, baud, timeout=0.1)
            self.running     = True
            self.last_port   = port
            self.last_baud   = baud
            self.connect_button.after(0, lambda: self.connect_button.configure(
                text="Disconnect",
                fg_color=self.get_button_style("red")[0]
            ))
            self.terminal.after(0,
                lambda: self.append_to_terminal(f"✅ Connected to {port} @ {baud} baud\n"))
            # Start reader
            self.serial_thread = threading.Thread(target=self.read_serial, daemon=True)
            self.serial_thread.start()
            return True

        except serial.SerialException:
            self.terminal.after(0,
                lambda: self.append_to_terminal(f"❌ Failed to connect to {port}. Retrying...\n"))
            self.start_reconnect_thread()
            return False

    def disconnect(self):
        self.running = False
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None
        self.connect_button.after(0, lambda: self.connect_button.configure(
            text="Connect",
            fg_color=self.get_button_style("green")[0]
        ))
        self.terminal.after(0,
            lambda: self.append_to_terminal("🔌 Disconnected.\n"))

    def start_reconnect_thread(self):
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            return
        self.reconnect_thread = threading.Thread(target=self.reconnect_serial, daemon=True)
        self.reconnect_thread.start()

    def reconnect_serial(self):
        # Continuously try to reconnect
        while not self.running:
            try:
                self.serial_port = serial.Serial(self.last_port, self.last_baud, timeout=0.1)
                self.running = True
                self.connect_button.after(0, lambda: self.connect_button.configure(
                    text="Disconnect",
                    fg_color=self.get_button_style("red")[0]
                ))
                self.terminal.after(0,
                    lambda: self.append_to_terminal(f"✅ Reconnected to {self.last_port}\n"))
                self.serial_thread = threading.Thread(target=self.read_serial, daemon=True)
                self.serial_thread.start()
                return
            except serial.SerialException:
                time.sleep(1)

    def read_serial(self):
        while self.running and self.serial_port:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting)\
                                       .decode('utf-8', errors='ignore')
                    if data:
                        # Process data through data processor if available
                        try:
                            if self.data_processor:
                                self.data_processor.process_data(data, datetime.now())
                        except Exception as e:
                            print(f"Data processor error: {e}")
                        
                        # Update terminal
                        self.terminal.after(0, lambda d=data: self.append_to_terminal(d))
                            
            except serial.SerialException as e:
                print(f"Serial exception: {e}")
                self.terminal.after(0,
                    lambda: self.append_to_terminal("⚠ Device disconnected. Reconnecting...\n"))
                self.running = False
                self.start_reconnect_thread()
                break
            except Exception as e:
                print(f"Unexpected error in read_serial: {e}")
                traceback.print_exc()
                time.sleep(0.1)
    
    def append_to_terminal(self, text):
        """Simple terminal update"""
        try:
            self.terminal.config(state="normal")
            self.terminal.insert(tk.END, text)
            self.terminal.see(tk.END)
            self.terminal.config(state="disabled")
        except Exception as e:
            print(f"Error updating terminal: {e}")
    
    def send_message(self, message):
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(message.encode('utf-8'))
                self.terminal.after(0,
                    lambda: self.append_to_terminal(f"➡ {message.strip()}\n"))
            except serial.SerialException:
                self.terminal.after(0,
                    lambda: self.append_to_terminal("⚠ Failed to send message.\n"))