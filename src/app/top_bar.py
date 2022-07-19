from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from app.button_bar import ButtonBar
from utils import get_app

class TopBar(QHBoxLayout):
  def __init__(self, cfg_path):
    super().__init__()

    self.button_bar = ButtonBar()

    self.path_label = QLabel('Current Path:')
    self.path_label.setStyleSheet("QLabel { font-weight: bold; }")
    self.path = QLabel(cfg_path)
    self.path_change = QPushButton('Change')

    self.path_change.clicked.connect(lambda : get_app().PathChangeSignal.emit())

    self.addWidget(self.path_label, 0, Qt.AlignmentFlag.AlignLeft)
    self.addWidget(self.path, 0, Qt.AlignmentFlag.AlignLeft)
    self.addWidget(self.path_change, 0, Qt.AlignmentFlag.AlignLeft)
    self.addLayout(self.button_bar, Qt.AlignmentFlag.AlignRight)
