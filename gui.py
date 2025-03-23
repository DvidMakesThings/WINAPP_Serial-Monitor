import serial.tools.list_ports
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from serial_comm import SerialComm
from file_handler import save_log
import platform
import config  # Import our configuration settings

class SerialMonitorGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Serial Monitor")
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.center_window(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.configure(bg=config.BG_COLOR)

        self.serial_comm = None
        self.port_map = {}
        self.selected_port_full = ""

        # ----- Top Frame: Controls (organized using grid) -----
        self.top_frame = ctk.CTkFrame(self, fg_color=config.BG_COLOR, border_width=0)
        self.top_frame.pack(fill="x", padx=10, pady=5)
        
        # Row 0: Port label and OptionMenu with command callback
        port_label = ctk.CTkLabel(self.top_frame, text="Port:", fg_color=config.BG_COLOR,
                                  text_color="white", font=config.DEFAULT_FONT)
        port_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.port_combo = ctk.CTkOptionMenu(self.top_frame, values=[], font=config.DEFAULT_FONT,
                                           command=self.on_port_selected)
        self.port_combo.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        
        # Row 1: Baud label and OptionMenu
        baud_label = ctk.CTkLabel(self.top_frame, text="Baud:", fg_color=config.BG_COLOR,
                                  text_color="white", font=config.DEFAULT_FONT)
        baud_label.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        standard_baud_rates = [110, 300, 600, 1200, 2400, 4800, 9600, 14400, 19200,
                                 38400, 57600, 115200, 128000, 256000]
        baud_values = [str(b) for b in standard_baud_rates]
        self.baud_combo = ctk.CTkOptionMenu(self.top_frame, values=baud_values, font=config.DEFAULT_FONT)
        self.baud_combo.set("115200")
        self.baud_combo.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        
        # Row 2: Refresh and Connect buttons
        self.refresh_button = ctk.CTkButton(self.top_frame, text="Refresh Ports",
                                            command=self.refresh_ports,
                                            fg_color=config.BUTTON_STYLES["green"][0],
                                            hover_color=config.BUTTON_STYLES["green"][1],
                                            font=config.DEFAULT_FONT)
        self.refresh_button.grid(row=2, column=0, padx=5, pady=2, sticky="ew")
        self.connect_button = ctk.CTkButton(self.top_frame, text="Connect",
                                            command=self.toggle_connection,
                                            fg_color=config.BUTTON_STYLES["green"][0],
                                            hover_color=config.BUTTON_STYLES["green"][1],
                                            font=config.DEFAULT_FONT)
        self.connect_button.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        
        # Configure grid columns
        self.top_frame.grid_columnconfigure(0, weight=1)
        self.top_frame.grid_columnconfigure(1, weight=3)
        
        # ----- Middle Frame: Terminal -----
        self.middle_frame = ctk.CTkFrame(self, fg_color=config.BG_COLOR, border_width=0)
        self.middle_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.terminal = tk.Text(self.middle_frame, bg=config.TERMINAL_BG, fg=config.TERMINAL_FG,
                                font=("Courier", 12), state="disabled", bd=0, highlightthickness=0)
        self.terminal.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(self.middle_frame, command=self.terminal.yview)
        scrollbar.pack(side="right", fill="y")
        self.terminal.config(yscrollcommand=scrollbar.set)
        self.terminal.append = self.append_text
        self.terminal.insertPlainText = self.insert_plain_text

        # ----- Input Frame: User input and Send button -----
        self.input_frame = ctk.CTkFrame(self, fg_color=config.BG_COLOR, border_width=0)
        self.input_frame.pack(fill="x", padx=10, pady=5)
        self.message_input = ctk.CTkEntry(self.input_frame, placeholder_text="Type a message...",
                                           font=config.DEFAULT_FONT)
        self.message_input.pack(side="left", fill="x", expand=True, padx=5)
        self.message_input.bind("<Return>", lambda event: self.send_message())
        self.send_button = ctk.CTkButton(self.input_frame, text="Send", width=80,
                                         command=self.send_message,
                                         fg_color=config.BUTTON_STYLES["green"][0],
                                         hover_color=config.BUTTON_STYLES["green"][1],
                                         font=config.DEFAULT_FONT)
        self.send_button.pack(side="left", padx=5)

        # ----- Bottom Frame: Clear Terminal, Save Log, Auto Append -----
        self.bottom_frame = ctk.CTkFrame(self, fg_color=config.BG_COLOR, border_width=0)
        self.bottom_frame.pack(fill="x", padx=10, pady=5)
        self.clear_button = ctk.CTkButton(self.bottom_frame, text="Clear Terminal", width=120,
                                          command=self.clear_terminal,
                                          fg_color=config.BUTTON_STYLES["green"][0],
                                          hover_color=config.BUTTON_STYLES["green"][1],
                                          font=config.DEFAULT_FONT)
        self.clear_button.pack(side="left", padx=5)
        self.save_button = ctk.CTkButton(self.bottom_frame, text="Save Log", width=120,
                                         command=self.handle_save_log,
                                         fg_color=config.BUTTON_STYLES["blue"][0],
                                         hover_color=config.BUTTON_STYLES["blue"][1],
                                         font=config.DEFAULT_FONT)
        self.save_button.pack(side="left", padx=5)
        self.auto_terminate = ctk.CTkCheckBox(self.bottom_frame, text="Auto append \\r\\n",
                                              font=config.DEFAULT_FONT,
                                              text_color="white", fg_color=config.BG_COLOR)
        self.auto_terminate.select()
        self.auto_terminate.pack(side="left", padx=5)

        # Initial port refresh
        self.refresh_ports()

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def truncate_text(self, text, max_length=config.TRUNCATE_LENGTH):
        if len(text) > max_length:
            return text[:max_length-3] + "..."
        return text

    def on_port_selected(self, selection):
        self.selected_port_full = selection
        self.port_combo.set(self.truncate_text(selection))

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
        self.port_map.clear()
        ports = serial.tools.list_ports.comports()
        port_values = []
        for port in ports:
            desc = f"{port.device} - {port.description}"
            self.port_map[desc] = port.device
            port_values.append(desc)
        if platform.system() == "Linux":
            common_ports = ["/dev/ttyUSB0", "/dev/ttyACM0", "/dev/ttyS0"]
            for p in common_ports:
                if p not in self.port_map.values():
                    desc = f"{p} - (Common Linux Port)"
                    self.port_map[desc] = p
                    port_values.append(desc)
        self.port_combo.configure(values=port_values)
        if port_values:
            self.selected_port_full = port_values[0]
            self.port_combo.set(self.truncate_text(port_values[0]))
        else:
            self.port_combo.set("")

    def toggle_connection(self):
        if self.serial_comm and self.serial_comm.running:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        selected_desc = self.selected_port_full if self.selected_port_full else self.port_combo.get()
        if not selected_desc:
            self.append_text("⚠ No port selected.")
            return
        port = self.port_map.get(selected_desc)
        baud = int(self.baud_combo.get())
        self.serial_comm = SerialComm(
            self.port_combo, self.baud_combo, self.connect_button,
            self.terminal, self.port_map, self.get_button_style
        )
        if self.serial_comm.connect(port, baud):
            self.connect_button.configure(text="Disconnect", fg_color=config.BUTTON_STYLES["red"][0],
                                          hover_color=config.BUTTON_STYLES["red"][1])
            self.port_combo.configure(state="disabled")
            self.baud_combo.configure(state="disabled")

    def disconnect_serial(self):
        if self.serial_comm:
            self.serial_comm.disconnect()
        self.connect_button.configure(text="Connect", fg_color=config.BUTTON_STYLES["green"][0],
                                      hover_color=config.BUTTON_STYLES["green"][1])
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
        return config.BUTTON_STYLES.get(color, config.BUTTON_STYLES["green"])
