# Serial Monitor Application

A comprehensive Python-based serial communication tool with advanced data visualization, command management, and data processing capabilities.

![Serial Monitor](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)
![License](https://img.shields.io/badge/License-GPL3-blue.svg)

## Features

### 🔌 Serial Communication
- **Auto-detection** of available serial ports
- **Configurable baud rates** (110 to 1,000,000 bps)
- **Automatic reconnection** on device disconnect
- **Real-time data streaming** with buffering
- **Command history** with up/down arrow navigation

### 📊 Data Visualization
- **Real-time plotting** of structured data
- **Multiple data series** with individual subplots
- **Auto-scaling** with configurable time windows
- **Color-coded series** for easy identification
- **Interactive series selection** (show/hide individual measurements)

### 💾 Data Processing & Export
- **Structured data parsing** with `[DATA]`, `[PLOT]`, and `[MEAS]` tags
- **Multiple export formats**: CSV, JSON, Excel, Text
- **Data filtering** with regex support
- **Statistics calculation** (min, max, average, standard deviation)
- **Configurable buffer sizes** (up to 10,000 points)

### ⚙️ Command Management
- **Save and organize** frequently used commands
- **Command categories** for better organization
- **Custom terminators** (auto \\r\\n or custom)
- **Command descriptions** and metadata
- **Repeat commands** with configurable intervals
- **Import/Export** command libraries

### 🎛️ User Interface
- **Tabbed interface** with Terminal, Data Plot, and Analysis views
- **Dark theme** optimized for long usage sessions
- **Resizable panels** and responsive layout
- **Scroll pause/resume** functionality
- **Enhanced file handling** with multiple format support

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Required Dependencies
```bash
pip install -r requirements.txt
```

The `requirements.txt` includes:
- `pyserial` - Serial communication
- `customtkinter` - Modern UI components
- `matplotlib` - Data plotting
- `pandas` - Data processing
- `openpyxl` - Excel file support
- `numpy` - Numerical operations

### Quick Start
1. Clone or download the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python serial_monitor.py`

## Usage

### Basic Serial Communication
1. **Connect Device**: Select port and baud rate, click "Connect"
2. **Send Messages**: Type in the message box and press Enter or click "Send"
3. **View Data**: All received data appears in the terminal with timestamps

### Data Visualization
The application automatically detects and plots structured data with these tags:

```
[PLOT] voltage: 3.3
[PLOT] temperature: 25.6
[PLOT] current: 0.125
[DATA] sensor_id: 12345
[MEAS] pressure: 1013.25
```

- **[PLOT]** data appears in real-time plots
- **[DATA]** data is stored for analysis
- **[MEAS]** data is logged for measurements

### Command Management
1. **Add Commands**: Click "Add Command" to save frequently used commands
2. **Organize**: Use categories to group related commands
3. **Quick Send**: Select from dropdown and click "Send Command"
4. **Repeat**: Enable repeat mode with custom intervals

### Data Export
1. Go to **Analysis** tab
2. Click **Export Data** 
3. Choose data type (Raw, Filtered, Structured, etc.)
4. Select format (CSV, JSON, Excel, Text)
5. Include metadata for comprehensive reports

## Configuration

### File Locations
- **Commands**: Stored in `C:\ProgramData\SerialMonitor\commands.xml` (Windows)
- **Settings**: Configurable in `config.py`

### Customization
Edit `config.py` to modify:
- Window dimensions and colors
- Buffer sizes and limits
- Button styles and themes
- Default font settings

## Data Format Examples

### Voltage Monitoring
```
[PLOT] voltage_main: 12.6
[PLOT] voltage_backup: 11.8
[DATA] battery_level: 85
[MEAS] load_current: 2.3
```

### Temperature Sensors
```
[PLOT] temp_cpu: 45.2
[PLOT] temp_ambient: 23.1
[DATA] fan_speed: 1200
[MEAS] thermal_resistance: 0.8
```

### Multi-Sensor Data
```
[PLOT] sensor1: 100.5
[PLOT] sensor2: 200.3
[PLOT] sensor3: 150.7
[DATA] timestamp: 1640995200
[MEAS] calibration_offset: 0.05
```

## Advanced Features

### Data Filtering
- Use regex patterns to filter incoming data
- Real-time filtering with pattern matching
- Separate filtered and raw data buffers

### Statistics & Analysis
- Real-time statistics calculation
- Data distribution analysis
- Export capabilities with metadata
- Historical data review

### Plot Customization
- Individual subplots for each measurement
- Configurable time windows (10s to 1 hour)
- Auto-scaling with manual override
- Series selection and color coding

## Troubleshooting

### Common Issues

**Port Access Denied**
- Ensure no other applications are using the serial port
- Run as administrator if necessary (Windows)
- Check device permissions (Linux)

**Data Not Plotting**
- Verify data format matches expected tags: `[PLOT] name: value`
- Check that values are numeric
- Use "Test Tags" button to verify plotting functionality

**High Memory Usage**
- Reduce buffer sizes in `config.py`
- Clear data buffers regularly
- Export and clear old data

**Connection Issues**
- Verify correct baud rate settings
- Check cable connections
- Try different USB ports
- Restart the device

### Debug Mode
Enable debug output by modifying the logging level in the source code for detailed troubleshooting information.

## File Structure

```
serial-monitor/
├── serial_monitor.py          # Main application entry point
├── gui.py                     # Main GUI implementation
├── config.py                  # Configuration settings
├── serial_comm.py             # Serial communication handler
├── data_processor.py          # Data processing and filtering
├── plot_widget.py             # Real-time plotting widget
├── command_manager.py         # Basic command management
├── enhanced_command_manager.py # Advanced command management
├── file_handler.py            # Basic file operations
├── enhanced_file_handler.py   # Advanced file operations
├── scroll_pause.py            # Terminal scroll control
├── requirements.txt           # Python dependencies
├── commands.xml               # Saved commands (auto-generated)
└── README.md                  # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues, questions, or feature requests:
1. Check the troubleshooting section
2. Review existing issues
3. Create a new issue with detailed information

## Version History

- **v1.0.0** - Initial release with basic serial communication
- **v1.1.0** - Added data visualization and plotting
- **v1.2.0** - Enhanced command management and data export
- **v1.3.0** - Added structured data processing and analysis tools

---

**Note**: This application is designed for development, testing, and debugging of serial devices. Always ensure proper electrical safety when working with hardware devices.

## License

This project is licensed under the GPL3 License. See the LICENSE file for details.

## Contact

For questions or feedback:

- Email: s.dvid@hotmail.com
- GitHub: [DvidMakesThings](https://github.com/DvidMakesThings)


