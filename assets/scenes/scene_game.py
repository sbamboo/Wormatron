# [Imports]
import random
import tkinter as tk
from assets.sceneSystem import *
from assets.generalFuncs import *
from assets.sceneSystem import *

# [GameLoop]
def scene_game(csStore,sys="exp"):
    def updateLocal(csStore,hp):
        # Update local data
        updateCopyOfLocal(csStore)
        # Update local Save
        xpAdd = calcXP(csStore,hp)
        xp = int(csStore["localData"][csStore["player_username"]]["player_xp"])+ xpAdd
        if sys == "factor":
            lvl = calcLvl_factor(xp,factor=1.15)
        elif sys == "exp":
            lvl = calcLvl_exp(xp,exp=5)
        updateLocalData(csStore,file=csStore["PATH_LOCALDATAFILE"],newData={csStore["player_username"]:{"player_xp":xp,"player_lvl":lvl}})
        if csStore["hasInternet"] != False:
            syncLocalData(csStore)
    # Get Canvas and Window
    current_scene = csStore["current_scene"]
    canvas = current_scene["canvas"]
    window = csStore["window"]

    # LoadMods
    csStore["game_modsList"] = listMods(csStore["PATH_MODFOLDER"],csStore["GAME_VERSIONNR"],csStore["MOD_FORMATVER"])
    loadMods(csStore)
    # Get GameData & mapData
    gameData = csStore["game_Data"]
    mapData = csStore["game_mapData"]
    gameSelectedMap = csStore["game_selectedMap"]
    pathtags = csStore["pathtags"]

    # Modify canvas size
    width = mapData["WindowSize"][0]
    height = mapData["WindowSize"][1] + mapData["HotbarHeight"]
    canvas.configure(width=width, height=height)

    # Create default values
    csStore["gameRunning"] = False
    csStore["spawnEnemies"] = False
    lastClickCoords = [0,0]
    lastClickedButton = None
    Enemies = []
    Characters = []
    Projectiles = []
    _enemiesSpawned = 0
    player_xp = csStore["localData"][csStore['player_username']]["player_xp"]
    player_lvl = csStore["localData"][csStore['player_username']]["player_lvl"]

    # Register waitCycles
    wcs = waitCycle()
    wcs.create(name="spawnEnemies",max=int(mapData["EnemySpawnCooldown"])*3)
    wcs.create(name="spawnProjectile",max=int(mapData["ProjectileSpawnCooldown"])*3)
    wcs.create(name="moveEnemiesDirect",max=int(mapData["moveEnemiesCooldown"])*3)
    wcs.create(name="spawnEnemyDecrease",max=int(mapData["EnemySpawnRateCooldown"])*3)

    # Create background
    globals()["img_map_background"] = tk.PhotoImage(file=pathtag(pathtags,mapData["Background"]))
    map_background = canvas.create_image(0, 0, anchor=tk.NW, image=img_map_background)

    # Create HotbarBackground
    globals()["img_map_hotbarBackground"] = tk.PhotoImage(file=pathtag(pathtags,mapData["HotbarBackground"]))
    hotbarBackground = canvas.create_image(0, 500, anchor=tk.NW, image=img_map_hotbarBackground)

    # Prep textures
    gameTextures = {"Characters":{},"Enemies":{}}
    ## characters
    for char in gameData["Characters"]:
        globals()["temp_idle"] = tk.PhotoImage(file=pathtag(pathtags,gameData["Characters"][char]["Textures"]["idle"]))
        globals()["temp_shooting"] = tk.PhotoImage(file=pathtag(pathtags,gameData["Characters"][char]["Textures"]["shooting"]))
        globals()["temp_projectile"] = tk.PhotoImage(file=pathtag(pathtags,gameData["Characters"][char]["Textures"]["projectile"]))
        gameTextures["Characters"][char] = {
            "idle":       temp_idle,
            "shooting":   temp_shooting,
            "projectile": temp_projectile
        }
    ## enemies
    for enemy in gameData["Enemies"]:
        globals()["temp_texture"] = tk.PhotoImage(file=pathtag(pathtags,gameData["Enemies"][enemy]["Texture"]))
        gameTextures["Enemies"][enemy] = {
            "Texture": temp_texture
        }
    ## others
    globals()["img_victory"] = tk.PhotoImage(file=pathtag(pathtags,mapData["VictoryImage"]))
    globals()["img_gameover"] = tk.PhotoImage(file=pathtag(pathtags,mapData["GameoverImage"]))

    # Create grid
    gameGrid,gridTileWidth,gridTileHeight = generateGrid(mapData["WindowSize"],mapData["GridSize"])

    # Generate tracks and complexTracks
    enemyTrack = convertEnemyTrack(mapData["EnemyTrack"],False)
    enemyTrack_coords = convertEnemyTrack(mapData["EnemyTrack"],True,gameGrid)
    enemyTrack_complex_uncompressed = generateComplexTrack(enemyTrack_coords,mapData["WindowSize"],mapData["GridSize"])
    enemyTrack_complex = compressComplexTrack(enemyTrack_complex_uncompressed)

    # Drawgrid
    for xRow in gameGrid:
        for yRow in gameGrid[str(xRow)]:
            tile = gameGrid[str(xRow)][str(yRow)]
            topLeft = tile["gridCoordsTL"]
            topRight = tile["gridCoordsTR"]
            botLeft = tile["gridCoordsBL"]
            botRight = tile["gridCoordsBR"]
            canvas.create_line(topLeft[0],topLeft[1], topRight[0],topRight[1], fill=mapData["GridColor"], width=1)
            canvas.create_line(topRight[0],topRight[1], botRight[0],botRight[1], fill=mapData["GridColor"], width=1)

    # Draw home and enemy base
    globals()["img_homebase"] = tk.PhotoImage(file=pathtag(pathtags, mapData["HomeBase"]["Texture"]))
    homebase_cords = convertEnemyTrack([mapData["HomeBase"]["Tile"]])[0]
    homebase_tile = getTile(homebase_cords[0],homebase_cords[1], gameGrid)
    homebase = canvas.create_image(homebase_tile["gridCoordsTL"][0],homebase_tile["gridCoordsTL"][1], image=img_homebase, anchor=tk.NW)
    globals()["img_enemybase"] = tk.PhotoImage(file=pathtag(pathtags, mapData["EnemyBase"]["Texture"]))
    enemybase_cords = convertEnemyTrack([mapData["EnemyBase"]["Tile"]])[0]
    enemybase_tile = getTile(enemybase_cords[0],enemybase_cords[1], gameGrid)
    enemybase = canvas.create_image(enemybase_tile["gridCoordsTL"][0],enemybase_tile["gridCoordsTL"][1], image=img_enemybase, anchor=tk.NW)

    # Draw buttons
    charSelectButtons = {}
    btnOf = 0
    y = mapData["WindowSize"][1] + 5
    for char in list(mapData["SelectableCharacters"].keys()):
        char2 = char + f"(${gameData['Characters'][char]['Cost']})"
        lenOfCharPX = len(char2)*10 # 10 is px/char
        if btnOf+lenOfCharPX > mapData["WindowSize"][0]:
            y+= 20
            btnOf = 0
        charSelectButtons[char] = {}
        charSelectButtons[char]["rect"] = canvas.create_rectangle(5+btnOf,y, 5+btnOf+lenOfCharPX,y+20, fill='gray')
        charSelectButtons[char]["text"] = canvas.create_text(5+7+btnOf, y, text=char2, anchor=tk.NW, fill='white', font=("Consolas", 12)) # 12 is for amnt between objs
        btnOf += 5+lenOfCharPX
    # Draw info (setup)
    y = mapData["WindowSize"][1]+mapData["HotbarHeight"]
    player_hp = mapData['PlayerStartHealth']
    player_hp_obj = canvas.create_text(20, y-45, text=f"HP: {player_hp}", anchor=tk.NW, fill='Yellow', font=("Consolas", 12))
    player_money = mapData['PlayerStartMoney']
    player_money_obj = canvas.create_text(20, y-25, text=f"Cash: ${player_money}", anchor=tk.NW, fill='Yellow', font=("Consolas", 12))

    # Draw splash info
    globals()["img_splash"] = tk.PhotoImage(file=pathtag(pathtags,mapData["SplashImage"]))
    img_splash_obj = canvas.create_image((mapData["WindowSize"][0]/2),(mapData["WindowSize"][1]/2),image=img_splash)
    txt_splash_obj = canvas.create_text((mapData["WindowSize"][0]/2),(mapData["WindowSize"][1]/2)+30, text=f"Press '{keyOnly(gameData['Settings']['Keybinds']['start'])}' to start...", fill='Yellow', font=("Consolas", 12))
    splash = {"img":img_splash_obj,"text":txt_splash_obj}

    # FUNC: ===================[Define OnClick Function]===================
    def onClick(event):
        nonlocal lastClickCoords,lastClickedButton,player_money,Characters,gameGrid,mapData
        # Get event
        lastClickCoords = event.x, event.y
        # Check clicks
        if csStore["gameRunning"]:
            # Check click buttons
            for btn in charSelectButtons:
                coords = canvas.coords(charSelectButtons[btn]["rect"])
                tl = [coords[0],coords[1]]
                tr = [coords[2],coords[1]]
                bl = [coords[0],coords[3]]
                if wasClickedGen(tl,tr,bl,lastClickCoords):
                    # Reset button color
                    try: canvas.itemconfig(charSelectButtons[lastClickedButton]["rect"],fill="gray")
                    except: pass
                    lastClickedButton = btn
                    canvas.itemconfig(charSelectButtons[btn]["rect"],fill="DarkGray")
                    print(f"[\033[33mDEBUG\033[0m]: \033[90mClicked on button \033[34m{lastClickedButton}\033[0m")
            # Check click tiles
            for xRow in gameGrid:
                for yRow in gameGrid[str(xRow)]:
                    tile = gameGrid[str(xRow)][str(yRow)]
                    # Check if lastClickPosition was over the tile
                    if wasClickedTile(tile,lastClickCoords):
                        # if not excluded
                        if [xRow,yRow] not in enemyTrack:
                            justCreated = False
                            # check if char has been choosen
                            if lastClickedButton != "None" and lastClickedButton != None:
                                if gameGrid[str(xRow)][str(yRow)]["placedOn"] == False or gameGrid[str(xRow)][str(yRow)]["placedOn"] == None:
                                    pos = [ tile["gridCoordsTL"][0],tile["gridCoordsTL"][1] ]
                                    char = gameData["Characters"][lastClickedButton].copy()
                                    char["name"] = lastClickedButton
                                    # Check for cash
                                    if player_money >= char["Cost"]:
                                        char["Object"] = canvas.create_image(pos[0],pos[1], anchor=tk.NW, image=gameTextures["Characters"][lastClickedButton]["idle"])
                                        char["cooldownTilShoot"] = 0
                                        char["returnTextureIn"] = {"current":0,"max":0}
                                        Characters.append(char)
                                        gameGrid[str(xRow)][str(yRow)]["placedOn"] = True
                                        player_money -= char["Cost"]
                                        justCreated = True
                                    else:
                                        print(f"[\033[33mDEBUG\033[0m]: \033[31mNot enough money!\033[0m")                 
                                    # Reset button color
                                    canvas.itemconfig(charSelectButtons[lastClickedButton]["rect"],fill="gray")
                                    lastClickedButton = None
                                else:
                                    justCreated = True
                                    print(f"[\033[33mDEBUG\033[0m]: \033[90mTile already ocupied \033[31m[{xRow}, {yRow}]\033[0m")                 
                            # Sell:
                            if mapData["AllowSell"] and justCreated == False:
                                if gameGrid[str(xRow)][str(yRow)]["placedOn"] == True:
                                    pos = [ tile["gridCoordsTL"][0],tile["gridCoordsTL"][1] ]
                                    for index,char in enumerate(Characters):
                                        oPos = canvas.coords(char["Object"])
                                        if pos[0] == oPos[0] and pos[1] == oPos[1]:
                                            canvas.delete(char["Object"])
                                            Characters.pop(index)
                                            gameGrid[str(xRow)][str(yRow)]["placedOn"] = False
                                            # money
                                            if mapData.get("SellbackFactor") == None:
                                                player_money += char["Cost"]
                                            else:
                                                getBackMoney = round( int(char["Cost"])*mapData["SellbackFactor"] )
                                                player_money += getBackMoney
                            print(f"[\033[33mDEBUG\033[0m]: \033[90mClicked on tile \033[34m{tile['gridPlacement']}\033[0m")
    # FUNC: ===================[Define Binded Functions]===================
    def startGame(e):
        # Unbind space
        window.unbind(gameData["Settings"]["Keybinds"]["start"])
        # Setup
        csStore["spawnEnemies"] = True
        csStore["gameRunning"] = True
        # Play sounds
        if gameData["Settings"]["BackgroundMusic"] == "True":
            csStore["soundSys"].playSound(mapData["BackgroundSound"],loop=True)
        # Remove splash
        canvas.delete(splash["img"])
        canvas.delete(splash["text"])
        # Schedule gameloop
        canvas.after(10,game_loop)
    def exitGame(e):
        csStore["spawnEnemies"] = False
        csStore["gameRunning"] = False
        csStore["soundSys"].stopAll()
        switch_scene(csStore, "scene_mainMenu")
        runCurrentScene(csStore)
    # FUNC: ===================[Define GameLoop]===================
    def game_loop():
        nonlocal canvas,enemyTrack,gameData,Enemies,Characters,Projectiles,_enemiesSpawned,player_hp,player_hp_obj,player_money,player_hp
      # [DEBUG]
        if getDebugCon() == "exit":
            exitGame(0)
        else:
            actDebugCon(csStore)
      # [PREP]
        # Update the canvas
        canvas.update()
      # [MAIN]
        # Spawn enemies
        if csStore["spawnEnemies"] == True:
            if wcs.increment("spawnEnemies") == True:
                # spawn enemy
                pos = enemyTrack_coords[0][0]
                # TEMP, spawn random enemy
                toSpawn = random.choice( list(gameData["Enemies"].keys()) )
                # create object
                enemy = gameData["Enemies"][toSpawn].copy()
                offsetX = random.randint(-10,10)
                offsetY = random.randint(-10,10)
                enemy["Offsets"] = [offsetX, offsetY]
                enemy["Name"] = toSpawn
                enemy["Object"] = canvas.create_image(pos[0]+offsetX,pos[1]+offsetY, anchor=tk.NW, image=gameTextures["Enemies"][toSpawn]["Texture"])
                if enemy.get("debug_hp") == None: enemy["debug_hp"] = False
                if enemy["debug_hp"] == "True": enemy["debug_hp_obj"] = canvas.create_text(pos[0]+offsetX,pos[1]+offsetY, anchor=tk.NW, fill="red", text=str(enemy["Health"]))
                enemy["IndexOfTrack"] = 0
                enemy["shouldBeRemoved"] = False
                enemy["removeReason"] = "NONE"
                enemy["hidden"] = False
                enemy["hiddenUntil"] = 0
                Enemies.append(enemy)
                objs = list()
                for e in Enemies:
                    objs.append( e["Object"] )
                _enemiesSpawned += 1
                print(f"[\033[33mDEBUG\033[0m]: \033[90mSpawned enemy \033[34m{toSpawn}\033[90m at \033[34m{pos}\033[90m with id \033[34m{enemy['Object']}\033[90m (AlEnemies: \033[35m{objs}\033[90m) TotalForRound: \033[35m{_enemiesSpawned}\033[0m")
            # Decrese spawn cooldown
            if not int(mapData["EnemySpawnRateDecrese"]) < 0:
                if wcs.increment("spawnEnemyDecrease") == True:
                    oldEspawnCooldown = wcs.getMax("spawnEnemies")
                    wcs.decresMax("spawnEnemies",int(mapData["EnemySpawnRateDecrese"]),floor=True)
                    newEspawnCooldown = wcs.getMax("spawnEnemies")
                    print(f"[\033[33mDEBUG\033[0m]: \033[90mDecreased Enemy spawn rate form '\033[34m{oldEspawnCooldown}\033[90m' to '\033[35m{newEspawnCooldown}\033[90m'\033[0m")
        # Move enemies
        for index,enemy in enumerate(Enemies):
            hitHomebase = False
            # 'Smooth' move system
            if enemy["MovementType"].lower() == "smooth":
                # Enemy hit homebase
                pos = canvas.coords(enemy["Object"])
                unOffsetedX = pos[0] - enemy["Offsets"][0]
                unOffsetedY = pos[1] - enemy["Offsets"][1]
                homebase_pos = homebase_tile["gridCoordsTL"]
                if unOffsetedX == homebase_pos[0] and unOffsetedY == homebase_pos[1]:  hitHomebase = True
                # Move enemy
                _enemy,newIndexOfTrack,newPos = getNewCoords(CoordsPerMove=enemy["CoordsPerMove"],canvas=canvas, enemy=enemy, complexTrack=enemyTrack_complex, IndexOfTrack=enemy["IndexOfTrack"], currentPosUnoffseted=[unOffsetedX,unOffsetedY])
                enemy = _enemy
                Enemies[index] = _enemy
                Enemies[index]["IndexOfTrack"] = newIndexOfTrack
                offsetedX = newPos[0] + enemy["Offsets"][0]
                offsetedY = newPos[1] + enemy["Offsets"][1]
                canvas.coords(enemy["Object"],offsetedX,offsetedY)
                if (enemy["debug_hp"] == "True") and (enemy.get("debug_hp_obj") != None): canvas.coords(enemy["debug_hp_obj"],offsetedX,offsetedY)
                if (enemy["debug_hp"] == "True") and (enemy.get("debug_hp_obj") != None): canvas.itemconfig(enemy["debug_hp_obj"],text=str(enemy["Health"]))
            # 'Direct' move system
            else:
                if wcs.increment("moveEnemiesDirect") == True:
                    # Enemy hit homebase
                    if enemy["IndexOfTrack"] >= len(enemyTrack)-1:  hitHomebase = True
                    else:
                        # Move enemy
                        enemy["IndexOfTrack"] += 1 # increment tile of track index
                        ox,oy = int(enemy["Offsets"][0]),int(enemy["Offsets"][1])
                        x,y = enemyTrack_coords[enemy["IndexOfTrack"]][0]
                        canvas.coords(enemy["Object"],x+ox,y+oy ) # i=0 for topleft coorner coords
                        if (enemy["debug_hp"] == "True") and (enemy.get("debug_hp_obj") != None): canvas.coords(enemy["debug_hp_obj"],x+ox,y+oy)
                        if (enemy["debug_hp"] == "True") and (enemy.get("debug_hp_obj") != None): canvas.itemconfig(enemy["debug_hp_obj"],text=str(enemy["Health"]))
            # Did enemy hit homebase?
            if hitHomebase == True:
                Enemies[index]["shouldBeRemoved"] = True
                Enemies[index]["removeReason"] = "hitting-homebase"
                # Do damage to player
                damageDelt = int( enemy["Health"] + enemy["AdditionalDamage"] )
                player_hp -= damageDelt
                print(f"[\033[33mDEBUG\033[0m]: \033[90mTook \033[34m{damageDelt}\033[90m damage from object \033[34m{enemy['Object']}\033[90m and marked it for removal. (HP: \033[34m{player_hp+damageDelt}\033[90m >> \033[34m{player_hp}\033[90m)\033[0m")
        # Spawn projectiles
        if wcs.increment("spawnProjectile") == True:
            for index,char in enumerate(Characters):
                if char["cooldownTilShoot"] >= char["ShootingCooldown"]:
                    # Get pos
                    pos = canvas.coords(char["Object"])
                    width,height = getNWsize(canvas,char["Object"])
                    name = char["name"]
                    # Set shooting texture
                    canvas.itemconfig(char["Object"],image=gameTextures["Characters"][name]["shooting"])
                    Characters[index]["returnTextureIn"] = {"current":0,"max":int(char["ShootingTextureResetTime"])}
                    # Spawn projectile
                    for direction in char["ShootingDirection"]:
                        if char["ShootingDirection"][direction] == "True":
                            proj = dict()
                            proj["Speed"] = char["ProjectileSpeed"]
                            proj["Damage"] = char["Damage"]
                            proj["Direction"] = direction
                            proj["Object"] = canvas.create_image(pos[0]+(width/2),pos[1]+(height/2), anchor=tk.NW, image=gameTextures["Characters"][name]["projectile"])
                            proj["shouldBeRemoved"] = False
                            proj["MissChanceProcent"] = char["MissChanceProcent"]
                            Projectiles.append(proj)
                else:
                    char["cooldownTilShoot"] += 1
        # Reset char textures
        for index,char in enumerate(Characters):
            retTextIn = char["returnTextureIn"]
            c = retTextIn["current"]
            m = retTextIn["max"]
            if int(c) >= int(m) and int(m) != 0:
                canvas.itemconfig(char["Object"],image=gameTextures["Characters"][char['name']]["idle"])
                Characters[index]["returnTextureIn"] = {"current":0,"max":0}
            else:
                Characters[index]["returnTextureIn"]["current"] += 1
        # Move projectiles
        for proj in Projectiles:
            # Move
            x,y = canvas.coords(proj["Object"])
            if proj["Direction"].lower() == "down":
                y = y+int(proj["Speed"])
            elif proj["Direction"].lower() == "up":
                y = y-int(proj["Speed"])
            elif proj["Direction"].lower() == "left":
                x = x-int(proj["Speed"])
            elif proj["Direction"].lower() == "right":
                x = x+int(proj["Speed"])
            elif proj["Direction"].lower() == "down-left":
                y = y+int(proj["Speed"])
                x = x-int(proj["Speed"])
            elif proj["Direction"].lower() == "down-right":
                y = y+int(proj["Speed"])
                x = x+int(proj["Speed"])
            elif proj["Direction"].lower() == "up-left":
                y = y-int(proj["Speed"])
                x = x-int(proj["Speed"])
            elif proj["Direction"].lower() == "up-right":
                y = y-int(proj["Speed"])
                x = x+int(proj["Speed"])
            canvas.coords(proj["Object"],x,y)
            # Check if projectile is outside grid
            x,y = canvas.coords(proj["Object"])
            width,height = getNWsize(canvas,proj["Object"])
            if x >= mapData["WindowSize"][0]-(round(width/2)) or y >= mapData["WindowSize"][1]-(round(height/2)): # Width & Lenght /2 is the midpoint offset, since texture.anchor:NW
                proj["shouldBeRemoved"] = True
        # Check if enemy got hit by projectile
        toApply = list()
        for eindex,enemy in enumerate(Enemies):
            if enemy["hidden"] == False:
                # Guess collisionType
                if mapData["CollisionType"] == "Guess":
                    cords = canvas.coords(enemy["Object"])
                    width,height = getNWsize(canvas,enemy["Object"])
                    colliding = canvas.find_overlapping(cords[0], cords[1],
                                                    cords[0]+(width/2), cords[1]+(height/2)) # Width & Lenght /2 is the midpoint offset, since texture.anchor:NW
                    colliding = list(colliding)
                    for index,proj in enumerate(Projectiles):
                        if proj["Object"] in colliding:
                            if doMiss(int(proj["MissChanceProcent"])) == False:
                                Enemies[eindex]["Health"] -= proj["Damage"]
                                Projectiles[index]["shouldBeRemoved"] = True
                # Exact collsionType
                else:
                    ex1,ey1,ex2,ey2 = canvas.bbox(enemy["Object"])
                    for index,proj in enumerate(Projectiles):
                        px1,py1,px2,py2 = canvas.bbox(proj["Object"])
                        pW = px2 - px1
                        pH = py2 - py1
                        px = px1 + pW
                        py = py1 + pH
                        if isBetweenI(px,ex1,ex2) and isBetweenI(py,ey1,ey2):
                            if doMiss(int(proj["MissChanceProcent"])) == False:
                                Enemies[eindex]["Health"] -= proj["Damage"]
                                Projectiles[index]["shouldBeRemoved"] = True
            # Kill enemy with no life
            if enemy["Health"] <= 0:
                enemy["shouldBeRemoved"] = True
                enemy["removeReason"] = "projectile"
                player_money += enemy["Worth"]
                # SummonOnDeath
                for summon in enemy["SummonOnDeath"]:
                    x,y = canvas.coords(enemy["Object"])
                    offsetX = random.randint(-10,10)
                    offsetY = random.randint(-10,10)
                    toSummon = gameData["Enemies"][summon].copy()
                    toSummon["Offsets"] = [offsetX, offsetY]
                    toSummon["Name"] = summon
                    toSummon["Object"] = canvas.create_image(x+offsetX,y+offsetY, anchor=tk.NW, image=gameTextures["Enemies"][summon]["Texture"])
                    if toSummon.get("debug_hp") == None: toSummon["debug_hp"] = False
                    if toSummon["debug_hp"] == "True": toSummon["debug_hp_obj"] = canvas.create_text(pos[0]+offsetX,pos[1]+offsetY, anchor=tk.NW, fill="red", text=str(toSummon["Health"]))
                    toSummon["IndexOfTrack"] = enemy["IndexOfTrack"]
                    toSummon["shouldBeRemoved"] = False
                    toSummon["removeReason"] = "NONE"
                    toSummon["hidden"] = False
                    toSummon["hiddenUntil"] = 0
                    toApply.append(toSummon)
        # Apply changes from kill_enemy_no_life
        for enemy in toApply:
            Enemies.append(enemy)
        # clean up
        for index,proj in enumerate(Projectiles):
            if proj["shouldBeRemoved"] == True:
                canvas.delete(proj["Object"])
                Projectiles.pop(index)
        for index,enemy in enumerate(Enemies):
            if enemy["shouldBeRemoved"] == True:
                objs = list()
                for e in Enemies:
                    objs.append( e["Object"] )
                print(f"[\033[33mDEBUG\033[0m]: \033[90mEnemy \033[34m{enemy['Name']}\033[90m with index \033[34m{index}\033[90m died from {enemy['removeReason']}, at \033[34m{canvas.coords(enemy['Object'])}\033[90m and had id \033[34m{enemy['Object']}\033[90m (AlEnemies: \033[35m{objs}\033[90m)\033[0m")
                canvas.delete(enemy["Object"])
                if (enemy["debug_hp"] == "True") and (enemy.get("debug_hp_obj") != None): canvas.delete(enemy["debug_hp_obj"])
                Enemies.pop(index)
        # Update elements
        ## colors
        if player_money <= 0:  canvas.itemconfig(player_money_obj, fill="red")
        else: canvas.itemconfig(player_money_obj, fill="yellow")
        if player_hp <= int(mapData["PlayerStartHealth"])/2:
            if player_hp <= 0: canvas.itemconfig(player_hp_obj, fill="red")
            else: canvas.itemconfig(player_hp_obj, fill="orange")
        else: canvas.itemconfig(player_hp_obj, fill="yellow")
        ## Buttons
        for button in charSelectButtons:
            if int(gameData["Characters"][button]["Cost"]) > int(player_money):
                canvas.itemconfig(charSelectButtons[button]["text"],fill="red")
            else:
                canvas.itemconfig(charSelectButtons[button]["text"],fill="white")
        ## text
        canvas.itemconfig(player_hp_obj, text=f"HP: {player_hp}")
        canvas.itemconfig(player_money_obj, text=f"Cash: ${player_money}")
        # GAMEWON - SurvivedWhenAlEnemiesWasSpawned?
        if _enemiesSpawned >= int(mapData["EnemiesToSpawn"]):
            csStore["spawnEnemies"] == False
            csStore["gameRunning"] = False
            canvas.create_image((mapData["WindowSize"][0]/2),(mapData["WindowSize"][1]/2),image=img_victory)
            canvas.create_text((mapData["WindowSize"][0]/2),(mapData["WindowSize"][1]/2)+30,fill="yellow",text=f'Press {keyOnly(gameData["Settings"]["Keybinds"]["exit"])} to continue...')
            updateLocal(csStore,player_hp)
            csStore["soundSys"].stopAll()
            csStore["soundSys"].playSound(mapData["VictorySound"])
        # GAMEOVER
        if player_hp <= 0:
            csStore["spawnEnemies"] == False
            csStore["gameRunning"] = False
            canvas.create_image((mapData["WindowSize"][0]/2),(mapData["WindowSize"][1]/2),image=img_gameover)
            canvas.create_text((mapData["WindowSize"][0]/2),(mapData["WindowSize"][1]/2)+30,fill="yellow",text=f'Press {keyOnly(gameData["Settings"]["Keybinds"]["exit"])} to continue...')
            csStore["soundSys"].stopAll()
            csStore["soundSys"].playSound(mapData["GameoverSound"])
                
      # [POST]
        # Schedule loop
        if csStore["gameRunning"] == True:
            canvas.after(10, game_loop)

    # CODE: ===================[Launch code]===================
    canvas.after(0,game_loop)
    window.focus()
    window.bind(gameData["Settings"]["Keybinds"]["exit"],exitGame)
    window.bind(gameData["Settings"]["Keybinds"]["start"],startGame)
    window.bind(gameData["Settings"]["Keybinds"]["click"], onClick)