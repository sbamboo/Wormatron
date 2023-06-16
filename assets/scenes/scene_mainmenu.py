# [Imports]
import os
import tkinter as tk
from assets.sceneSystem import *
from assets.generalFuncs import clickStateStorage,pathtag,actDebugCon,updateLocalData

# [Main Menu]
def scene_mainMenu(csStore):
    # Get Canvas and Window
    current_scene = csStore["current_scene"]
    canvas = current_scene["canvas"]
    window = csStore["window"]
    pathtags = csStore["pathtags"]
    winMid = [ current_scene["width"]/2, current_scene["height"]/2 ]
    # Update data
    if csStore["localData"] == None or csStore["localData"].get(csStore["player_username"]) == None:
        csStore["localData"] = updateLocalData(csStore,file=csStore["PATH_LOCALDATAFILE"],newData={csStore["player_username"]:{"player_xp":0,"player_lvl":0}})
    # Define a clickStateStorage
    clickStates = clickStateStorage()
    # Create Backgrounds
    globals()["mm_background"] = tk.PhotoImage( file=pathtag(pathtags,csStore["gameData_defaults"]["HeldSettings"]["mainMenuBackground"]) )
    canvas.create_image(0,0,anchor=tk.NW,image=mm_background)
    # Create titleText
    canvas.create_text(winMid[0], winMid[1]-170, text="Wormatron", fill='yellow', font=("Consolas", 50))
    # Define buttons
    btn_startGame_obj = tk.Button(window, text="Start", command=lambda:clickStates.toggle("startGame"),font=("Consolas", 15),width=18)
    btn_startgame = canvas.create_window(winMid[0],winMid[1]-70, window=btn_startGame_obj)
    btn_scoreboard_obj = tk.Button(window, text="Scoreboard/Account", command=lambda:clickStates.toggle("scoreboard"),font=("Consolas", 15),width=18)
    btn_scoreboard = canvas.create_window(winMid[0],winMid[1]-20, window=btn_scoreboard_obj)
    btn_options_obj = tk.Button(window, text="Options", command=lambda:clickStates.toggle("options"),font=("Consolas", 15),width=18)
    btn_options = canvas.create_window(winMid[0],winMid[1]+30, window=btn_options_obj)
    btn_exitGame_obj = tk.Button(window, text="Exit", command=lambda:clickStates.toggle("exitGame"),font=("Consolas", 15),width=18)
    btn_exitgame = canvas.create_window(winMid[0],winMid[1]+80, window=btn_exitGame_obj)
    snowNextScene = False
    doLoop = True
    # No internet info
    if csStore["hasInternet"] == False:
        x,y = 5,current_scene["height"]-5
        canvas.create_rectangle(x-2,y+2,x+550,y-20,fill="black")
        canvas.create_text(x,y,anchor=tk.SW,text="No internet, data will be saved localy and synced on restart!", fill="red", font=("Consolas", 12))
    # Signed in as
    canvas.create_rectangle(0,0,270,30,fill="lightblue")
    canvas.create_text(5,5, anchor=tk.NW, text=f"Signed in as: ",font=("Consolas", 12),fill="Black")
    canvas.create_text(130,5, anchor=tk.NW, text=csStore['player_username'],font=("Consolas", 12),fill="Orange")
    # Define menu loop
    def internal_loop():
        nonlocal doLoop,snowNextScene
        actDebugCon(csStore) # DEBUG
        # Update the canvas
        canvas.update()
        # Get scenes and current_scene
        scenes = csStore["scenes"]
        current_scene = csStore["current_scene"]
        # StartGame
        if clickStates.get("startGame") == True:
            globals()["ui_waiting"] = tk.PhotoImage(file=f"{csStore['GAME_PARENTPATH']}\\assets\\ui\\ui_waiting.png".replace("\\",os.sep))
            csStore["ui_waiting_texture"] = ui_waiting
            csStore["ui_waiting_canvas"] = canvas
            csStore["ui_waiting_object"] = csStore["ui_waiting_canvas"].create_image(round(int(csStore["current_scene"]["width"])/2),round(int(csStore["current_scene"]["height"])/2),image=ui_waiting)
            csStore["ui_waiting_canvas"].itemconfigure(btn_startgame,state="hidden")
            csStore["ui_waiting_canvas"].itemconfigure(btn_scoreboard,state="hidden")
            csStore["ui_waiting_canvas"].itemconfigure(btn_options,state="hidden")
            csStore["ui_waiting_canvas"].itemconfigure(btn_exitgame,state="hidden")
            if snowNextScene == True:
                doLoop = False
                switch_scene(csStore,"scene_levelSelect")
                runCurrentScene(csStore)
            else:
                snowNextScene = True
        # Scoreboard
        if clickStates.get("scoreboard") == True:
            globals()["ui_waiting"] = tk.PhotoImage(file=f"{csStore['GAME_PARENTPATH']}\\assets\\ui\\ui_waiting.png".replace("\\",os.sep))
            csStore["ui_waiting_texture"] = ui_waiting
            csStore["ui_waiting_canvas"] = canvas
            csStore["ui_waiting_object"] = csStore["ui_waiting_canvas"].create_image(round(int(csStore["current_scene"]["width"])/2),round(int(csStore["current_scene"]["height"])/2),image=ui_waiting)
            csStore["ui_waiting_canvas"].itemconfigure(btn_startgame,state="hidden")
            csStore["ui_waiting_canvas"].itemconfigure(btn_scoreboard,state="hidden")
            csStore["ui_waiting_canvas"].itemconfigure(btn_options,state="hidden")
            csStore["ui_waiting_canvas"].itemconfigure(btn_exitgame,state="hidden")
            if snowNextScene == True:
                doLoop = False
                switch_scene(csStore,"scene_scoreboard")
                runCurrentScene(csStore)
            else:
                snowNextScene = True
        # Options
        if clickStates.get("options") == True:
            switch_scene(csStore,"scene_options")
            runCurrentScene(csStore)
            doLoop = False
        # ExitGame
        if clickStates.get("exitGame") == True:
            doLoop = False
            window.destroy()
            exit()
        # Schedule if no buttons was clicked
        if doLoop == True:
            canvas.after(100, internal_loop)
    # Execute first cycle
    internal_loop()