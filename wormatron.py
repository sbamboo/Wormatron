# Imports
import os
import sys
import inspect
import json
import tkinter as tk
from PIL import Image, ImageTk
from assets.libs.libConUtils import *
from assets.sceneSystem import *
from assets.generalFuncs import *
from assets.libs.GamehubAPI.libs.libcrypto.aes import GenerateKey,encdec

# Import SceneData
from assets.scenes.scene_sync import scene_sync
from assets.scenes.scene_game import *
from assets.scenes.scene_mainmenu import *
from assets.scenes.scene_levelselect import *
from assets.scenes.scene_options import *
from assets.scenes.scene_gameLoading import *
from assets.scenes.bdvd.scene_bdvd import *
from assets.scenes.scene_scoreboard import scene_scoreboard

# Setup console
os.system("") # Enable ANSI-codes on windows

# Get Arguments
cli_arguments = {}
try:
    cli_arguments["raw"] = sys.argv[1:]
except:
    cli_arguments["raw"] = []
# Set arguments
toPop = []
cli_arguments["usr"] = None
cli_arguments["exportLocal"] = False
cli_arguments["importLocal"] = None
if "--debug" in cli_arguments["raw"]:
    cli_arguments["debug"] = "--debug" in cli_arguments["raw"]
    i = cli_arguments["raw"].index("--debug")
    cli_arguments["raw"].pop(i)
for i,a in enumerate(cli_arguments["raw"]):
    if "-usr" == str(a):
        cli_arguments["usr"] = cli_arguments["raw"][i+1]
        toPop.append(i)
        toPop.append(i)
    if "--exportLocal" == str(a):
        cli_arguments["exportLocal"] = True
        toPop.append(i)
    if "-importLocal" == str(a):
        cli_arguments["importLocal"] = cli_arguments["raw"][i+1]
        toPop.append(i)
        toPop.append(i)
for i in toPop:
    cli_arguments["raw"].pop(i)
if len(cli_arguments["raw"]) > 0:
    cli_arguments["id"] = cli_arguments["raw"][0]

# Game Variables
GAME_VERSIONNR = "0.1"
MOD_FORMATVER = "1"
GAME_STDTITLE = f"Wormatron - Frogs Unite ({GAME_VERSIONNR}) MVP"
GAME_PARENTPATH = os.path.dirname( inspect.getabsfile(inspect.currentframe()) )
PATH_DEFAULTDATAFILE = f"{GAME_PARENTPATH}{os.sep}assets{os.sep}default.jsonc"
PATH_MODFOLDER = f"{GAME_PARENTPATH}{os.sep}mods"
PATH_LOCALDATAFILE = f"{GAME_PARENTPATH}{os.sep}assets{os.sep}local.data"
URL_LICENSE = "https://raw.githubusercontent.com/sbamboo/Wormatron/main/License"

# Debug file
if cli_arguments.get("debug") == True:
    open(f"{GAME_PARENTPATH}{os.sep}debug.state","w").write("True")
else:
    if os.path.exists(f"{GAME_PARENTPATH}{os.sep}debug.state"): os.remove(f"{GAME_PARENTPATH}{os.sep}debug.state")

# Setup console
setConTitle(f"{GAME_STDTITLE} - Console")

# Global Variables
current_scene = dict()

# Create CrossSceneStorage
csStore = crossSceneStorage()
# Save GameVariables
csStore.update(
    {
        "GAME_VERSIONNR": GAME_VERSIONNR,
        "MOD_FORMATVER": MOD_FORMATVER,
        "GAME_STDTITLE": GAME_STDTITLE,
        "GAME_PARENTPATH": GAME_PARENTPATH,
        "PATH_DEFAULTDATAFILE": PATH_DEFAULTDATAFILE,
        "PATH_MODFOLDER": PATH_MODFOLDER,
        "PATH_LOCALDATAFILE": PATH_LOCALDATAFILE,
        "URL_LICENSE": URL_LICENSE
    }
)
# Save cliArguments
csStore["cliArguments"] = cli_arguments

# Get defaultData
csStore["gameData_defaults_raw"] = removeComments(open(PATH_DEFAULTDATAFILE).read())
csStore["gameData_defaults"] = json.loads(csStore["gameData_defaults_raw"])
csStore["game_Data"] = csStore["gameData_defaults"].copy()

# Get localData
localDataMigrationKey = GenerateKey("GAMEHUBKEY_Wormatron_Export:154237a9-fcee-453f-9dfc-a8e677e9cd64:DONTSHARE!!!")
if csStore["cliArguments"]["importLocal"] != None:
    if os.path.exists(PATH_LOCALDATAFILE): os.remove(PATH_LOCALDATAFILE)
    PATH_LOCALDATAFILE_exp = csStore["cliArguments"]["importLocal"]
    if os.path.exists(PATH_LOCALDATAFILE_exp):
        content = open(PATH_LOCALDATAFILE_exp,"r").read()
        content = encdec(localDataMigrationKey, content, mode="dec")
        content = json.loads(content)
        csStore["localData"] = updateLocalData(csStore,PATH_LOCALDATAFILE,content)
    print("\033[32mImported localdata from migrationFile\033[0m")
else:
    csStore["localData"] = getLocalData(csStore,file=PATH_LOCALDATAFILE)
