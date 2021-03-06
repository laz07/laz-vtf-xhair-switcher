import sys
import os
import pickle
import re
import shutil

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from constants.associations import weapon_associations
from constants.regex import RE_WEAPON
from constants.ui import PATHSELECT_INVALID_DIALOG_TEXT, PATHSELECT_INVALID_DIALOG_INFO_TEXT, \
  PATHSELECT_INVALID_DIALOG_TITLE
from constants.constants import DATA_FILE_PATH, ASSET_ICON_APP, ASSET_SAMPLE_SCRIPTS, APPLY_SELECTION,\
  APPLY_CLASS, APPLY_SLOT, APPLY_ALL, BULK_APPLY_OPTIONS, ITALIC_TAG, BOLD_TAG
from utils import get_association

from utils import change_xhair_in_cfg, prepare_entries, gen_hash, \
  get_xhair_from_cfg, get_xhairs, write_cfg, format_path_by_os, \
  resource_path, initialize_local_storage
from parser import CfgParser

from app.controls import Controls
from app.logs import Logs
from app.table import Table
from app.top_bar import TopBar
from app.repair_dialog import RepairDialog





class CrosshairAppOptions:
  def __init__(self):
    self.cfg_path = ''
    self.backup_scripts = False
    self.weapon_display_type = False
    self.custom_apply_groups = {}
    self.history = CrosshairHistory()

class CrosshairHistory:
  def __init__(self):
    self.undo_stack = []
    self.redo_stack = []

  def add_item(self, weapons_list, previous_list, current_list, log="Last action"):
    self.undo_stack.append({
      "weapons_list": weapons_list,
      "previous_list": previous_list,
      "current_list": current_list,
      "log": log
    })

    self.redo_stack = []

  def undo(self):
    if len(self.undo_stack) == 0:
      return None

    last_action = self.undo_stack.pop()
    self.redo_stack.append(last_action)

    return last_action

  def redo(self):
    if len(self.redo_stack) == 0:
      return None

    last_undid = self.redo_stack.pop()
    self.undo_stack.append(last_undid)

    return last_undid


