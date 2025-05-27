import os
import xml.etree.ElementTree as ET
import config  # for COMMANDS_XML

class CommandManager:
    def __init__(self, xml_path=None):
        # default to our shared ProgramData XML
        self.xml_path = xml_path or config.COMMANDS_XML
        self.commands = {}  # name -> {'cmd':…, 'terminator':…}

        # ensure file exists (touch if missing)
        if not os.path.exists(self.xml_path):
            self._write_empty()

        # attempt to load; if it fails (empty/malformed), reinitialize
        try:
            self._load()
        except ET.ParseError:
            self._write_empty()
            self._load()

    def _write_empty(self):
        """Create an empty <commands/> file."""
        root = ET.Element("commands")
        tree = ET.ElementTree(root)
        tree.write(self.xml_path, encoding="utf-8", xml_declaration=True)

    def _load(self):
        """Load commands from XML into self.commands."""
        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        self.commands.clear()
        for elem in root.findall("command"):
            name = elem.get("name")
            cmd = elem.findtext("cmd", default="")
            term = elem.findtext("terminator", default="")
            self.commands[name] = {"cmd": cmd, "terminator": term}

    def add(self, name, cmd, terminator):
        """Add or overwrite a command and persist to disk."""
        self.commands[name] = {"cmd": cmd, "terminator": terminator}
        self._save()

    def get(self, name):
        """Retrieve a saved command by name."""
        return self.commands.get(name)

    def names(self):
        """Return a list of all saved command names."""
        return list(self.commands.keys())

    def _save(self):
        """Write out the current self.commands dict to XML."""
        root = ET.Element("commands")
        for name, data in self.commands.items():
            c = ET.SubElement(root, "command", name=name)
            e_cmd = ET.SubElement(c, "cmd")
            e_cmd.text = data["cmd"]
            e_term = ET.SubElement(c, "terminator")
            e_term.text = data["terminator"]
        tree = ET.ElementTree(root)
        tree.write(self.xml_path, encoding="utf-8", xml_declaration=True)
