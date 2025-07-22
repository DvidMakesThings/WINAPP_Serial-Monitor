import os
import xml.etree.ElementTree as ET
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, simpledialog
import config

class EnhancedCommandManager:
    def __init__(self, xml_path=None):
        # Use the existing commands.xml in the current directory if no path specified
        if xml_path:
            self.xml_path = xml_path
        elif hasattr(config, 'COMMANDS_XML'):
            self.xml_path = config.COMMANDS_XML
        else:
            # Fallback to current directory
            self.xml_path = os.path.join(os.getcwd(), "commands.xml")
        
        self.commands = {}  # name -> {'cmd':…, 'terminator':…, 'category':…, 'description':…}
        self.categories = set()
        
        # ensure file exists
        if not os.path.exists(self.xml_path):
            self._write_empty()
        
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
        self.categories.clear()
        
        for elem in root.findall("command"):
            name = elem.get("name")
            cmd = elem.findtext("cmd", default="")
            term = elem.findtext("terminator", default="")
            category = elem.findtext("category", default="General")
            description = elem.findtext("description", default="")
            
            self.commands[name] = {
                "cmd": cmd, 
                "terminator": term,
                "category": category,
                "description": description
            }
            self.categories.add(category)
    
    def add(self, name, cmd, terminator, category="General", description=""):
        """Add or overwrite a command and persist to disk."""
        self.commands[name] = {
            "cmd": cmd, 
            "terminator": terminator,
            "category": category,
            "description": description
        }
        self.categories.add(category)
        self._save()
    
    def get(self, name):
        """Retrieve a saved command by name."""
        return self.commands.get(name)
    
    def delete(self, name):
        """Delete a command by name."""
        if name in self.commands:
            del self.commands[name]
            self._save()
            return True
        return False
    
    def get_by_category(self, category):
        """Get all commands in a specific category."""
        return {name: data for name, data in self.commands.items() 
                if data.get("category", "General") == category}
    
    def get_categories(self):
        """Return a list of all categories."""
        return sorted(list(self.categories))
    
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
            
            e_cat = ET.SubElement(c, "category")
            e_cat.text = data.get("category", "General")
            
            e_desc = ET.SubElement(c, "description")
            e_desc.text = data.get("description", "")
        
        tree = ET.ElementTree(root)
        tree.write(self.xml_path, encoding="utf-8", xml_declaration=True)


