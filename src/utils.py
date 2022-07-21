import os
import re
import sys

from PyQt6.QtWidgets import QApplication

from constants.constants import FOLDER_PATH, DATA_DIR
from constants.regex import RE_WEAPON
from constants.associations import weapon_associations

# generate a (probably) unique hash to append to the
# backup folders' names to give each folder a unique name
def gen_hash():
    import hashlib
    import time

    ha = hashlib.sha1()
    ha.update(str(time.time()).encode("utf-8"))

    return ha.hexdigest()[:15]

def get_scripts_path():
    return "{}/scripts".format(FOLDER_PATH)

def read_cfgs(dirname):
  if not os.path.isdir(dirname):
    return None

  files = [f for f in os.listdir(dirname) if os.path.isfile(os.path.join(dirname, f))]
  res = []

  for filename in files:
    wep = re.search(RE_WEAPON, filename)

    if not wep:
      continue

    filepath = "{}/{}".format(dirname, filename)

    with open(filepath, "r") as f:
      lines = f.readlines()

      res += [{
        "path": filepath,
        "name": wep.group(1),
        "contents": lines
      }]

  return res

def get_xhairs(path):
  if not os.path.isdir(path):
      return []

  files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

  return [{ "path": os.path.join(path, x), "name": x[:-4] } for x in list(filter(lambda x: x.endswith(".vtf"), files))]


def get_xhair_from_cfg(cfg):
  return cfg["WeaponData"]["TextureData"]["\"crosshair\""]["file"].split('/')[-1]

def change_xhair_in_cfg(cfg, xhair):
  cfg["WeaponData"]["TextureData"]["\"crosshair\""]["file"] = "vgui/replay/thumbnails/{}".format(xhair)

def write_cfg(lines, cfg_path, xhair):
  xhair_path = os.path.join(cfg_path, "scripts", "{}.txt".format(xhair))

  if not os.path.exists(xhair_path):
    return

  with open(xhair_path, 'w') as f:
    f.close()

  with open(xhair_path, 'a') as f:
    for line in lines:
      f.write(line)

def initialize_local_storage():
    # Initialize local storage directory
    if not os.path.isdir(DATA_DIR):
      os.mkdir(DATA_DIR)

    preview_path = "{}/previews".format(DATA_DIR)
    if not os.path.isdir(preview_path):
      os.mkdir(preview_path)

# Prepare entries for display by filtering out any extra files and sorting
def prepare_entries(path):
  cfgs = read_cfgs(path)

  if cfgs is None:
      return []

  entries = [x for x in cfgs if x["name"] in weapon_associations]

  return entries

def format_path_by_os(path):
    is_windows = os.name == 'nt'
    delim = "\\" if is_windows else "/"

    return path.replace("\\", delim).replace("/", delim)

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    return os.path.join(base_path, relative_path)

def get_app():
  return QApplication.instance()
