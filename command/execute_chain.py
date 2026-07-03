import platform
import subprocess


def execute_command():
    current_platform = platform.system()

    if current_platform == "Linux":
        # make it executable
        subprocess.run("chmod +x install.sh", shell=True)

        #create a user service
        subprocess.run("mkdir -p ~/.config/systemd/user", shell=True)
        subprocess.run("nano ~/.config/systemd/user/startup.service", shell=True)
