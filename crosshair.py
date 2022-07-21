import re
import wx
import wx.lib.mixins.listctrl
import os
import shutil
import datetime
import functools
import platform
import json
from associations import *
from collections import OrderedDict

def gen_hash():
    import hashlib
    import time

    hash = hashlib.sha1()
    hash.update(str(time.time()).encode("utf-8"))

    return hash.hexdigest()[:15]


constants = {
    "default_materials_path": "materials",
    "default_scripts_path": "scripts",
    "backup_folder_path": "scripts/backup_{}".format(gen_hash()),
    "min_window_size": (600, 400),
    "font_size": 8,
    "data_dir": os.path.expanduser('~/.crosshair-data.txt'),
    "logs_path": "xhs_logs.txt"
}
options = {
    "materials_path": constants["default_materials_path"],
    "scripts_path": constants["default_scripts_path"],
    "backup_scripts": False,
    "weapon_display_type": False
}

ui = {
    "btn_apply": "Apply",
    "btn_apply_class": "Apply to all weapons of this class",
    "btn_apply_slot": "Apply to all weapons of this slot",
    "btn_apply_all": "Apply to all weapons",
    "btn_change_folders": "Change scanned folders",
    "chk_display_toggle": "Toggle display type",
    "chk_backup_scripts": "Backup scripts before modifying",
    "error_msg": "Either scripts or thumbnails folder is missing or invalid\nPlease indicate their location below"
}


