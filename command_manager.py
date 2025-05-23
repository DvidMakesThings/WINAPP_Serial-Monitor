import os
import xml.etree.ElementTree as ET

class CommandManager:
    def __init__(self, xml_path="commands.xml"):
        self.xml_path = xml_path
        self.commands = {}  # name -> {'cmd':…, 'terminator':…}
        if not os.path.exists(self.xml_path):
            self._write_empty()
        self._load()

    def _write_empty(self):
        root = ET.Element("commands")
        ET.ElementTree(root).write(self.xml_path)

    def _load(self):
        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        for elem in root.findall("command"):
            name = elem.get("name")
            cmd = elem.findtext("cmd", default="")
            term = elem.findtext("terminator", default="")
            self.commands[name] = {"cmd": cmd, "terminator": term}

    def add(self, name, cmd, terminator):
        self.commands[name] = {"cmd": cmd, "terminator": terminator}
        self._save()

    def get(self, name):
        return self.commands.get(name)

    def names(self):
        return list(self.commands.keys())

    def _save(self):
        root = ET.Element("commands")
        for name, data in self.commands.items():
            c = ET.SubElement(root, "command", name=name)
            e_cmd = ET.SubElement(c, "cmd")
            e_cmd.text = data["cmd"]
            e_term = ET.SubElement(c, "terminator")
            e_term.text = data["terminator"]
        ET.ElementTree(root).write(self.xml_path)
