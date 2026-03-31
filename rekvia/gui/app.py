import os
import threading
import webbrowser
import logging
import customtkinter as ctk
from tkinter import filedialog, messagebox

from rekvia.config.settings import CONTACT_LINKS, APP_VERSION
from rekvia.core.engine import run_logic
from rekvia.gui.settings_window import SettingsWindow
from rekvia.core.updater import check_for_updates

logger = logging.getLogger("rekvia.gui")

ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class GSTApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Rekvia - Reconciliation Engine")
        self.geometry("500x650")
        self.resizable(False, False)

        # Try mapping the runtime Taskbar/Window icon if the user has provided one!
        self.bind_taskbar_icon()

        self.path_books = ctk.StringVar()
        self.path_2b = ctk.StringVar()

        self.create_widgets()

        # Stealth startup check for OTA updates
        self.after(2000, lambda: threading.Thread(target=lambda: check_for_updates(quiet=True, parent_tk_window=self), daemon=True).start())

    def bind_taskbar_icon(self):
        try:
            import sys, os
            if getattr(sys, 'frozen', False):
                # When packaged as an exe via Pyinstaller, it unpacks into a temporary MEIPASS folder
                base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            else:
                # Normal dev environment running top level
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                
            icon_path = os.path.join(base_dir, 'icon.ico')
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            logger.warning(f"Could not load custom application icon: {e}")

    def create_widgets(self):
        # Header Frame
        self.frame_header = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_header.pack(pady=(20, 10), padx=20, fill="x")

        self.lbl_title = ctk.CTkLabel(self.frame_header, text="Rekvia - Automated Reconciliation", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_title.pack(side="left")

        self.btn_settings = ctk.CTkButton(self.frame_header, text="⚙️ Settings", width=40, fg_color="transparent", 
                                          hover_color="#555555", border_width=1, command=self.open_settings)
        self.btn_settings.pack(side="right")

        # Files Frame
        self.frame_files = ctk.CTkFrame(self)
        self.frame_files.pack(pady=10, padx=20, fill="x")

        # Purchase Books
        self.lbl_books = ctk.CTkLabel(self.frame_files, text="Purchase Register (Books):")
        self.lbl_books.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        
        self.entry_books = ctk.CTkEntry(self.frame_files, textvariable=self.path_books, width=320)
        self.entry_books.grid(row=1, column=0, padx=10, pady=(0, 10))
        
        self.btn_books = ctk.CTkButton(self.frame_files, text="Browse", width=80, command=self.browse_books)
        self.btn_books.grid(row=1, column=1, padx=10, pady=(0, 10))

        # GSTR-2B
        self.lbl_2b = ctk.CTkLabel(self.frame_files, text="GSTR-2B File:")
        self.lbl_2b.grid(row=2, column=0, padx=10, pady=(10, 0), sticky="w")
        
        self.entry_2b = ctk.CTkEntry(self.frame_files, textvariable=self.path_2b, width=320)
        self.entry_2b.grid(row=3, column=0, padx=10, pady=(0, 10))
        
        self.btn_2b = ctk.CTkButton(self.frame_files, text="Browse", width=80, command=self.browse_2b)
        self.btn_2b.grid(row=3, column=1, padx=10, pady=(0, 10))

        # Action Button & Progress
        self.btn_run = ctk.CTkButton(self, text="Start Reconciliation", fg_color="#28a745", hover_color="#218838", 
                                     font=ctk.CTkFont(size=14, weight="bold"), height=40, command=self.start_process)
        self.btn_run.pack(pady=15, padx=20, fill="x")

        self.progress_bar = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress_bar.pack(pady=(0, 10), padx=20, fill="x")
        self.progress_bar.set(0)

        # Log Text Box
        self.lbl_log = ctk.CTkLabel(self, text="Process Log:", anchor="w")
        self.lbl_log.pack(padx=20, fill="x")

        self.txt_log = ctk.CTkTextbox(self, height=180, state="disabled", font=ctk.CTkFont(family="Consolas", size=12))
        self.txt_log.pack(padx=20, pady=(0, 10), fill="both", expand=True)

        # Social Links
        self.frame_social = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_social.pack(pady=10, fill="x")
        
        self.lbl_contact = ctk.CTkLabel(self.frame_social, text="Suggestions? Contact:", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_contact.pack(pady=(0, 5))

        self.buttons_frame = ctk.CTkFrame(self.frame_social, fg_color="transparent")
        self.buttons_frame.pack()

        self.btn_update = ctk.CTkButton(self.buttons_frame, text="Check for Updates", width=120, fg_color="#6c757d", hover_color="#5a6268", command=self.manual_update_check)
        self.btn_update.pack(side="left", padx=10)

        self.btn_gh = ctk.CTkButton(self.buttons_frame, text="GitHub", width=100, command=lambda: self.open_link('github'))
        self.btn_gh.pack(side="left", padx=10)

        self.btn_li = ctk.CTkButton(self.buttons_frame, text="LinkedIn", width=100, command=lambda: self.open_link('linkedin'))
        self.btn_li.pack(side="left", padx=10)

    def browse_books(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xls")])
        if filename: 
            self.path_books.set(filename)

    def browse_2b(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xls")])
        if filename: 
            self.path_2b.set(filename)

    def open_settings(self):
        # Only allow one configuration window at a time
        if not hasattr(self, "settings_win") or not self.settings_win.winfo_exists():
            self.settings_win = SettingsWindow(self)
            self.settings_win.grab_set()

    def manual_update_check(self):
        threading.Thread(target=lambda: check_for_updates(quiet=False, parent_tk_window=self), daemon=True).start()

    def log(self, message: str):
        # Must be called from main thread or handled generically. CTk handles it okay sometimes, but safe to use after()
        def append():
            self.txt_log.configure(state="normal")
            self.txt_log.insert("end", message + "\n")
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")
        self.after(0, append)

    def open_link(self, key: str):
        url = CONTACT_LINKS.get(key)
        if url: 
            webbrowser.open(url)

    def start_process(self):
        p_books = self.path_books.get()
        p_2b = self.path_2b.get()

        if not p_books or not p_2b:
            messagebox.showwarning("Missing Files", "Please select both files before starting.")
            return

        if not os.path.exists(p_books) or not os.path.exists(p_2b):
            messagebox.showerror("Error", "One or both selected files could not be found.")
            return

        self.btn_run.configure(state="disabled")
        self.progress_bar.start()
        
        self.txt_log.configure(state="normal")
        self.txt_log.delete("0.0", "end")
        self.txt_log.configure(state="disabled")
        
        self.log("Starting Rekvia Engine...")
        
        # Run in thread
        threading.Thread(target=self.run_thread, args=(p_books, p_2b), daemon=True).start()

    def run_thread(self, p_books: str, p_2b: str):
        try:
            output_file = run_logic(p_books, p_2b, self.log)
            if output_file:
                self.after(0, lambda: self.ask_open_file(output_file))
        except Exception as e:
            self.log(f"An unexpected error occurred: {e}")
            logger.error("Engine crashed natively", exc_info=True)
        finally:
            self.after(0, self.finish_process)

    def finish_process(self):
        self.progress_bar.stop()
        self.btn_run.configure(state="normal")
        self.log("Process complete.")

    def ask_open_file(self, output_file: str):
        response = messagebox.askyesno("Success", "Rekvia has finished!\nDo you want to open the report?")
        if response:
            try:
                os.startfile(output_file)
            except AttributeError:
                import subprocess
                # For non-windows fallbacks if needed
                subprocess.call(['open', output_file])
