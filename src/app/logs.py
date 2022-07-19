from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from utils import get_app
import datetime

class Logs(QTextEdit):
  LogSignal = pyqtSignal(str)

  def __init__(self):
    super().__init__('')

    self.setGeometry(0, 0, 800, 200)
    self.setMaximumHeight(200)
    self.setReadOnly(True)

    self.logs = []

    self.LogSignal.connect(self.add_log)

  def add_log(self, log):
    now = datetime.datetime.now()
    time = [now.hour, now.minute, now.second]

    def pad(n):
        out = str(n)
        return "0" + out if len(out) == 1 else out

    self.logs.append([time, log])
    self.moveCursor(QTextCursor.MoveOperation.End);
    self.insertHtml("<b>[{}:{}:{}]</b> {}<br/>".format(
        pad(time[0]), pad(time[1]), pad(time[2]), log));
