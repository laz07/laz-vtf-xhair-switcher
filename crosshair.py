import re
import wx
from associations import *
from collections import OrderedDict 
from os import listdir
from os.path import isfile, join


def parse_cfg(lines):
	data_map = OrderedDict()

	if len(lines) < 2:
		return {}

	re_header = "\s*(\"?.+\"?)\s*"
	re_data = "\s*\"(.+)\"\s*\"(.+)\"\s*"
	re_bracket_open = "\s*{\s*"
	re_bracket_close = "\s*}\s*"
	re_comment = "\s*\/\/(.+)"

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

		# Insert data into map
		if data:
			data_map[data.group(1)] = data.group(2)

		# Insert comment into map with special #comment_0 key format
		elif cmt:
			data_map["#comment_{}".format(cmts)] = cmt.group(1)
			cmts += 1

		# Found a nested map structure, recurse and increment "it" past the sub map	
		elif it < len(lines) - 2 and re.search(re_header, ln) and re.search(re_bracket_open, lines[it+1]):
			submap = get_submap(it+2)

			data_map[re.search(re_header, ln).group(1)] = parse_cfg(submap)
			it += len(submap) + 1
	
		it += 1

	return data_map


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
				lines.append("{}\\\\ {}\n".format('\t'*indent, value))
			# Else insert the data in the correct format
			else:
				lines.append("{}\"{}\"\t\"{}\"\n".format('\t'*indent, key, value))

	return lines		

def write_cfg(path, lines):
	open(path, 'w').close()
	with open(path, "a") as f:
		for line in lines:
			f.write(line)


