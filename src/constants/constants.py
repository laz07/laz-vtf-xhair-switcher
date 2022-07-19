import os

FOLDER_PATH = ""
BACKUP_SCRIPTS = False
WEAPON_DISPLAY_TYPE = False

FONT_SIZE = 8
DATA_DIR = os.path.expanduser('~/.laz-vtf-crosshair-switcher/')
DATA_FILE_PATH: "{}/.data.txt".format(DATA_DIR)
LOGS_PATH = "xhs_logs.txt"

XHAIR_PREVIEW_PATH = "{}/preview/"  # Format with materials directory
XHAIR_PREVIEW_BG = '#aaa'

ICON_APP = "assets/app.png"
ICON_UNDO = "assets/undo.png"
ICON_REDO = "assets/redo.png"
ICON_INFO = "assets/info.png"

APPLY_SELECTION = 'apply'
APPLY_CLASS = 'class'
APPLY_SLOT = 'slot'
APPLY_ALL = 'all'

BULK_APPLY_OPTIONS = {
  'select...': None,
  'All weapons of this class': APPLY_CLASS,
  'All weapons of this slot': APPLY_SLOT,
  'All weapons': APPLY_ALL
}

ITALIC_TAG = "<span style=\"font-style: italic;\">{}</span>"