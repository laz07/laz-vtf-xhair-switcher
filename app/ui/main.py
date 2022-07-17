from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from vtf2img import Parser
import sys
import os

# from app.utils import (
#     prepare_entries,
#     get_crosshairs
# )
from app.constants.associations import weapon_associations
from app.constants.ui import *
from app.utils import prepare_entries, get_xhair_from_cfg
from app.parser import CfgParser

class CrosshairAppOptions:
  cfg_path = ''
  weapon_display_type = ''

class CrosshairApp:
  def __init__(self):
    self.app = QApplication([])

    # self.xhairs = get_crosshairs()

    self.xhairs = []

    self.options = CrosshairAppOptions()
    self.options.cfg_path = ''
    self.options.weapon_display_type = True

    self.parser = CfgParser()

    self.build_gui()

    self.app.exec()


  def handle_path_select(self):
    if (not self.options.cfg_path or len(self.options.cfg_path) == 0):
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

  def build_gui(self):
    self.window = QWidget()
    self.window.setWindowTitle('VTF Crosshair Changer')
    self.window.setGeometry(100, 100, 800, 400)
    self.window.move(60, 15)

    self.layout = QGridLayout()
    self.layout.setRowStretch(0, 2)
    self.layout.setRowStretch(1, 1)
    self.layout.setColumnStretch(0, 1)
    self.layout.setColumnStretch(1, 1)

    self.build_table()
    self.build_controls()
    self.build_logs()

    self.layout.addWidget(self.table, 0, 0)
    self.layout.addWidget(self.controls, 0, 1)
    self.layout.addWidget(self.logs, 1, 0, 1, 2)

    self.window.setLayout(self.layout)
    self.window.show()

    self.handle_path_select()
    self.parse_cfgs()
    self.populate_table()



  def build_table(self):
    self.table = QTableWidget(len(weapon_associations), 2)
    self.table.setHorizontalHeaderLabels(['Weapon', 'Crosshair'])
    self.table.verticalHeader().hide()
    self.table.setColumnWidth(0, self.table.width() // 2)
    self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    self.table.setMinimumWidth(400)
    self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    self.table.verticalHeader().setDefaultSectionSize(20)


  def parse_cfgs(self):
    cfg_path = self.options.cfg_path

    if (not cfg_path or len(cfg_path) == 0):
      return

    self.entries = prepare_entries("{}/scripts".format(cfg_path))

    for entry in self.entries:
      label = entry["name"] if self.options.weapon_display_type else \
        "{}: {}".format(weapon_associations[entry["name"]]["class"], weapon_associations[entry["name"]]["display"])

      self.parser.cfgs[label] = self.parser.parse_cfg(entry["contents"])

  def populate_table(self):
      if len(self.parser.cfgs) > 0:
        i = 0
        for label, cfg in self.parser.cfgs.items():
          print(label, cfg)
          self.table.setItem(i, 0, QTableWidgetItem(label))
          self.table.setItem(i, 1, QTableWidgetItem(get_xhair_from_cfg(cfg)))
          i += 1

  def build_controls(self):
    self.controls = QWidget()
    self.controls_layout = QGridLayout()

    self.info = QTextEdit('info')
    self.info.setMinimumWidth(200)
    self.crosshair_image_pixmap = QPixmap('image.png')
    self.crosshair_image = QLabel()
    self.crosshair_image.setPixmap(self.crosshair_image_pixmap)

    self.build_selector()

    self.controls_layout.addWidget(self.info, 0, 0)
    self.controls_layout.addWidget(self.crosshair_image, 0, 1)
    self.controls_layout.addWidget(self.selector_container, 1, 0, 1, 2)

    self.controls.setLayout(self.controls_layout)

  def build_selector(self):
    self.selector_container = QWidget()
    self.selector_container_layout = QVBoxLayout()

    self.selector = QComboBox()
    self.selector.addItems(['test', 'test1', 'test2', 'test3'])
    self.button_apply = QPushButton('Apply')
    self.button_applyclass = QPushButton('Apply to all weapons of this class')
    self.button_applyslot = QPushButton('Apply to all weapons of this slot')
    self.button_applyall = QPushButton('Apply to all weapons')

    self.selector_container_layout.addWidget(self.selector)
    self.selector_container_layout.addWidget(self.button_apply)
    self.selector_container_layout.addWidget(self.button_applyclass)
    self.selector_container_layout.addWidget(self.button_applyslot)

    self.selector_container_layout.addWidget(self.button_applyall)

    self.selector_container.setLayout(self.selector_container_layout)
    self.selector.addItems(self.xhairs)

  def build_logs(self):
    self.logs = QTextEdit('these are logs')
    self.logs.setGeometry(0, 0, 800, 200)

def show_app():
    return CrosshairApp()
