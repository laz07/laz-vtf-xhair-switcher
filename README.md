# laz-vtf-crosshair-switcher
![crosshair_ICXozgybYe](https://user-images.githubusercontent.com/109486500/180332700-27332f20-12e4-49a9-8c26-b7cb4a4a237a.png)

# Version
3.0

# Installation

Download the latest .exe and run it.

# Build
If you want to build the code yourself, make sure you have Python 3.7 and pip3 installed.
Clone the repo, cd into it, and type

```
pip install -r requirements.txt
```

Then, to generate an .exe output, type
```
pyinstaller crosshair.spec
```

You should see a crosshair.exe in a newly-created dist folder in that directory.

# Acknowledgments

Thanks to julienc91 for his vtf2img library (https://github.com/julienc91/vtf2img), which I yoinked into this codebase because PyInstaller was complaining about importing it as a module
