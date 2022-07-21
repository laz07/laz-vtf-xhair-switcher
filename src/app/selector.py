from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from constants.constants import BULK_APPLY_OPTIONS, APPLY_SELECTION, ITALIC_TAG
from utils import get_app

class Selector(QVBoxLayout):
  def __init__(self, xhairs):
    super().__init__()

    self.selected_weapons = []

    self.combo = QComboBox()
    self.combo.addItems([x["name"] for x in xhairs])
    self.combo.textActivated.connect(lambda : get_app().CrosshairChangeSignal.emit(self.combo.currentText()))

    self.button_apply = QPushButton('Apply to selection')
    self.button_apply.setEnabled(False)
    self.button_apply.clicked.connect(lambda: get_app().ApplySignal.emit(APPLY_SELECTION, self.combo.currentText()))


    self.bulk_layout = QHBoxLayout()

    self.bulk_combo = QComboBox()
    self.bulk_combo.addItems(BULK_APPLY_OPTIONS.keys())
    self.bulk_combo.textActivated.connect(self.on_bulk_select)

    self.bulk_button_apply = QPushButton('Bulk Apply')
    self.bulk_button_apply.setEnabled(False)
    self.bulk_button_apply.clicked.connect(self.bulk_apply)

    self.bulk_button_save = QPushButton('Save group')
    self.bulk_button_save.setEnabled(False)
    self.bulk_button_save.clicked.connect(self.save_bulk_group)

    self.bulk_button_delete = QPushButton('Delete group')
    self.bulk_button_delete.setEnabled(False)
    self.bulk_button_delete.clicked.connect(self.delete_bulk_group)

    self.bulk_layout.addWidget(self.bulk_combo)
    self.bulk_layout.addWidget(self.bulk_button_apply)
    self.bulk_layout.addWidget(self.bulk_button_save)
    self.bulk_layout.addWidget(self.bulk_button_delete)


    self.addWidget(self.combo, 0, Qt.AlignmentFlag.AlignTop)
    self.addWidget(self.button_apply, 0, Qt.AlignmentFlag.AlignTop)
    self.addLayout(self.bulk_layout, Qt.AlignmentFlag.AlignTop)


    get_app().WeaponSelectSignal.connect(self.on_weapon_select)

  def save_bulk_group(self):
    (group, success) = QInputDialog.getText(get_app().window, "Enter a custom name for this weapon group", "Name")

    if not success or not group:
      return

    get_app().OptionSignal.emit('custom_apply_groups', (group, self.selected_weapons))
    get_app().LogSignal\
      .emit("Added group {} with weapons {}"\
        .format(ITALIC_TAG, ITALIC_TAG).format(group, ", ".join(self.selected_weapons[::2]))
        )

  def delete_bulk_group(self):
    group = self.bulk_combo.currentText()
    get_app().OptionSignal.emit('custom_apply_groups', (group, None))
    get_app().LogSignal.emit("Deleted group {}".format(ITALIC_TAG).format(group))

  def on_weapon_select(self, weapons):
    self.selected_weapons = weapons

    if len(weapons) > 0:
      self.button_apply.setEnabled(True)
      self.bulk_button_save.setEnabled(True)
    else:
      self.button_apply.setEnabled(False)
      self.bulk_button_save.setEnabled(False)

  def on_bulk_select(self, value):
    self.bulk_button_apply.setEnabled(bool(value not in BULK_APPLY_OPTIONS or BULK_APPLY_OPTIONS[value]))
    self.bulk_button_delete.setEnabled(bool(value not in BULK_APPLY_OPTIONS))

  def bulk_apply(self):
    custom_selection = self.bulk_combo.currentText()

    get_app().ApplySignal.emit(
      BULK_APPLY_OPTIONS[custom_selection] if custom_selection in BULK_APPLY_OPTIONS else custom_selection,
      self.combo.currentText()
    )
