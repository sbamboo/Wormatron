# [Imports]
import tkinter as tk
from assets.sceneSystem import *
from assets.generalFuncs import clickStateStorage,listMods,actDebugCon,gainBadge

# [Options]
def scene_options(csStore):
    # Get Canvas and Window
    current_scene = csStore["current_scene"]
    canvas = current_scene["canvas"]
    window = csStore["window"]
    actDebugCon(csStore) # DEBUG
    # Define a clickStateStorage
    clickStates = clickStateStorage()
    # Define buttons
    btn_gotoMenu_obj = tk.Button(window, text="🔙", command=lambda:clickStates.toggle("gotoMenu"),font=('Consolas',18))
    btn_gotoMenu = canvas.create_window(0,0,anchor=tk.NW, window=btn_gotoMenu_obj)
    # Get mods
    csStore["game_modsList"] = listMods(csStore["PATH_MODFOLDER"],csStore["GAME_VERSIONNR"],csStore["MOD_FORMATVER"])
    # Define menu loop
    def internal_loop():
        # Update the canvas
        canvas.update()
        # Get scenes and current_scene
        scenes = csStore["scenes"]
        current_scene = csStore["current_scene"]
        # GotoMenu
        if clickStates.get("gotoMenu") == True:
            switch_scene(csStore,"scene_mainMenu")
            runCurrentScene(csStore)
        # Schedule if no buttons was clicked
        else:
            canvas.after(100, internal_loop)
    # Execute first cycle
    internal_loop()