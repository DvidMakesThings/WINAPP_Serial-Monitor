import serial.tools.list_ports
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from serial_comm import SerialComm
from file_handler import save_log
import platform
import config
import timestamping
import data_converter
import data_visualizer

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
        self.all_messages = []
        self.filter_text = ""
        self.paused = False
        self.scroll_buffer = []
        self.visualizer = None

        # ----- Filter Frame -----
        self.filter_frame = ctk.CTkFrame(self, fg_color=config.BG_COLOR, border_width=0)
        self.filter_frame.pack(fill="x", padx=10, pady=5)
        self.filter_entry = ctk.CTkEntry(self.filter_frame, placeholder_text="Filter messages...", font=config.DEFAULT_FONT)
        self.filter_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.filter_entry.bind("<KeyRelease>", lambda e: self.on_filter_change())

        # ----- Top Frame (Port, Baud, Refresh, Connect) -----
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
        # Configure grid columns so that long port strings don’t push out controls.
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

        # ----- Input Frame: Message Input, Send Button, Auto \r\n -----
        self.input_frame = ctk.CTkFrame(self, fg_color=config.BG_COLOR, border_width=0)
        self.input_frame.pack(fill="x", padx=10, pady=5)
        self.message_input = ctk.CTkEntry(self.input_frame, placeholder_text="Type a message...", font=config.DEFAULT_FONT)
        self.message_input.pack(side="left", fill="x", expand=True, padx=5)
        self.message_input.bind("<Return>", lambda event: self.send_message())
        self.send_button = ctk.CTkButton(self.input_frame, text="Send", width=80,
                                         command=self.send_message,
                                         fg_color=config.BUTTON_STYLES["green"][0],
                                         hover_color=config.BUTTON_STYLES["green"][1],
                                         font=config.DEFAULT_FONT)
        self.send_button.pack(side="left", padx=5)
        # Auto \r\n checkbox placed next to the Send button
        self.auto_terminate = ctk.CTkCheckBox(self.input_frame, text="Auto \\r\\n",
                                              font=config.DEFAULT_FONT, text_color="white",
                                              fg_color=config.BG_COLOR)
        self.auto_terminate.select()  # default ON
        self.auto_terminate.pack(side="left", padx=5)

        # ----- Bottom Frame: Additional Controls (Grid-based) -----
        self.bottom_frame = ctk.CTkFrame(self, fg_color=config.BG_COLOR, border_width=0)
        self.bottom_frame.pack(fill="x", padx=10, pady=5)
        # Configure grid: Row 0 for Clear, Save, Timestamp, Hex mode, Pause
        for col in range(5):
            self.bottom_frame.grid_columnconfigure(col, weight=1)
        self.clear_button = ctk.CTkButton(self.bottom_frame, text="Clear Terminal", width=120,
                                          command=self.clear_terminal,
                                          fg_color=config.BUTTON_STYLES["green"][0],
                                          hover_color=config.BUTTON_STYLES["green"][1],
                                          font=config.DEFAULT_FONT)
        self.clear_button.grid(row=0, column=0, padx=5, pady=2, sticky="ew")
        self.save_button = ctk.CTkButton(self.bottom_frame, text="Save Log", width=120,
                                         command=self.handle_save_log,
                                         fg_color=config.BUTTON_STYLES["blue"][0],
                                         hover_color=config.BUTTON_STYLES["blue"][1],
                                         font=config.DEFAULT_FONT)
        self.save_button.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.timestamp_checkbox = ctk.CTkCheckBox(self.bottom_frame, text="Timestamp",
                                                  font=config.DEFAULT_FONT, text_color="white",
                                                  fg_color=config.BG_COLOR)
        self.timestamp_checkbox.select()
        self.timestamp_checkbox.grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.hex_checkbox = ctk.CTkCheckBox(self.bottom_frame, text="Hex mode",
                                            font=config.DEFAULT_FONT, text_color="white",
                                            fg_color=config.BG_COLOR)
        self.hex_checkbox.grid(row=0, column=3, padx=5, pady=2, sticky="w")
        self.pause_button = ctk.CTkButton(self.bottom_frame, text="Pause", width=100,
                                          command=self.toggle_pause,
                                          fg_color=config.BUTTON_STYLES["green"][0],
                                          hover_color=config.BUTTON_STYLES["green"][1],
                                          font=config.DEFAULT_FONT)
        self.pause_button.grid(row=0, column=4, padx=5, pady=2, sticky="ew")
        # Row 1: Visualization controls: Keyword entry (span 4) and Visualize button
        self.bottom_frame.grid_columnconfigure(4, weight=1)
        self.vis_keyword_entry = ctk.CTkEntry(self.bottom_frame, placeholder_text="Visualization keyword",
                                               font=config.DEFAULT_FONT)
        self.vis_keyword_entry.grid(row=1, column=0, columnspan=4, padx=5, pady=2, sticky="ew")
        self.vis_button = ctk.CTkButton(self.bottom_frame, text="Visualize", width=100,
                                        command=self.start_visualization,
                                        fg_color=config.BUTTON_STYLES["blue"][0],
                                        hover_color=config.BUTTON_STYLES["blue"][1],
                                        font=config.DEFAULT_FONT)
        self.vis_button.grid(row=1, column=4, padx=5, pady=2, sticky="ew")

        # Initial port refresh
        self.refresh_ports()

    # --------------- UTILITY & CALLBACK METHODS ---------------

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2 - 50
        self.geometry(f"{width}x{height}+{x}+{y}")

    def truncate_text(self, text, max_length=config.TRUNCATE_LENGTH):
        if len(text) > max_length:
            return text[:max_length-3] + "..."
        return text

    def on_port_selected(self, selection):
        self.selected_port_full = selection
        self.port_combo.set(self.truncate_text(selection))

    def on_filter_change(self):
        self.filter_text = self.filter_entry.get()
        self.update_terminal_display()

    def update_terminal_display(self):
        if not self.paused:
            self.terminal.config(state="normal")
            self.terminal.delete("1.0", tk.END)
            for msg in self.all_messages:
                if self.filter_text == "" or self.filter_text.lower() in msg.lower():
                    self.terminal.insert(tk.END, msg + "\n")
            self.terminal.config(state="disabled")
            self.terminal.see(tk.END)

    def append_text(self, text):
        # Optionally prepend timestamp
        if self.timestamp_checkbox.get():
            text = timestamping.prepend_timestamp(text)
        # Optionally convert to hex
        if self.hex_checkbox.get():
            text = data_converter.to_hex(text)

        self.all_messages.append(text)
        # Send to visualizer if active
        if self.visualizer:
            self.visualizer.add_data(text)
        if not self.paused:
            self.update_terminal_display()
        else:
            self.scroll_buffer.append(text)

    def insert_plain_text(self, text):
        self.terminal.config(state="normal")
        self.terminal.insert(tk.END, text)
        self.terminal.see(tk.END)
        self.terminal.config(state="disabled")

    def clear_terminal(self):
        self.terminal.config(state="normal")
        self.terminal.delete("1.0", tk.END)
        self.terminal.config(state="disabled")
        self.all_messages = []

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
            self.connect_button.configure(text="Disconnect",
                                          fg_color=config.BUTTON_STYLES["red"][0],
                                          hover_color=config.BUTTON_STYLES["red"][1])
            self.port_combo.configure(state="disabled")
            self.baud_combo.configure(state="disabled")

    def disconnect_serial(self):
        if self.serial_comm:
            self.serial_comm.disconnect()
        self.connect_button.configure(text="Connect",
                                      fg_color=config.BUTTON_STYLES["green"][0],
                                      hover_color=config.BUTTON_STYLES["green"][1])
        self.port_combo.configure(state="normal")
        self.baud_combo.configure(state="normal")

    def send_message(self):
        if self.serial_comm and self.serial_comm.serial_port and self.serial_comm.serial_port.is_open:
            message = self.message_input.get()
            # Append \r\n if auto-terminate is enabled
            if self.auto_terminate.get():
                message += "\r\n"
            self.serial_comm.send_message(message)
            self.message_input.delete(0, tk.END)

    def handle_save_log(self):
        filename = filedialog.asksaveasfilename(
            title="Save Log",
            filetypes=[("Text File", "*.txt")]
        )
        if filename:
            log_text = self.terminal.get("1.0", tk.END)
            save_log(log_text, filename)
            self.append_text(f"💾 Log saved to {filename}")

    def toggle_pause(self):
        if self.paused:
            self.paused = False
            self.pause_button.configure(text="Pause")
            for msg in self.scroll_buffer:
                self.all_messages.append(msg)
            self.scroll_buffer = []
            self.update_terminal_display()
        else:
            self.paused = True
            self.pause_button.configure(text="Resume")

    def start_visualization(self):
        keyword = self.vis_keyword_entry.get().strip()
        if keyword:
            self.visualizer = data_visualizer.DataVisualizer(keyword)
        else:
            self.append_text("⚠ Please enter a visualization keyword.")

    def get_button_style(self, color):
        return config.BUTTON_STYLES.get(color, config.BUTTON_STYLES["green"])

    # Placeholder for auto_terminate method if needed
    def auto_terminate(self):
        pass
