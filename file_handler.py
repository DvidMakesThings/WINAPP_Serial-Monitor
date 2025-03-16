def save_log(log_text, filename):
    """
    Save the provided log_text to a text file.
    If the filename does not end with ".txt", it appends the extension.
    """
    if not filename.endswith(".txt"):
        filename += ".txt"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(log_text)
