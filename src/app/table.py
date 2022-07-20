from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from utils import get_app, get_xhair_from_cfg

class Table(QTableWidget):
  def __init__(self):
    super().__init__(0, 2)

    self.setHorizontalHeaderLabels(['Weapon', 'Crosshair'])
    self.verticalHeader().hide()
    self.setColumnWidth(0, self.width() // 2)
    self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    self.setMinimumWidth(400)
    self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    self.verticalHeader().setDefaultSectionSize(20)
    self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    self.itemSelectionChanged.connect(
      lambda: get_app().WeaponSelectSignal.emit([x.text() for x in self.selectedItems()])
    )

  def populate(self, cfgs):
    """ Populate contents of the main table using the parsed configs """
    if len(cfgs) > 0:
      self.setRowCount(len(cfgs))
      self.setSortingEnabled(False)

      i = 0
      for label, cfg in cfgs.items():
        self.setItem(i, 0, QTableWidgetItem(label))
        self.setItem(i, 1, QTableWidgetItem(get_xhair_from_cfg(cfg)))
        i += 1

      self.setSortingEnabled(True)
