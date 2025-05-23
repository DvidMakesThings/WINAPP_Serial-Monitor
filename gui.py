import serial.tools.list_ports
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from serial_comm import SerialComm
from file_handler import save_log
import platform
import config  # Import our configuration settings
from scroll_pause import ScrollController
from command_manager import CommandManager
import tkinter as tk


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

        # ----- Top Frame: Port & Baud + Connect/Refresh -----
        self.top_frame = ctk.CTkFrame(self, fg_color=config.BG_COLOR, border_width=0)
        self.top_frame.pack(fill="x", padx=10, pady=5)
        for col in range(5):
            self.top_frame.grid_columnconfigure(col, weight=0)
        self.top_frame.grid_columnconfigure(5, weight=1)

        ctk.CTkLabel(self.top_frame, text="Port:", fg_color=config.BG_COLOR,
                     text_color="white", font=config.DEFAULT_FONT) \
            .grid(row=0, column=0, padx=(0,5), pady=2, sticky="w")
        self.port_combo = ctk.CTkOptionMenu(
            self.top_frame, values=[], width=180, font=config.DEFAULT_FONT,
            command=self.on_port_selected
        )
        self.port_combo.grid(row=0, column=1, padx=(0,15), pady=2, sticky="w")

        ctk.CTkLabel(self.top_frame, text="Baud:", fg_color=config.BG_COLOR,
                     text_color="white", font=config.DEFAULT_FONT) \
            .grid(row=0, column=3, padx=(0,5), pady=2, sticky="w")
        standard_baud_rates = [110,300,600,1200,2400,4800,9600,14400,19200,38400,57600,115200,128000,256000]
        self.baud_combo = ctk.CTkOptionMenu(
            self.top_frame, values=[str(b) for b in standard_baud_rates],
            width=100, font=config.DEFAULT_FONT
        )
        self.baud_combo.set("115200")
        self.baud_combo.grid(row=0, column=4, padx=(0,5), pady=2, sticky="w")

        self.refresh_button = ctk.CTkButton(
            self.top_frame, text="Refresh Ports", width=180,
            command=self.refresh_ports,
            fg_color=config.BUTTON_STYLES["green"][0],
            hover_color=config.BUTTON_STYLES["green"][1],
            font=config.DEFAULT_FONT
        )
        self.refresh_button.grid(row=1, column=1, padx=(0,5), pady=2, sticky="w")

        self.connect_button = ctk.CTkButton(
            self.top_frame, text="Connect", width=100,
            command=self.toggle_connection,
            fg_color=config.BUTTON_STYLES["green"][0],
            hover_color=config.BUTTON_STYLES["green"][1],
            font=config.DEFAULT_FONT
        )
        self.connect_button.grid(row=1, column=4, padx=(0,5), pady=2, sticky="w")

        ctk.CTkLabel(self.top_frame, text="", fg_color=config.BG_COLOR) \
            .grid(row=0, column=5, rowspan=2, sticky="nsew")

        # ----- Middle Frame: Terminal -----
        self.middle_frame = ctk.CTkFrame(self, fg_color=config.BG_COLOR, border_width=0)
        self.middle_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.middle_frame.grid_columnconfigure(0, weight=1)
        self.middle_frame.grid_rowconfigure(0, weight=1)

        self.terminal = tk.Text(
            self.middle_frame,
            bg=config.TERMINAL_BG,
            fg=config.TERMINAL_FG,
            font=("Courier", 10),
            state="disabled",
            bd=0,
            highlightthickness=0,
            wrap="none"
        )
        self.terminal.grid(row=0, column=0, sticky="nsew")
        v_scroll = tk.Scrollbar(self.middle_frame, orient="vertical", command=self.terminal.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll = tk.Scrollbar(self.middle_frame, orient="horizontal", command=self.terminal.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")

        self.terminal.config(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.scroll_controller = ScrollController(self.terminal)
        self.terminal.append = self.scroll_controller.append
        self.terminal.insertPlainText = self.scroll_controller.append
        self._partial_line = ""

        # ----- Bottom Section: 3 Rows -----
        self.bottom_section = ctk.CTkFrame(self, fg_color=config.BG_COLOR, border_width=0)
        self.bottom_section.pack(fill="x", padx=10, pady=5)

        # Row 1: Clear, Save, Auto-append
        row1 = ctk.CTkFrame(self.bottom_section, fg_color=config.BG_COLOR, border_width=0)
        row1.pack(fill="x", pady=(0,5))
        self.clear_button = ctk.CTkButton(
            row1, text="Clear Terminal", width=120,
            command=self.clear_terminal,
            fg_color=config.BUTTON_STYLES["green"][0],
            hover_color=config.BUTTON_STYLES["green"][1],
            font=config.DEFAULT_FONT
        )
        self.clear_button.pack(side="left", padx=5)
        self.save_button = ctk.CTkButton(
            row1, text="Save Log", width=120,
            command=self.handle_save_log,
            fg_color=config.BUTTON_STYLES["blue"][0],
            hover_color=config.BUTTON_STYLES["blue"][1],
            font=config.DEFAULT_FONT
        )
        self.save_button.pack(side="left", padx=5)
        self.auto_terminate = ctk.CTkCheckBox(
            row1, text="Auto append \\r\\n",
            font=config.DEFAULT_FONT,
            text_color="white", fg_color=config.BG_COLOR
        )
        self.auto_terminate.select()
        self.auto_terminate.pack(side="left", padx=5)

        # Row 2: Message entry + Send
        row2 = ctk.CTkFrame(self.bottom_section, fg_color=config.BG_COLOR, border_width=0)
        row2.pack(fill="x", pady=(0,5))
        self.message_input = ctk.CTkEntry(
            row2, placeholder_text="Type a message.",
            font=config.DEFAULT_FONT
        )
        self.message_input.pack(side="left", fill="x", expand=True, padx=5)
        self.message_input.bind("<Return>", lambda e: self.send_message())
        self.send_button = ctk.CTkButton(
            row2, text="Send", width=80,
            command=self.send_message,
            fg_color=config.BUTTON_STYLES["green"][0],
            hover_color=config.BUTTON_STYLES["green"][1],
            font=config.DEFAULT_FONT
        )
        self.send_button.pack(side="left", padx=5)

        # ---- COMMAND HISTORY (fix) ----
        self.command_history = []
        self.history_index = -1
        self.message_input.bind("<Up>", self.on_history_up)
        self.message_input.bind("<Down>", self.on_history_down)

        # Row 3: Command dropdown, Send Command, Add, Repeat
        row3 = ctk.CTkFrame(self.bottom_section, fg_color=config.BG_COLOR, border_width=0)
        row3.pack(fill="x")
        self.cmd_manager = CommandManager()
        names = self.cmd_manager.names()
        if names:
            vals, sel, st = names, names[0], "normal"
        else:
            vals, sel, st = ["No saved commands"], "No saved commands", "disabled"

        self.cmd_dropdown = ctk.CTkOptionMenu(
            row3, values=vals, width=200, font=config.DEFAULT_FONT
        )
        self.cmd_dropdown.set(sel)
        self.cmd_dropdown.pack(side="left", padx=5)

        self.send_cmd_button = ctk.CTkButton(
            row3, text="Send Command", width=120,
            command=self.send_command,
            fg_color=config.BUTTON_STYLES["green"][0],
            hover_color=config.BUTTON_STYLES["green"][1],
            font=config.DEFAULT_FONT,
            state=st
        )
        self.send_cmd_button.pack(side="left", padx=5)

        self.add_cmd_button = ctk.CTkButton(
            row3, text="Add Command", width=100,
            command=self.open_add_command_window,
            fg_color=config.BUTTON_STYLES["blue"][0],
            hover_color=config.BUTTON_STYLES["blue"][1],
            font=config.DEFAULT_FONT
        )
        self.add_cmd_button.pack(side="left", padx=5)

        self.repeat_var = tk.BooleanVar(value=False)
        self.repeat_checkbox = ctk.CTkCheckBox(
            row3, text="Repeat", variable=self.repeat_var,
            font=config.DEFAULT_FONT, text_color="white", fg_color=config.BG_COLOR
        )
        self.repeat_checkbox.pack(side="left", padx=(15,5))
        self.interval_entry = ctk.CTkEntry(
            row3, width=80, placeholder_text="Interval ms",
            font=config.DEFAULT_FONT
        )
        self.interval_entry.insert(0, "1000")
        self.interval_entry.pack(side="left", padx=5)
        self.stop_repeat_button = ctk.CTkButton(
            row3, text="Stop Repeat", width=100,
            command=self.stop_repeat,
            fg_color=config.BUTTON_STYLES["red"][0],
            hover_color=config.BUTTON_STYLES["red"][1],
            font=config.DEFAULT_FONT,
            state="disabled"
        )
        self.stop_repeat_button.pack(side="left", padx=5)

        # Populate ports list
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
        """Delegate all single‐line appends to the ScrollController."""
        self.scroll_controller.append(text)

    def insert_plain_text(self, text):
        """
        Reassemble arbitrary serial chunks so that *only* real '\n'
        (sent by the device) break lines. We split *keeping* the '\n'
        and feed them verbatim into append().
        """
        data = self._partial_line + text
        segments = data.splitlines(keepends=True)
        self._partial_line = ""

        for seg in segments:
            if seg.endswith("\n"):
                # seg includes the '\n' exactly where the device sent it
                self.scroll_controller.append(seg)
            else:
                # no newline yet—stash for next time
                self._partial_line += seg


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
        if not (self.serial_comm and self.serial_comm.serial_port and self.serial_comm.serial_port.is_open):
            return

        # 1) Determine text to send
        raw = self.message_input.get().strip()
        if not raw:
            sel = self.cmd_dropdown.get()
            data = self.cmd_manager.get(sel)
            if data:
                raw = data["cmd"] + data["terminator"]
        if not raw:
            return

        # 2) History
        if raw:
            self.command_history.append(raw)
        self.history_index = -1

        # 3) Send
        self.serial_comm.send_message(raw + ("" if raw.endswith("\n") else "\r\n"))
        self.message_input.delete(0, tk.END)

        # 4) If repeat requested, start it
        if self.repeat_var.get():
            self.start_repeat()

    def on_history_up(self, event):
        """Show previous command."""
        if not self.command_history:
            return "break"
        # if first time, point to last
        if self.history_index == -1:
            self.history_index = len(self.command_history) - 1
        elif self.history_index > 0:
            self.history_index -= 1

        cmd = self.command_history[self.history_index]
        self.message_input.delete(0, tk.END)
        self.message_input.insert(0, cmd)
        return "break"      # stop Tk from beeping

    def on_history_down(self, event):
        """Show next command (or clear if at newest)."""
        if not self.command_history:
            return "break"
        # move forward, or clear at end
        if 0 <= self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            cmd = self.command_history[self.history_index]
        else:
            self.history_index = -1
            cmd = ""

        self.message_input.delete(0, tk.END)
        self.message_input.insert(0, cmd)
        return "break"

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

    def open_add_command_window(self):
        win = ctk.CTkToplevel(self)
        win.title("Add Command")
        win_width, win_height = 300, 180
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - win_width) // 2
        y = self.winfo_y() + (self.winfo_height() - win_height) // 2
        win.geometry(f"{win_width}x{win_height}+{x}+{y}")
        win.transient(self)
        win.grab_set()

        # --- Fields ---
        ctk.CTkLabel(win, text="Name:", font=config.DEFAULT_FONT) \
            .grid(row=0, column=0, padx=5, pady=5, sticky="e")
        name_e = ctk.CTkEntry(win, font=config.DEFAULT_FONT)
        name_e.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(win, text="Command:", font=config.DEFAULT_FONT) \
            .grid(row=1, column=0, padx=5, pady=5, sticky="e")
        cmd_e = ctk.CTkEntry(win, font=config.DEFAULT_FONT)
        cmd_e.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        term_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            win, text="Append \\r\\n", variable=term_var,
            font=config.DEFAULT_FONT
        ).grid(row=2, column=0, columnspan=2, pady=5)

        def _save():
            name = name_e.get().strip()
            cmd  = cmd_e.get()
            term = "\r\n" if term_var.get() else ""
            if name and cmd:
                self.cmd_manager.add(name, cmd, term)
                # update dropdown and enable Send Command
                names = self.cmd_manager.names()
                self.cmd_dropdown.configure(values=names)
                self.cmd_dropdown.set(names[0])
                self.send_cmd_button.configure(state="normal")
                win.destroy()

        ctk.CTkButton(
            win, text="Save", command=_save, font=config.DEFAULT_FONT
        ).grid(row=3, column=0, columnspan=2, pady=10)

    def start_repeat(self):
        # disable the checkbox, enable Stop
        self.repeat_checkbox.configure(state="disabled")
        self.stop_repeat_button.configure(state="normal")
        interval = 1000
        try:
            interval = int(self.interval_entry.get())
        except ValueError:
            pass
        # schedule first send
        self._repeat_id = self.after(interval, self._repeat_send)

    def _repeat_send(self):
        sel = self.cmd_dropdown.get()
        data = self.cmd_manager.get(sel)
        if data and self.serial_comm and self.serial_comm.serial_port.is_open:
            self.serial_comm.send_message(data["cmd"] + data["terminator"])
        # schedule next
        interval = 1000
        try:
            interval = int(self.interval_entry.get())
        except ValueError:
            pass
        self._repeat_id = self.after(interval, self._repeat_send)

    def stop_repeat(self):
        # cancel the after() loop
        if hasattr(self, "_repeat_id"):
            self.after_cancel(self._repeat_id)
            del self._repeat_id
        # re-enable controls
        self.repeat_var.set(False)
        self.repeat_checkbox.configure(state="normal")
        self.stop_repeat_button.configure(state="disabled")

    def send_command(self):
        """Send the selected saved command over serial (if any)."""
        sel = self.cmd_dropdown.get()
        # nothing to do if no commands
        if sel == "No saved commands":
            return

        data = self.cmd_manager.get(sel)
        if not data:
            return

        cmd = data["cmd"] + data["terminator"]
        if self.serial_comm \
        and self.serial_comm.serial_port \
        and self.serial_comm.serial_port.is_open:
            self.serial_comm.send_message(cmd)
