import re
import wx
import os 
import shutil
import datetime
import functools
import platform
from associations import *
from collections import OrderedDict

def gen_hash():
	import hashlib
	import time

	hash = hashlib.sha1()
	hash.update(str(time.time()).encode("utf-8"))

	return hash.hexdigest()[:15]

options = {
	"logs_path": "xhs_logs.txt",
	"xhair_path": "materials/vgui/replay/thumbnails/",
	"scripts_path": "scripts/",
	"backup_scripts": True,
	"backup_folder_path": "scripts/backup_{}".format(gen_hash()),
	"weapon_display_type": False,
}

ui = {
	"btn_apply": "Apply",
	"btn_apply_class": "Apply to all weapons of this class",
	"btn_apply_slot": "Apply to all weapons of this slot",
	"btn_apply_all": "Apply to all weapons",
	"chk_display_toggle": "Toggle display type",
	"chk_backup_scripts": "Backup scripts before modifying",
	"error_msg": "Either scripts or thumbnails folder is missing\nCheck that, relative to this" + \
		" file, the following paths exist and aren't empty:\n{}\n{}".format(options["scripts_path"], options["xhair_path"])
}

# Main GUI frame
class CrosshairFrame(wx.Frame):
	def __init__(self, parent, title, size, entries):
		super(CrosshairFrame, self).__init__(parent, title = title, size = size, style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
		# Setup
		self.SetIcon(wx.Icon("xhair.ico"))

		self.entries = entries
		self.cur_entry = {}
		self.cur_xhair = ""
		self.xhairs = get_crosshairs()

		self.SetMaxSize(size)
		self.SetMinSize(size)


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
		self.list_box = wx.ListBox(self.main_panel, size = (300,-1), choices = [], style = wx.LB_SINGLE)
		self.list_box.SetFont(wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.NORMAL, wx.NORMAL))
		self.Bind(wx.EVT_LISTBOX, self.on_list_box, self.list_box)
		self.populate_list()

		# Top-right weapon info text panel 
		self.text = wx.TextCtrl(self.main_panel, style = wx.TE_MULTILINE | wx.TE_READONLY)
		self.text.Bind(wx.EVT_KEY_DOWN, self.disable_textctrl_input)
		self.text.SetFont(wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.NORMAL, wx.NORMAL))

		# Actions in right panel under info (xhair select, buttons)
		self.xhair_choice = wx.Choice(self.main_panel, choices = self.xhairs)
		self.apply_button = wx.Button(self.main_panel)
		self.dup_class_button = wx.Button(self.main_panel)
		self.dup_slot_button = wx.Button(self.main_panel)
		self.dup_all_button = wx.Button(self.main_panel)

		self.apply_button.SetLabel(ui["btn_apply"])
		self.dup_class_button.SetLabel(ui["btn_apply_class"])
		self.dup_slot_button.SetLabel(ui["btn_apply_slot"])
		self.dup_all_button.SetLabel(ui["btn_apply_all"])

		self.apply_button.Bind(wx.EVT_BUTTON, self.button_clicked)
		self.dup_class_button.Bind(wx.EVT_BUTTON, self.button_clicked)
		self.dup_slot_button.Bind(wx.EVT_BUTTON, self.button_clicked)
		self.dup_all_button.Bind(wx.EVT_BUTTON, self.button_clicked)

		box_buttons.Add(self.xhair_choice)
		box_buttons.Add(self.apply_button)
		box_buttons.Add(self.dup_class_button)
		box_buttons.Add(self.dup_slot_button)
		box_buttons.Add(self.dup_all_button)

		self.xhair_preview = wx.Panel(self.main_panel)
		self.draw_crosshair()

		box_controls.Add(box_buttons, wx.SizerFlags().Expand().Proportion(50))
		box_controls.Add(self.xhair_preview,  wx.SizerFlags().Expand().Proportion(50))

		box_weapon_info.Add(self.text, wx.SizerFlags().Expand().Proportion(50))
		box_weapon_info.Add(box_controls, wx.SizerFlags().Expand().Proportion(50))

		



		box_weapon.Add(self.list_box, wx.SizerFlags().Expand().Proportion(50))
		box_weapon.Add(box_weapon_info, wx.SizerFlags().Expand().Proportion(50))
		

		# Bottom-left logging panel
		self.logger = wx.TextCtrl(self.main_panel, style = wx.TE_MULTILINE | wx.TE_READONLY)
		self.logger.AppendText("LOGS:\n")
		self.logger.SetFont(wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.NORMAL, wx.BOLD))
		self.logger.Bind(wx.EVT_KEY_DOWN, self.disable_textctrl_input)

		self.logs = []

		# Bottom-right options controls
		self.checkbox_display_type = wx.CheckBox(self.main_panel, label=ui["chk_display_toggle"])
		self.checkbox_backup = wx.CheckBox(self.main_panel, label=ui["chk_backup_scripts"])

		self.checkbox_display_type.SetValue(options["weapon_display_type"])
		self.checkbox_backup.SetValue(options["backup_scripts"])

		self.checkbox_display_type.Bind(wx.EVT_CHECKBOX, self.checkbox_clicked)
		self.checkbox_backup.Bind(wx.EVT_CHECKBOX, self.checkbox_clicked)


		box_opts.Add(self.checkbox_display_type)
		box_opts.Add(self.checkbox_backup)

		box_bottom.Add(self.logger, wx.SizerFlags().Expand().Proportion(70))
		box_bottom.Add(box_opts, wx.SizerFlags().Expand().Proportion(30))

		box_main.Add(box_weapon, wx.SizerFlags().Expand().Proportion(70))
		box_main.Add(box_bottom, wx.SizerFlags().Expand().Proportion(30).Border(wx.TOP, 10))

		self.main_panel.SetSizer(box_main)
		self.main_panel.Fit()

		self.Centre()
		self.Show(True)

		self.toggle_controls(False)


	### Logs
	
	# Add a log with a timestamp and show in logger
	def logs_add(self, item):
		now = datetime.datetime.now()
		time = [now.hour, now.minute, now.second]

		def pad(n):
			out = str(n)
			return "0" + out if len(out) == 1 else out

		self.logs.append([time, item])
		self.logger.AppendText("[{}:{}:{}] {}\n".format(pad(time[0]), pad(time[1]), pad(time[2]), item))
	
	# Clear logs
	def logs_clear(self):
		self.logs = []
		self.logger.SetValue("LOGS:\n")
	
	# Write logs to file (unused)
	def logs_write(self):
		with open(options["logs_path"], "w+") as f:
			f.write("\n".join(map(lambda x: "[{}:{}:{}] {}\n".format(x[0][0], x[0][1], x[0][2], x[1]), self.logs)))
	


	def disable_textctrl_input(self, event):
		event.Skip()

	# Toggle controls depending on if a list box option is selected
	def toggle_controls(self, on):
		if on:
			self.xhair_choice.Enable()
			self.apply_button.Enable()
			self.dup_class_button.Enable()
			self.dup_slot_button.Enable()
		else:
			self.xhair_choice.Disable()
			self.apply_button.Disable()
			self.dup_class_button.Disable()
			self.dup_slot_button.Disable()

	def draw_crosshair(self):
		# VTFLib only works on Windows
		#if platform.system() != "Windows":
		#	return

		img = wx.Image("xhair.ico").ConvertToBitmap()
		self.xhair_preview = wx.StaticBitmap(self.main_panel, -1, img, (10, 5), (16, 16))

	# Populate list box with weapon 
	def populate_list(self):
		self.list_box.Clear()

		# Get the longest label so that the (crosshair) display can be positioned correctly
		label_len = lambda x: len(x["name"] if options["weapon_display_type"] \
			 else "{}: {}".format(weapon_associations[x["name"]]["class"], weapon_associations[x["name"]]["display"]))
		longest = label_len(functools.reduce(lambda x,y: (x if label_len(x) > label_len(y) else y), self.entries))

		for x in self.entries:
			item_xhair = x["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"].split("/")[-1]

			if options["weapon_display_type"]:
				label = x["name"]
				self.list_box.Append("{}{}({})".format(label, ' ' * (longest - len(label) + 3), item_xhair))
			else:
				item_name = weapon_associations[x["name"]]["class"]
				item_display = weapon_associations[x["name"]]["display"]
				label = "{}: {}".format(item_name, item_display)

				self.list_box.Append("{}{}({})".format(label, ' ' * (longest - len(label) + 3), item_xhair))

		self.list_box.EnsureVisible(0)

	def backup_scripts(self):
		if os.path.isdir(options["backup_folder_path"]):
			return

		os.mkdir(options["backup_folder_path"])
		files = [f for f in os.listdir(options["scripts_path"]) if os.path.isfile(os.path.join(options["scripts_path"], f))]
		re_weapon = "^(tf_weapon_[a-zA-Z_]+)\.txt$"

		for file in files:
			if not re.search(re_weapon, file):
				continue
			
			shutil.copyfile("{}/{}".format(options["scripts_path"], file), "{}/{}".format(options["backup_folder_path"], file))
			self.logs_add("Backed up {} to folder /{}/".format(file, options["backup_folder_path"]))


	def button_clicked(self, event):
		label = event.GetEventObject().GetLabel()

		if len(self.cur_entry) == 0:
			return

		cur_xhair = self.xhair_choice.GetString(self.xhair_choice.GetSelection())


		def change_entry(entry):
			fname = entry["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"]
			old_xhair = fname.split("/")[-1]

			if old_xhair == cur_xhair:
				self.logs_add("Skipped {} (was already {})".format(entry["name"], old_xhair))
			else:
				entry["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"] = "/".join(fname.split("/")[:-1]) + "/" + cur_xhair
				out = reconstruct_cfg(entry["cfg"])
				write_cfg(entry["path"], out)
				self.logs_add("{} changed from {} to {}".format(entry["name"], old_xhair, cur_xhair))


		if options["backup_scripts"]:
			self.backup_scripts()

		if label == ui["btn_apply"]:
			change_entry(self.cur_entry)
		elif label == ui["btn_apply_class"]:
			class_name = weapon_associations[self.cur_entry["name"]]["class"]
			included_names = { k:v for (k,v) in weapon_associations.items() if v["class"] == class_name }.keys()
			included_entries = filter(lambda x: x["name"] in included_names, self.entries)

			for entry in included_entries:
				change_entry(entry)
		elif label == ui["btn_apply_slot"]:
			slot = weapon_associations[self.cur_entry["name"]]["slot"]
			included_names = { k:v for (k,v) in weapon_associations.items() if v["slot"] == slot }.keys()
			included_entries = filter(lambda x: x["name"] in included_names, self.entries)

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

	def on_list_box(self, event):
		entry = self.entries[event.GetSelection()]
		asc = weapon_associations[entry["name"]]

		def addText(text, color):
			self.text.SetDefaultStyle(wx.TextAttr(color))
			self.text.AppendText(text)

		self.text.SetValue("")
		addText("Class: ", wx.BLUE)
		addText("{}\n".format(asc["class"]), wx.BLACK)
		addText("Weapon Class: ", wx.BLUE)
		addText("{}\n".format(entry["name"]), wx.BLACK)
		addText("Category: ", wx.BLUE)
		addText("{}\n\n".format(asc["display"]), wx.BLACK)
		addText("Affected Weapons:\n", wx.BLUE)
		for item in asc["all"]:
			addText("{}\n".format(item), wx.BLACK)

		self.cur_entry = list(filter(lambda x: x["name"] == entry["name"], self.entries))[0]
		cur_xhair = self.cur_entry["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"].split("/")[-1]

		self.xhair_choice.SetSelection(self.xhairs.index(cur_xhair))
		self.toggle_controls(True)

