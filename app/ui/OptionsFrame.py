import wx
from app.constants import cn
from app.utils import prepare_entries, persist_options, resource_path

class OptionsFrame(wx.Frame):

    def checkbox_clicked(self, event):
        checked = True if event.GetInt() == 1 else False
        label = event.GetEventObject().GetLabel()

        if label == cn["ui"]["chk_display_toggle"]:
            cn["options"]["weapon_display_type"] = checked
            self.parent.entries = prepare_entries()
            self.parent.populate_list()
        elif label == cn["ui"]["chk_backup_scripts"]:
            cn["options"]["backup_scripts"] = checked

        persist_options()


    def click_close(self, event):
        self.Close()



    def __init__(self, parent, title, size):
        super(OptionsFrame, self).__init__(parent, title=title, size=size, style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP ^ wx.RESIZE_BORDER)

        self.parent = parent

        self.SetIcon(wx.Icon(resource_path("xhair.ico")))
        self.SetMinSize(size)

        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.VERTICAL)

        close_btn = wx.Button(panel, label="Close", size=(100, 30))
        close_btn.Bind(wx.EVT_BUTTON, self.click_close)

        checkbox_display_type = wx.CheckBox(panel, label=cn["ui"]["chk_display_toggle"])
        checkbox_backup = wx.CheckBox(panel, label=cn["ui"]["chk_backup_scripts"])

        checkbox_display_type.SetValue(cn["options"]["weapon_display_type"])
        checkbox_backup.SetValue(cn["options"]["backup_scripts"])

        checkbox_display_type.Bind(wx.EVT_CHECKBOX, self.checkbox_clicked)
        checkbox_backup.Bind(wx.EVT_CHECKBOX, self.checkbox_clicked)

        box.Add(checkbox_display_type, wx.SizerFlags().Center().Border(wx.TOP, 10))
        box.Add(checkbox_backup, wx.SizerFlags().Center().Border(wx.TOP, 5))
        box.Add(close_btn, wx.SizerFlags().Center().Border(wx.ALL, 10))

        panel.SetSizerAndFit(box)

        self.Center()
        self.Show(True)
