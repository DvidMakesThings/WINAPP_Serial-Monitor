def to_hex(text):
    """
    Convert a text string to a hex representation.
    """
    return " ".join(f"{ord(c):02x}" for c in text)

def to_ascii(hex_str):
    """
    Convert a hex string (space separated) back to ASCII.
    """
    try:
        # Remove extra spaces and convert to bytes
        bytes_object = bytes.fromhex("".join(hex_str.split()))
        return bytes_object.decode("utf-8", errors="ignore")
    except Exception:
        return ""