class FixedWidthListCtrl(wx.ListCtrl, wx.lib.mixins.listctrl.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        wx.lib.mixins.listctrl.ListCtrlAutoWidthMixin.__init__(self)
        self.setResizeColumn(0)

# Main GUI frame
class CrosshairFrame(wx.Frame):
    def __init__(self, parent, title, size, entries):
        super(CrosshairFrame, self).__init__(
            parent, title=title, size=size, style=wx.DEFAULT_FRAME_STYLE)
        # Setup
        # self.SetIcon(wx.Icon("xhair.ico"))

        self.entries = entries
        self.cur_entries = []
        self.cur_xhair = ""
        self.xhairs = get_crosshairs()

        self.SetMinSize(constants["min_window_size"])

        # Main panel
        self.main_panel = wx.Panel(self)

        # Top/bottom layout, divides the weapon list & weapon info from the log viewer & options
        box_main = wx.BoxSizer(wx.VERTICAL)

        # Left/right layout, divides the weapon list from the weapon info (nested inside box_tb)
        box_weapon = wx.BoxSizer(wx.HORIZONTAL)

        # Vertical layout within weapon info panel to arrange the info text with the xhair combo box, apply buttons, and xhair preview
        box_weapon_info = wx.BoxSizer(wx.VERTICAL)

        # Separates the xhair selector/buttons from the xhair preview
        box_controls = wx.BoxSizer(wx.HORIZONTAL)

        # Contains xhair selector/buttons
        box_buttons = wx.BoxSizer(wx.VERTICAL)

        # Horizontal layout for bottom panel (log viewer & options)
        box_bottom = wx.BoxSizer(wx.HORIZONTAL)

        # Layout for options panel
        box_opts = wx.BoxSizer(wx.VERTICAL)

        # Initialize controls for top layout

        # Top-left weapon list panel
        self.weapon_list = FixedWidthListCtrl(self.main_panel, -1, size=(
            300, -1), style=wx.LC_REPORT)

        self.weapon_list.SetFont(
            wx.Font(constants["font_size"], wx.FONTFAMILY_TELETYPE, wx.NORMAL, wx.NORMAL))
        self.weapon_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_list_select)
        self.weapon_list.Bind(wx.EVT_LIST_COL_CLICK, self.col_click)
        self.weapon_list_sort = [1,0]
        self.populate_list()

        # Top-right weapon info text panel
        self.text = wx.TextCtrl(
            self.main_panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH)
        self.text.Bind(wx.EVT_KEY_DOWN, self.disable_textctrl_input)
        self.text.SetFont(
            wx.Font(constants["font_size"], wx.FONTFAMILY_TELETYPE, wx.NORMAL, wx.NORMAL))

        # Actions in right panel under info (xhair select, buttons)
        self.xhair_choice = wx.Choice(self.main_panel, choices=self.xhairs)
        self.btn_apply = wx.Button(self.main_panel, label=ui["btn_apply"])
        self.btn_apply_class = wx.Button(
            self.main_panel, label=ui["btn_apply_class"])
        self.btn_apply_slot = wx.Button(
            self.main_panel, label=ui["btn_apply_slot"])
        self.btn_apply_all = wx.Button(
            self.main_panel, label=ui["btn_apply_all"])

        self.btn_apply.Bind(wx.EVT_BUTTON, self.btn_apply_clicked)
        self.btn_apply_class.Bind(wx.EVT_BUTTON, self.btn_apply_clicked)
        self.btn_apply_slot.Bind(wx.EVT_BUTTON, self.btn_apply_clicked)
        self.btn_apply_all.Bind(wx.EVT_BUTTON, self.btn_apply_clicked)

        box_buttons.Add(self.xhair_choice)
        box_buttons.Add(self.btn_apply)
        box_buttons.Add(self.btn_apply_class)
        box_buttons.Add(self.btn_apply_slot)
        box_buttons.Add(self.btn_apply_all)

        self.xhair_preview = wx.Panel(self.main_panel)

        box_controls.Add(box_buttons, wx.SizerFlags().Expand().Proportion(50))
        box_controls.Add(self.xhair_preview,
                         wx.SizerFlags().Expand().Proportion(50))

        box_weapon_info.Add(self.text, wx.SizerFlags().Expand().Proportion(50))
        box_weapon_info.Add(
            box_controls, wx.SizerFlags().Expand().Proportion(50))

        box_weapon.Add(self.weapon_list, wx.SizerFlags().Expand().Proportion(50).Border(wx.ALL, 10))
        box_weapon.Add(box_weapon_info,
                       wx.SizerFlags().Expand().Proportion(50).Border(wx.ALL, 10))

        # Bottom-left logging panel
        self.logger = wx.TextCtrl(
            self.main_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.logger.AppendText("LOGS:\n")
        self.logger.SetFont(
            wx.Font(constants["font_size"], wx.FONTFAMILY_TELETYPE, wx.NORMAL, wx.BOLD))
        self.logger.Bind(wx.EVT_KEY_DOWN, self.disable_textctrl_input)

        self.logs = []

        # Bottom-right options controls
        self.checkbox_display_type = wx.CheckBox(
            self.main_panel, label=ui["chk_display_toggle"])
        self.checkbox_backup = wx.CheckBox(
            self.main_panel, label=ui["chk_backup_scripts"])

        self.checkbox_display_type.SetValue(options["weapon_display_type"])
        self.checkbox_backup.SetValue(options["backup_scripts"])

        self.checkbox_display_type.Bind(wx.EVT_CHECKBOX, self.checkbox_clicked)
        self.checkbox_backup.Bind(wx.EVT_CHECKBOX, self.checkbox_clicked)

        self.btn_change_folders = wx.Button(
            self.main_panel, label=ui["btn_change_folders"])
        self.btn_change_folders.Bind(
            wx.EVT_BUTTON, self.btn_change_folders_clicked)

        box_opts.Add(self.checkbox_display_type)
        box_opts.Add(self.checkbox_backup)
        box_opts.Add(self.btn_change_folders)

        box_bottom.Add(self.logger, wx.SizerFlags().Expand().Proportion(70))
        box_bottom.Add(box_opts, wx.SizerFlags().Expand().Proportion(30))

        box_main.Add(box_weapon, wx.SizerFlags().Expand().Proportion(70))
        box_main.Add(box_bottom, wx.SizerFlags(
        ).Expand().Proportion(30).Border(wx.TOP, 10))

        self.main_panel.SetSizer(box_main)
        self.main_panel.Fit()

        self.Centre()
        self.Show(True)

        self.toggle_controls(False)
        self.logs_add("Scripts being read from {}".format(
            os.path.abspath(options["scripts_path"])))
        self.logs_add("Crosshairs being read from {}/vgui/replay/thumbnails/".format(
            os.path.abspath(options["materials_path"])))

    # Logs

    # Add a log with a timestamp and show in logger

    def logs_add(self, item):
        now = datetime.datetime.now()
        time = [now.hour, now.minute, now.second]

        def pad(n):
            out = str(n)
            return "0" + out if len(out) == 1 else out

        self.logs.append([time, item])
        self.logger.AppendText("[{}:{}:{}] {}\n".format(
            pad(time[0]), pad(time[1]), pad(time[2]), item))

    # Clear logs
    def logs_clear(self):
        self.logs = []
        self.logger.SetValue("LOGS:\n")

    # Write logs to file (unused)
    def logs_write(self):
        with open(constants["logs_path"], "w+") as f:
            f.write("\n".join(map(lambda x: "[{}:{}:{}] {}\n".format(
                x[0][0], x[0][1], x[0][2], x[1]), self.logs)))

    def disable_textctrl_input(self, event):
        event.Skip()

    # Toggle controls depending on if a list box option is selected
    def toggle_controls(self, on):
        if on:
            self.xhair_choice.Enable()
            self.btn_apply.Enable()
            self.btn_apply_class.Enable()
            self.btn_apply_slot.Enable()
        else:
            self.xhair_choice.Disable()
            self.btn_apply.Disable()
            self.btn_apply_class.Disable()
            self.btn_apply_slot.Disable()

    def draw_crosshair(self):
        #stub, todo
        pass

    # Populate list box with weapon
    def populate_list(self):
        sort_entries(self.entries, self.weapon_list_sort)

        self.weapon_list.ClearAll()
        self.weapon_list.InsertColumn(0, "Weapon", width=150)
        self.weapon_list.InsertColumn(1, "Crosshair", wx.LIST_FORMAT_RIGHT, width=150)

        # Get the longest label so that the (crosshair) display can be positioned correctly
        def label_len(x): return len(x["name"] if options["weapon_display_type"]
                                     else "{}: {}".format(weapon_associations[x["name"]]["class"], weapon_associations[x["name"]]["display"]))
        longest = label_len(functools.reduce(lambda x, y: (
            x if label_len(x) > label_len(y) else y), self.entries))

        for x in self.entries:
            label = x["name"] if options["weapon_display_type"] else "{}: {}".format(weapon_associations[x["name"]]["class"], weapon_associations[x["name"]]["display"])
            
            self.weapon_list.Append([label, x["xhair"]])

        self.weapon_list.EnsureVisible(0)

    def backup_scripts(self):
        if os.path.isdir(constants["backup_folder_path"]):
            return

        os.mkdir(constants["backup_folder_path"])
        files = [f for f in os.listdir(options["scripts_path"]) if os.path.isfile(
            os.path.join(options["scripts_path"], f))]
        re_weapon = "^(tf_weapon_[a-zA-Z_]+)\.txt$"

        for file in files:
            if not re.search(re_weapon, file):
                continue

            shutil.copyfile("{}/{}".format(options["scripts_path"], file), "{}/{}".format(
                constants["backup_folder_path"], file))
            self.logs_add("Backed up {} to folder /{}/".format(file,
                                                               constants["backup_folder_path"]))

    def btn_apply_clicked(self, event):
        label = event.GetEventObject().GetLabel()

        if len(self.cur_entries) == 0:
            return

        cur_xhair = self.xhair_choice.GetString(
            self.xhair_choice.GetSelection())

        def change_entry(entry):
            fname = entry["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"]
            old_xhair = fname.split("/")[-1]

            if old_xhair == cur_xhair:
                self.logs_add("Skipped {} (was already {})".format(
                    entry["name"], old_xhair))
            else:
                entry["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"] = "/".join(
                    fname.split("/")[:-1]) + "/" + cur_xhair
                entry["xhair"] = cur_xhair

                out = reconstruct_cfg(entry["cfg"])
                write_cfg(entry["path"], out)
                self.logs_add("{} changed from {} to {}".format(
                    entry["name"], old_xhair, cur_xhair))

        if options["backup_scripts"]:
            self.backup_scripts()

        if label == ui["btn_apply"]:
            for entry in self.cur_entries:
                change_entry(entry)

        elif label == ui["btn_apply_class"]:
            class_name = weapon_associations[self.cur_entries[0]
                                             ["name"]]["class"]
            included_names = {k: v for (k, v) in weapon_associations.items(
            ) if v["class"] == class_name}.keys()
            included_entries = filter(
                lambda x: x["name"] in included_names, self.entries)

            for entry in included_entries:
                change_entry(entry)
        elif label == ui["btn_apply_slot"]:
            slot = weapon_associations[self.cur_entries[0]["name"]]["slot"]
            included_names = {
                k: v for (k, v) in weapon_associations.items() if v["slot"] == slot}.keys()
            included_entries = filter(
                lambda x: x["name"] in included_names, self.entries)

            for entry in included_entries:
                change_entry(entry)
        elif label == ui["btn_apply_all"]:
            for entry in self.entries:
                change_entry(entry)

        self.populate_list()

    def checkbox_clicked(self, event):
        checked = True if event.GetInt() == 1 else False
        label = event.GetEventObject().GetLabel()

        if label == ui["chk_display_toggle"]:
            options["weapon_display_type"] = checked
            self.entries = build_entries()
            self.populate_list()
        elif label == ui["chk_backup_scripts"]:
            options["backup_scripts"] = checked

    def on_list_select(self, event):
        display = {"classes": [], "weapons": [],
                   "categories": [], "affected": []}

        def get_selected_items():
            s = []
            it = -1
            while (True):
                nxt = self.weapon_list.GetNextSelected(it)
                if nxt == -1:
                    return s
                
                s.append(nxt)
                it = nxt

        selected = get_selected_items()
        self.cur_entries = []

        for i in selected:
            entry = self.entries[i]
            asc = weapon_associations[entry["name"]]

            asc["class"] not in display["classes"] and display["classes"].append(
                asc["class"])
            display["weapons"].append(entry["name"])
            asc["display"] not in display["categories"] and display["categories"].append(
                asc["display"])

            for item in asc["all"]:
                item not in display["affected"] and display["affected"].append(
                    item)

            self.cur_entries.append(
                list(filter(lambda x: x["name"] == entry["name"], self.entries))[0])
            cur_xhair = self.cur_entries[-1]["xhair"]

            self.xhair_choice.SetSelection(self.xhairs.index(cur_xhair))
            self.toggle_controls(True)

        def addText(text, color):
            # doesnt work on windows? very unfortunate
            self.text.SetDefaultStyle(wx.TextAttr(color))
            self.text.AppendText(text)

        self.text.SetValue("")

        if len(selected) > 1:
            addText("<multiple>\n", wx.BLACK)

        addText("Class{}: ".format("es" if len(
            display["classes"]) > 1 else ""), wx.BLUE)
        addText("{}\n\n".format(", ".join(display["classes"])), wx.BLACK)

        addText("Weapon Class{}: ".format("es" if len(
            display["weapons"]) > 1 else ""), wx.BLUE)
        addText("{}\n\n".format(", ".join(display["weapons"])), wx.BLACK)

        addText("Categor{}: ".format("ies" if len(
            display["categories"]) > 1 else "y"), wx.BLUE)
        addText("{}\n\n".format(", ".join(display["categories"])), wx.BLACK)

        addText("Slot: ", wx.BLUE)

        if len(selected) > 1:
            addText("<multiple>\n\n", wx.BLACK)
        else:
            addText("{}\n\n".format({1: "Primary", 2: "Secondary", 3: "Melee", 4: "PDA"}[
                    weapon_associations[self.cur_entries[0]["name"]]["slot"]]), wx.BLACK)

        addText("Affected Weapons:\n", wx.BLUE)
        addText("\n".join(display["affected"]), wx.BLACK)

        if len(self.cur_entries) > 0:
            def entries_homogeneous(field):
                fil = filter(lambda x: weapon_associations[x["name"]][field] ==
                             weapon_associations[self.cur_entries[0]["name"]][field], self.cur_entries)
                return len(list(fil)) == len(self.cur_entries)

            if entries_homogeneous("class"):
                self.btn_apply_class.Enable()
            else:
                self.btn_apply_class.Disable()

            if entries_homogeneous("slot"):
                self.btn_apply_slot.Enable()
            else:
                self.btn_apply_slot.Disable()

        self.text.ScrollPages(-100)

    def col_click(self, event):
        col = event.GetColumn()
        cur = self.weapon_list_sort[col] 
        self.weapon_list_sort[col] = 1 if cur == 0 else cur * -1
        self.weapon_list_sort[1 if col == 0 else 0] = 0
        
        self.populate_list()

    def btn_change_folders_clicked(self, event):
        self.Close()
        clear_persisted_data()
        handle_frame_type()
        # handle_frame_type()


# wxPython popup frame to show when one of the two necessary folders is not present
class DirPickerFrame(wx.Frame):
    def __init__(self, parent, title, size, errtext):
        super(DirPickerFrame, self).__init__(parent, title=title, size=size)
        self.SetMinSize(size)

        self.paths = {
            "materials_path": "",
            "scripts_path": ""
        }
        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.VERTICAL)

        errortext = wx.StaticText(
            panel, style=wx.ALIGN_CENTRE_HORIZONTAL | wx.TE_MULTILINE)
        errortext.SetLabel(errtext)
        errortext.SetForegroundColour((255, 0, 0))
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        errortext.SetFont(font)

        materials_picker = wx.DirPickerCtrl(panel)
        materials_picker.Bind(wx.EVT_DIRPICKER_CHANGED,
                              self.materials_picker_changed)
        scripts_picker = wx.DirPickerCtrl(panel)
        scripts_picker.Bind(wx.EVT_DIRPICKER_CHANGED,
                            self.scripts_picker_changed)

        self.continue_btn = wx.Button(panel, label="Continue")
        self.continue_btn.Disable()
        self.continue_btn.Bind(wx.EVT_BUTTON, self.click_continue)

        close_btn = wx.Button(panel, label="Close")
        close_btn.Bind(wx.EVT_BUTTON, self.click_close)

        box_btns = wx.BoxSizer(wx.HORIZONTAL)
        box_btns.Add(close_btn, wx.EXPAND)
        box_btns.Add(self.continue_btn, wx.EXPAND)

        box.Add(errortext, wx.EXPAND, wx.EXPAND)
        box.Add(wx.StaticText(
            panel, label="Materials Directory (materials/):"))
        box.Add(materials_picker, wx.EXPAND, wx.EXPAND)
        box.Add(wx.StaticText(panel, label="Scripts Directory (scripts/):"))
        box.Add(scripts_picker, wx.EXPAND, wx.EXPAND)

        box.Add(box_btns, 0, wx.EXPAND)

        panel.SetSizer(box)
        panel.Fit()
        self.Centre()
        self.Show(True)

    def click_close(self, event):
        self.Close()

    def click_continue(self, event):
        self.Close()

        persist_data(self.paths)
        handle_frame_type()

    def path_changed(self, which, path):
        self.paths["materials_path" if which == 0 else "scripts_path"] = path

        if len(self.paths["materials_path"]) > 0 and len(self.paths["scripts_path"]) > 0:
            self.continue_btn.Enable()
        else:
            self.continue_btn.Disable()

    def materials_picker_changed(self, event):
        self.path_changed(0, event.GetPath())

    def scripts_picker_changed(self, event):
        self.path_changed(1, event.GetPath())


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
        elif it < len(lines) - 2 and re.search(re_header, ln) and re.search(re_bracket_open, lines[it+1]):
            submap = get_submap(it+2)

            data_map[re.search(re_header, ln).group(1)] = parse_cfg(submap)
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
                lines.append("{}// {}\n".format('\t'*indent, value))
            # Else insert the data in the correct format
            else:
                lines.append("{}\"{}\"\t\"{}\"\n".format(
                    '\t'*indent, key, value))

    return lines

