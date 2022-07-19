from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from utils import get_app

class Selector(QVBoxLayout):
  def __init__(self, xhairs):
    super().__init__()

    self.combo = QComboBox()
    self.combo.addItems([x["name"] for x in xhairs])

    self.button_apply = QPushButton('Apply to selection')


    self.custom_layout = QHBoxLayout()

    self.apply_selector = QComboBox()
    self.apply_selector.addItems(['select...', 'All weapons of this class', 'All weapons of this slot', 'All weapons'])
    self.custom_button_apply = QPushButton('Bulk Apply')
    self.custom_button_save = QPushButton('Save selection as')

    self.custom_layout.addWidget(self.apply_selector)
    self.custom_layout.addWidget(self.custom_button_apply)
    self.custom_layout.addWidget(self.custom_button_save)


    self.button_apply.clicked.connect(lambda: get_app().ApplySignal.emit('apply', self.combo.currentText()))
    self.combo.activated.connect(lambda : get_app().CrosshairChangeSignal.emit(self.combo.currentText()))

    self.addWidget(self.combo, 0, Qt.AlignmentFlag.AlignTop)
    self.addWidget(self.button_apply, 0, Qt.AlignmentFlag.AlignTop)
    self.addLayout(self.custom_layout, Qt.AlignmentFlag.AlignTop)
