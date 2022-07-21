import wx
import os
import shutil

from app.constants import cn
from app.utils import resource_path

class CrosshairImageFrame(wx.Frame):

    def copy_png(self, path, xhair):
        newpath = "{}/display/{}.png".format(cn["constants"]["data_dir"], xhair)
        shutil.copyfile(path, newpath)

        self.parent.Destroy()
        self.Destroy()

        newframe = self.make_frame()
        newframe.logs_add("{} copied to {}".format(path, os.path.abspath(newpath)))

    def layout_content(self, extra_xhairs):
        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.VERTICAL)

        text_info = wx.StaticText(panel, id=-1, label=cn["ui"]["xhair_image_content_msg"])

        choice_xhairs = wx.Choice(panel, choices=extra_xhairs)


        def open_file_dialog(_):
            with wx.FileDialog(self, "Choose PNG", wildcard="PNG files (*.png)|*.png", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
                if file_dialog.ShowModal() == wx.ID_CANCEL:
                    return
                
                path = file_dialog.GetPath()
                self.copy_png(path, choice_xhairs.GetString(choice_xhairs.GetSelection()))

        btn_pngfile = wx.Button(panel, label="Choose PNG")
        btn_pngfile.Bind(wx.EVT_BUTTON, open_file_dialog)
        
        box.Add(text_info, wx.SizerFlags().Center().Border(wx.TOP, 10))
        box.Add(choice_xhairs, wx.SizerFlags().Center().Border(wx.TOP, 5))
        box.Add(btn_pngfile, wx.SizerFlags().Center().Border(wx.TOP, 5))

        panel.SetSizerAndFit(box)

    def layout_no_content(self):
        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.VERTICAL)

        text_noxhairs = wx.StaticText(panel, label=cn["ui"]["xhair_image_no_content_msg"], style=wx.ALIGN_CENTRE)
        text_noxhairs.Wrap(cn["ui"]["window_size_crosshair_image_frame"][0] - 50)
        btn_close = wx.Button(panel, label="Close")
        btn_close.Bind(wx.EVT_BUTTON, lambda _: self.Destroy())

        box.Add(text_noxhairs, wx.SizerFlags().Center().Border(wx.TOP, 10))
        box.Add(btn_close, wx.SizerFlags().Center().Border(wx.TOP, 15))

        panel.SetSizerAndFit(box)


    def find_extra_xhairs(self):
        display_path = resource_path("assets/display")
        files = [f[:-4] for f in os.listdir(display_path) if os.path.isfile(os.path.join(display_path, f))]
        return [f for f in self.xhairs if f not in files]


    def __init__(self, parent, title, size, xhairs, make_frame):
        super(CrosshairImageFrame, self).__init__(parent, title=title, size=size, style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP ^ wx.RESIZE_BORDER)

        self.SetIcon(wx.Icon(resource_path("xhair.ico")))
        self.parent = parent
        self.xhairs = xhairs
        self.make_frame = make_frame
        
        extra_xhairs = self.find_extra_xhairs()

        if len(extra_xhairs) == 0:
            self.layout_no_content()
        else:
            self.layout_content(extra_xhairs)
        
        self.Center()
        self.Show(True)
