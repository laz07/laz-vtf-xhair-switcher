# tf2-vtf-crosshair-selector

# Installation

Download a release, and then drag the .exe into the root custom folder where your VTF crosshair files are located.

If your custom folder looks like this:

```
tf/custom/custom_crosshairs/materials/vgui/replay/thumbnails/<crosshair vtfs/vmts here>
```
```
tf/custom/custom_crosshairs/scripts/<crosshair scripts here>
```

Then crosshair.exe should be placed in 
```
tf/custom/custom_crosshairs/crosshair.exe
```

Then, simply run it.

If you want to be able to run the program from your desktop, for example, you can just make a shortcut to this file for now. In the future I'll probably add the ability to choose your crosshair folder path.

# Build

If you want to build the code yourself, make sure you have Python 3.7 and pip3 installed, clone the repo, cd into it, and type 
```pip install -r requirements.txt```

Then, to generate an .exe output, type
```pyinstaller --onefile --windowed --icon=xhair.ico crosshair.py```

If everything went correctly, you should see a crosshair.exe in a newly-created dist folder in that directory.