# wxPython popup frame to show when one of the two necessary folders is not present
class ErrorFrame(wx.Frame):
    def __init__(self, parent, title, size, errtext):
        super(ErrorFrame, self).__init__(parent, title = title, size = size)
        self.SetMinSize(size)

        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.VERTICAL)

        self.errortext = wx.StaticText(panel, style = wx.ALIGN_CENTRE_HORIZONTAL | wx.TE_MULTILINE)
        self.errortext.SetLabel(errtext)
        self.errortext.SetForegroundColour((255,0,0))
        font = wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.errortext.SetFont(font)

        self.closebutton = wx.Button(panel, style = wx.ALIGN_CENTRE_HORIZONTAL)
        self.closebutton.SetLabel("Close")
        self.closebutton.Bind(wx.EVT_BUTTON, self.closeClick)
        box.Add(self.errortext, wx.EXPAND, wx.EXPAND)
        box.Add(self.closebutton, 0, wx.EXPAND)

        panel.SetSizer(box)
        panel.Fit()
        self.Centre()
        self.Show(True)

    def closeClick(self, event):
        self.Close()

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
def get_weapons():
	files = [f for f in os.listdir(options["scripts_path"]) if os.path.isfile(os.path.join(options["scripts_path"], f))]
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
			data.append(datum)

	return data

