import os
import re
from app.constants.constants import FOLDER_PATH, DATA_DIR
from app.constants.regex import RE_WEAPON
from app.constants.associations import weapon_associations

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

def get_xhair_from_cfg(cfg):
  return cfg["WeaponData"]["TextureData"]["\"crosshair\""]["file"].split('/')[-1]

def initialize_local_storage():
    # Initialize local storage directory
    if not os.path.isdir(DATA_DIR):
        os.mkdir(DATA_DIR)

    display_path = "{}/display".format(DATA_DIR)
    if not os.path.isdir(display_path):
      os.mkdir(display_path)

# Prepare entries for display by filtering out any extra files and sorting
def prepare_entries(path):
  cfgs = read_cfgs(path)

  if cfgs is None:
      return []

  entries = [x for x in cfgs if x["name"] in weapon_associations]

  return entries
