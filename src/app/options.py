from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from utils import get_app
from constants.associations import weapon_associations, reverse_associations

class Options(QVBoxLayout):
  def __init__(self, initial_options):
    super().__init__()

    self.display_type_chkbox = QCheckBox('Display weapon names')
    self.display_type_chkbox.setChecked(False)
    self.display_type_chkbox.clicked.connect(lambda val : get_app().OptionSignal.emit("weapon_display_type", val))

    self.backup_chkbox = QCheckBox('Backup scripts before modifying')
    self.display_type_chkbox.setChecked(initial_options.backup_scripts)
    self.backup_chkbox.clicked.connect(lambda val : get_app().OptionSignal.emit("backup_scripts", val))

    self.addWidget(self.display_type_chkbox, 0, Qt.AlignmentFlag.AlignTop)
    self.addWidget(self.backup_chkbox, 1, Qt.AlignmentFlag.AlignTop)
