# VTF crosshair switcher, v3, by laz
import os
import sys
import ctypes

sys.path.insert(0, os.path.abspath('./src'))

from src.utils import initialize_local_storage
from src.app.main import show_app

# Get the icon to show on the windows taskbar
myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

if __name__ == "__main__":
    initialize_local_storage()
    show_app()
