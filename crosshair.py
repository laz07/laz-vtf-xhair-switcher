# VTF crosshair switcher, v3, by laz
import os
import sys
import ctypes

sys.path.append(os.path.abspath('/app'))
sys.path.append(os.path.abspath('/app/ui'))

from app.utils import initialize_local_storage
from app.app import show_app

# Get the icon to show on the windows taskbar
myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

if __name__ == "__main__":
    initialize_local_storage()
    show_app()
