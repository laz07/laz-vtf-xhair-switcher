import os

FOLDER_PATH = ""
BACKUP_SCRIPTS = False
WEAPON_DISPLAY_TYPE = False

FONT_SIZE = 8
DATA_DIR = os.path.expanduser('~/.laz-vtf-crosshair-switcher/')
DATA_FILE_PATH = os.path.join(DATA_DIR, "data.txt")
PREVIEW_HASH_PATH = os.path.join(DATA_DIR, "preview_hash.txt")
LOGS_PATH = "xhs_logs.txt"

XHAIR_PREVIEW_PATH = "{}/preview/"  # Format with materials directory
XHAIR_PREVIEW_BG = '#aaa'

ASSET_ICON_APP = "assets/app.png"
ASSET_ICON_UNDO = "assets/undo.png"
ASSET_ICON_REDO = "assets/redo.png"
ASSET_ICON_INFO = "assets/info.png"
ASSET_SAMPLE_SCRIPTS = "assets/sample-scripts"

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
BOLD_TAG = "<span style=\"font-weight: bold;\">{}</span>"
BLUE_TAG = "<span style=\"color: #0088dd\">{}</span>"

REQUIRED_CFG = {
  'WeaponData',
  'WeaponData.printname',
  'WeaponData.BuiltRightHanded',
  'WeaponData.weight',
  'WeaponData.WeaponType',
  'WeaponData.bucket',
  'WeaponData.bucket_position',
  'WeaponData.SoundData',
  'WeaponData.TextureData',
  'WeaponData.TextureData."crosshair"',
  'WeaponData.TextureData."crosshair".file',
  'WeaponData.TextureData."crosshair".x',
  'WeaponData.TextureData."crosshair".y',
  'WeaponData.TextureData."crosshair".width',
  'WeaponData.TextureData."crosshair".height'
}