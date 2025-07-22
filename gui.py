import serial.tools.list_ports
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from serial_comm import SerialComm
from enhanced_file_handler import EnhancedFileHandler
import platform
import config  # Import our configuration settings
from scroll_pause import ScrollController
from enhanced_command_manager import EnhancedCommandManager, CommandManagerWindow
from data_processor import DataProcessor
from plot_widget import PlotWidget
import tkinter as tk
from datetime import datetime
import traceback
import sys
import threading
import queue
import time


class ExportDialog:
    def __init__(self, parent, data_processor, file_handler):
        self.data_processor = data_processor
        self.file_handler = file_handler
        
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Export Data")
        self.window.geometry("400x550")
        
        # Center window
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 550) // 2
        self.window.geometry(f"400x550+{x}+{y}")
        
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup export dialog UI"""
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Data type selection
        ctk.CTkLabel(main_frame, text="Data Type:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 5))
        self.data_type_var = ctk.StringVar(value="filtered")
        data_types = [
            ("All Filtered Data", "filtered"), 
            ("Raw Data", "raw"), 
            ("All Structured Data", "structured"),
            ("DATA entries only", "data"), 
            ("PLOT entries only", "plot"), 
            ("MEAS entries only", "meas")
        ]
        
        for text, value in data_types:
            ctk.CTkRadioButton(main_frame, text=text, variable=self.data_type_var, 
                              value=value).pack(anchor="w", padx=10, pady=2)
        
        # Format selection
        ctk.CTkLabel(main_frame, text="Export Format:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(20, 5))
        self.format_var = ctk.StringVar(value="csv")
        formats = [("CSV", "csv"), ("JSON", "json"), ("Excel", "xlsx"), ("Text", "txt")]
        
        for text, value in formats:
            ctk.CTkRadioButton(main_frame, text=text, variable=self.format_var, 
                              value=value).pack(anchor="w", padx=10, pady=2)
        
        # Options
        ctk.CTkLabel(main_frame, text="Options:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(20, 5))
        self.include_metadata_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(main_frame, text="Include metadata", 
                       variable=self.include_metadata_var).pack(anchor="w", padx=10, pady=2)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        
        ctk.CTkButton(button_frame, text="Cancel", 
                     command=self.window.destroy).pack(side="right", padx=(5, 0))
        ctk.CTkButton(button_frame, text="Export", 
                     command=self.export_data).pack(side="right")
    
    def export_data(self):
        """Perform the data export"""
        data_type = self.data_type_var.get()
        format_type = self.format_var.get()
        include_metadata = self.include_metadata_var.get()
        
        if self.file_handler.export_data_advanced(
            self.data_processor, None, format_type, data_type, include_metadata
        ):
            self.window.destroy()


class SerialMonitorGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Set up global exception handler
        self.setup_exception_handler()
        
        # Track all scheduled callbacks for cleanup
        self._after_ids = set()
        self._repeat_id = None
        
        self.title("Serial Monitor")
        # Increase window size for new features
        window_width = config.WINDOW_WIDTH + 400
        window_height = config.WINDOW_HEIGHT + 200
        self.geometry(f"{window_width}x{window_height}")
        self.center_window(window_width, window_height)
        self.configure(bg=config.BG_COLOR)

        self.serial_comm = None
        self.port_map = {}
        self.selected_port_full = ""
        
        # Initialize enhanced components
        self.data_processor = DataProcessor()
        self.file_handler = EnhancedFileHandler()
        
        # Setup data processing callbacks
        self.data_processor.add_data_callback(self.on_new_data)
        self.data_processor.add_plot_callback(self.on_new_plot_data)
        self.data_processor.add_structured_callback(self.on_structured_data)
        
        self.setup_ui()
        
        # Populate ports list
        self.refresh_ports()
        
        # Bind cleanup to window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_exception_handler(self):
        """Set up global exception handler to catch unhandled exceptions"""
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            error_msg = f"Unhandled exception: {exc_type.__name__}: {exc_value}\n"
            error_msg += "".join(traceback.format_tb(exc_traceback))
            
            print(f"ERROR: {error_msg}")
            
            # Try to log to terminal if it exists
            try:
                if hasattr(self, 'terminal'):
                    self.safe_append_text(f"🚨 ERROR: {exc_type.__name__}: {exc_value}\n")
            except:
                pass
        
        sys.excepthook = handle_exception
    
    def safe_append_text(self, text):
        """Safely append text to terminal with error handling"""
        try:
            if hasattr(self, 'scroll_controller') and self.scroll_controller:
                self.scroll_controller.append(text)
            else:
                # Fallback direct append
                self.terminal.config(state="normal")
                self.terminal.insert(tk.END, text)
                self.terminal.see(tk.END)
                self.terminal.config(state="disabled")
        except Exception as e:
            print(f"Error appending to terminal: {e}")
    
    def on_closing(self):
        """Clean up resources before closing"""
        print("Cleaning up application...")
        
        # Stop repeat commands first
        self.stop_repeat()
        
        # Cancel all scheduled after() callbacks
        for after_id in list(self._after_ids):
            try:
                self.after_cancel(after_id)
            except:
                pass
        self._after_ids.clear()
        
        # Clean up plot widget first
        if hasattr(self, 'plot_widget'):
            try:
                self.plot_widget.destroy()
            except:
                pass
        
        # Disconnect serial
        if hasattr(self, 'serial_comm') and self.serial_comm:
            try:
                self.serial_comm.disconnect()
            except:
                pass
        
        # Destroy window
        self.destroy()
    
    def setup_ui(self):
        """Setup the main UI components"""
        # Create main container with notebook for tabs
        self.notebook = ctk.CTkTabview(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Main terminal tab
        self.terminal_tab = self.notebook.add("Terminal")
        self.setup_terminal_tab()
        
        # Data visualization tab
        self.plot_tab = self.notebook.add("Data Plot")
        self.setup_plot_tab()
        
        # Data analysis tab
        self.analysis_tab = self.notebook.add("Analysis")
        self.setup_analysis_tab()
    
    def setup_terminal_tab(self):
        """Setup the main terminal interface"""
        terminal_frame = self.terminal_tab

        # ----- Top Frame: Port & Baud + Connect/Refresh -----
        self.top_frame = ctk.CTkFrame(terminal_frame, fg_color=config.BG_COLOR, border_width=0)
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
        standard_baud_rates = [110,300,600,1200,2400,4800,9600,14400,19200,38400,57600,115200,128000,256000,1000000]
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
        self.middle_frame = ctk.CTkFrame(terminal_frame, fg_color=config.BG_COLOR, border_width=0)
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

        # Bind pause/resume scroll functionality
        self.terminal.bind("<Button-1>", lambda e: self.scroll_controller.pause())
        self.terminal.bind("<KeyPress>", lambda e: self.scroll_controller.pause())
        self.terminal.bind("<Button-3>", lambda e: self.scroll_controller.resume())

        # ----- Bottom Section: 3 Rows -----
        self.bottom_section = ctk.CTkFrame(terminal_frame, fg_color=config.BG_COLOR, border_width=0)
        self.bottom_section.pack(fill="x", padx=10, pady=5)

        # Row 1: Clear, Save, Export, Pause/Resume, Auto-append
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
            row1, text="Save Log", width=100,
            command=self.handle_save_log,
            fg_color=config.BUTTON_STYLES["blue"][0],
            hover_color=config.BUTTON_STYLES["blue"][1],
            font=config.DEFAULT_FONT
        )
        self.save_button.pack(side="left", padx=5)
        
        self.export_button = ctk.CTkButton(
            row1, text="Export Data", width=100,
            command=self.handle_export_data,
            fg_color=config.BUTTON_STYLES["blue"][0],
            hover_color=config.BUTTON_STYLES["blue"][1],
            font=config.DEFAULT_FONT
        )
        self.export_button.pack(side="left", padx=5)
        
        # Pause/Resume scroll button
        self.pause_button = ctk.CTkButton(
            row1, text="Pause Scroll", width=120,
            command=self.toggle_scroll_pause,
            fg_color=config.BUTTON_STYLES["blue"][0],
            hover_color=config.BUTTON_STYLES["blue"][1],
            font=config.DEFAULT_FONT
        )
        self.pause_button.pack(side="left", padx=5)
        
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

        # ---- COMMAND HISTORY ----
        self.command_history = []
        self.history_index = -1
        self.message_input.bind("<Up>", self.on_history_up)
        self.message_input.bind("<Down>", self.on_history_down)

        # Row 3: Command dropdown, Send Command, Add, Manage, Repeat
        row3 = ctk.CTkFrame(self.bottom_section, fg_color=config.BG_COLOR, border_width=0)
        row3.pack(fill="x")
        
        # Enhanced command manager
        self.cmd_manager = EnhancedCommandManager()
        
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
            command=self.open_command_manager,
            fg_color=config.BUTTON_STYLES["blue"][0],
            hover_color=config.BUTTON_STYLES["blue"][1],
            font=config.DEFAULT_FONT
        )
        self.add_cmd_button.pack(side="left", padx=5)
        
        self.manage_cmd_button = ctk.CTkButton(
            row3, text="Manage", width=80,
            command=self.open_command_manager,
            fg_color=config.BUTTON_STYLES["blue"][0],
            hover_color=config.BUTTON_STYLES["blue"][1],
            font=config.DEFAULT_FONT
        )
        self.manage_cmd_button.pack(side="left", padx=5)

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

    def setup_plot_tab(self):
        """Setup the data plotting tab"""
        plot_frame = self.plot_tab
        
        # Create plot widget
        self.plot_widget = PlotWidget(plot_frame)
        self.plot_widget.pack(fill="both", expand=True)
    
    def setup_analysis_tab(self):
        """Setup the data analysis tab"""
        analysis_frame = self.analysis_tab
        
        # Statistics frame
        stats_frame = ctk.CTkFrame(analysis_frame)
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(stats_frame, text="Data Statistics", 
                    font=("Arial", 16, "bold")).pack(pady=10)
        
        self.stats_text = ctk.CTkTextbox(stats_frame, height=150)
        self.stats_text.pack(fill="x", padx=10, pady=10)
        
        # Control buttons
        button_frame = ctk.CTkFrame(analysis_frame)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            button_frame, text="Refresh Stats",
            command=self.update_statistics,
            fg_color=config.BUTTON_STYLES["green"][0],
            hover_color=config.BUTTON_STYLES["green"][1]
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame, text="Clear Data Buffers",
            command=self.clear_data_buffers,
            fg_color=config.BUTTON_STYLES["red"][0],
            hover_color=config.BUTTON_STYLES["red"][1]
        ).pack(side="left", padx=5)
        
        # Data preview
        preview_frame = ctk.CTkFrame(analysis_frame)
        preview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(preview_frame, text="Recent Data Preview", 
                    font=("Arial", 14, "bold")).pack(pady=5)
        
        self.preview_text = ctk.CTkTextbox(preview_frame, height=200)
        self.preview_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Auto-update statistics
        self.update_statistics()

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

    def on_new_data(self, data_entry):
        """Callback for when new data is processed"""
        try:
            # Update preview in analysis tab
            if hasattr(self, 'update_data_preview'):
                after_id = self.after_idle(self.update_data_preview)
                self._after_ids.add(after_id)
        except Exception as e:
            print(f"Error in on_new_data: {e}")
            traceback.print_exc()
    
    def process_serial_data(self, data, timestamp):
        """Process incoming serial data through the data processor"""
        try:
            if hasattr(self, 'data_processor'):
                # Process the data for filtering, analysis, and plotting
                self.data_processor.process_data(data, timestamp)
        except Exception as e:
            print(f"Data processing error: {e}")
            traceback.print_exc()
    
    def on_new_plot_data(self, timestamp, value, name="default"):
        """Callback for when new numeric data is available for plotting"""
        try:
            if hasattr(self, 'plot_widget') and not getattr(self.plot_widget, 'destroyed', False):
                self.plot_widget.add_data_point(timestamp, value, name)
        except Exception as e:
            print(f"Error in on_new_plot_data: {e}")
            traceback.print_exc()
    
    def on_structured_data(self, data_type, name, value, timestamp):
        """Callback for structured data updates"""
        try:
            # Update the analysis tab with structured data info
            if hasattr(self, 'update_structured_preview'):
                after_id = self.after_idle(self.update_structured_preview)
                self._after_ids.add(after_id)
        except Exception as e:
            print(f"Error in on_structured_data: {e}")
            traceback.print_exc()
    
    def update_statistics(self):
        """Update the statistics display"""
        try:
            if not hasattr(self, 'stats_text'):
                return
                
            stats = self.data_processor.get_statistics()
            
            stats_text = "Data Processing Statistics:\n"
            stats_text += "=" * 30 + "\n\n"
            
            # Add available measurement names
            available_names = self.data_processor.get_available_names()
            if available_names:
                stats_text += f"Available Measurements:\n"
                for name in available_names:
                    data_count = len(self.data_processor.get_data_by_name(name, 'DATA'))
                    plot_count = len(self.data_processor.get_data_by_name(name, 'PLOT'))
                    meas_count = len(self.data_processor.get_data_by_name(name, 'MEAS'))
                    stats_text += f"  {name}: DATA={data_count}, PLOT={plot_count}, MEAS={meas_count}\n"
                stats_text += "\n"
            
            for key, value in stats.items():
                if isinstance(value, float):
                    stats_text += f"{key.replace('_', ' ').title()}: {value:.2f}\n"
                else:
                    stats_text += f"{key.replace('_', ' ').title()}: {value}\n"
            
            stats_text += f"\nLast Updated: {datetime.now().strftime('%H:%M:%S')}"
            
            if hasattr(self, 'stats_text') and self.stats_text:
                self.stats_text.delete("1.0", tk.END)
                self.stats_text.insert("1.0", stats_text)
        except Exception as e:
            print(f"Error updating statistics: {e}")
            traceback.print_exc()
    
    def update_data_preview(self):
        """Update the data preview display"""
        if not hasattr(self, 'preview_text'):
            return
            
        recent_data = self.data_processor.get_recent_structured_data(count=20)
        
        preview_text = "Recent Structured Data (Last 20 entries):\n"
        preview_text += "=" * 40 + "\n\n"
        
        if recent_data:
            for entry in recent_data[-10:]:  # Show last 10
                timestamp = entry['timestamp'].strftime('%H:%M:%S.%f')[:-3]
                preview_text += f"[{timestamp}] [{entry['type']}] {entry['name']}: {entry['value']}\n"
        else:
            preview_text += "No structured data received yet.\n"
            preview_text += "\nExpected format:\n"
            preview_text += "[DATA] name: value\n"
            preview_text += "[PLOT] name: value\n"
            preview_text += "[MEAS] name: value\n"
        
        try:
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", preview_text)
        except:
            pass  # Widget might be destroyed
    
    def update_structured_preview(self):
        """Update the structured data preview display"""
        if not hasattr(self, 'preview_text'):
            return
            
        recent_data = self.data_processor.get_recent_structured_data(count=20)
        
        preview_text = "Recent Structured Data (Last 20 entries):\n"
        preview_text += "=" * 40 + "\n\n"
        
        # Show available measurement names
        available_names = self.data_processor.get_available_names()
        if available_names:
            preview_text += f"Available measurements: {', '.join(available_names)}\n\n"
        
        if recent_data:
            for entry in recent_data[-10:]:  # Show last 10
                timestamp = entry['timestamp'].strftime('%H:%M:%S.%f')[:-3]
                preview_text += f"[{timestamp}] [{entry['type']}] {entry['name']}: {entry['value']}\n"
        else:
            preview_text += "No structured data received yet.\n"
            preview_text += "\nExpected format:\n"
            preview_text += "[DATA] temperature: 25.6\n"
            preview_text += "[PLOT] voltage: 3.3\n"
            preview_text += "[MEAS] current: 0.125\n"
        
        try:
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", preview_text)
        except:
            pass  # Widget might be destroyed
    
    def clear_terminal(self):
        """Clear the terminal display"""
        try:
            self.terminal.config(state="normal")
            self.terminal.delete("1.0", tk.END)
            self.terminal.config(state="disabled")
        except Exception as e:
            print(f"Error clearing terminal: {e}")
    
    def clear_data_buffers(self):
        """Clear all data processing buffers"""
        self.data_processor.clear_buffers()
        if hasattr(self, 'plot_widget') and not getattr(self.plot_widget, 'destroyed', False):
            self.plot_widget.clear_plot()
        self.update_statistics()
        self.update_data_preview()
        self.append_text("🗑️ Data buffers cleared\n")
    
    def append_text(self, text):
        """Append text to terminal"""
        try:
            if hasattr(self, 'scroll_controller') and self.scroll_controller:
                self.scroll_controller.append(text)
            else:
                # Fallback direct append
                self.terminal.config(state="normal")
                self.terminal.insert(tk.END, text)
                self.terminal.see(tk.END)
                self.terminal.config(state="disabled")
        except Exception as e:
            print(f"Error in append_text: {e}")
            traceback.print_exc()

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

    def handle_export_data(self):
        """Handle advanced data export"""
        export_window = ExportDialog(self, self.data_processor, self.file_handler)

    def toggle_scroll_pause(self):
        """Toggle scroll pause/resume"""
        if self.scroll_controller.paused:
            self.scroll_controller.resume()
            self.pause_button.configure(text="Pause Scroll")
        else:
            self.scroll_controller.pause()
            self.pause_button.configure(text="Resume Scroll")

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
        """Enhanced log saving with format options"""
        log_text = self.terminal.get("1.0", tk.END)
        if self.file_handler.save_log(log_text):
            self.append_text("💾 Log saved successfully\n")

    def get_button_style(self, color):
        return config.BUTTON_STYLES.get(color, config.BUTTON_STYLES["green"])

    def open_command_manager(self):
        """Open the enhanced command manager window"""
        CommandManagerWindow(self, self.cmd_manager, self.update_command_dropdown)
    
    def update_command_dropdown(self):
        """Update the command dropdown after changes"""
        names = self.cmd_manager.names()
        if names:
            self.cmd_dropdown.configure(values=names)
            if self.cmd_dropdown.get() not in names:
                self.cmd_dropdown.set(names[0])
            self.send_cmd_button.configure(state="normal")
        else:
            self.cmd_dropdown.configure(values=["No saved commands"])
            self.cmd_dropdown.set("No saved commands")
            self.send_cmd_button.configure(state="disabled")

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
        self._after_ids.add(self._repeat_id)

    def _repeat_send(self):
        if self._repeat_id in self._after_ids:
            self._after_ids.remove(self._repeat_id)
            
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
        self._after_ids.add(self._repeat_id)

    def stop_repeat(self):
        # cancel the after() loop
        if hasattr(self, "_repeat_id") and self._repeat_id:
            try:
                self.after_cancel(self._repeat_id)
                if self._repeat_id in self._after_ids:
                    self._after_ids.remove(self._repeat_id)
            except:
                pass
            self._repeat_id = None
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