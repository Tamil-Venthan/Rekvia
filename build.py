import os
import subprocess
import customtkinter

def build():
    print("Preparing to build Rekvia Windows Executable...")
    
    # CustomTkinter needs its assets explicitly added
    ctk_path = os.path.dirname(customtkinter.__file__)
    
    # We use PyInstaller
    # --noconfirm: overwrite existing
    # --onedir or --onefile: let's do --onefile for a cleaner distribution
    # --windowed: no cmd window pops up
    # --name: Rekvia
    # --add-data: Bundle custom tkinter

    # Format the add-data properly for Windows using semicolon
    add_data_str = f"{ctk_path};customtkinter/"

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "Rekvia",
        "--add-data", add_data_str
    ]

    # Dynamically bind the app icon if the user placed an 'icon.ico' in the root directory
    if os.path.exists("icon.ico"):
        cmd.extend(["--icon", "icon.ico"])
        cmd.extend(["--add-data", f"icon.ico;."])
        
    cmd.append("main.py")
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\nSUCCESS! Build complete.")
        print("Your executable is located in the 'dist' folder (dist/Rekvia.exe).")
    else:
        print("\nERROR: Build failed. See PyInstaller output above.")

if __name__ == "__main__":
    build()
