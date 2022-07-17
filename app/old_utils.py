import os
import json
import re
import sys
from collections import OrderedDict

from app.associations import weapon_associations
from app.constants import cn

# Parse a tf_weapon config file into a tree-like OrderedDict representation recursively
def parse_cfg(lines):
    data_map = OrderedDict()

    if len(lines) < 2:
        return {}

    re_header = "^\s*(\"?[^\s]+\"?)\s*$"
    re_data = "^\s*([^\s]+)\s+([^\s]+)\s*$"
    re_bracket_open = "^\s*{\s*$"
    re_bracket_close = "^\s*}\s*$"
    re_comment = "^\s*\/\/(.+)$"

    # From startIndex = index of open bracket + 1, search through lines to find corresponding close bracket
    # If there are nested open brackets, take this into account by incrementing a count variable
    def get_submap(startIndex):
        count = 0

        for i in range(startIndex, len(lines)):
            ln = lines[i]

            if re.search(re_bracket_open, ln):
                count += 1
            elif re.search(re_bracket_close, ln):
                if count > 0:
                    count -= 1
                else:
                    return lines[startIndex:i]

        return []

    it = 0
    cmts = 0

    while it < len(lines):
        ln = lines[it]
        data = re.search(re_data, ln)
        cmt = re.search(re_comment, ln)

        # Insert comment into map with special #comment_0 key format
        if cmt:
            data_map["#comment_{}".format(cmts)] = cmt.group(1)
            cmts += 1

        # Insert data into map
        elif data:
            data_map[data.group(1).strip("\"")] = data.group(2).strip("\"")

        # Found a nested map structure, recurse and increment "it" past the sub map
        elif it < len(lines) - 2:
            header_match = re.search(re_header, ln)

            # found a header and a bracket on the next line, expect a sub map
            if header_match and re.search(re_bracket_open, lines[it+1]):
                # hack to ensure that "fWeaponData" or similar is still matched as a header
                header = "WeaponData" if "WeaponData" in header_match.group(1) else header_match.group(1)
                submap = get_submap(it+2)

                data_map[header] = parse_cfg(submap)
                it += len(submap) + 1

        it += 1

    return data_map

# Reconstruct line-by-line CFG from the OrderedDict representation
def reconstruct_cfg(data_map, indent=0):
    lines = []

    re_comment = "#comment_\d+"

    for key, value in data_map.items():
        # Recursion for sub maps
        if type(value) is OrderedDict:
            tab = '\t'*indent
            lines.append(tab + key + "\n")
            lines.append(tab + "{\n")

            lines = lines + reconstruct_cfg(value, indent+1)
            lines.append(tab + "}\n")
        elif type(value) is str:
            # If the key/value pair indicates a comment, insert a newline and then the comment
            if re.search(re_comment, key):
                lines.append("\n")
                lines.append("{}// {}\n".format('\t'*indent, value.strip()))
            # Else insert the data in the correct format
            else:
                lines.append("{}\"{}\"\t\"{}\"\n".format('\t'*indent, key, value))

    return lines

# Simply write to the cfg file line by line, making sure that we clear the file first
def write_cfg(path, lines):
    open(path, 'w').close()
    with open(path, "a") as f:
        for line in lines:
            f.write(line)


# Build list of data structures containing key information about each weapon
# Each entry includes the file path, the weapon class name, and the parsed file contents
def build_entries():
    if not os.path.isdir(get_scripts_path()):
        return None

    global debug_lastfile
    files = [f for f in os.listdir(get_scripts_path()) if os.path.isfile(os.path.join(get_scripts_path(), f))]
    re_weapon = "^(tf_weapon_[a-zA-Z_]+)\.txt$"

    data = []

    for fn in files:
        wep = re.search(re_weapon, fn)
        if not wep:
            continue

        fpath = "{}/{}".format(get_scripts_path(), fn)
        debug_lastfile = "/".join(fpath.replace("\\", "/").split("/")[-2:])

        with open(fpath, "r") as f:
            datum = {
                "path": fpath,
                "name": wep.group(1),
                "cfg": parse_cfg(f.readlines())
            }
            datum["xhair"] = datum["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"].split("/")[-1]
            data.append(datum)

    return data