# DeEncryptData
if csStore["cliArguments"]["exportLocal"] == True:
    PATH_LOCALDATAFILE_exp = PATH_LOCALDATAFILE + ".export"
    if os.path.exists(PATH_LOCALDATAFILE_exp): os.remove(PATH_LOCALDATAFILE_exp)
    content = json.dumps(csStore["localData"])
    content = encdec(localDataMigrationKey, content, mode="enc")
    open(PATH_LOCALDATAFILE_exp,"x").write(content)
    print("\033[32mExported localdata\033[0m")
    exit()

# Define canvases/scenes
scenes = {
    "_uiCanvas": {
        "width": csStore["gameData_defaults"]["HeldSettings"]["uiCanvasSize"][0],
        "height": csStore["gameData_defaults"]["HeldSettings"]["uiCanvasSize"][1],
        "highlightThickness": 0,
        "backgroundColor": "magenta",
        "hiddenOnCreate": True,
        "reconstructOnSwitch": True,
        "overwrite": None
    },
    "scene_gameLoading": {
        "overwrite": "_uiCanvas",
        "function": scene_gameLoading
    },
    "scene_mainMenu": {
        "overwrite": "_uiCanvas",
        "function": scene_mainMenu
    },
    "scene_levelSelect": {
        "overwrite": "_uiCanvas",
        "function": scene_levelSelect
    },
    "scene_options": {
        "overwrite": "_uiCanvas",
        "function": scene_options
    },
    "scene_scoreboard": {
        "overwrite": "_uiCanvas",
        "function": scene_scoreboard
    },
    "scene_sync": {
        "overwrite": "_uiCanvas",
        "function": scene_sync
    },
    "scene_game": {
        "width": 500,
        "height": 500,
        "highlightThickness": 0,
        "backgroundColor": "green",
        "hiddenOnCreate": True,
        "reconstructOnSwitch": False,
        "overwrite": None,
        "function": scene_game
    },
    "scene_bdvd": {
        "width": 800,
        "height": 600,
        "highlightThickness": 0,
        "backgroundColor": "black",
        "hiddenOnCreate": True,
        "reconstructOnSwitch": True,
        "overwrite": None,
        "function": scene_bdvd
    }
}

# Setup basic pathtags
csStore["pathtags"] = {"source":f"{GAME_PARENTPATH}{os.sep}assets"}

# Load scoreboardOptions
csStore["scoreboardEnabled"] = bool(csStore["game_Data"]["Settings"]["Scoreboard"])
csStore["scoreboardOfflineMode"] = bool(csStore["game_Data"]["Settings"]["OfflineMode"])
csStore["scoreboard_apiConf"] = pathtag(csStore["pathtags"],csStore["game_Data"]["Settings"]["GamehubAPIConfFile"])

# Setup gamehub API connector
if csStore["scoreboardEnabled"] == True:
    from assets.libs.GamehubAPI import quickuseAPI
    csStore["scoreboardConnector"] = quickuseAPI.apiConfigScoreboardConnector(apiConfPath=csStore["scoreboard_apiConf"])
    # Ensure scoreboard exists
    if csStore["scoreboardConnector"].doesExist("wormatron") != True:
        csStore["scoreboardConnector"].create("wormatron",{})

# Asign soundSys
csStore["soundSys"] = SoundMap(csStore)

# Create the main window
tkWindow = tk.Tk()
tkWindow.title(f"{GAME_STDTITLE}")
tkWindow.configure(background=csStore["game_Data"]["HeldSettings"]["windowBackground"]["color"])
if csStore["game_Data"]["HeldSettings"]["windowBackground"]["image"]["enabled"] == "True":
    windowBackground_img = Image.open(pathtag(csStore["pathtags"],csStore["game_Data"]["HeldSettings"]["windowBackground"]["image"]["file"]))
    if csStore["game_Data"]["HeldSettings"]["windowBackground"]["image"]["useAverageColor"] == "True":
        windowBackground_lbl = tk.Label(tkWindow,bg=get_average_color(windowBackground_img),highlightthickness=0)
    else:
        windowBackground_lbl = tk.Label(tkWindow,bg=csStore["game_Data"]["HeldSettings"]["windowBackground"]["color"],highlightthickness=0)
    windowBackground_lbl.place(x=0, y=0, relwidth=1, relheight=1)
    csStore["windowBackground_resizeEventID"] = None
    tkWindow.bind("<Configure>", lambda event:winBack_resizeImage_caller(window=tkWindow,oImg=windowBackground_img,label=windowBackground_lbl,csStore=csStore,updateRate=csStore["game_Data"]["HeldSettings"]["windowBackground"]["image"]["updateRateMS"]))
    winBack_resizeImage_caller(window=tkWindow,oImg=windowBackground_img,label=windowBackground_lbl,csStore=csStore,updateRate=csStore["game_Data"]["HeldSettings"]["windowBackground"]["image"]["updateRateMS"])
# Hide if hiddenByDef
if csStore["gameData_defaults"]["HeldSettings"]["windowHiddenByDef"] == "True": tkWindow.withdraw()

# Save scene and window
csStore["window"] = tkWindow
csStore["scenes"] = scenes
csStore["current_scene"] = current_scene

# Create the canvases for each scene
create_scenes(csStore)

# Switch to the main menu scene
switch_scene(csStore,"scene_gameLoading")

# Start the main menu loop
runCurrentScene(csStore)

# Bind dvd
tkWindow.bind("<KeyPress-F4>",func=lambda event:switchAndRun(csStore, "scene_bdvd"))

# Start the tkinter appLoop
tkWindow.mainloop()