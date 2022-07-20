import re
from collections import OrderedDict
from sysconfig import parse_config_h
from constants.regex import RE_BRACKET_OPEN, RE_BRACKET_CLOSE, RE_DATA, RE_COMMENT, RE_HEADER
from constants.constants import REQUIRED_CFG

def get_header_sub_index(cfg, header_match, index):
  if (index >= len(cfg) - 2 or not header_match):
    return -1

  bracket_on_line = len(header_match.groups()) == 2
  bracket_next_line = re.search(RE_BRACKET_OPEN, cfg[index + 1])

  if bracket_on_line:
    return 1

  if bracket_next_line:
    return 2

  return -1

# From startIndex = index of open bracket + 1, search through lines to find corresponding close bracket
# If there are nested open brackets, take this into account by incrementing a count variable
def get_submap(cfg, start_index):
  count = 0
  for i in range(start_index, len(cfg)):
      ln = cfg[i]

      header_match = re.search(RE_HEADER, cfg[i])
      header_sub_index = get_header_sub_index(cfg, header_match, i)


      if header_sub_index > -1:
        count += 1
      elif re.search(RE_BRACKET_CLOSE, ln):
        count -= 1

      if count < 0:
        return cfg[start_index:i+1]

  return []



class CfgParser:
  def __init__(self):
    self.cfgs = OrderedDict()
    self.invalid_scripts = []

  def parse_cfg(self, cfg):
    data_map = OrderedDict()

    if len(cfg) == 0:
        return {}

    it = 0
    cmts = 0

    while it < len(cfg):
        ln = cfg[it]

        data_match = re.search(RE_DATA, ln)
        cmt_match = re.search(RE_COMMENT, ln)
        header_match = re.search(RE_HEADER, ln)
        header_sub_index = get_header_sub_index(cfg, header_match, it)

        # Insert comment into map with special #comment_0 key format
        if cmt_match:
            data_map["#comment_{}".format(cmts)] = cmt_match.group(1).strip()
            cmts += 1

        # Found a nested map structure, recurse and increment "it" past the sub map
        elif header_sub_index > -1:
            # hack to ensure that "fWeaponData" or similar is still matched as a header
            header = "WeaponData" if "WeaponData" in header_match.group(1) else header_match.group(1)
            submap = get_submap(cfg, it + header_sub_index)

            data_map[header] = self.parse_cfg(submap)
            it += len(submap)

        # Insert data into map
        elif data_match:
            data_map[data_match.group(1).strip("\"")] = data_match.group(2).strip("\"")

        it += 1

    return data_map

  def reconstruct_cfg(self, data_map, indent=0):
    lines = []

    for key, value in data_map.items():
        # Recursion for sub maps
        if type(value) is OrderedDict:
            tab = '\t'*indent
            lines.append(tab + key + "\n")
            lines.append(tab + "{\n")

            lines = lines + self.reconstruct_cfg(value, indent+1)
            lines.append(tab + "}\n")
        elif type(value) is str:
            # If the key/value pair indicates a comment, insert a newline and then the comment
            if key.startswith('#comment'):
                lines.append("{}// {}\n".format('\t'*indent, value.strip()))
            # Else insert the data in the correct format
            else:
                lines.append("{}\"{}\"\t\"{}\"\n".format('\t'*indent, key, value))

    return lines

  def validate_cfg(self, parsed_cfg):
    for check in REQUIRED_CFG:

      fields = check.split(".")
      dive = parsed_cfg

      for field in fields:
        if field not in dive:
          return False

        dive = dive[field]

    return True
