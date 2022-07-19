import os
import sys
from vtf2img import Parser
from math import floor

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from utils import get_app
from app.selector import Selector
from app.options import Options
from constants.constants import XHAIR_PREVIEW_BG, DATA_DIR
from constants.associations import weapon_associations, reverse_associations

class Controls(QGridLayout):
  def generate_previews(self, xhairs):
    """ Convert VTFs to PNGs and display loading dialog """
    progress = QProgressDialog("Generating Preview Images...", "Cancel", 0, 100, get_app().window)
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setAutoClose(True)
    progress.canceled.connect(lambda: sys.exit(), type=Qt.ConnectionType.DirectConnection)
    progress.forceShow()

    for i, xhair in enumerate(xhairs):
      xhair_path = xhair["path"]
      image_path = os.path.join(DATA_DIR, "previews", "{}.png".format(xhair["name"]))

      if not os.path.exists(image_path):
        vtf_parser = Parser(xhair_path)
        image = vtf_parser.get_image()
        image.save(image_path)

      progress.setValue(floor(i / len(xhairs) * 100))

    progress.setValue(100)

  def update_xhair_preview(self, xhairs):
    """ Change the crosshair preview image """
    if len(xhairs) == 0 or xhairs.count(xhairs[0]) != len(xhairs):
      self.crosshair_image.setPixmap(QPixmap())
      return

    xhair = xhairs[0]

    image_path = os.path.join(DATA_DIR, "previews", "{}.png".format(xhair))

    if os.path.exists(image_path):
      self.crosshair_image_pixmap = QPixmap(image_path)

      self.crosshair_image.setPixmap(self.crosshair_image_pixmap)
      self.crosshair_image.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter);

  def update_info(self, weapons):
    """ Change the info textbox to reflect passed in weapons list data """
    display_class = ''
    display_name = ''
    display_slot = ''
    display_all = []
    weapon_slots = ["Primary", "Secondary", "Melee"]
    multiple_string = '&lt;Multiple&gt;'

    for weapon in weapons:
      if (weapon not in weapon_associations and weapon not in reverse_associations):
        continue

      assoc = weapon_associations[weapon] if weapon in weapon_associations else reverse_associations[weapon]

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


  def __init__(self, initial_options, xhairs):
    super().__init__()

    self.info = QTextEdit('')
    self.info.setMinimumWidth(200)
    self.info.setReadOnly(True)

    self.crosshair_image = QLabel()
    self.crosshair_image.setMinimumSize(200, 200)

    self.crosshair_image.setStyleSheet("QLabel { background-color: " + XHAIR_PREVIEW_BG + "; }")

    self.selector = Selector(xhairs)
    self.options = Options(initial_options)

    self.addWidget(self.info, 0, 0)
    self.addWidget(self.crosshair_image, 0, 1)
    self.addLayout(self.selector, 1, 0)
    self.addLayout(self.options, 1, 1)

    self.setRowStretch(0, 1)

