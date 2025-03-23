import serial.tools.list_ports
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from serial_comm import SerialComm
from file_handler import save_log
import platform

class SerialMonitorGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Serial Monitor")
        self.geometry("500x750")
        self.center_window(500, 750)
        self.configure(bg="#222")

        self.serial_comm = None
        self.port_map = {}

        # ----- Top Frame: Controls (re-organized using grid) -----
        # This frame now has three rows:
        # Row 0: Port label and OptionMenu
        # Row 1: Baud label and OptionMenu
        # Row 2: Refresh and Connect buttons
        self.top_frame = ctk.CTkFrame(self, fg_color="#222", border_width=0)
        self.top_frame.pack(fill="x", padx=10, pady=5)
        
        # Row 0: Port label and OptionMenu
        port_label = ctk.CTkLabel(
            self.top_frame, text="Port:", fg_color="#222", text_color="white", font=("Helvetica", 14)
        )
        port_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.port_combo = ctk.CTkOptionMenu(self.top_frame, values=[], font=("Helvetica", 14))
        self.port_combo.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        
        # Row 1: Baud label and OptionMenu
        baud_label = ctk.CTkLabel(
            self.top_frame, text="Baud:", fg_color="#222", text_color="white", font=("Helvetica", 14)
        )
        baud_label.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        standard_baud_rates = [110, 300, 600, 1200, 2400, 4800, 9600, 14400, 19200,
                                 38400, 57600, 115200, 128000, 256000]
        baud_values = [str(b) for b in standard_baud_rates]
        self.baud_combo = ctk.CTkOptionMenu(self.top_frame, values=baud_values, font=("Helvetica", 14))
        self.baud_combo.set("115200")
        self.baud_combo.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        
        # Row 2: Refresh and Connect buttons
        self.refresh_button = ctk.CTkButton(
            self.top_frame, text="Refresh Ports", command=self.refresh_ports,
            fg_color="#009600", hover_color="#006400", font=("Helvetica", 14)
        )
        self.refresh_button.grid(row=2, column=0, padx=5, pady=2, sticky="ew")
        self.connect_button = ctk.CTkButton(
            self.top_frame, text="Connect", command=self.toggle_connection,
            fg_color="#009600", hover_color="#006400", font=("Helvetica", 14)
        )
        self.connect_button.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        
        # Allow the second column to expand more for long port descriptions
        self.top_frame.grid_columnconfigure(0, weight=1)
        self.top_frame.grid_columnconfigure(1, weight=3)
        
        # ----- Middle Frame: Terminal -----
        self.middle_frame = ctk.CTkFrame(self, fg_color="#222", border_width=0)
        self.middle_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.terminal = tk.Text(
            self.middle_frame,
            bg="#111",
            fg="#0f0",
            font=("Courier", 12),
            state="disabled",
            bd=0,  # remove border
            highlightthickness=0
        )
        self.terminal.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(self.middle_frame, command=self.terminal.yview)
        scrollbar.pack(side="right", fill="y")
        self.terminal.config(yscrollcommand=scrollbar.set)
        # Patch the terminal with helper methods so SerialComm can call .append() and .insertPlainText()
        self.terminal.append = self.append_text
        self.terminal.insertPlainText = self.insert_plain_text

        # ----- Input Frame: Dedicated row for user input and Send button -----
        self.input_frame = ctk.CTkFrame(self, fg_color="#222", border_width=0)
        self.input_frame.pack(fill="x", padx=10, pady=5)
        self.message_input = ctk.CTkEntry(
            self.input_frame, placeholder_text="Type a message...", font=("Helvetica", 14)
        )
        self.message_input.pack(side="left", fill="x", expand=True, padx=5)
        self.message_input.bind("<Return>", lambda event: self.send_message())
        self.send_button = ctk.CTkButton(
            self.input_frame, text="Send", width=80,
            command=self.send_message, fg_color="#009600", hover_color="#006400", font=("Helvetica", 14)
        )
        self.send_button.pack(side="left", padx=5)

        # ----- Bottom Frame: Clear Terminal, Save Log, and Auto Append checkbox -----
        self.bottom_frame = ctk.CTkFrame(self, fg_color="#222", border_width=0)
        self.bottom_frame.pack(fill="x", padx=10, pady=5)
        self.clear_button = ctk.CTkButton(
            self.bottom_frame, text="Clear Terminal", width=120,
            command=self.clear_terminal, fg_color="#009600", hover_color="#006400", font=("Helvetica", 14)
        )
        self.clear_button.pack(side="left", padx=5)
        self.save_button = ctk.CTkButton(
            self.bottom_frame, text="Save Log", width=120,
            command=self.handle_save_log, fg_color="#0064C8", hover_color="#004696", font=("Helvetica", 14)
        )
        self.save_button.pack(side="left", padx=5)
        self.auto_terminate = ctk.CTkCheckBox(
            self.bottom_frame, text="Auto append \\r\\n",
            font=("Helvetica", 14), text_color="white", fg_color="#222"
        )
        self.auto_terminate.select()
        self.auto_terminate.pack(side="left", padx=5)

        # Initial port refresh
        self.refresh_ports()

    def center_window(self, width, height):
        # Get screen width and height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        # Calculate position x and y coordinates to center the window
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def append_text(self, text):
        self.terminal.config(state="normal")
        self.terminal.insert(tk.END, text + "\n")
        self.terminal.see(tk.END)
        self.terminal.config(state="disabled")

    def insert_plain_text(self, text):
        self.terminal.config(state="normal")
        self.terminal.insert(tk.END, text)
        self.terminal.see(tk.END)
        self.terminal.config(state="disabled")

    def clear_terminal(self):
        self.terminal.config(state="normal")
        self.terminal.delete("1.0", tk.END)
        self.terminal.config(state="disabled")

    def refresh_ports(self):
        """ Refresh the list of available COM ports with names. """
        self.port_map.clear()
        ports = serial.tools.list_ports.comports()
        port_values = []
        for port in ports:
            desc = f"{port.device} - {port.description}"
            self.port_map[desc] = port.device
            port_values.append(desc)
        # Added Linux support: Append common Linux serial ports if not already detected
        if platform.system() == "Linux":
            common_ports = ["/dev/ttyUSB0", "/dev/ttyACM0", "/dev/ttyS0"]
            for p in common_ports:
                if p not in self.port_map.values():
                    desc = f"{p} - (Common Linux Port)"
                    self.port_map[desc] = p
                    port_values.append(desc)
        self.port_combo.configure(values=port_values)
        if port_values:
            self.port_combo.set(port_values[0])
        else:
            self.port_combo.set("")

    def toggle_connection(self):
        if self.serial_comm and self.serial_comm.running:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        selected_desc = self.port_combo.get()
        if not selected_desc:
            self.append_text("⚠ No port selected.")
            return
        port = self.port_map.get(selected_desc)
        baud = int(self.baud_combo.get())
        # Create the SerialComm instance with references to necessary GUI elements.
        self.serial_comm = SerialComm(
            self.port_combo, self.baud_combo, self.connect_button,
            self.terminal, self.port_map, self.get_button_style
        )
        if self.serial_comm.connect(port, baud):
            self.connect_button.configure(text="Disconnect", fg_color="#C80000", hover_color="#960000")
            self.port_combo.configure(state="disabled")
            self.baud_combo.configure(state="disabled")

    def disconnect_serial(self):
        if self.serial_comm:
            self.serial_comm.disconnect()
        self.connect_button.configure(text="Connect", fg_color="#009600", hover_color="#006400")
        self.port_combo.configure(state="normal")
        self.baud_combo.configure(state="normal")

    def send_message(self):
        if self.serial_comm and self.serial_comm.serial_port and self.serial_comm.serial_port.is_open:
            message = self.message_input.get()
            if self.auto_terminate.get():
                message += "\r\n"
            self.serial_comm.send_message(message)
            self.message_input.delete(0, tk.END)

    def handle_save_log(self):
        filename = filedialog.asksaveasfilename(
            title="Save Log",
            filetypes=[("Text File", "*.txt"), ("Excel File", "*.xls")]
        )
        if filename:
            log_text = self.terminal.get("1.0", tk.END)
            save_log(log_text, filename)
            self.append_text(f"💾 Log saved to {filename}")

    def get_button_style(self, color):
        # Return a tuple of (fg_color, hover_color)
        colors = {
            "green": ("#009600", "#006400"),
            "blue": ("#0064C8", "#004696"),
            "red": ("#C80000", "#960000")
        }
        return colors.get(color, ("#009600", "#006400"))
