from gc import isenabled
import sys
import os
import pickle
import datetime
from urllib.request import AbstractDigestAuthHandler
from xml.dom.pulldom import SAX2DOM

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from constants.associations import weapon_associations, reverse_associations
from constants.ui import *
from constants.constants import DATA_DIR, ICON_APP, APPLY_SELECTION, APPLY_CLASS, APPLY_SLOT, APPLY_ALL, BULK_APPLY_OPTIONS

from utils import change_xhair_in_cfg, prepare_entries, get_xhair_from_cfg, get_xhairs, write_cfg
from parser import CfgParser

from app.controls import Controls
from app.logs import Logs
from app.table import Table
from app.top_bar import TopBar




class CrosshairAppOptions:
  def __init__(self):
    self.cfg_path = ''
    self.backup_scripts = True
    self.weapon_display_type = False
    self.custom_apply_groups = {}

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

  def __init__(self):
    super().__init__([])

    self.window = QMainWindow()
    self.window.setWindowTitle('VTF Crosshair Changer')
    self.window.setGeometry(100, 100, 800, 400)
    self.window.move(60, 15)
    self.window.setWindowIcon(QIcon(ICON_APP))

    self.wid = QWidget(self.window)
    self.window.setCentralWidget(self.wid)

    self.xhairs = []
    self.selected_items = []
    self.logs = []
    self.history = CrosshairHistory()

    self.options = CrosshairAppOptions()
    self.retrieve_options()
    self.associations = reverse_associations if self.options.weapon_display_type else weapon_associations

    if (not self.options.cfg_path or len(self.options.cfg_path) == 0):
      self.handle_path_select()

    self.xhairs = get_xhairs("{}/materials/vgui/replay/thumbnails".format(self.options.cfg_path))

    self.build_gui()
    self.parser = CfgParser()

    self.parse_cfgs()
    self.table.populate(self.parser.cfgs)

    self.OptionSignal.connect(self.on_option_changed)
    self.ApplySignal.connect(self.on_apply)
    self.WeaponSelectSignal.connect(self.on_weapon_selected)
    self.CrosshairChangeSignal.connect(self.on_xhair_selected)
    self.UndoRedoSignal.connect(self.on_undo_redo)
    self.LogSignal.connect(self.add_log)
    self.PathChangeSignal.connect(self.on_path_change)

    self.exec()
    self.write_options()

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

    for entry in self.entries:
      label = entry["name"] if not self.options.weapon_display_type else \
        "{}: {}".format(weapon_associations[entry["name"]]["class"], weapon_associations[entry["name"]]["display"])

      self.parser.cfgs[label] = self.parser.parse_cfg(entry["contents"])


  def retrieve_options(self):
    """ Retrieve and unpickle stored options from the user directory """
    data_path = os.path.join(DATA_DIR, 'data.txt')

    if os.path.exists(data_path):
      with open(data_path, "rb") as f:
        try:
          loaded = pickle.load(f)

          for k in loaded.__dict__.keys():
            setattr(self.options, k, getattr(loaded, k))

        except:
          f.close()


  def write_options(self):
    """ Pickle and store options to the user directory """
    data_path = os.path.join(DATA_DIR, 'data.txt')


    if os.path.exists(data_path):
      with open(data_path, "w") as f:
        f.close()

    with open(data_path, "wb") as f:
      pickle.dump(self.options, f)

  def add_log(self, log):
    self.logs.add_log(log)


  # --------- CALLBACKS ----------

  def on_option_changed(self, option, new_val):
    """ User has changed an option """

    if not hasattr(self.options, option):
      return

    if option == "weapon_display_type":
      self.associations = reverse_associations if new_val else weapon_associations
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
    self.table.populate(self.parser.cfgs)



  def on_apply(self, action_type, new_xhair):
    """ User has tried to apply a new crosshair to selected weapon(s) """
    changed = []

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
        if weapon not in self.parser.cfgs or \
          (action_type == APPLY_SELECTION and weapon not in self.associations):
          continue

        if action_type == APPLY_SELECTION:
          modify(weapon)
        elif action_type == APPLY_CLASS:
          cur_class = self.associations[weapon]["class"]
          filtered = list(filter(lambda x, check=cur_class : self.associations[x]["class"] == check, self.associations.keys()))

          for wep in filtered:
            modify(wep)
        elif action_type == APPLY_SLOT:
          cur_slot = self.associations[weapon]["slot"]
          filtered = list(filter(lambda x, check=cur_slot : self.associations[x]["slot"] == check, self.associations.keys()))

          for wep in filtered:
            modify(wep)

        elif action_type == APPLY_ALL:
          for wep in self.associations.keys():
            modify(wep)

    log = ""

    if len(changed) == len(self.parser.cfgs):
      log = "Changed all weapons to {}".format(new_xhair)
    else:
      log = "Changed <span style=\"font-style: italic;\">{}</span> to {}".format(", ".join([x[0] for x in changed]), new_xhair)

    self.add_log(log)
    self.history.add_item([x[0] for x in changed], [x[1] for x in changed], [new_xhair] * len(changed), log)
    self.table.populate(self.parser.cfgs)
    self.WeaponSelectSignal.emit([])


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
    item = self.history.undo() if undo else self.history.redo()

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
    self.table.populate(self.parser.cfgs)

  def on_path_change(self):
    self.options.cfg_path = ''
    self.handle_path_select()
    self.xhairs = get_xhairs("{}/materials/vgui/replay/thumbnails".format(self.options.cfg_path))
    self.parse_cfgs()
    self.table.populate(self.parser.cfgs)
    self.top_bar.path.setText(self.options.cfg_path)
    self.add_log('Changed path to {}'.format(self.options.cfg_path))




def show_app():
  CrosshairApp()
