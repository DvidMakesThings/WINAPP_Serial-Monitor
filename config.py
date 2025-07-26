import os
import sys
import shutil

# Window dimensions
WINDOW_WIDTH = 780
WINDOW_HEIGHT = 750

# Fonts
DEFAULT_FONT = ("Helvetica", 12)

BG_COLOR      = "#222"
TERMINAL_BG   = "#111"
TERMINAL_FG   = "#0f0"

TRUNCATE_LENGTH = 50

BUTTON_STYLES = {
    "green": ("#009600", "#006400"),
    "blue":  ("#0064C8", "#004696"),
    "red":   ("#C80000", "#960000")
}


# ─── COMMANDS.XML LOCATION ──────────────────────────────────────────────────
def get_shared_data_path():
    """
    Returns the shared-writable folder:
      C:\\ProgramData\\SerialMonitor
    Creates it if needed.
    """
    base = os.getenv("PROGRAMDATA") or os.getenv("ALLUSERSPROFILE")
    folder = os.path.join(base, "SerialMonitor")
    os.makedirs(folder, exist_ok=True)
    return folder

def get_commands_xml_path():
    """
    Returns the full path to commands.xml in ProgramData, 
    creating an empty file if it doesn't exist yet.
    """
    data_dir = get_shared_data_path()
    xml_path = os.path.join(data_dir, "commands.xml")
    if not os.path.exists(xml_path):
        # touch an empty file
        open(xml_path, "w").close()
    return xml_path

# Used by CommandManager and GUI everywhere
COMMANDS_XML = get_commands_xml_path()


# ─── COMMANDS.XML LOCATION ──────────────────────────────────────────────────
def get_shared_data_path():
    """
    Returns the shared-writable folder:
      C:\\ProgramData\\SerialMonitor
    Creates it if needed.
    """
    base = os.getenv("PROGRAMDATA") or os.getenv("ALLUSERSPROFILE")
    folder = os.path.join(base, "SerialMonitor")
    os.makedirs(folder, exist_ok=True)
    return folder

def get_commands_xml_path():
    """
    Returns the full path to commands.xml in ProgramData, 
    creating an empty file if it doesn't exist yet.
    """
    data_dir = get_shared_data_path()
    xml_path = os.path.join(data_dir, "commands.xml")
    if not os.path.exists(xml_path):
        # touch an empty file
        open(xml_path, "w").close()
    return xml_path

# Used by CommandManager and GUI everywhere
COMMANDS_XML = get_commands_xml_path()