import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime
import re

class DataVisualizer:
    def __init__(self, keyword, x_axis="time", y_axis="value"):
        """
        keyword: the string to search for in incoming messages.
        x_axis: label for x-axis (e.g., "Time")
        y_axis: label for y-axis (e.g., "Temperature")
        """
        self.keyword = keyword
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.x_data = []
        self.y_data = []
        
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], 'r-', lw=2)
        self.ax.set_xlabel(self.x_axis)
        self.ax.set_ylabel(self.y_axis)
        self.ax.set_title(f"Real-time Plot for '{self.keyword}'")
        
        # Disable caching frame data to suppress the warning.
        self.ani = animation.FuncAnimation(
            self.fig, self.update_plot, interval=1000, blit=False, cache_frame_data=False
        )
        plt.show(block=False)

    def add_data(self, message):
        """
        Check if the message contains the keyword. If so, extract the first number found
        and add it to the plot data. The x-axis is the current time.
        """
        if self.keyword in message:
            match = re.search(r"([-+]?\d*\.\d+|\d+)", message)
            if match:
                value = float(match.group(0))
                self.x_data.append(datetime.now())
                self.y_data.append(value)

    def update_plot(self, frame):
        self.line.set_data(self.x_data, self.y_data)
        self.ax.relim()
        self.ax.autoscale_view()
        return self.line,
