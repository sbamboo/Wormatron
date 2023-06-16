# [Configuration]
_wormatron_file = "wormatron.py"



# [Code]
# Imports
import os
import sys
import traceback

# Ensure tkinter
try: import tkinter as tk
except:
    os.system("python3 -m pip install tkinter")

# Handle arguments
## Traceback: switches _traceback to true
if "--traceback" in " ".join(argv):
    _wormatron_traceback = True
    for i,a in enumerate(argv):
        if a == "--traceback":
            argv = argv.pop(i)
else: _wormatron_traceback = False
## Info: prints out information from info.txt
if "--info" in " ".join(argv):
    print(  open("info.txt",'r').read()  )
    exit()

# Prepare globals for modification
_wormatron_globalVars = globals()
# Overwrite __file__ and save the old one for later
_wormatron_oldFile = _wormatron_globalVars["__file__"]
_wormatron_globalVars["__file__"] = f"{CSScriptRoot}{os.sep}{_wormatron_file}"

# Get the directory of the wrapped script and add it to the pythonInstance path at index 0
sys.path.insert(0, os.path.dirname(os.path.abspath(_wormatron_globalVars["__file__"])))

# Save old working directory
_wormatron_oldDir = os.getcwd()

# Set the working directory to the CSScriptRoot (crosshell.csscriptroot)
os.chdir(CSScriptRoot)

# Execute File, and print traceback if turned on and encountered
try:
    exec(open(f"{CSScriptRoot}{os.sep}{_wormatron_file}").read(),_wormatron_globalVars)
except tk.TclError:
    print("\033[91mA Tkinter Error occurred: To print it out use --traceback\033[0m")
    if _wormatron_traceback == True:
        print("\033[33m")
        traceback.print_last()
        print("\033[0m")


# Restore original file
globals()[__file__] = _wormatron_oldFile
# Reset working directory to the original
os.chdir(_wormatron_oldDir)
# Remove the sub_dir from sys.path (Remove the subscripts folder from path)
sys.path.pop(0)