# Serial Monitor - Python (customtkinter)

## Overview

This Serial Monitor is a GUI application built with customtkinter and pySerial for communicating with serial devices. It was born out of frustration with the buggy and unreliable serial monitor in Visual Studio Code, which constantly disconnected, lagged, and failed to display messages correctly.

Tired of dealing with those issues, this custom serial monitor was created to be fast, reliable, and hassle-free. It features an intuitive dark-themed interface, real-time message handling, automatic reconnection, and logging capabilities. Whether you're debugging embedded systems or testing serial communication, this tool ensures a smooth and frustration-free experience.

## Features

- Selectable COM port with device descriptions
- Configurable baud rate (300 to 921600)
- Persistent connection with automatic reconnection
- Message sending with optional line termination (\r\n or \n)
- Terminal with real-time data display and auto-scrolling
- Clear terminal function
- Save log to text (.txt) 
- Modern GUI with hover effects and status indicators

## Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python serial_monitor.py
```

## Usage

1. Select the desired COM port and baud rate.
2. Click "Connect" to establish a connection.
3. View incoming serial data in the terminal.
4. Enter text in the input field and press "Send" or hit Enter to transmit messages.
5. Use the "Clear Terminal" button to remove all displayed messages.
6. Click "Save Log" to store the terminal output in .txt or format.
7. If the device is disconnected, the monitor will attempt to reconnect automatically.
8. Click "Disconnect" to close the connection manually.

## Application Structure

### User Interface

- Built using customtkinter with a dark theme.
- Dropdown selection for available COM ports and baud rate configuration.
- Styled buttons for clear, save, send, and connect/disconnect actions.
- Terminal window displaying incoming messages with auto-scroll.

### Serial Communication

- Uses pySerial to establish and maintain serial connections.
- Reads incoming data continuously in a background thread.
- Sends messages with optional automatic line termination.

### Connection Handling

- Detects device disconnection and starts an immediate reconnection attempt.
- Runs a background thread that continuously retries the connection until successful.

### Logging and Message Handling

- Messages are displayed in real time.
- Terminal logs can be saved in text or Excel format.

## Notes

- The connect button changes color based on connection status (green when disconnected, red when connected).
- Logs are stored in UTF-8 format for text files and use pandas for Excel export.
- The application maintains performance by handling serial operations in background threads.

## License

This project is licensed under the GPL3 License. See the LICENSE file for details.

## Contact

For questions or feedback:

- Email: s.dvid@hotmail.com
- GitHub: [DvidMakesThings](https://github.com/DvidMakesThings)