class CommandManagerWindow:
    def __init__(self, parent, command_manager, on_update_callback=None):
        self.parent = parent
        self.cmd_manager = command_manager
        self.on_update_callback = on_update_callback
        
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Command Manager")
        self.window.geometry("800x600")
        
        # Center the window
        self.center_window()
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()
        self.refresh_command_list()
    
    def center_window(self):
        """Center the window on the parent"""
        self.parent.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - 800) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - 600) // 2
        self.window.geometry(f"800x600+{x}+{y}")
    
    def setup_ui(self):
        """Setup the command manager UI"""
        # Main container
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel - Command list
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Category filter
        filter_frame = ctk.CTkFrame(left_frame)
        filter_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(filter_frame, text="Category:").pack(side="left", padx=5)
        categories = ["All"] + self.cmd_manager.get_categories()
        self.category_var = ctk.StringVar(value="All")
        self.category_combo = ctk.CTkOptionMenu(
            filter_frame, values=categories, variable=self.category_var,
            command=self.on_category_changed
        )
        self.category_combo.pack(side="left", padx=5, fill="x", expand=True)
        
        # Search
        search_frame = ctk.CTkFrame(left_frame)
        search_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        ctk.CTkLabel(search_frame, text="Search:").pack(side="left", padx=5)
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self.on_search_changed)
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var)
        search_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # Command list
        list_frame = ctk.CTkFrame(left_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Create treeview for commands
        import tkinter.ttk as ttk
        self.tree = ttk.Treeview(list_frame, columns=("Category", "Description"), show="tree headings")
        self.tree.heading("#0", text="Command Name")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Description", text="Description")
        
        self.tree.column("#0", width=200)
        self.tree.column("Category", width=100)
        self.tree.column("Description", width=200)
        
        # Scrollbars for treeview
        tree_scroll_y = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll_y.pack(side="right", fill="y")
        tree_scroll_x.pack(side="bottom", fill="x")
        
        self.tree.bind("<<TreeviewSelect>>", self.on_command_selected)
        self.tree.bind("<Double-1>", self.on_command_double_click)
        
        # Buttons
        button_frame = ctk.CTkFrame(left_frame)
        button_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkButton(button_frame, text="Add", command=self.add_command).pack(side="left", padx=2)
        ctk.CTkButton(button_frame, text="Edit", command=self.edit_command).pack(side="left", padx=2)
        ctk.CTkButton(button_frame, text="Delete", command=self.delete_command).pack(side="left", padx=2)
        ctk.CTkButton(button_frame, text="Duplicate", command=self.duplicate_command).pack(side="left", padx=2)
        
        # Right panel - Command details
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="right", fill="y", padx=(5, 0))
        right_frame.configure(width=300)
        
        ctk.CTkLabel(right_frame, text="Command Details", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Details display
        self.details_frame = ctk.CTkScrollableFrame(right_frame)
        self.details_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.selected_command = None
        self.show_command_details(None)
    
    def refresh_command_list(self):
        """Refresh the command list display"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get filtered commands
        category_filter = self.category_var.get()
        search_filter = self.search_var.get().lower()
        
        commands = self.cmd_manager.commands
        if category_filter != "All":
            commands = {name: data for name, data in commands.items() 
                       if data.get("category", "General") == category_filter}
        
        if search_filter:
            commands = {name: data for name, data in commands.items() 
                       if search_filter in name.lower() or 
                          search_filter in data.get("description", "").lower()}
        
        # Add commands to tree
        for name, data in sorted(commands.items()):
            self.tree.insert("", "end", text=name, 
                           values=(data.get("category", "General"), 
                                  data.get("description", "")))
    
    def on_category_changed(self, value):
        """Handle category filter change"""
        self.refresh_command_list()
    
    def on_search_changed(self, *args):
        """Handle search filter change"""
        self.refresh_command_list()
    
    def on_command_selected(self, event):
        """Handle command selection"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            command_name = self.tree.item(item, "text")
            self.selected_command = command_name
            self.show_command_details(command_name)
    
    def on_command_double_click(self, event):
        """Handle double-click on command"""
        self.edit_command()
    
    def show_command_details(self, command_name):
        """Show details of selected command"""
        # Clear existing details
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        
        if not command_name or command_name not in self.cmd_manager.commands:
            ctk.CTkLabel(self.details_frame, text="No command selected").pack(pady=20)
            return
        
        cmd_data = self.cmd_manager.commands[command_name]
        
        # Name
        ctk.CTkLabel(self.details_frame, text="Name:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 2))
        ctk.CTkLabel(self.details_frame, text=command_name, wraplength=250).pack(anchor="w", padx=10)
        
        # Category
        ctk.CTkLabel(self.details_frame, text="Category:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 2))
        ctk.CTkLabel(self.details_frame, text=cmd_data.get("category", "General")).pack(anchor="w", padx=10)
        
        # Command
        ctk.CTkLabel(self.details_frame, text="Command:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 2))
        cmd_text = ctk.CTkTextbox(self.details_frame, height=60, wrap="word")
        cmd_text.pack(fill="x", padx=10, pady=2)
        cmd_text.insert("1.0", cmd_data["cmd"])
        cmd_text.configure(state="disabled")
        
        # Terminator
        ctk.CTkLabel(self.details_frame, text="Terminator:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 2))
        term_display = repr(cmd_data["terminator"]) if cmd_data["terminator"] else "None"
        ctk.CTkLabel(self.details_frame, text=term_display).pack(anchor="w", padx=10)
        
        # Description
        ctk.CTkLabel(self.details_frame, text="Description:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 2))
        desc_text = ctk.CTkTextbox(self.details_frame, height=80, wrap="word")
        desc_text.pack(fill="x", padx=10, pady=2)
        desc_text.insert("1.0", cmd_data.get("description", ""))
        desc_text.configure(state="disabled")
    
    def add_command(self):
        """Add a new command"""
        dialog = CommandEditDialog(self.window, self.cmd_manager)
        if dialog.result:
            self.refresh_command_list()
            self.update_categories()
            if self.on_update_callback:
                self.on_update_callback()
    
    def edit_command(self):
        """Edit selected command"""
        if not self.selected_command:
            messagebox.showwarning("No Selection", "Please select a command to edit.")
            return
        
        dialog = CommandEditDialog(self.window, self.cmd_manager, self.selected_command)
        if dialog.result:
            self.refresh_command_list()
            self.update_categories()
            self.show_command_details(self.selected_command)
            if self.on_update_callback:
                self.on_update_callback()
    
    def delete_command(self):
        """Delete selected command"""
        if not self.selected_command:
            messagebox.showwarning("No Selection", "Please select a command to delete.")
            return
        
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete '{self.selected_command}'?"):
            self.cmd_manager.delete(self.selected_command)
            self.refresh_command_list()
            self.update_categories()
            self.show_command_details(None)
            if self.on_update_callback:
                self.on_update_callback()
    
    def duplicate_command(self):
        """Duplicate selected command"""
        if not self.selected_command:
            messagebox.showwarning("No Selection", "Please select a command to duplicate.")
            return
        
        original = self.cmd_manager.get(self.selected_command)
        if original:
            new_name = f"{self.selected_command} (Copy)"
            counter = 1
            while new_name in self.cmd_manager.commands:
                new_name = f"{self.selected_command} (Copy {counter})"
                counter += 1
            
            dialog = CommandEditDialog(self.window, self.cmd_manager, 
                                     command_name=new_name, 
                                     initial_data=original)
            if dialog.result:
                self.refresh_command_list()
                self.update_categories()
                if self.on_update_callback:
                    self.on_update_callback()
    
    def update_categories(self):
        """Update category dropdown"""
        categories = ["All"] + self.cmd_manager.get_categories()
        self.category_combo.configure(values=categories)


class CommandEditDialog:
    def __init__(self, parent, command_manager, command_name=None, initial_data=None):
        self.cmd_manager = command_manager
        self.command_name = command_name
        self.result = None
        
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Add Command" if not command_name else "Edit Command")
        self.window.geometry("600x600")
        
        # Center the window
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 600) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 550) // 2
        self.window.geometry(f"600x600+{x}+{y}")
        
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui(initial_data)
        self.window.wait_window()
    
    def setup_ui(self, initial_data=None):
        """Setup the edit dialog UI"""
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Name
        ctk.CTkLabel(main_frame, text="Command Name:").pack(anchor="w", pady=(0, 5))
        self.name_entry = ctk.CTkEntry(main_frame, width=500)
        self.name_entry.pack(fill="x", pady=(0, 10))
        
        # Category
        ctk.CTkLabel(main_frame, text="Category:").pack(anchor="w", pady=(0, 5))
        categories = self.cmd_manager.get_categories()
        if not categories:
            categories = ["General"]
        self.category_var = ctk.StringVar(value="General")
        category_frame = ctk.CTkFrame(main_frame)
        category_frame.pack(fill="x", pady=(0, 10))
        
        self.category_combo = ctk.CTkOptionMenu(category_frame, values=categories, 
                                              variable=self.category_var)
        self.category_combo.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(category_frame, text="New", width=60, 
                     command=self.add_new_category).pack(side="right")
        
        # Command
        ctk.CTkLabel(main_frame, text="Command:").pack(anchor="w", pady=(0, 5))
        self.command_text = ctk.CTkTextbox(main_frame, height=120)
        self.command_text.pack(fill="x", pady=(0, 10))
        
        # Terminator
        ctk.CTkLabel(main_frame, text="Terminator:").pack(anchor="w", pady=(0, 5))
        term_frame = ctk.CTkFrame(main_frame)
        term_frame.pack(fill="x", pady=(0, 10))
        
        self.auto_term_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(term_frame, text="Auto \\r\\n", 
                       variable=self.auto_term_var).pack(side="left")
        
        ctk.CTkLabel(term_frame, text="Custom:").pack(side="left", padx=(20, 5))
        self.custom_term_entry = ctk.CTkEntry(term_frame, width=100)
        self.custom_term_entry.pack(side="left", padx=(0, 5))
        
        # Description
        ctk.CTkLabel(main_frame, text="Description:").pack(anchor="w", pady=(0, 5))
        self.description_text = ctk.CTkTextbox(main_frame, height=100)
        self.description_text.pack(fill="x", pady=(0, 20))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x")
        
        ctk.CTkButton(button_frame, text="Cancel", 
                     command=self.cancel).pack(side="right", padx=(5, 0))
        ctk.CTkButton(button_frame, text="Save", 
                     command=self.save).pack(side="right")
        
        # Load initial data
        if initial_data:
            self.load_data(initial_data)
        elif self.command_name:
            existing_data = self.cmd_manager.get(self.command_name)
            if existing_data:
                self.load_data(existing_data)
        
        if self.command_name:
            self.name_entry.insert(0, self.command_name)
    
    def load_data(self, data):
        """Load data into the form"""
        self.command_text.insert("1.0", data["cmd"])
        self.description_text.insert("1.0", data.get("description", ""))
        self.category_var.set(data.get("category", "General"))
        
        if data["terminator"] == "\r\n":
            self.auto_term_var.set(True)
        else:
            self.auto_term_var.set(False)
            self.custom_term_entry.insert(0, data["terminator"])
    
    def add_new_category(self):
        """Add a new category"""
        new_category = simpledialog.askstring("New Category", "Enter category name:")
        if new_category and new_category.strip():
            categories = self.cmd_manager.get_categories()
            categories.append(new_category.strip())
            self.category_combo.configure(values=sorted(categories))
            self.category_var.set(new_category.strip())
    
    def save(self):
        """Save the command"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Command name is required.")
            return
        
        command = self.command_text.get("1.0", "end-1c").strip()
        if not command:
            messagebox.showerror("Error", "Command is required.")
            return
        
        # Check for duplicate names (except when editing)
        if name != self.command_name and name in self.cmd_manager.commands:
            messagebox.showerror("Error", "A command with this name already exists.")
            return
        
        category = self.category_var.get()
        description = self.description_text.get("1.0", "end-1c").strip()
        
        if self.auto_term_var.get():
            terminator = "\r\n"
        else:
            terminator = self.custom_term_entry.get()
        
        # If editing and name changed, delete old command
        if self.command_name and self.command_name != name:
            self.cmd_manager.delete(self.command_name)
        
        self.cmd_manager.add(name, command, terminator, category, description)
        self.result = True
        self.window.destroy()
    
    def cancel(self):
        """Cancel the dialog"""
        self.result = False
        self.window.destroy()