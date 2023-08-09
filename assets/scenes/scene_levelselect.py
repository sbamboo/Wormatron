# [Imports]
import os
import tkinter as tk
from assets.sceneSystem import *
from assets.generalFuncs import *

# [LevelSelect]
def scene_levelSelect(csStore):
  # [FUNCTIONS]
    # Function to render the placks on a row
    def renderGrid(canvas,rows,oSize,hPad,vPad,winPadX,cSize,gridWidth,player_lvl,player_xp):
        rGrid = {"shiftEvent":{"type":None,"currentY":None,"finalY":None},"minY":None,"maxY":None,"rows":[]}
        for rIndex,rowD in enumerate(rows):
            # Calculate Y base Coords
            baseY = cSize[1]/2 - oSize[1]/2
            # moveFactor should be adjusted 0.5 per row, but we want to start 3 steps back from 1 so 1-(0.5*3) = -0.5, this excludes footer/header +1. Then we add 0.5 per row
            adj = 0.5
            moveFactor = -adj + adj*len(rows)
            topY = baseY - ((oSize[1]+vPad)*((len(rows)-1)/2))/moveFactor
            curY = topY + (oSize[1]+vPad)*rIndex
            # Calculate startingY
            rGrid["shiftEvent"]["currentY"] = topY
            # Calculate min/max Y
            rGrid["maxY"] = topY + (oSize[1]+vPad)
            rGrid["minY"] = topY + (oSize[1]+vPad)*(len(rows)-2)
            # Calculate X
            row = {"pos":rIndex,"placks":[]}
            if rowD.get("placks") == None: rowD["placks"] = []
            for pIndex,plack in enumerate(rowD["placks"]):
                xId = pIndex+1
                centerPadding = round( ((cSize[0]-(2*winPadX)) - (gridWidth*(oSize[0]+hPad)))/2 )
                # Objects
                curX = oSize[0]*pIndex + hPad*xId + centerPadding*xId
              # Prep
                plack["lock"]["locked"] = isLvl(plack["lock"]["unlock"],player_xp,player_lvl)
              # Render
                # Get info
                name = plack["name"]
                oid = f"levelSelect_{name}"
                # Objects
                objects = {
                    "edge": canvas.create_image(curX,curY,anchor=tk.NW,image=globals()[f"{oid}_edge"]),
                    "icon": canvas.create_image(curX+25,curY+25,anchor=tk.NW,image=globals()[f"{oid}_icon"]),
                    "name": canvas.create_text(curX+(oSize[0]/2),curY+10,text=name,font=('Consolas',15)),
                    "desc": canvas.create_text(curX+(oSize[0]/2),curY+200,text=plack["description"],font=('Consolas',7)),
                    "diff": canvas.create_text(curX+(oSize[0]/2),curY+220,text=f"Difficulty: {plack['difficulty']}",font=('Consolas',8)),
                    "lock": canvas.create_image(curX+25,curY+25,anchor=tk.NW),
                    "lock_text": canvas.create_text(curX+(oSize[0]/2),curY+40,fill="yellow")
                }
                if plack["lock"]["locked"] == True: 
                    canvas.itemconfig(objects["lock"],image=globals()["levelLocked"])
                    if plack['lock']['unlock'] == "never":
                        canvas.itemconfig(objects["lock_text"],text=f"Permanently Locked",fill="red")
                    elif plack['lock']['unlock'] == "comming-soon":
                        canvas.itemconfig(objects["lock_text"],text=f"Comming soon")
                    else:
                        text,overwrite = isLvlText(plack['lock']['unlock'])
                        if overwrite == False:
                            canvas.itemconfig(objects["lock_text"],text=f"Unlocks at {text}")
                        else:
                            canvas.itemconfig(objects["lock_text"],text=text)
                row["placks"].append({"name":name,"objects":objects,"lock":plack["lock"]})
            rGrid["rows"].append(row)
        return rGrid
    def onClick(event):
        nonlocal rGrid,oSize,doLoop
        # Get event
        cX,cY = event.x, event.y
        # Go trough the placks and check if it was clicked
        for row in rGrid["rows"]:
            for plack in row["placks"]:
                x1,y1 = canvas.coords(plack["objects"]["edge"])
                if y1 == rGrid["maxY"]:
                    x2,y2 = x1+oSize[0],y1+oSize[1]
                    if isBetweenI(cX,x1,x2) and isBetweenI(cY,y1,y2): 
                        if plack["lock"]["locked"] == False:
                            doLoop = False
                            csStore["game_selectedMap"] = plack["name"]
                            csStore["game_mapData"] = csStore["game_Data"]["Maps"][ csStore["game_selectedMap"] ]
                            switch_scene(csStore,"scene_game")
                            runCurrentScene(csStore)


  # [INIT]
    # Update local data
    updateCopyOfLocal(csStore)
    # Get Canvas and Window
    current_scene = csStore["current_scene"]
    canvas = current_scene["canvas"]
    window = csStore["window"]
    pathtags = csStore["pathtags"]
    gameData = csStore["game_Data"]
    player_xp = csStore["localData"][csStore['player_username']]["player_xp"]
    player_lvl = csStore["localData"][csStore['player_username']]["player_lvl"]
    # Default Values
    doLoop = True
    placks = []
    # Define a clickStateStorage
    clickStates = clickStateStorage()
    # Define buttons
    btn_gotoMenu_obj = tk.Button(window, text="🔙", command=lambda:clickStates.toggle("gotoMenu"),font=('Canvases',18))
    btn_gotoMenu = canvas.create_window(0,0,anchor=tk.NW, window=btn_gotoMenu_obj)
    # Fallback System Setup
    if csStore["game_Data"]["Settings"]["LevelSelectSystem"].lower() == "fallback":
        infoText = canvas.create_text(20, 20, text="Using fallback levelSelector, see console!", anchor=tk.NW, fill='white', font=("Consolas", 12))
        canvas.coords(btn_gotoMenu,20,40)
        fallback_selector_input = "CODE:ERR_INVALID_ID"
        fallback_selector_wasCalled = False
    # UI system setup
    else:
        # Preset prepping
        hasPreset = None
        for index,key in enumerate(csStore["game_Data"]["Maps"].keys()):
            isIndex = str(csStore["cliArguments"].get("id")) == str(index)
            isStr = str(csStore["cliArguments"].get("id")) == str(key)
            if isIndex == True or isStr == True:
                if isIndex == True: key = list(csStore["game_Data"]["Maps"].keys())[index]
                hasPreset = key
        # Show ui if not preset
        if hasPreset == None:
            # GenerateLevelList
            hPad = 20
            vPad = 30
            oSize = [200,250]
            cSize = [int(canvas["width"]),int(canvas["height"])]
            wPad = [40,40]
            levelList = generateLevelList(csStore["game_Data"]["Maps"],pathtags)
            gridWidth = getGridWidth(winWidth=int(cSize[0]),winPadX=wPad[0],horizPad=hPad,objSizeX=oSize[0])
            # Prepare texture
            for level in levelList:
                name = f"levelSelect_{level['name']}"
                globals()[f"{name}_edge"] = tk.PhotoImage(file=level["edgeBackgroundPath"])
                globals()[f"{name}_icon"] = tk.PhotoImage(file=level["iconPath"])
            # Prepare other textures
            globals()["levelLocked"] = tk.PhotoImage(file=f"{csStore['GAME_PARENTPATH']}\\assets\\ui\\lock.png".replace("\\",os.sep))
            # Generate grid
            levelGrid = generateGrid_empty(levelList,gridWidth)
            rGrid = renderGrid(canvas=canvas,rows=levelGrid["rows"],oSize=oSize,hPad=hPad,vPad=vPad,winPadX=wPad[0],cSize=cSize,gridWidth=gridWidth,player_lvl=player_lvl,player_xp=player_xp)
            # Define up/down buttons
            btn_up_obj = tk.Button(window, text="⮝", command=lambda:clickStates.set("up",True),font=('Consolas',12),width=2)
            btn_up = canvas.create_window(int(canvas["width"])/2,wPad[0], window=btn_up_obj)
            btn_down_obj = tk.Button(window, text="⮟", command=lambda:clickStates.set("down",True),font=('Consolas',12),width=2)
            btn_down = canvas.create_window(int(canvas["width"])/2,(int(canvas["height"])-wPad[0]), window=btn_down_obj)
            # Define gradients
            globals()[f"levelSelect_upperGrad"] = tk.PhotoImage(file=pathtag(pathtags,"%source%\\ui\\upper_grad_gray.png"))
            upperGrad = canvas.create_image(0,0,anchor=tk.NW,image=levelSelect_upperGrad)
            globals()[f"levelSelect_lowerGrad"] = tk.PhotoImage(file=pathtag(pathtags,"%source%\\ui\\lower_grad_gray.png"))
            lowerGrad = canvas.create_image(0,cSize[1]-100,anchor=tk.NW,image=levelSelect_lowerGrad)
            # Show play stats
            pstat_back = canvas.create_rectangle(46,-1,226,46,outline="gray",fill="white")
            pstat_lvl =  canvas.create_text(54,3, text=f"Player LVL: {player_lvl}", fill="blue", font=('Consolas',14), anchor=tk.NW)
            pstat_lvl =  canvas.create_text(54,20, text=f"Player XP:  {player_xp}", fill="blue", font=('Consolas',14), anchor=tk.NW)

    # Define menu loop
    def internal_loop():
        nonlocal doLoop,placks,fallback_selector_input,fallback_selector_wasCalled,rGrid,oSize,hPad,player_lvl,player_xp
      # [DEBUG]
        actDebugCon(csStore)
      # [PREP]
        # Update the canvas
        canvas.update()
      # [FALLBACKsys]
        if csStore["game_Data"]["Settings"]["LevelSelectSystem"].lower() == "fallback":
            # Select a map using the fallback function and switch to game
            if fallback_selector_input == "CODE:ERR_INVALID_ID":
                if fallback_selector_wasCalled == False:
                    fallback_selector_wasCalled = True
                    fallback_selector_input = showMapSelector(gameData=csStore["game_Data"],preset=csStore["cliArguments"].get("id"),lockingSys={"hp":player_xp,"lvl":player_lvl})
                    fallback_selector_wasCalled = False
            else:
                if fallback_selector_input == "CODE:EXIT":
                    doLoop = False
                    clickStates.set("gotoMenu",True)
                else:
                    doLoop = False
                    csStore["game_selectedMap"] = fallback_selector_input
                    csStore["game_mapData"] = csStore["game_Data"]["Maps"][ csStore["game_selectedMap"] ]
                    switch_scene(csStore,"scene_game")
                    runCurrentScene(csStore)
      # [UIsys]
        if csStore["game_Data"]["Settings"]["LevelSelectSystem"].lower() == "ui":
            # Preset
            if hasPreset != None:
                doLoop = False
                csStore["game_selectedMap"] = hasPreset
                csStore["game_mapData"] = csStore["game_Data"]["Maps"][ csStore["game_selectedMap"] ]
                switch_scene(csStore,"scene_game")
                runCurrentScene(csStore)
            else:
                # Show/Hide buttons
                updateButtonShows(rGrid,canvas,upBtn=btn_up,dwBtn=btn_down)
                # Check buttons
                if clickStates.get("up") == True:
                    clickStates.set("up",False)
                    rGrid = gridDown(rGrid,oSize,vPad,canvas)
                if clickStates.get("down") == True:
                    clickStates.set("down",False)
                    rGrid = gridUp(rGrid,oSize,vPad,canvas)
                # Move grid
                rGrid = moveGrid(rGrid,canvas,12)
      # [POST]
        # GotoMenu
        if clickStates.get("gotoMenu") == True:
            switch_scene(csStore,"scene_mainMenu")
            runCurrentScene(csStore)
        # Schedule if no buttons was clicked
        else:
            if doLoop == True:
                canvas.after(10, internal_loop)
            
    # Execute first cycle
    window.bind(gameData["Settings"]["Keybinds"]["click"], onClick)
    internal_loop()