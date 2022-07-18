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
from vtf2img import Parser
from math import floor

from app.constants.associations import weapon_associations
from app.constants.ui import *
from app.constants.constants import DATA_DIR, XHAIR_PREVIEW_BG
from app.utils import change_xhair_in_cfg, prepare_entries, get_xhair_from_cfg, get_xhairs, write_cfg
from app.parser import CfgParser


class CrosshairAppOptions:
  cfg_path = ''
  weapon_display_type = ''

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


class CrosshairApp(QMainWindow):
  history_signal = pyqtSignal()

  def __init__(self):
    super().__init__()

    self.setWindowTitle('VTF Crosshair Changer')
    self.setGeometry(100, 100, 800, 400)
    self.move(60, 15)
    self.setWindowIcon(QIcon('assets/seekerOL.png'))

    self.wid = QWidget(self)
    self.setCentralWidget(self.wid)

    self.xhairs = []
    self.selected_items = []
    self.logs = []
    self.history = CrosshairHistory()

    self.options = CrosshairAppOptions()
    self.options.cfg_path = ''
    self.options.weapon_display_type = True
    self.retrieve_options()

    self.build_gui()
    self.handle_cfg()

    self.write_options()


  def handle_cfg(self):
    self.parser = CfgParser()

    if (not self.options.cfg_path or len(self.options.cfg_path) == 0):
      self.handle_path_select()
      self.top_path.setText(self.options.cfg_path)

    self.xhairs = get_xhairs("{}/materials/vgui/replay/thumbnails".format(self.options.cfg_path))
    self.selector.addItems([x["name"] for x in self.xhairs])

    self.generate_previews()
    self.parse_cfgs()
    self.populate_table()




  def build_gui(self):
    self.layout = QGridLayout()

    self.build_logs()
    self.build_top_bar()
    self.build_controls()
    self.build_table()

    self.layout.addLayout(self.top_bar, 0, 0, 1, 2)
    self.layout.addWidget(self.table, 1, 0)
    self.layout.addWidget(self.controls, 1, 1)
    self.layout.addWidget(self.logger, 2, 0, 1, 2)

    self.wid.setLayout(self.layout)
    self.show()

  def build_top_bar(self):
    self.top_bar = QHBoxLayout()

    self.build_undo_redo()

    self.top_path_label = QLabel('Current Path:')
    self.top_path_label.setStyleSheet("QLabel { font-weight: bold; }")
    self.top_path = QLabel(self.options.cfg_path)
    self.top_path_change = QPushButton('Change')

    def path_change_clicked():
      self.options.cfg_path = ''
      self.handle_cfg()
      self.add_log('Changed path to {}'.format(self.options.cfg_path))

    self.top_path_change.clicked.connect(path_change_clicked)

    self.top_bar.addWidget(self.top_path_label, 0, Qt.AlignmentFlag.AlignLeft)
    self.top_bar.addWidget(self.top_path, 0, Qt.AlignmentFlag.AlignLeft)
    self.top_bar.addWidget(self.top_path_change, 0, Qt.AlignmentFlag.AlignLeft)
    self.top_bar.addLayout(self.undo_redo, Qt.AlignmentFlag.AlignRight)


  def build_logs(self):
    self.logger = QTextEdit('')
    self.logger.setGeometry(0, 0, 800, 200)
    self.logger.setMaximumHeight(200)
    self.logger.setReadOnly(True)

  def build_controls(self):
    self.controls = QWidget()
    self.controls_layout = QGridLayout()

    self.info = QTextEdit('')
    self.info.setMinimumWidth(200)
    self.info.setReadOnly(True)

    self.crosshair_image = QLabel()
    self.crosshair_image.setMinimumSize(200, 200)

    self.crosshair_image.setStyleSheet("QLabel { background-color: " + XHAIR_PREVIEW_BG + "; }")

    self.build_selector()
    self.build_undo_redo()

    self.controls_layout.addWidget(self.info, 1, 0)
    self.controls_layout.addWidget(self.crosshair_image, 1, 1)
    self.controls_layout.addLayout(self.selector_container, 2, 0, 1, 2)

    self.controls.setLayout(self.controls_layout)

  def build_undo_redo(self):
    self.undo_redo = QHBoxLayout()

    self.undo_button = QPushButton('')
    self.undo_button.setToolTip('Undo')
    self.undo_button.setFixedSize(QSize(32, 32))
    undo_pixmap = QPixmap('assets/undo.png')
    self.undo_button.setIcon(QIcon(undo_pixmap))
    self.undo_button.setIconSize(QSize(23, 23))

    def undo():
      item = self.history.undo()

      if not item:
        return

      weapons_list = item["weapons_list"]
      previous_list = item["previous_list"]
      log = item["log"]

      for i in range(len(weapons_list)):
        weapon = weapons_list[i]
        xhair = previous_list[i]

        if weapon not in self.parser.cfgs:
          continue

        self.modify_weapon(weapon, xhair)

      self.add_log("Undid `<span style=\"font-style: italic\">{}</span>`".format(log))
      self.populate_table()

    shortcut_undo = QShortcut(QKeySequence('Ctrl+Z'), self.wid)
    self.undo_button.clicked.connect(undo)
    shortcut_undo.activated.connect(undo)



    self.redo_button = QPushButton('')
    self.redo_button.setToolTip('Redo')
    self.redo_button.setFixedSize(QSize(32, 32))
    redo_pixmap = QPixmap('assets/redo.png')
    self.redo_button.setIcon(QIcon(redo_pixmap))
    self.redo_button.setIconSize(QSize(23, 23))

    def redo():
      item = self.history.redo()

      if not item:
        return

      weapons_list = item["weapons_list"]
      current_list = item["current_list"]
      log = item["log"]

      for i in range(len(weapons_list)):
        weapon = weapons_list[i]
        xhair = current_list[i]

        if weapon not in self.parser.cfgs:
          continue

        self.modify_weapon(weapon, xhair)

      self.add_log("Redid `<span style=\"font-style: italic\">{}</span>`".format(log))
      self.populate_table()

    shortcut_redo = QShortcut(QKeySequence('Ctrl+Y'), self)
    self.redo_button.clicked.connect(redo)
    shortcut_redo.activated.connect(undo)


    self.undo_redo.addWidget(self.undo_button, 1, Qt.AlignmentFlag.AlignRight)
    self.undo_redo.addWidget(self.redo_button, 0, Qt.AlignmentFlag.AlignRight)




  def build_selector(self):
    self.selector_container = QVBoxLayout()
    self.selector = QComboBox()

    self.selector.activated.connect(lambda : self.on_xhair_selected(self.selector.currentText()))

    self.button_apply = QPushButton('Apply')
    self.button_applyclass = QPushButton('Apply to all weapons of this class')
    self.button_applyslot = QPushButton('Apply to all weapons of this slot')
    self.button_applyall = QPushButton('Apply to all weapons')

    self.button_apply.clicked.connect(lambda: self.apply_clicked('apply', self.selector.currentText()))
    self.button_applyclass.clicked.connect(lambda: self.apply_clicked('class', self.selector.currentText()))
    self.button_applyslot.clicked.connect(lambda: self.apply_clicked('slot', self.selector.currentText()))
    self.button_applyall.clicked.connect(lambda: self.apply_clicked('all', self.selector.currentText()))

    self.selector_container.addWidget(self.selector)
    self.selector_container.addWidget(self.button_apply)
    self.selector_container.addWidget(self.button_applyclass)
    self.selector_container.addWidget(self.button_applyslot)
    self.selector_container.addWidget(self.button_applyall)


  def build_table(self):
    self.table = QTableWidget(0, 2)
    self.table.setHorizontalHeaderLabels(['Weapon', 'Crosshair'])
    self.table.verticalHeader().hide()
    self.table.setColumnWidth(0, self.table.width() // 2)
    self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    self.table.setMinimumWidth(400)
    self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    self.table.verticalHeader().setDefaultSectionSize(20)
    self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    self.table.itemSelectionChanged.connect(
      lambda: self.on_weapon_selected([x.text() for x in self.table.selectedItems()])
    )


  def populate_table(self):
    if len(self.parser.cfgs) > 0:
      self.table.setRowCount(len(self.parser.cfgs))
      self.table.setSortingEnabled(False)

      i = 0
      for label, cfg in self.parser.cfgs.items():
        self.table.setItem(i, 0, QTableWidgetItem(label))
        self.table.setItem(i, 1, QTableWidgetItem(get_xhair_from_cfg(cfg)))
        i += 1

      self.table.setSortingEnabled(True)


  def on_weapon_selected(self, selected_items):
    self.selected_items = list(zip(selected_items[::2], selected_items[1::2]))
    self.update_xhair_preview(selected_items[1::2])
    self.update_info(selected_items[::2])

  def on_xhair_selected(self, xhair):
    self.update_xhair_preview([xhair])

  def modify_weapon(self, weapon, xhair):
    cfg = self.parser.cfgs[weapon]
    change_xhair_in_cfg(cfg, xhair)
    lines = self.parser.reconstruct_cfg(cfg)
    write_cfg(lines, self.options.cfg_path, weapon)
    self.parser.cfgs[weapon] = cfg

  def apply_clicked(self, action_type, new_xhair):
    changed = []

    def modify(wep):
      if wep not in self.parser.cfgs:
        return

      nonlocal changed
      changed += [(wep, get_xhair_from_cfg(self.parser.cfgs[wep]) if wep in self.parser.cfgs else None)]
      self.modify_weapon(wep, new_xhair)

    for weapon in [x[0] for x in self.selected_items]:
      if weapon not in self.parser.cfgs:
        continue

      if action_type == "apply":
        modify(weapon)
      else:
        if weapon not in weapon_associations:
          continue

        if action_type == "class":
          cur_class = weapon_associations[weapon]["class"]
          filtered = list(filter(lambda x, check=cur_class : weapon_associations[x]["class"] == check, weapon_associations.keys()))

          for wep in filtered:
            modify(wep)

        elif action_type == "slot":
          cur_slot = weapon_associations[weapon]["slot"]
          filtered = list(filter(lambda x, check=cur_slot : weapon_associations[x]["slot"] == check, weapon_associations.keys()))

          for wep in filtered:
            modify(wep)

        elif action_type == "all":
          for wep in weapon_associations.keys():
            modify(wep)

    log = ""

    if len(changed) == len(self.parser.cfgs):
      log = "Changed all weapons to {}".format(new_xhair)
    else:
      log = "Changed <span style=\"font-style: italic;\">{}</span> to {}".format(", ".join([x[0] for x in changed]), new_xhair)

    self.add_log(log)
    self.history.add_item([x[0] for x in changed], [x[1] for x in changed], [new_xhair] * len(changed), log)
    self.populate_table()


  def generate_previews(self):
    progress = QProgressDialog("Generating Preview Images...", "Cancel", 0, 100, self)
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setAutoClose(True)
    progress.canceled.connect(lambda: sys.exit(), type=Qt.ConnectionType.DirectConnection)
    progress.forceShow()

    for i, xhair in enumerate(self.xhairs):
      xhair_path = xhair["path"]
      image_path = os.path.join(DATA_DIR, "previews", "{}.png".format(xhair["name"]))

      if not os.path.exists(image_path):
        vtf_parser = Parser(xhair_path)
        image = vtf_parser.get_image()
        image.save(image_path)

      progress.setValue(floor(i / len(self.xhairs) * 100))

    progress.setValue(100)

  def handle_path_select(self):
    path = str(QFileDialog.getExistingDirectory(self, "Select Crosshair Folder"))

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
    cfg_path = self.options.cfg_path

    if (not cfg_path or len(cfg_path) == 0):
      return

    self.entries = prepare_entries("{}/scripts".format(cfg_path))

    for entry in self.entries:
      label = entry["name"] if self.options.weapon_display_type else \
        "{}: {}".format(weapon_associations[entry["name"]]["class"], weapon_associations[entry["name"]]["display"])

      self.parser.cfgs[label] = self.parser.parse_cfg(entry["contents"])


  def update_xhair_preview(self, xhairs):
    if len(xhairs) > 1:
      self.crosshair_image.setPixmap(QPixmap())
      return

    xhair = xhairs[0]

    image_path = os.path.join(DATA_DIR, "previews", "{}.png".format(xhair))

    if os.path.exists(image_path):
      self.crosshair_image_pixmap = QPixmap(image_path)

      self.crosshair_image.setPixmap(self.crosshair_image_pixmap)
      self.crosshair_image.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter);

  def update_info(self, weapons):
    display_class = ''
    display_name = ''
    display_slot = ''
    display_all = []
    weapon_slots = ["Primary", "Secondary", "Melee"]
    multiple_string = '&lt;Multiple&gt;'

    for weapon in weapons:
      if (weapon not in weapon_associations):
        continue

      assoc = weapon_associations[weapon]

      display_class = assoc["class"] if assoc["class"] == display_class \
        or len(display_class) == 0 else multiple_string
      display_name = assoc["display"] if assoc["display"] == display_name \
        or len(display_name) == 0 else multiple_string
      display_slot = weapon_slots[assoc["slot"] - 1] if \
        weapon_slots[assoc["slot"] - 1] == display_slot or len(display_slot) == 0 else multiple_string

      display_all += assoc["all"]

    html = ""
    templ = "<span style=\"color: #0088dd\">{}</span>: {}<br/>"

    html += templ.format("Class", display_class)
    html += templ.format("Name", display_name)
    html += templ.format("Slot", display_slot)
    html += "<span style=\"color: #0088dd\">Associated Weapons:</span><br/>"

    for wep in display_all:
      html += "{}<br/>".format(wep)

    self.info.setHtml(html)


  def retrieve_options(self):
    data_path = os.path.join(DATA_DIR, 'data.txt')

    if os.path.exists(data_path):
      with open(data_path, "rb") as f:
        try:
          self.options = pickle.load(f)
        except:
          f.close()


  def write_options(self):
    data_path = os.path.join(DATA_DIR, 'data.txt')

    if os.path.exists(data_path):
      with open(data_path, "w") as f:
        f.close()

    with open(data_path, "wb") as f:
      pickle.dump(self.options, f)

  def add_log(self, log):
    now = datetime.datetime.now()
    time = [now.hour, now.minute, now.second]

    def pad(n):
        out = str(n)
        return "0" + out if len(out) == 1 else out

    self.logs.append([time, log])
    self.logger.moveCursor(QTextCursor.MoveOperation.End);
    self.logger.insertHtml("<b>[{}:{}:{}]</b> {}<br/>".format(
        pad(time[0]), pad(time[1]), pad(time[2]), log));

def show_app():
  app = QApplication([])
  CrosshairApp()
  app.exec()
