import shutil
import subprocess


def open_character_map():
    for cmd in ("gnome-characters", "gucharmap", "kcharselect"):
        exe = shutil.which(cmd)
        if exe:
            subprocess.Popen([exe])
            return True
    return False
