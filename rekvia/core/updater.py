import urllib.request
import json
import os
import sys
import threading
from tkinter import messagebox
import webbrowser

from rekvia.config.settings import APP_VERSION

REPO_API_URL = "https://api.github.com/repos/Tamil-Venthan/Rekvia/releases/latest"

def check_for_updates(quiet: bool = True, parent_tk_window=None):
    try:
        # User-Agent is mandatory for GitHub API
        req = urllib.request.Request(REPO_API_URL, headers={'User-Agent': 'Rekvia-App'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        latest_version = data.get("tag_name", "")
        # Equality check with APP_VERSION
        if latest_version and latest_version.strip() != APP_VERSION.strip():
            prompt_update(data, parent_tk_window)
        else:
            if not quiet:
                # If manual check triggered, inform the user they are up to date
                invoke_on_main(parent_tk_window, lambda: messagebox.showinfo("Up to Date", f"You are running the latest version ({APP_VERSION})."))
                
    except Exception as e:
        if not quiet:
            invoke_on_main(parent_tk_window, lambda: messagebox.showerror("Update Error", f"Could not connect to update server:\n{str(e)}"))

def invoke_on_main(window, func):
    """Safely executes a tkinter function on the main thread."""
    if window:
        window.after(0, func)
    else:
        func()

def prompt_update(release_data, window):
    latest_version = release_data.get("tag_name", "Unknown")
    release_notes = release_data.get("body", "")
    download_url = None
    
    # Seek out the .exe asset URL
    for asset in release_data.get("assets", []):
        if asset.get("name", "").endswith(".exe"):
            download_url = asset.get("browser_download_url")
            break
            
    def ask():
        msg = f"A new version ({latest_version}) is available!\n\nRelease Notes:\n{release_notes[:150]}...\n\nWould you like to install the update now?"
        if messagebox.askyesno("Update Available", msg):
            if download_url and getattr(sys, 'frozen', False):
                # When running natively as an .exe, we can auto-update
                threading.Thread(target=download_and_install, args=(download_url,), daemon=True).start()
            else:
                # If running as script or no exe found, redirect to the browser
                html_url = release_data.get("html_url")
                if html_url:
                    webbrowser.open(html_url)
    
    invoke_on_main(window, ask)

def download_and_install(download_url):
    import ssl
    try:
        current_exe = sys.executable
        download_path = current_exe + ".new"
        
        # Bypass potential corporate firewall proxy SSL blocks 
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as response, open(download_path, 'wb') as out_file:
            out_file.write(response.read())

        # Construct the batch file to bypass Windows executable locks (WinError 32)
        bat_path = os.path.join(os.path.dirname(current_exe), "update_rekvia.bat")
        with open(bat_path, "w") as b:
            b.write("@echo off\n")
            # Wait 3 seconds to ensure the parent process cleanly shuts down
            b.write("timeout /t 3 /nobreak > NUL\n")
            # Overwrite the old executable with the new payload
            b.write(f'move /y "{download_path}" "{current_exe}"\n')
            # Resurrect the application
            b.write(f'start "" "{current_exe}"\n')
            # Destroy the batch script
            b.write(f'del "%~f0"\n')
        
        # Trigger the script and immediately kill the user application
        os.startfile(bat_path)
        os._exit(0)
    except Exception as e:
        print(f"Failed to auto-update: {e}")
