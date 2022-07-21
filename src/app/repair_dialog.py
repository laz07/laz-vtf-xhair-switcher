from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

class RepairDialog(QDialog):
  @staticmethod
  def getWeaponsToRepair(parent, weapons):
    instance = RepairDialog(parent, weapons)

    value = instance.exec()

    if value == QDialog.DialogCode.Accepted:
      return instance.get_checked_weapons()

    if value == QDialog.DialogCode.Rejected:
      return []

    else:
      return [x.text() for x in instance.chkboxes]

  def get_checked_weapons(self):
    return [x.text() for x in self.chkboxes if x.isChecked() == True]

  def __init__(self, parent, weapons = []):
    super().__init__(parent)

    self.button_box = QDialogButtonBox(self)
    self.button_box.setGeometry(QRect(30, 240, 341, 32))
    self.button_box.setOrientation (Qt.Orientation.Horizontal)

    self.main_layout = QVBoxLayout()
    self.chkboxes = []

    if len(weapons) > 0:
      self.setFixedSize(400, 300)
      self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
      self.button_box.button(QDialogButtonBox.StandardButton.Cancel).clicked.connect(self.reject)

      self.repair_button = QPushButton("Repair all")
      self.button_box.addButton(self.repair_button, QDialogButtonBox.ButtonRole.AcceptRole)
      self.repair_button.clicked.connect(lambda : self.done(2))

      self.group_box = QGroupBox("Select weapons to repair")

      self.scroll_area_layout = QVBoxLayout()

      self.scroll_area_content = QWidget()
      self.scroll_area_content.setLayout(self.scroll_area_layout)

      self.scroll_area = QScrollArea()
      self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
      self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
      self.scroll_area.setWidgetResizable(True)
      self.scroll_area.setWidget(self.scroll_area_content)


      for weapon in weapons:

        weapon_chkbox = QCheckBox(weapon)
        self.scroll_area_layout.addWidget(weapon_chkbox)
        self.chkboxes.append(weapon_chkbox)

      self.group_box_layout = QVBoxLayout()
      self.group_box_layout.addWidget(self.scroll_area)
      self.group_box.setLayout(self.group_box_layout)

      self.main_layout.addWidget(self.group_box)
    else:
      self.setFixedSize(200, 100)
      self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Ok)

      self.main_layout.addWidget(QLabel('No invalid scripts found'))

    self.main_layout.addWidget(self.button_box)


    self.setLayout(self.main_layout)
    self.setWindowTitle("Repair scripts")

    self.button_box.button(QDialogButtonBox.StandardButton.Ok).clicked.connect(self.accept)
