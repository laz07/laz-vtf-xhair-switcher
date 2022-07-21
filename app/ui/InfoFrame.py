import wx

from app.utils import resource_path

class InfoFrame(wx.Frame):
    def __init__(self, parent, title, size, info_text, btn_text, btn_func):
        super(InfoFrame, self).__init__(parent, title=title, size=size, style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
        self.parent = parent
        
        self.SetIcon(wx.Icon(resource_path("xhair.ico")))
        self.SetMinSize(size)

        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.VERTICAL)

        text_info = wx.StaticText(panel, id=-1, label=info_text)
        text_info.Wrap(size[0] - 50)

        btn_action = wx.Button(panel, label=btn_text, size=(100, 30))
        btn_action.Bind(wx.EVT_BUTTON, lambda e: btn_func(e, self))

        box.Add(text_info, wx.SizerFlags().Center().Border(wx.ALL, 10))
        box.Add(btn_action, wx.SizerFlags().Center().Border(wx.ALL, 10))

        panel.SetSizerAndFit(box)

        self.Center()
        self.Show(True)
        