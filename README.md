# tf2-vtf-crosshair-selector

# Installation

Download the latest .exe and run it.

# Build
If you want to build the code yourself, make sure you have Python 3.7 and pip3 installed. Due to PyInstaller being dumb, the build process is a bit convoluted. I may automate this in the future.

Clone the repo, cd into it, and type 
```
pip install -r requirements.txt
```

Next, type
```
pyi-makespec --onefile --windowed --icon=xhair.ico crosshair.py
```

This will generate a file in the same folder called `crosshair.spec`. You'll have to edit this slightly for the build to work. Open `crosshair.spec` with your favorite text editor and go to the line that looks like `datas=[]` (should be line 9). Replace this with:
```
datas=[
    ('assets', './assets'),
    ('xhair.ico', '.')
],
```

So your file should look something like
```
...
a = Analysis(['crosshair.py'],
             pathex=['C:\\some\\path'],
             binaries=[],
             datas=[
                ('assets', './assets'),
                ('xhair.ico', '.')
             ],
             hiddenimports=[],
             hookspath=[],
...
```
Then, to generate an .exe output, type
```
pyinstaller crosshair.spec
```

If everything went correctly, you should see a crosshair.exe in a newly-created dist folder in that directory.