# Simply write to the cfg file line by line, making sure that we clear the file first


def write_cfg(path, lines):
    open(path, 'w').close()
    with open(path, "a") as f:
        for line in lines:
            f.write(line)


# Build list of data structures containing key information about each weapon
# Each entry includes the file path, the weapon class name, and the parsed file contents
def get_weapons():
    files = [f for f in os.listdir(options["scripts_path"]) if os.path.isfile(
        os.path.join(options["scripts_path"], f))]
    re_weapon = "^(tf_weapon_[a-zA-Z_]+)\.txt$"

    data = []

    for fn in files:
        wep = re.search(re_weapon, fn)
        if not wep:
            continue

        fpath = "{}/{}".format(options["scripts_path"], fn)
        with open(fpath, "r") as f:
            datum = {
                "path": fpath,
                "name": wep.group(1),
                "cfg": parse_cfg(f.readlines())
            }
            datum["xhair"] = datum["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"].split("/")[-1]
            data.append(datum)

    return data


def sort_entries(entries, sort_arr):
    which = sort_arr[0] == 0
    direction = sort_arr[1 if which else 0] < 0

    if not which:
        if options["weapon_display_type"]:
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
# If display by category is enabled, sort by Class index, then alphabetically
# If display by weapon class is enabled, simply sort alphabetically
def build_entries():
    weps = get_weapons()

    entries = [x for x in weps if x["name"] in weapon_associations]

    sort_entries(entries, [1, 0])

    return entries

