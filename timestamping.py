from datetime import datetime

def prepend_timestamp(message):
    """
    Returns the message string with a timestamp prepended.
    Timestamp format: YYYY-MM-DD HH:MM:SS
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{timestamp}] {message}"
