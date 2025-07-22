import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import numpy as np
from collections import deque
from datetime import datetime, timedelta
import threading

class PlotWidget:
    def __init__(self, parent, max_points=1000):
        self.parent = parent
        self.max_points = max_points
        self.destroyed = False
        self.animation = None  # Initialize animation reference
        self.canvas = None
        
        # Data storage - separate for each measurement name
        self.data_series = {}  # name -> {'timestamps': deque, 'values': deque, 'color': str}
        self.available_colors = ['lime', 'cyan', 'yellow', 'magenta', 'orange', 'red', 'blue', 'green']
        self.color_index = 0
        self.lock = threading.Lock()
        
        # Plot settings
        self.auto_scale = True
        self.time_window = 60  # seconds
        self.update_interval = 100  # milliseconds
        self.selected_series = set()  # Which series to display
        
        self.setup_ui()
        self.setup_plot()
        
        # Start animation after everything is set up
        try:
            self.animation = FuncAnimation(
                self.fig, self.update_plot, 
                interval=self.update_interval,
                blit=False,
                cache_frame_data=False,
                repeat=True
            )
            # Keep a reference to prevent garbage collection
            self.canvas.animation = self.animation
        except Exception:
            self.animation = None
        
        # Bind cleanup to widget destruction
        self.frame.bind("<Destroy>", self.on_destroy)
    
    def on_destroy(self, event=None):
        """Clean up when widget is destroyed"""
        if event and event.widget != self.frame:
            return  # Only handle our own destruction
        
        self.destroyed = True
        
        # Stop animation
        if hasattr(self, 'animation') and self.animation is not None:
            try:
                self.animation.event_source.stop()
                self.animation = None
            except:
                pass
        
        # Clear canvas animation reference
        if hasattr(self, 'canvas') and self.canvas:
            try:
                if hasattr(self.canvas, 'animation'):
                    delattr(self.canvas, 'animation')
            except:
                pass
        
        # Close matplotlib figure
        try:
            plt.close(self.fig)
        except:
            pass
    
    def setup_ui(self):
        """Setup the plot widget UI"""
        self.frame = ttk.Frame(self.parent)
        
        # Control frame
        self.control_frame = ttk.Frame(self.frame)
        self.control_frame.pack(fill="x", padx=5, pady=2)
        
        # Auto-scale checkbox
        self.auto_scale_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.control_frame, text="Auto Scale", 
            variable=self.auto_scale_var,
            command=self.on_auto_scale_changed
        ).pack(side="left", padx=5)
        
        # Time window control
        ttk.Label(self.control_frame, text="Time Window (s):").pack(side="left", padx=5)
        self.time_window_var = tk.StringVar(value="60")
        time_spinbox = ttk.Spinbox(
            self.control_frame, from_=10, to=3600, width=8,
            textvariable=self.time_window_var,
            command=self.on_time_window_changed
        )
        time_spinbox.pack(side="left", padx=5)
        
        # Clear button
        ttk.Button(
            self.control_frame, text="Clear Plot",
            command=self.clear_plot
        ).pack(side="left", padx=5)
        
        # Series selection frame
        series_frame = ttk.LabelFrame(self.control_frame, text="Data Series")
        series_frame.pack(side="left", padx=10, fill="x", expand=True)
        
        self.series_listbox = tk.Listbox(series_frame, height=3, selectmode=tk.MULTIPLE)
        self.series_listbox.pack(side="left", fill="x", expand=True)
        self.series_listbox.bind("<<ListboxSelect>>", self.on_series_selection_changed)
        
        series_buttons = ttk.Frame(series_frame)
        series_buttons.pack(side="right", fill="y")
        ttk.Button(series_buttons, text="All", command=self.select_all_series).pack(fill="x")
        ttk.Button(series_buttons, text="None", command=self.select_no_series).pack(fill="x")
        
        # Statistics label
        self.stats_label = ttk.Label(self.control_frame, text="No data")
        self.stats_label.pack(side="right", padx=5)
    
    def setup_plot(self):
        """Setup matplotlib plot"""
        try:
            plt.style.use('dark_background')
        except:
            pass  # Fallback if style not available
        self.fig, self.ax = plt.subplots(figsize=(8, 4), facecolor='#2b2b2b')
        self.ax.set_facecolor('#1e1e1e')
        
        # Configure plot appearance
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlabel('Time', color='white')
        self.ax.set_ylabel('Value', color='white')
        self.ax.tick_params(colors='white')
        
        # Plot lines will be created dynamically
        self.plot_lines = {}  # name -> line object
        
        # Embed plot in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, self.frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # Tight layout
        self.fig.tight_layout()
    
    def add_data_point(self, timestamp, value, name="default"):
        """Add a new data point to a specific data series"""
        if self.destroyed:
            return
        with self.lock:
            # Create series if it doesn't exist
            if name not in self.data_series:
                color = self.available_colors[self.color_index % len(self.available_colors)]
                self.color_index += 1
                self.data_series[name] = {
                    'timestamps': deque(maxlen=self.max_points),
                    'values': deque(maxlen=self.max_points),
                    'color': color
                }
                # Update series listbox
                try:
                    self.series_listbox.insert(tk.END, name)
                    # Auto-select new series
                    self.series_listbox.selection_set(tk.END)
                    self.selected_series.add(name)
                except:
                    pass
            
            # Add data point
            self.data_series[name]['timestamps'].append(timestamp)
            self.data_series[name]['values'].append(value)
    
    def update_plot(self, frame):
        """Update the plot with new data"""
        if self.destroyed:
            return []
            
        with self.lock:
            if not self.data_series:
                return []
            
            # Clear old lines
            for line in self.plot_lines.values():
                line.remove()
            self.plot_lines.clear()
            
            all_times = []
            all_values = []
            
            # Plot each selected series
            for name, series_data in self.data_series.items():
                if name not in self.selected_series:
                    continue
                    
                times = np.array(series_data['timestamps'])
                vals = np.array(series_data['values'])
                
                if len(times) == 0:
                    continue
                
                # Filter data based on time window
                if len(times) > 0:
                    current_time = times[-1]
                    time_threshold = current_time - timedelta(seconds=self.time_window)
                    mask = times >= time_threshold
                    times = times[mask]
                    vals = vals[mask]
                
                if len(times) == 0:
                    continue
                
                # Convert timestamps to relative seconds for plotting
                if len(times) > 1:
                    time_seconds = [(t - times[0]).total_seconds() for t in times]
                else:
                    time_seconds = [0]
                
                # Create plot line
                line, = self.ax.plot(time_seconds, vals, 
                                   color=series_data['color'], 
                                   linewidth=1.5, alpha=0.8, 
                                   label=name)
                self.plot_lines[name] = line
                
                all_times.extend(time_seconds)
                all_values.extend(vals)
            
            # Update axes limits
            if self.auto_scale and len(all_values) > 0:
                if len(all_times) > 0:
                    self.ax.set_xlim(min(all_times), max(all_times))
                y_margin = (max(all_values) - min(all_values)) * 0.1 if len(all_values) > 1 else 1
                self.ax.set_ylim(min(all_values) - y_margin, max(all_values) + y_margin)
            
            # Update legend if multiple series
            if len(self.plot_lines) > 1:
                self.ax.legend(loc='upper right')
            else:
                legend = self.ax.get_legend()
                if legend:
                    legend.remove()
            
            # Update statistics
            self.update_statistics(all_values)
        
        return list(self.plot_lines.values())
    
    def on_series_selection_changed(self, event=None):
        """Handle series selection change"""
        if self.destroyed:
            return
        try:
            selected_indices = self.series_listbox.curselection()
            self.selected_series.clear()
            for i in selected_indices:
                name = self.series_listbox.get(i)
                self.selected_series.add(name)
        except:
            pass
    
    def select_all_series(self):
        """Select all available series"""
        if self.destroyed:
            return
        try:
            self.series_listbox.selection_set(0, tk.END)
            self.selected_series = set(self.data_series.keys())
        except:
            pass
    
    def select_no_series(self):
        """Deselect all series"""
        if self.destroyed:
            return
        try:
            self.series_listbox.selection_clear(0, tk.END)
            self.selected_series.clear()
        except:
            pass
    
    def update_statistics(self, values):
        """Update statistics display"""
        if self.destroyed:
            return
            
        if len(values) > 0:
            stats_text = f"Series: {len(self.selected_series)} | Points: {len(values)} | "
            stats_text += f"Min: {min(values):.2f} | "
            stats_text += f"Max: {max(values):.2f} | "
            stats_text += f"Avg: {np.mean(values):.2f}"
            if len(values) > 1:
                stats_text += f" | Std: {np.std(values):.2f}"
        else:
            stats_text = "No data"
        
        try:
            self.stats_label.config(text=stats_text)
        except:
            pass  # Widget might be destroyed
    
    def on_auto_scale_changed(self):
        """Handle auto-scale checkbox change"""
        if self.destroyed:
            return
        self.auto_scale = self.auto_scale_var.get()
    
    def on_time_window_changed(self):
        """Handle time window change"""
        if self.destroyed:
            return
        try:
            self.time_window = int(self.time_window_var.get())
        except ValueError:
            self.time_window_var.set(str(self.time_window))
    
    def clear_plot(self):
        """Clear all plot data"""
        if self.destroyed:
            return
        with self.lock:
            for series_data in self.data_series.values():
                series_data['timestamps'].clear()
                series_data['values'].clear()
            
            # Clear plot lines
            for line in self.plot_lines.values():
                line.remove()
            self.plot_lines.clear()
            
        try:
            self.stats_label.config(text="No data")
        except:
            pass
    
    def pack(self, **kwargs):
        """Pack the widget frame"""
        if self.destroyed:
            return
        self.frame.pack(**kwargs)
    
    def destroy(self):
        """Clean up resources"""
        self.on_destroy()
        
        self.destroyed = True
        
        # Destroy the frame
        try:
            self.frame.destroy()
        except:
            pass
        
        if hasattr(self, 'animation'):
            try:
                if self.animation:
                    self.animation.event_source.stop()
                    self.animation = None
            except:
                pass
        
        try:
            plt.close(self.fig)
        except:
            pass