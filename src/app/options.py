from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from utils import get_app
from constants.ui import OPTIONS_WEAPON_DISPLAY_TYPE, OPTIONS_BACKUP_SCRIPTS

class Options(QVBoxLayout):
  def __init__(self, initial_options):
    super().__init__()

    self.display_type_chkbox = QCheckBox(OPTIONS_WEAPON_DISPLAY_TYPE)
    self.display_type_chkbox.setChecked(initial_options.weapon_display_type)
    self.display_type_chkbox.clicked.connect(lambda val : get_app().OptionSignal.emit("weapon_display_type", val))

    self.backup_chkbox = QCheckBox(OPTIONS_BACKUP_SCRIPTS)
    self.backup_chkbox.setChecked(initial_options.backup_scripts)
    self.backup_chkbox.clicked.connect(lambda val : get_app().OptionSignal.emit("backup_scripts", val))

    self.invalid_scripts_button = QPushButton("Repair scripts")
    self.invalid_scripts_button.clicked.connect(lambda : get_app().RepairScriptsSignal.emit())

    self.addWidget(self.display_type_chkbox, 0, Qt.AlignmentFlag.AlignTop)
    self.addWidget(self.backup_chkbox, 0, Qt.AlignmentFlag.AlignTop)
    self.addWidget(self.invalid_scripts_button, 1, Qt.AlignmentFlag.AlignTop)