class CrosshairApp(QApplication):
  OptionSignal = pyqtSignal(str, object)
  ApplySignal = pyqtSignal(str, str)
  WeaponSelectSignal = pyqtSignal(list)
  CrosshairChangeSignal = pyqtSignal(str)
  UndoRedoSignal = pyqtSignal(bool)
  LogSignal = pyqtSignal(str)
  PathChangeSignal = pyqtSignal()
  RepairScriptsSignal = pyqtSignal()

  def __init__(self):
    super().__init__([])

    self.window = QMainWindow()
    self.window.setWindowTitle('VTF Crosshair Changer')
    self.window.setGeometry(100, 100, 800, 400)
    self.window.move(60, 15)
    self.window.setWindowIcon(QIcon(resource_path(ASSET_ICON_APP)))

    self.wid = QWidget(self.window)
    self.window.setCentralWidget(self.wid)

    self.xhairs = []
    self.selected_items = []
    self.logs = []

    self.backup_hash = gen_hash()

    self.options = CrosshairAppOptions()
    self.retrieve_options()

    if (not self.options.cfg_path or len(self.options.cfg_path) == 0):
      self.handle_path_select()

    self.build_gui()
    self.parser = CfgParser()

    self.initialize()

    self.OptionSignal.connect(self.on_option_changed)
    self.ApplySignal.connect(self.on_apply)
    self.WeaponSelectSignal.connect(self.on_weapon_selected)
    self.CrosshairChangeSignal.connect(self.on_xhair_selected)
    self.UndoRedoSignal.connect(self.on_undo_redo)
    self.LogSignal.connect(self.add_log)
    self.PathChangeSignal.connect(self.on_path_change)
    self.RepairScriptsSignal.connect(self.repair_scripts)

    self.exec()
    self.write_options()

  def populate_table(self):
    self.table.populate(self.parser.cfgs, self.options.weapon_display_type)

  def initialize(self):
    self.xhairs = get_xhairs("{}/materials/vgui/replay/thumbnails".format(self.options.cfg_path))
    initialize_local_storage()
    self.parse_cfgs()
    self.controls.generate_previews(self.xhairs)
    self.controls.selector.combo.clear()
    self.controls.selector.combo.addItems([x["name"] for x in self.xhairs])
    self.populate_table()
    self.top_bar.path.setText(self.options.cfg_path)

  def build_gui(self):
    """ Create layout and instantiate all  portions of the UI """
    self.layout = QGridLayout()

    self.logs = Logs()
    self.top_bar = TopBar(self.options.cfg_path)
    self.controls = Controls(self.options, self.xhairs)
    self.table = Table()

    self.controls.generate_previews(self.xhairs)
    self.controls.selector.bulk_combo.addItems(self.options.custom_apply_groups)

    self.layout.addLayout(self.top_bar, 0, 0, 1, 2)
    self.layout.addWidget(self.table, 1, 0)
    self.layout.addLayout(self.controls, 1, 1)
    self.layout.addWidget(self.logs, 2, 0, 1, 2)

    self.wid.setLayout(self.layout)
    self.window.show()


  def modify_weapon(self, weapon, xhair):
    """ Change the crosshair associated with a weapon in the relevant parsed config, then write to file """
    cfg = self.parser.cfgs[weapon]
    change_xhair_in_cfg(cfg, xhair)
    lines = self.parser.reconstruct_cfg(cfg)
    write_cfg(lines, self.options.cfg_path, weapon)
    self.parser.cfgs[weapon] = cfg

  def handle_path_select(self):
    """ Show config path selection dialog and update options with selected path """
    path = str(QFileDialog.getExistingDirectory(self.window, "Select Crosshair Folder"))

    invalid_path = not path or len(path) == 0 or \
      not os.path.isdir("{}/scripts".format(path)) or \
      not os.path.isdir("{}/materials/vgui/replay/thumbnails".format(path))

    if invalid_path:
      if not self.options.cfg_path:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText(PATHSELECT_INVALID_DIALOG_TEXT)
        msg.setInformativeText(PATHSELECT_INVALID_DIALOG_INFO_TEXT)
        msg.setWindowTitle(PATHSELECT_INVALID_DIALOG_TITLE)
        msg.setStandardButtons(QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Close)
        sel = msg.exec()

        if sel == QMessageBox.StandardButton.Retry:
          self.handle_path_select()
        else:
          sys.exit()
    else:
      self.options.cfg_path = path


  def parse_cfgs(self):
    """ Parse config files into internal OrderedDict representations """
    cfg_path = self.options.cfg_path

    if (not cfg_path or len(cfg_path) == 0):
      return

    self.entries = prepare_entries("{}/scripts".format(cfg_path))
    self.parser.cfgs = {}
    self.parser.invalid_scripts = []

    for entry in self.entries:
      label = entry["name"]
      parsed = self.parser.parse_cfg(entry["contents"])

      if self.parser.validate_cfg(parsed):
        self.parser.cfgs[label] = parsed
      else:
        self.parser.invalid_scripts.append(label)


  def retrieve_options(self):
    """ Retrieve and unpickle stored options from the user directory """
    if os.path.exists(DATA_FILE_PATH):
      with open(DATA_FILE_PATH, "rb") as f:
        try:
          loaded = pickle.load(f)

          for k in loaded.__dict__.keys():
            setattr(self.options, k, getattr(loaded, k))

        except:
          f.close()


  def write_options(self):
    """ Pickle and store options to the user directory """
    initialize_local_storage()

    if os.path.exists(DATA_FILE_PATH):
      with open(DATA_FILE_PATH, "w") as f:
        f.close()

    with open(DATA_FILE_PATH, "wb") as f:
      pickle.dump(self.options, f)


  def add_log(self, log):
    self.logs.add_log(log)


  def backup_scripts(self):
    scripts_path = os.path.join(self.options.cfg_path, "scripts")
    backup_path = os.path.join(scripts_path, "backup_{}".format(self.backup_hash))

    if os.path.isdir(backup_path):
      return

    os.mkdir(backup_path)

    files = [f for f in os.listdir(scripts_path) if os.path.isfile(os.path.join(scripts_path, f))]

    for file in files:
      if not re.search(RE_WEAPON, file):
          continue

      shutil.copyfile("{}/{}".format(scripts_path, file), "{}/{}".format(backup_path, file))
      self.add_log("Backed up {} to folder {}".format(ITALIC_TAG, ITALIC_TAG).format(file, format_path_by_os(backup_path)))

  def repair_scripts(self):
    weapons = RepairDialog.getWeaponsToRepair(self.wid, self.parser.invalid_scripts)

    if len(weapons) == 0:
      return

    sample_dir = resource_path(ASSET_SAMPLE_SCRIPTS)
    scripts_dir = os.path.join(self.options.cfg_path, "scripts")

    for weapon in weapons:
      sample_path = os.path.join(sample_dir, "{}.txt".format(weapon))
      scripts_path = os.path.join(scripts_dir, "{}.txt".format(weapon))

      if not os.path.exists(sample_path):
        continue

      shutil.copyfile(sample_path, scripts_path)

    self.add_log("Repaired scripts for {}".format(ITALIC_TAG).format(", ".join(weapons)))
    self.parse_cfgs()
    self.populate_table()


  # --------- CALLBACKS ----------

  def on_option_changed(self, option, new_val):
    """ User has changed an option """

    if not hasattr(self.options, option):
      return

    if option == "weapon_display_type":
      setattr(self.options, option, new_val)
    elif option == "custom_apply_groups":
      (name, weapons) = new_val

      if not weapons:
        self.options.custom_apply_groups.pop(name, None)
      else:
        self.options.custom_apply_groups[name] = weapons

      self.controls.selector.bulk_combo.clear()
      self.controls.selector.bulk_combo.addItems(BULK_APPLY_OPTIONS.keys())
      self.controls.selector.bulk_combo.addItems(self.options.custom_apply_groups)
    else:
      setattr(self.options, option, new_val)

    self.parse_cfgs()
    self.populate_table()



  def on_apply(self, action_type, new_xhair):
    """ User has tried to apply a new crosshair to selected weapon(s) """
    changed = []
    all_weapons = weapon_associations.keys()

    def modify(wep):
      if wep not in self.parser.cfgs:
        return

      nonlocal changed
      changed += [(wep, get_xhair_from_cfg(self.parser.cfgs[wep]) if wep in self.parser.cfgs else None)]
      self.modify_weapon(wep, new_xhair)

    if action_type in self.options.custom_apply_groups:
      for wep in self.options.custom_apply_groups[action_type]:
        modify(wep)
    else:
      for weapon in [x[0] for x in self.selected_items]:
        data = get_association(weapon)

        if not data or data["code"] not in self.parser.cfgs:
          continue

        if action_type == APPLY_SELECTION:
          modify(data["code"])

        elif action_type == APPLY_CLASS:
          cur_class = data["class"]
          filtered = list(filter(lambda x, check=cur_class : weapon_associations[x]["class"] == check, all_weapons))

          for wep in filtered:
            modify(wep)

        elif action_type == APPLY_SLOT:
          cur_slot = data["slot"]
          filtered = list(filter(lambda x, check=cur_slot : weapon_associations[x]["slot"] == check, all_weapons))

          for wep in filtered:
            modify(wep)

        elif action_type == APPLY_ALL:
          for wep in all_weapons:
            modify(wep)

    log = ""

    if len(changed) > 0:
      if len(changed) == len(self.parser.cfgs):
        log = "Changed all weapons to {}".format(BOLD_TAG).format(new_xhair)
      else:
        log = "Changed {} to {}".format(ITALIC_TAG, BOLD_TAG).format(", ".join([x[0] for x in changed]), new_xhair)

      self.add_log(log)
      if self.options.backup_scripts:
        self.backup_scripts()

      self.options.history.add_item([x[0] for x in changed], [x[1] for x in changed], [new_xhair] * len(changed), log)
      self.populate_table()


  def on_weapon_selected(self, selected_items):
    """ User has selected a weapon in the table """
    self.selected_items = list(zip(selected_items[::2], selected_items[1::2]))

    self.controls.update_xhair_preview(selected_items[1::2])
    self.controls.update_info(selected_items[::2])


  def on_xhair_selected(self, xhair):
    """ User has selected a crosshair, either through the table or the selector """
    self.controls.update_xhair_preview([xhair])


  def on_undo_redo(self, undo = True):
    """ User has clicked undo or redo """
    item = self.options.history.undo() if undo else self.options.history.redo()

    if not item:
      return

    weapons_list = item["weapons_list"]
    new_list = item["previous_list" if undo else "current_list"]
    log = item["log"]

    for i in range(len(weapons_list)):
      weapon = weapons_list[i]
      xhair = new_list[i]

      if weapon not in self.parser.cfgs:
        continue

      self.modify_weapon(weapon, xhair)

    self.add_log("{} `<span style=\"font-style: italic\">{}</span>`".format("Undid" if undo else "Redid", log))
    self.populate_table()

  def on_path_change(self):
    old_path = self.options.cfg_path

    self.handle_path_select()

    if old_path != self.options.cfg_path:
      self.initialize()
      self.add_log('Changed path to {}'.format(ITALIC_TAG).format(self.options.cfg_path))




def show_app():
  CrosshairApp()