# Prepare entries for display by Filter out any extra files and sorting
# If display by category is enabled, sort by Class index, then alphabetically
# If display by weapon class is enabled, simply sort alphabetically
def build_entries():
	weps = get_weapons()

	entries = [x for x in weps if x["name"] in weapon_associations]

	if options["weapon_display_type"]:
		entries.sort(key = lambda x: x["name"])
	else:
		order = {"Scout": 1, "Soldier": 2, "Pyro": 3, "Demoman": 4, "Heavy": 5, "Engineer": 6, "Medic": 7, "Sniper": 8, "Spy": 9}

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

		entries.sort(key = sort_value)
	return entries

# Search through materials/vgui/replay/thumbnails for vtf files 
# (arbitrarily choose vtf and discard vmts since both should be present for each xhair)
def get_crosshairs():
	files = [f for f in os.listdir(options["xhair_path"]) if os.path.isfile(os.path.join(options["xhair_path"], f))]
	return [x[:-4] for x in list(filter(lambda x: x.endswith(".vtf"), files))]


if __name__ == "__main__":
	a = wx.App()

	if not os.path.isdir(options["scripts_path"]) or \
		not os.path.isdir(options["xhair_path"]) or \
		len(os.listdir(options["scripts_path"])) == 0 or \
		len(os.listdir(options["xhair_path"])) == 0:
		print(os.listdir(options["scripts_path"]))
		print(os.listdir(options["xhair_path"]))

		ErrorFrame(None, "Error", (600, 150), ui["error_msg"])
	else:
		entries = build_entries()
		CrosshairFrame(None, "VTF Crosshair Changer", (850, 600), entries)

	a.MainLoop()