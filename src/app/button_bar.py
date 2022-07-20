from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from utils import get_app
from constants.constants import ICON_INFO, ICON_UNDO, ICON_REDO

class ButtonBar(QHBoxLayout):
  def __init__(self):
    super().__init__()

    self.undo_button = QPushButton('')
    self.undo_button.setToolTip('Undo')
    self.undo_button.setFixedSize(QSize(32, 32))
    self.undo_button.setIcon(QIcon(QPixmap(ICON_UNDO)))
    self.undo_button.setIconSize(QSize(23, 23))
    self.undo_button.clicked.connect(lambda : get_app().UndoRedoSignal.emit(True))

    self.redo_button = QPushButton('')
    self.redo_button.setToolTip('Redo')
    self.redo_button.setFixedSize(QSize(32, 32))
    self.redo_button.setIcon(QIcon(QPixmap(ICON_REDO)))
    self.redo_button.setIconSize(QSize(23, 23))
    self.redo_button.clicked.connect(lambda : get_app().UndoRedoSignal.emit(False))

    self.info_button = QPushButton('')
    self.info_button.setToolTip('Info')
    self.info_button.setFixedSize(QSize(32, 32))
    self.info_button.setIcon(QIcon(QPixmap(ICON_INFO)))
    self.info_button.setIconSize(QSize(23, 23))
    self.info_button.clicked.connect(self.show_info)

    self.addWidget(self.info_button, 1, Qt.AlignmentFlag.AlignRight)
    self.addWidget(self.undo_button, 0, Qt.AlignmentFlag.AlignRight)
    self.addWidget(self.redo_button, 0, Qt.AlignmentFlag.AlignRight)

  def show_info(self):
    self.info_dialog = QMessageBox()
    self.info_dialog.setWindowIcon(QIcon(QPixmap('assets/app.png')))
    self.info_dialog.setWindowTitle("About")
    self.info_dialog.setText("Made by Max M/laz")
    self.info_dialog.show()
