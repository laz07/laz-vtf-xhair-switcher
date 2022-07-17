# VTF crosshair switcher, v1.2, by laz
import os
import sys

sys.path.append(os.path.abspath('/app'))
sys.path.append(os.path.abspath('/app/ui'))

from app.utils import initialize_local_storage
from app.ui.main import show_app

# Decide on which frame to show based on the user's saved settings and
# whether the relevant folders exist and aren't empty
# def handle_frame_type():
#     retrieve_persisted_options()
#     # Paths in persisted data are correct (these take precedence)
#     p_check = valid_xhair_folder(cn["options"]["folder_path"])
#     # Paths relative to the executable are correct
#     d_check = valid_xhair_folder(cn["constants"]["defaults"]["folder_path"])


#     if p_check or d_check:
#         if not p_check and d_check:
#             cn["options"]["folder_path"] = cn["constants"]["defaults"]["folder_path"]

#     show_app()

if __name__ == "__main__":
    initialize_local_storage()

    show_app()
