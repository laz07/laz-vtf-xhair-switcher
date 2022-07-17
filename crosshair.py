# VTF crosshair switcher, v1.2, by laz

import re
import wx
import wx.lib.mixins.listctrl
import os
import time
import shutil
import datetime
import functools
import platform
import json
from associations import *
from collections import OrderedDict


# generate a (probably) unique hash to append to the
# backup folders' names to give each folder a unique name
def gen_hash():
    import hashlib
    import time

    hash = hashlib.sha1()
    hash.update(str(time.time()).encode("utf-8"))

    return hash.hexdigest()[:15]


dd = os.path.expanduser('~/.tf2-crosshair-switcher/')
constants = {
    "defaults": {
        "folder_path": "",
        "backup_scripts": False,
        "weapon_display_type": False
    },
    "backup_folder_path": "{}/backup_" + gen_hash(),
    "window_size": (950, 600),
    "options_window_size": (500, 150),
    "min_window_size": (900, 500),
    "font_size": 8,
    "data_dir": dd,
    "data_file_path": "{}/.data.txt".format(dd),
    "logs_path": "xhs_logs.txt",
    "xhair_preview_path": "{}/preview/"  # Format with materials directory
}

options = constants["defaults"].copy()






##########################
#           UI           #
##########################

ui = {
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
    "add_custom_xhairs_msg": "Will add custom crosshairs to the available list of crosshairs in the dropdown. Ensure the folder you select contains two sub-folders:\n\n/crosshairs -- for the crosshair vtf/vmts\n/display -- for the crosshair display .pngs.\n\nNAMES MUST MATCH BETWEEN THESE TWO FOLDERS"
}

# use a global to track the last parsed file before exception
debug_lastfile = ""