# Search through materials/vgui/replay/thumbnails for vtf files
# (arbitrarily choose vtf and discard vmts since both should be present for each xhair)


def get_crosshairs():
    xp = "{}/vgui/replay/thumbnails".format(options["materials_path"])

    files = [f for f in os.listdir(xp) if os.path.isfile(os.path.join(xp, f))]
    return [x[:-4] for x in list(filter(lambda x: x.endswith(".vtf"), files))]


def check_folders(spath, mpath):
    scripts_path = spath
    xhair_path = "{}/vgui/replay/thumbnails".format(mpath)

    return os.path.isdir(scripts_path) \
        and len(os.listdir(scripts_path)) > 0 \
        and os.path.isdir(xhair_path) \
        and len(os.listdir(xhair_path)) > 0


def persist_data(data):
    if not type(data) == dict:
        return

    with open(constants["data_dir"], "w") as f:
        f.write(json.dumps(data))


def clear_persisted_data():
    open(constants["data_dir"], "w").close()

    options["materials_path"] = constants["default_materials_path"]
    options["scripts_path"] = constants["default_scripts_path"]


def retrieve_persisted_data():
    data = {}

    try:
        with open(constants["data_dir"], "r") as f:
            data = json.loads(f.read())
    except:
        pass

    return data


def handle_frame_type():
    pd = retrieve_persisted_data()
    # Paths in persisted data are correct (these take precedence)
    p_check = len(pd) > 0 and check_folders(
        pd["scripts_path"], pd["materials_path"])
    # Paths relative to the executable are correct
    d_check = check_folders(options["scripts_path"], options["materials_path"])

    if p_check or d_check:
        if p_check:
            options["scripts_path"] = pd["scripts_path"]
            options["materials_path"] = pd["materials_path"]

        make_frame(True)
    else:
        make_frame(False)


def make_frame(type):
    if type:
        entries = build_entries()
        CrosshairFrame(None, "VTF Crosshair Changer", (850, 600), entries)
    else:
        DirPickerFrame(None, "Error", (600, 200), ui["error_msg"])


if __name__ == "__main__":
    a = wx.App()
    handle_frame_type()
    a.MainLoop()