# Sort entries, sort_arr is a list with two values, either -1, 0, 1,
# indicating which column to sort by and whether to sort ascending
# or descending
def sort_entries(entries, sort_arr):
    which = sort_arr[0] == 0
    direction = sort_arr[1 if which else 0] < 0

    if not which:
        if cn["options"]["weapon_display_type"]:
            entries.sort(key=lambda x: x["name"], reverse=direction)
        else:
            order = {"Scout": 1, "Soldier": 2, "Pyro": 3, "Demoman": 4,
                     "Heavy": 5, "Engineer": 6, "Medic": 7, "Sniper": 8, "Spy": 9}

            def sort_value(item):
                asc = weapon_associations[item["name"]]
                val = order[asc["class"]] * 100

                for i in range(len(asc["display"])):
                    o = ord(asc["display"][i])

                    lwr = (o > 65) and (o < 90)
                    upr = (o > 90) and (o < 122)

                    if not lwr and not upr:
                        continue

                    ind = (o - 64) if lwr else (o - 89)
                    val += (10 ** -i) * ind

                return val

            entries.sort(key=sort_value, reverse=direction)
    else:
        entries.sort(key=lambda x: x["xhair"], reverse=direction)


# Prepare entries for display by filtering out any extra files and sorting
def prepare_entries():
    weps = build_entries()

    if weps is None:
        return []

    entries = [x for x in weps if x["name"] in weapon_associations]

    sort_entries(entries, [1, 0])

    return entries

# Search through materials/vgui/replay/thumbnails for vtf files
# (arbitrarily choose vtf and discard vmts since both should be present for each xhair)
def get_crosshairs():
    xp = get_xhairs_path()
    if not os.path.isdir(xp):
        return []

    files = [f for f in os.listdir(xp) if os.path.isfile(os.path.join(xp, f))]
    return [x[:-4] for x in list(filter(lambda x: x.endswith(".vtf"), files))]


def get_scripts_path():
    return "{}/scripts".format(cn["options"]["folder_path"])

def get_xhairs_path():
    return "{}/materials/vgui/replay/thumbnails".format(cn["options"]["folder_path"])

# ensure that the folder exists and has a valid structure
def valid_xhair_folder(path):
    scripts_path = get_scripts_path()
    xhairs_path = get_xhairs_path()

    return os.path.isdir(path) \
        and os.path.isdir(scripts_path) \
        and len(os.listdir(scripts_path)) > 0 \
        and os.path.isdir(xhairs_path) \
        and len(os.listdir(xhairs_path)) > 0



## functions for persisting options between program runs
## by default save a text file with a json representation
## of the options to the user's home directory

def persist_options():
    with open(cn["constants"]["data_file_path"], "w") as f:
        f.write(json.dumps(cn["options"]))

def clear_persisted_options():
    open(cn["constants"]["data_file_path"], "w").close()

    cn["options"] = cn["constants"]["defaults"].copy()

def retrieve_persisted_options():
    data = {}

    try:
        with open(cn["constants"]["data_file_path"], "r") as f:
            data = json.loads(f.read())
    except:
        pass

    if len(data) == len(cn["options"]):
        cn["options"] = data


def initialize_local_storage():
    # Initialize local storage directory
    if not os.path.isdir(cn["constants"]["data_dir"]):
        os.mkdir(cn["constants"]["data_dir"])

    display_path = "{}/display".format(cn["constants"]["data_dir"])
    if not os.path.isdir(display_path):
        os.mkdir(display_path)

def get_xhair_display_path(xhair):
    path1 = resource_path("assets/display/{}.png".format(xhair))
    path2 = "{}/display/{}.png".format(cn["constants"]["data_dir"], xhair)

    if os.path.isfile(path2):
        return path2

    if os.path.isfile(path1):
        return path1

    return None

def format_path_by_os(path):
    is_windows = os.name == 'nt'
    delim = "\\" if is_windows else "/"

    return path.replace("\\", delim).replace("/", delim)

# Get absolute path to resource, works for dev and for PyInstaller
def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    return os.path.join(base_path, relative_path)

def gen_hash():
    import hashlib
    import time

    ha = hashlib.sha1()
    ha.update(str(time.time()).encode("utf-8"))

    return ha.hexdigest()[:15]