# Main GUI frame
class CrosshairFrame(wx.Frame):

    def __init__(self, parent, title, size, entries):
        super(CrosshairFrame, self).__init__(parent, title=title, size=size, style=wx.DEFAULT_FRAME_STYLE)
        
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.SetIcon(wx.Icon("xhair.ico"))

        self.entries = entries
        self.cur_entries = []
        self.cur_xhair = ""
        self.xhairs = get_crosshairs()
        self.SetMinSize(constants["min_window_size"])


        # Main panel
        self.main_panel = wx.Panel(self)

        self.setup_menu_bar()
        self.setup_panels()
        self.init_log()

        self.Centre()
        self.Show(True)

        self.toggle_controls(False)

    def on_close(self, e):
        for child in self.GetChildren():
            child.Destroy()

        self.Destroy()


    def init_log(self):
        if os.path.isdir(get_scripts_path()):
            display_path = format_path_by_os(os.path.abspath(get_scripts_path()))
            self.logs_add("Scripts being read from {}".format(display_path))

        if os.path.isdir(get_xhairs_path()):
            display_path = format_path_by_os(os.path.abspath(get_xhairs_path()))
            self.logs_add("Crosshairs being read from {}".format(display_path))


    def setup_menu_bar(self):
        self.menu_bar = wx.MenuBar()
        file_menu = wx.Menu()

        file_open_item = file_menu.Append(wx.ID_OPEN, 'Open Folder', 'Open Crosshair Folder')
        file_opts_item = file_menu.Append(wx.ID_PROPERTIES, 'Options', 'Options')
        file_gen_xhairs_item = file_menu.Append(wx.Window.NewControlId(), 'Generate Config', 'Generate Sample xhair Config')
        file_add_xhairs_item = file_menu.Append(wx.Window.NewControlId(), 'Add Crosshair PNGs', 'Add a display PNG for a crosshair')

        file_quit_item = file_menu.Append(wx.ID_EXIT, 'Quit', 'Quit application')

        self.menu_bar.Append(file_menu, 'File')

        def change_folders_dialog(func):
            def _func(e, parent=None):
                folder_dialog = wx.DirDialog(self, "Choose a directory", style=wx.DD_DEFAULT_STYLE)

                folder_path = ""
                print(folder_dialog.GetChildren())

                status = folder_dialog.ShowModal()
                
                if parent is not None:
                    parent.Destroy()

                if status == wx.ID_OK:
                    folder_path = folder_dialog.GetPath()
                    folder_dialog.Destroy()
                    func(folder_path)
                    

            return _func


        def open_new_folder(path):
            options["folder_path"] = path
            persist_options()
            self.Destroy()
            make_frame()


        def generate_config(path):
            shutil.copytree("assets/sample-xhair-config/materials", "{}/materials".format(path))
            shutil.copytree("assets/sample-xhair-config/scripts", "{}/scripts".format(path))

            options["folder_path"] = path
            persist_options()

            self.Destroy()
            newframe = make_frame()

            newframe.logs_add("Generated sample config at {}".format(path))


        def add_custom_xhairs(path):
            options["addional_xhairs_path"] = path
            persist_options()

            self.Destroy()
            make_frame()


        self.Bind(wx.EVT_MENU, change_folders_dialog(open_new_folder), file_open_item)
        self.Bind(wx.EVT_MENU, lambda _: OptionsFrame(self, "Options", constants["options_window_size"]), file_opts_item)
        self.Bind(wx.EVT_MENU, lambda _: self.Close(), file_quit_item)

        def gen_xhairs_item_action(_):
            InfoFrame(
                self, 
                title="Generate Sample Crosshair Config", 
                size=constants["options_window_size"],
                info_text=ui["generate_config_msg"],
                btn_text="Select a folder",
                btn_func=change_folders_dialog(generate_config)
            )
        self.Bind(wx.EVT_MENU, gen_xhairs_item_action, file_gen_xhairs_item)


        def add_xhairs_item_action(_):
            XHairPNGFrame(
                self, 
                title="Add Crosshair PNGs", 
                size=(500, 215),
                xhairs=self.xhairs
            )
        self.Bind(wx.EVT_MENU, add_xhairs_item_action, file_add_xhairs_item)


        self.SetMenuBar(self.menu_bar)

    def setup_panels(self):
        
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

        # Initialize controls for top layout

        # Top-left weapon list panel
        self.weapon_list = FixedWidthListCtrl(self.main_panel, -1, size=(500, -1), style=wx.LC_REPORT)

        self.weapon_list.SetFont(wx.Font(constants["font_size"], wx.FONTFAMILY_TELETYPE, wx.NORMAL, wx.NORMAL))
        self.weapon_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_list_select)
        self.weapon_list.Bind(wx.EVT_LIST_COL_CLICK, self.col_click)
        self.weapon_list_sort = [1, 0]
        self.last_selection = 0

        self.populate_list()

        # Top-right weapon info text panel
        self.text = wx.TextCtrl(self.main_panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH)
        self.text.Bind(wx.EVT_KEY_DOWN, lambda e: e.Skip())
        self.text.SetFont(wx.Font(constants["font_size"], wx.FONTFAMILY_TELETYPE, wx.NORMAL, wx.NORMAL))

        # Actions in right panel under info (xhair select, buttons)
        self.xhair_choice = wx.Choice(self.main_panel, choices=self.xhairs)
        self.btn_apply = wx.Button(self.main_panel, label=ui["btn_apply"])
        self.btn_apply_class = wx.Button(self.main_panel, label=ui["btn_apply_class"])
        self.btn_apply_slot = wx.Button(self.main_panel, label=ui["btn_apply_slot"])
        self.btn_apply_all = wx.Button(self.main_panel, label=ui["btn_apply_all"])

        def xhair_chosen(evt):
            choice = self.xhair_choice.GetStringSelection()
            xhair_display_path = get_xhair_display_path(choice)

            if xhair_display_path is None:
                self.set_image("")
            else:
                self.set_image(xhair_display_path)

        self.xhair_choice.Bind(wx.EVT_CHOICE, xhair_chosen)
        self.btn_apply.Bind(wx.EVT_BUTTON, self.btn_apply_clicked)
        self.btn_apply_class.Bind(wx.EVT_BUTTON, self.btn_apply_clicked)
        self.btn_apply_slot.Bind(wx.EVT_BUTTON, self.btn_apply_clicked)
        self.btn_apply_all.Bind(wx.EVT_BUTTON, self.btn_apply_clicked)

        box_buttons.Add(self.xhair_choice, wx.SizerFlags().Border(wx.TOP, 10))
        box_buttons.Add(self.btn_apply)
        box_buttons.Add(self.btn_apply_class)
        box_buttons.Add(self.btn_apply_slot)
        box_buttons.Add(self.btn_apply_all)

        self.xhair_preview = wx.StaticBitmap(self.main_panel, -1)
        self.xhair_preview.SetBackgroundColour(wx.Colour(120, 120, 120))


        box_controls.Add(box_buttons, wx.SizerFlags().Expand().Proportion(50))
        box_controls.Add(self.xhair_preview, wx.SizerFlags().Expand().Proportion(50))

        box_weapon_info.Add(self.text, wx.SizerFlags().Expand().Proportion(50))
        box_weapon_info.Add(box_controls, wx.SizerFlags().Expand().Proportion(50))

        box_weapon.Add(self.weapon_list, wx.SizerFlags().Expand().Proportion(50).Border(wx.ALL, 10))
        box_weapon.Add(box_weapon_info, wx.SizerFlags().Expand().Proportion(50).Border(wx.ALL, 10))

        # Bottom-left logging panel
        self.logger = wx.TextCtrl(self.main_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.logger.AppendText("LOGS:\n")
        self.logger.SetFont(wx.Font(constants["font_size"], wx.FONTFAMILY_TELETYPE, wx.NORMAL, wx.BOLD))
        self.logger.Bind(wx.EVT_KEY_DOWN, lambda e: e.Skip())

        self.logs = []

        box_bottom.Add(self.logger, wx.SizerFlags().Expand().Proportion(100).Border(wx.ALL, 10))

        box_main.Add(box_weapon, wx.SizerFlags().Expand().Proportion(70))
        box_main.Add(box_bottom, wx.SizerFlags().Expand().Proportion(30).Border(wx.TOP, 10))

        self.main_panel.SetSizer(box_main)
        self.main_panel.Fit()



    def set_image(self, image):
        bitmap = wx.NullBitmap

        if os.path.exists(image):
            bitmap = wx.Bitmap(image)

        self.xhair_preview.SetBitmap(bitmap)
        self.main_panel.Layout()

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

    # Toggle controls depending on if a list box option is selected
    def toggle_controls(self, on):
        if on:
            self.xhair_choice.Enable()
            self.btn_apply.Enable()
            self.btn_apply_class.Enable()
            self.btn_apply_slot.Enable()
            self.btn_apply_all.Enable()
        else:
            self.xhair_choice.Disable()
            self.btn_apply.Disable()
            self.btn_apply_class.Disable()
            self.btn_apply_slot.Disable()
            self.btn_apply_all.Disable()


    # Populate list box with weapon
    def populate_list(self):
        sort_entries(self.entries, self.weapon_list_sort)

        self.weapon_list.ClearAll()
        self.weapon_list.InsertColumn(0, "Weapon", width=200)
        self.weapon_list.InsertColumn(1, "Crosshair", wx.LIST_FORMAT_RIGHT, width=200)

        for x in self.entries:
            label = x["name"] if options["weapon_display_type"] else "{}: {}".format(weapon_associations[x["name"]]["class"], weapon_associations[x["name"]]["display"])

            self.weapon_list.Append([label, x["xhair"]])

        self.weapon_list.EnsureVisible(self.last_selection)

    # copy all script files to the backup folder
    def backup_scripts(self):
        scripts_path = get_scripts_path()
        backup_path = constants["backup_folder_path"].format(scripts_path)

        if os.path.isdir(backup_path) or not os.path.isdir(scripts_path):
            return

        os.mkdir(backup_path)

        files = [f for f in os.listdir(scripts_path) if os.path.isfile(os.path.join(scripts_path, f))]
        re_weapon = "^(tf_weapon_[a-zA-Z_]+)\.txt$"

        for file in files:
            if not re.search(re_weapon, file):
                continue

            shutil.copyfile("{}/{}".format(scripts_path, file), "{}/{}".format(backup_path, file))
            self.logs_add("Backed up {} to folder {}".format(file, constants["backup_folder_path"].format(scripts_path)))

    # on-click for the 4 apply buttons
    def btn_apply_clicked(self, event):
        label = event.GetEventObject().GetLabel()

        if len(self.cur_entries) == 0:
            return

        cur_xhair = self.xhair_choice.GetString(self.xhair_choice.GetSelection())

        def change_entry(entry):
            fname = entry["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"]
            old_xhair = fname.split("/")[-1]

            if old_xhair == cur_xhair:
                self.logs_add("Skipped {} (was already {})".format(
                    entry["name"], old_xhair))
            else:
                entry["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"] = "/".join(fname.split("/")[:-1]) + "/" + cur_xhair
                entry["xhair"] = cur_xhair

                out = reconstruct_cfg(entry["cfg"])
                write_cfg(entry["path"], out)
                self.logs_add("{} changed from {} to {}".format(entry["name"], old_xhair, cur_xhair))

        if options["backup_scripts"]:
            self.backup_scripts()

        if label == ui["btn_apply"]:
            for entry in self.cur_entries:
                change_entry(entry)

        elif label == ui["btn_apply_class"]:
            # filter out weapons with different classes
            class_name = weapon_associations[self.cur_entries[0]["name"]]["class"]
            included_names = {k: v for (k, v) in weapon_associations.items() if v["class"] == class_name}.keys()
            included_entries = filter(lambda x: x["name"] in included_names, self.entries)

            for entry in included_entries:
                change_entry(entry)
        elif label == ui["btn_apply_slot"]:
            # filter out entries with different slots
            slot = weapon_associations[self.cur_entries[0]["name"]]["slot"]
            included_names = {k: v for (k, v) in weapon_associations.items() if v["slot"] == slot}.keys()
            included_entries = filter(lambda x: x["name"] in included_names, self.entries)

            for entry in included_entries:
                change_entry(entry)
        elif label == ui["btn_apply_all"]:
            for entry in self.entries:
                change_entry(entry)

        self.populate_list()

    def on_list_select(self, event):
        self.weapon_list.setResizeColumn(0)

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

            asc["class"] not in display["classes"] and display["classes"].append(asc["class"])
            display["weapons"].append(entry["name"])
            asc["display"] not in display["categories"] and display["categories"].append(asc["display"])

            for item in asc["all"]:
                item not in display["affected"] and display["affected"].append(item)

            self.cur_entries.append(list(filter(lambda x: x["name"] == entry["name"], self.entries))[0])
            cur_xhair = self.cur_entries[-1]["xhair"]

            self.xhair_choice.SetSelection(self.xhairs.index(cur_xhair))
            self.toggle_controls(True)

        def addText(text, color):
            self.text.SetDefaultStyle(wx.TextAttr(color))
            self.text.AppendText(text)

        self.text.SetValue("")

        if len(selected) == 1:
            xhair = self.entries[selected[0]]["xhair"]
            xhair_display_path = get_xhair_display_path(xhair)

            if xhair_display_path is None:
                self.set_image("")
            else:
                self.set_image(xhair_display_path)
        else:
            self.set_image("")

        if len(selected) > 1:
            addText("<multiple>\n", wx.BLACK)

        addText("Class{}: ".format("es" if len(display["classes"]) > 1 else ""), wx.BLUE)
        addText("{}\n\n".format(", ".join(display["classes"])), wx.BLACK)

        addText("Weapon Class{}: ".format("es" if len(display["weapons"]) > 1 else ""), wx.BLUE)
        addText("{}\n\n".format(", ".join(display["weapons"])), wx.BLACK)

        addText("Categor{}: ".format("ies" if len(display["categories"]) > 1 else "y"), wx.BLUE)
        addText("{}\n\n".format(", ".join(display["categories"])), wx.BLACK)

        addText("Slot: ", wx.BLUE)

        if len(selected) > 1:
            addText("<multiple>\n\n", wx.BLACK)
        else:
            addText("{}\n\n".format({1: "Primary", 2: "Secondary", 3: "Melee", 4: "PDA"}[weapon_associations[self.cur_entries[0]["name"]]["slot"]]), wx.BLACK)

        addText("Affected Weapons:\n", wx.BLUE)
        addText("\n".join(display["affected"]), wx.BLACK)

        if len(self.cur_entries) > 0:
            def entries_homogeneous(field):
                fil = filter(lambda x: weapon_associations[x["name"]][field] == weapon_associations[self.cur_entries[0]["name"]][field], self.cur_entries)
                return len(list(fil)) == len(self.cur_entries)

            if entries_homogeneous("class"):
                self.btn_apply_class.Enable()
            else:
                self.btn_apply_class.Disable()

            if entries_homogeneous("slot"):
                self.btn_apply_slot.Enable()
            else:
                self.btn_apply_slot.Disable()

            self.last_selection = selected[0]

        self.text.ScrollPages(-100) # hacky way to scroll to the top of the text control

    # column header on click
    def col_click(self, event):
        col = event.GetColumn()
        cur = self.weapon_list_sort[col]
        self.weapon_list_sort[col] = 1 if cur == 0 else cur * -1
        self.weapon_list_sort[1 if col == 0 else 0] = 0

        self.populate_list()

    def change_folders(self, event):
        self.Close()
        clear_persisted_options()
        handle_frame_type()




# mixin to ensure columns cannot be resized past the viewport
class FixedWidthListCtrl(wx.ListCtrl, wx.lib.mixins.listctrl.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        wx.lib.mixins.listctrl.ListCtrlAutoWidthMixin.__init__(self)
        self.setResizeColumn(0)

class InfoFrame(wx.Frame):
    def __init__(self, parent, title, size, info_text, btn_text, btn_func):
        super(InfoFrame, self).__init__(parent, title=title, size=size, style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
        self.parent = parent
        
        self.SetIcon(wx.Icon("xhair.ico"))
        self.SetMinSize(size)

        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.VERTICAL)

        text_info = wx.StaticText(panel, id=-1, label=info_text)
        text_info.Wrap(size[0] - 50)

        btn_action = wx.Button(panel, label=btn_text, size=(100, 30))
        btn_action.Bind(wx.EVT_BUTTON, lambda e: btn_func(e, self))

        box.Add(text_info, wx.SizerFlags().Center().Border(wx.ALL, 10))
        box.Add(btn_action, wx.SizerFlags().Center().Border(wx.ALL, 10))

        panel.SetSizerAndFit(box)

        self.Center()
        self.Show(True)
        

class OptionsFrame(wx.Frame):
    def __init__(self, parent, title, size):
        super(OptionsFrame, self).__init__(parent, title=title, size=size, style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP ^ wx.RESIZE_BORDER)

        self.parent = parent

        self.SetIcon(wx.Icon("xhair.ico"))
        self.SetMinSize(size)

        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.VERTICAL)

        close_btn = wx.Button(panel, label="Close", size=(100, 30))
        close_btn.Bind(wx.EVT_BUTTON, self.click_close)

        checkbox_display_type = wx.CheckBox(panel, label=ui["chk_display_toggle"])
        checkbox_backup = wx.CheckBox(panel, label=ui["chk_backup_scripts"])

        checkbox_display_type.SetValue(options["weapon_display_type"])
        checkbox_backup.SetValue(options["backup_scripts"])

        checkbox_display_type.Bind(wx.EVT_CHECKBOX, self.checkbox_clicked)
        checkbox_backup.Bind(wx.EVT_CHECKBOX, self.checkbox_clicked)

        box.Add(checkbox_display_type, wx.SizerFlags().Center().Border(wx.TOP, 10))
        box.Add(checkbox_backup, wx.SizerFlags().Center().Border(wx.TOP, 5))
        box.Add(close_btn, wx.SizerFlags().Center().Border(wx.ALL, 10))

        panel.SetSizerAndFit(box)

        self.Center()
        self.Show(True)


    def checkbox_clicked(self, event):
        checked = True if event.GetInt() == 1 else False
        label = event.GetEventObject().GetLabel()

        if label == ui["chk_display_toggle"]:
            options["weapon_display_type"] = checked
            self.parent.entries = prepare_entries()
            self.parent.populate_list()
        elif label == ui["chk_backup_scripts"]:
            options["backup_scripts"] = checked

        persist_options()


    def click_close(self, event):
        self.Close()

class XHairPNGFrame(wx.Frame):

    def copy_png(self, path, xhair):
        newpath = "{}/display/{}.png".format(constants["data_dir"], xhair)
        shutil.copyfile(path, newpath)

        self.parent.Destroy()
        self.Destroy()

        newframe = make_frame()
        newframe.logs_add.Add("{} copied to {}".format(path, os.path.abspath(newpath)))

    def __init__(self, parent, title, size, xhairs):
        super(XHairPNGFrame, self).__init__(parent, title=title, size=size, style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)

        self.SetIcon(wx.Icon("xhair.ico"))
        self.parent = parent

        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.VERTICAL)

        text_info = wx.StaticText(panel, id=-1, label="PNG will be copied to your user directory with the name of the crosshair")

        self.xhairs = xhairs
        extra_xhairs = self.find_extra_xhairs()
        choice_xhairs = wx.Choice(panel, choices=extra_xhairs)


        def open_file_dialog(_):
            with wx.FileDialog(self, "Choose PNG", wildcard="PNG files (*.png)|*.png", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
                if file_dialog.ShowModal() == wx.ID_CANCEL:
                    return
                
                path = file_dialog.GetPath()
                self.copy_png(path, choice_xhairs.GetString(choice_xhairs.GetSelection()))

        btn_pngfile = wx.Button(panel, label="Choose PNG")
        btn_pngfile.Bind(wx.EVT_BUTTON, open_file_dialog)
        
        box.Add(text_info, wx.SizerFlags().Center().Border(wx.TOP, 10))
        box.Add(choice_xhairs, wx.SizerFlags().Center().Border(wx.TOP, 5))
        box.Add(btn_pngfile, wx.SizerFlags().Center().Border(wx.TOP, 5))

        panel.SetSizerAndFit(box)

        self.Center()
        self.Show(True)

    def find_extra_xhairs(self):
        files = [f[:-4] for f in os.listdir('assets/display') if os.path.isfile(os.path.join('assets/display', f))]
        return [f for f in self.xhairs if f not in files]



#########################
#       Util funcs      #
#########################


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
    return "{}/scripts".format(options["folder_path"])

def get_xhairs_path():
    return "{}/materials/vgui/replay/thumbnails".format(options["folder_path"])

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
    with open(constants["data_file_path"], "w") as f:
        f.write(json.dumps(options))

def clear_persisted_options():
    global options
    open(constants["data_file_path"], "w").close()

    options = constants["defaults"].copy()

def retrieve_persisted_options():
    global options
    data = {}

    try:
        with open(constants["data_file_path"], "r") as f:
            data = json.loads(f.read())
    except:
        pass

    if len(data) == len(options):
        options = data



# Decide on which frame to show based on the user's saved settings and
# whether the relevant folders exist and aren't empty
def handle_frame_type():
    retrieve_persisted_options()
    # Paths in persisted data are correct (these take precedence)
    p_check = valid_xhair_folder(options["folder_path"])
    # Paths relative to the executable are correct
    d_check = valid_xhair_folder(constants["defaults"]["folder_path"])


    if p_check or d_check:
        if not p_check and d_check:
            options["folder_path"] = constants["defaults"]["folder_path"]
    
    make_frame()


def make_frame():
    entries = prepare_entries()
    return CrosshairFrame(None, "VTF Crosshair Changer", constants["window_size"], entries)

def initialize_local_storage():
    # Initialize local storage directory
    if not os.path.isdir(constants["data_dir"]):
        os.mkdir(constants["data_dir"])
    
    display_path = "{}/display".format(constants["data_dir"])
    if not os.path.isdir(display_path):
        os.mkdir(display_path)

def get_xhair_display_path(xhair):
    path1 = "assets/display/{}.png".format(xhair)
    path2 = "{}/display/{}.png".format(constants["data_dir"], xhair)

    if os.path.isfile(path2):
        return path2

    if os.path.isfile(path1):
        return path1

    return None

def format_path_by_os(path):
    is_windows = os.name == 'nt'
    delim = "\\" if is_windows else "/"

    return path.replace("\\", delim).replace("/", delim)


if __name__ == "__main__":
    initialize_local_storage()

    a = wx.App()
    handle_frame_type()
    a.MainLoop()
