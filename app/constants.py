import os
import wx

# generate a (probably) unique hash to append to the
# backup folders' names to give each folder a unique name
def gen_hash():
    import hashlib
    import time

    hash = hashlib.sha1()
    hash.update(str(time.time()).encode("utf-8"))

    return hash.hexdigest()[:15]

dd = os.path.expanduser('~/.tf2-crosshair-switcher/')

defaults = {
    "folder_path": "",
    "backup_scripts": False,
    "weapon_display_type": False
}

cn = {
    "constants": {
        "defaults": defaults,
        "backup_folder_path": "{}/backup_" + gen_hash(),
        "font_size": 8,
        "data_dir": dd,
        "data_file_path": "{}/.data.txt".format(dd),
        "logs_path": "xhs_logs.txt",
        "xhair_preview_path": "{}/preview/"  # Format with materials directory
    },

    "options": defaults.copy(),

    ##########################
    #           UI           #
    ##########################

    "ui": {
        "btn_apply": "Apply",
        "btn_apply_class": "Apply to all weapons of this class",
        "btn_apply_slot": "Apply to all weapons of this slot",
        "btn_apply_all": "Apply to all weapons",
        "btn_change_folders": "Change scanned folders",
        "chk_display_toggle": "Toggle display type",
        "chk_backup_scripts": "Backup scripts before modifying",
        "invalid_folder_msg": "Either scripts or thumbnails folder is missing or invalid\nPlease indicate their location below",
        "parse_error_msg": "Error parsing some crosshair scripts. \n Error in file {} \n Please double check that your scripts are valid",
        "generate_config_msg": "Will generate scripts/ and /materials/vgui/replay/thumbnail folders within the folder you select and populate them with sample weapon configs and crosshair files",
        "add_custom_xhairs_msg": "Will add custom crosshairs to the available list of crosshairs in the dropdown. Ensure the folder you select contains two sub-folders:\n\n/crosshairs -- for the crosshair vtf/vmts\n/display -- for the crosshair display .pngs.\n\nNAMES MUST MATCH BETWEEN THESE TWO FOLDERS",
        "gen_xhair_config_frame_title": "Generate Sample Crosshair Config",
        "xhair_image_frame_title": "Add Crosshair PNGs",
        "xhair_image_content_msg": "PNG will be copied to your user directory with the name of the crosshair",
        "xhair_image_no_content_msg": "You have not added any additional crosshairs in this folder. Once you add some, you'll be able to assign PNGs to them here.",
        "about_msg": "Made by Max \"laz\" M",

        "menubar_file_open_text": "Open Folder",
        "menubar_file_open_description": "Open Crosshair Folder",
        "menubar_file_opts_text": "Options",
        "menubar_file_opts_description": "Options",
        "menubar_file_gen_xhairs_text": "Generate Config",
        "menubar_file_gen_xhairs_description": "Generate Sample Crosshair Config",
        "menubar_file_add_xhairs_text": "Add Crosshair PNGs",
        "menubar_file_add_xhairs_description": "Add a display PNG for a crosshair",
        "menubar_file_quit_text": "Quit",
        "menubar_file_quit_description": "Quit application",

        "menubar_about_about_text": "About",
        "menubar_about_about_description": "About",


        "window_size": (950, 600),
        "window_size_options": (500, 150),
        "window_size_min": (900, 500),
        "window_size_options_frame": (500, 135),
        "window_size_info_frame": (500, 150),
        "window_size_crosshair_image_frame": (500, 135),
        "window_size_about_frame": (500, 135),

        "xhair_preview_background_color": wx.Colour(150, 150, 150)
    }
}