import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, Any

from rekvia.config.settings import load_settings, save_settings

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.title("Configuration Settings")
        self.geometry("700x600")
        self.resizable(False, False)
        
        # Bring to front
        self.transient(master)
        self.grab_set()

        self.current_settings = load_settings()
        self.entries = {}
        
        self.create_widgets()

    def create_widgets(self):
        # Title
        self.lbl_title = ctk.CTkLabel(self, text="Manage Column Aliases", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_title.pack(pady=(15, 5))
        
        # Scrollable Frame
        self.scroll = ctk.CTkScrollableFrame(self, width=650, height=450)
        self.scroll.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Default Tolerance
        self.create_tolerance_section()

        # Book Aliases
        self.create_alias_section("📘 Purchase Register Column Aliases", "BOOK_COLUMN_ALIASES")
        
        # 2B Aliases
        self.create_alias_section("📙 GSTR-2B Column Aliases", "GSTR2B_COLUMN_ALIASES")
        
        # Save Button
        self.btn_save = ctk.CTkButton(self, text="Save & Apply", fg_color="#007bff", hover_color="#0056b3",
                                      font=ctk.CTkFont(size=14, weight="bold"), height=40, command=self.save_all)
        self.btn_save.pack(pady=10, padx=20, fill="x")

    def create_tolerance_section(self):
        lbl = ctk.CTkLabel(self.scroll, text="Engine Parameters", font=ctk.CTkFont(size=14, weight="bold"), text_color="#28a745")
        lbl.pack(anchor="w", pady=(10, 5))
        
        frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        frame.pack(fill="x", pady=2)
        
        lbl_field = ctk.CTkLabel(frame, text="Tolerance (₹):", width=120, anchor="w")
        lbl_field.pack(side="left")
        
        entry = ctk.CTkEntry(frame, width=100)
        entry.pack(side="left", fill="x", padx=10, expand=True)
        
        val = self.current_settings.get("TOLERANCE", 2.0)
        entry.insert(0, str(val))
        self.entries["TOLERANCE"] = entry

    def create_alias_section(self, title: str, dict_key: str):
        lbl = ctk.CTkLabel(self.scroll, text=title, font=ctk.CTkFont(size=14, weight="bold"), text_color="#17a2b8")
        lbl.pack(anchor="w", pady=(20, 10))

        data = self.current_settings.get(dict_key, {})
        self.entries[dict_key] = {}
        
        for k, lst in data.items():
            frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
            frame.pack(fill="x", pady=2)
            
            lbl_field = ctk.CTkLabel(frame, text=k.replace("_", " ").title() + ":", width=120, anchor="w")
            lbl_field.pack(side="left")
            
            entry = ctk.CTkEntry(frame)
            entry.pack(side="left", fill="x", padx=10, expand=True)
            
            current_val = ", ".join(lst)
            entry.insert(0, current_val)
            
            self.entries[dict_key][k] = entry

    def save_all(self):
        # Extract tolerance
        tol_str = self.entries["TOLERANCE"].get()
        try:
            self.current_settings["TOLERANCE"] = float(tol_str)
        except ValueError:
            messagebox.showerror("Invalid Input", "Tolerance must be a valid number.")
            return

        # Extract dicts
        for key_type in ["BOOK_COLUMN_ALIASES", "GSTR2B_COLUMN_ALIASES"]:
            for k, entry in self.entries[key_type].items():
                raw_str = entry.get()
                parsed_list = [item.strip() for item in raw_str.split(",") if item.strip()]
                self.current_settings[key_type][k] = parsed_list
                
        # Save to JSON
        try:
            save_settings(self.current_settings)
            messagebox.showinfo("Success", "Settings saved successfully! They will apply to the next execution.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
