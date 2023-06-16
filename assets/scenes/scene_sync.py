# [Imports]
import tkinter as tk
from assets.sceneSystem import *
from assets.generalFuncs import clickStateStorage,actDebugCon,syncLocalData,pathtag
from assets.libs.libnetwa import netwa
import json
import webbrowser

# [Options]
def scene_sync(csStore):
    def open_link_TOS(event):
        nonlocal csStore
        GHTOS = json.loads(open(f"{csStore['GAME_PARENTPATH']}\\assets\\libs\\GamehubAPI\\API.json").read())["License"]
        webbrowser.open(GHTOS)
    def open_link_license(event):
        nonlocal csStore
        GHTOS = csStore['URL_LICENSE']
        webbrowser.open(GHTOS)
    # Get Canvas and Window
    current_scene = csStore["current_scene"]
    canvas = current_scene["canvas"]
    window = csStore["window"]
    actDebugCon(csStore) # DEBUG
    # Get scoreboard and if no internet, just switch to mainMenu
    hasInternet = netwa.has_connection()
    if hasInternet != False:
        hasInternet == True
    csStore["hasInternet"] = hasInternet
    # Check for url user
    if csStore["cliArguments"]["usr"] != None:
        csStore["player_username"] = csStore["cliArguments"]["usr"]
        switchAndRun(csStore,"scene_mainMenu")
    # Define a clickStateStorage
    clickStates = clickStateStorage()
    # Define ui objs
    globals()["background_img"] = tk.PhotoImage(file=pathtag(csStore["pathtags"],csStore["game_Data"]["HeldSettings"]["mainMenuBackground"]))
    background = canvas.create_image(0,0,anchor=tk.NW,image=background_img)
    backgroundBox = canvas.create_rectangle(150,0,850,250,fill="gray")
    title = canvas.create_text(current_scene["width"]/2,20,text="Enter your GamehubAPI username:",font=("Consolas",30))
    entry = tk.Entry(window,font=("Consolas",15),fg="Black",bg="White",insertbackground="black")
    entry_window = canvas.create_window(current_scene["width"]/2, 80, window=entry)
    button = tk.Button(window, text="Sync", command=lambda:clickStates.toggle("username"),font=("Consolas",15),fg="green")
    button_window = canvas.create_window(current_scene["width"]/2-40, 120, window=button)
    btn_exit_obj = tk.Button(window, text="Exit", command=lambda:clickStates.toggle("exit"),font=('Consolas',15),fg="red")
    btn_exit = canvas.create_window(current_scene["width"]/2+40, 120, window=btn_exit_obj)
    disclaimer = canvas.create_text(current_scene["width"]/2,180,fill="red",text="By pressing sync, you agree to the\naswell as the\nRemember that you are only allowed to have one account on gamehub's official servers! (so check your name)\nTo not use GamehubAPI, disable scoreboard in settings or use your own api.conf file!")
    TosLink = canvas.create_text((current_scene["width"]/2)-220,180-8, fill="Tomato",text="TOS for gamehubAPI.",anchor=tk.W)
    canvas.tag_bind(TosLink,"<Button-1>",open_link_TOS)
    LicenseLink = canvas.create_text((current_scene["width"]/2)-108,180-23, fill="Tomato",text="license agreement for wormatron,",anchor=tk.W)
    canvas.tag_bind(LicenseLink,"<Button-1>",open_link_license)
    # No internet info
    if csStore["hasInternet"] == False:
        x,y = 5,current_scene["height"]-5
        canvas.create_rectangle(x-2,y+2,x+550,y-20,fill="black")
        canvas.create_text(x,y,anchor=tk.SW,text="No internet, data will be saved localy and synced on restart!", fill="red", font=("Consolas", 12))
    # Define menu loop
    def internal_loop():
        # Update the canvas
        canvas.update()
        # Get scenes and current_scene
        scenes = csStore["scenes"]
        current_scene = csStore["current_scene"]
        # GotoMenu
        if clickStates.get("exit") == True:
            window.destroy()
            exit()
        # Username entered
        elif clickStates.get("username") == True:
            csStore["player_username"] = entry.get()
            syncLocalData(csStore)
            switchAndRun(csStore,"scene_mainMenu")
        # Schedule if no buttons was clicked
        else:
            canvas.after(100, internal_loop)
    # Execute first cycle
    internal_loop()