class CrosshairFrame(wx.Frame):
	def toggleControls(self, on):
		if on:
			self.combo.Enable()
			self.apply_button.Enable()
			self.dup_class_button.Enable()
			self.dup_slot_button.Enable()
		else:
			self.combo.Disable()
			self.apply_button.Disable()
			self.dup_class_button.Disable()
			self.dup_slot_button.Disable()

	def populateList(self):
		self.list_box.Clear()

		for x in entries:
			item_name = weapon_associations[x["name"]]["class"]
			item_display = weapon_associations[x["name"]]["display"]

			item_xhair = list(filter(lambda y: x["name"] == y["name"], self.entries)) \
				[0]["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"].split("/")[-1]

			self.list_box.Append("{}: {}     ({})".format(item_name, item_display, item_xhair))

		
	def __init__(self, parent, title, size, entries):
		super(CrosshairFrame, self).__init__(parent, title = title, size = size)

		self.SetIcon(wx.Icon("xhair.ico"))

		self.entries = entries
		self.cur_entry = {}
		self.cur_xhair = ""
		self.xhairs = get_crosshairs()

		self.SetMinSize((600, 300))


		panel = wx.Panel(self)
		box = wx.BoxSizer(wx.HORIZONTAL)

		self.text = wx.TextCtrl(panel, style = wx.TE_MULTILINE)

		self.combo = wx.ComboBox(panel, style = wx.CB_DROPDOWN, choices = self.xhairs)

		self.apply_button = wx.Button(panel)
		self.apply_button.SetLabel("Apply")
		self.apply_button.Bind(wx.EVT_BUTTON, self.OnClicked)

		self.dup_class_button = wx.Button(panel)
		self.dup_class_button.SetLabel("Apply to all weapons of this class")
		self.dup_class_button.Bind(wx.EVT_BUTTON, self.OnClicked)

		self.dup_slot_button = wx.Button(panel)
		self.dup_slot_button.SetLabel("Apply to all weapons of this slot")
		self.dup_slot_button.Bind(wx.EVT_BUTTON, self.OnClicked)

		self.dup_all_button = wx.Button(panel)
		self.dup_all_button.SetLabel("Apply to all weapons")
		self.dup_all_button.Bind(wx.EVT_BUTTON, self.OnClicked)

		info_container_sizer = wx.BoxSizer(wx.VERTICAL)
		info_container_sizer.Add(self.text, wx.EXPAND, wx.EXPAND)
		info_container_sizer.Add(self.combo)

		info_container_sizer.Add(self.apply_button)
		info_container_sizer.Add(self.dup_class_button)
		info_container_sizer.Add(self.dup_slot_button)
		info_container_sizer.Add(self.dup_all_button)

		
		self.list_box = wx.ListBox(panel, size = (300,-1), choices = [], style = wx.LB_SINGLE)
		self.populateList()

		box.Add(self.list_box, 0, wx.EXPAND) 
		box.Add(info_container_sizer, 1, wx.EXPAND) 

		panel.SetSizer(box) 
		panel.Fit() 

		self.Centre() 
		self.Bind(wx.EVT_LISTBOX, self.onListBox, self.list_box) 
		self.Show(True)  

		self.toggleControls(False)

	def OnClicked(self, event):
		label = event.GetEventObject().GetLabel()

		if len(self.cur_entry) == 0:
			return

		cur_xhair = self.combo.GetValue()


		if label == "Apply":
			fname = self.cur_entry["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"]
			fname = "/".join(fname.split("/")[:-1]) + "/" + cur_xhair
			self.cur_entry["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"] = fname

			out = reconstruct_cfg(self.cur_entry["cfg"])
			write_cfg(self.cur_entry["path"], out)
			self.populateList()

		elif label == "Apply to all weapons of this class":
			class_name = weapon_associations[self.cur_entry["name"]]["class"]
			included_names = { k:v for (k,v) in weapon_associations.items() if v["class"] == class_name }.keys()
			included_entries = filter(lambda x: x["name"] in included_names, self.entries)

			for entry in included_entries:
				fname = entry["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"]
				fname = "/".join(fname.split("/")[:-1]) + "/" + cur_xhair
				entry["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"] = fname

				out = reconstruct_cfg(entry["cfg"])
				write_cfg(entry["path"], out)

			self.populateList()
		elif label == "Apply to all weapons of this slot":
			slot = weapon_associations[self.cur_entry["name"]]["slot"]
			included_names = { k:v for (k,v) in weapon_associations.items() if v["slot"] == slot }.keys()
			included_entries = filter(lambda x: x["name"] in included_names, self.entries)

			for entry in included_entries:
				fname = entry["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"]
				fname = "/".join(fname.split("/")[:-1]) + "/" + cur_xhair
				entry["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"] = fname

				out = reconstruct_cfg(entry["cfg"])
				write_cfg(entry["path"], out)

			self.populateList()

		elif label == "Apply to all weapons":
			for entry in self.entries:
				fname = entry["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"]
				fname = "/".join(fname.split("/")[:-1]) + "/" + cur_xhair
				entry["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"] = fname

				out = reconstruct_cfg(entry["cfg"])
				write_cfg(entry["path"], out)

			self.populateList()


		
	def onListBox(self, event): 
		key = re.search("(.+)(\s{5})+\(.+\)", event.GetEventObject().GetStringSelection()).group(1)
		data = reverse_associations[key]

		self.text.SetValue("")
		self.text.SetDefaultStyle(wx.TextAttr(wx.BLUE))
		self.text.AppendText("Class: ")
		self.text.SetDefaultStyle(wx.TextAttr(wx.BLACK))
		self.text.AppendText("{}\n".format(data["class"]))
		self.text.SetDefaultStyle(wx.TextAttr(wx.BLUE))
		self.text.AppendText("Weapon Class: ")
		self.text.SetDefaultStyle(wx.TextAttr(wx.BLACK))
		self.text.AppendText("{}\n\n".format(data["name"]))

		self.text.AppendText("Affected Weapons:\n")
		for item in data["all"]:
			self.text.AppendText("{}\n".format(item))

		self.cur_entry = list(filter(lambda x: x["name"] == data["name"], self.entries))[0]
		cur_xhair = self.cur_entry["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"].split("/")[-1]

		self.combo.SetSelection(self.xhairs.index(cur_xhair))
		self.toggleControls(True)




def get_weapons():
	files = [f for f in listdir("scripts") if isfile(join("scripts", f))]
	re_weapon = "^(tf_weapon_[a-zA-Z_]+)\.txt$"

	data = []

	for fn in files:
		wep = re.search(re_weapon, fn)
		if not wep:
			continue

		fpath = "scripts/{}".format(fn)
		with open(fpath, "r") as f:
			datum = {
				"path": fpath,
				"name": wep.group(1),
				"cfg": parse_cfg(f.readlines())
			}
			data.append(datum)

	return data

def build_entries():
	weps = get_weapons()

	order = {"Scout": 1, "Soldier": 2, "Pyro": 3, "Demoman": 4, "Heavy": 5, "Engineer": 6, "Medic": 7, "Sniper": 8, "Spy": 9}

	entries = [x for x in weps if x["name"] in weapon_associations]

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

def get_crosshairs():
	files = [f for f in listdir("materials/vgui/replay/thumbnails") if isfile(join("materials/vgui/replay/thumbnails", f))]
	return [x[:-4] for x in list(filter(lambda x: x.endswith(".vtf"), files))]


if __name__ == "__main__":
	entries = build_entries()

	a = wx.App()
	CrosshairFrame(None, "VTF Crosshair Changer", (600, 500), entries)
	a.MainLoop()