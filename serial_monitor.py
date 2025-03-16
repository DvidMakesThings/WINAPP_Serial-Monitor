import sys
from PyQt6.QtWidgets import QApplication
from gui import SerialMonitorGUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SerialMonitorGUI()
    window.show()
    sys.exit(app.exec())
