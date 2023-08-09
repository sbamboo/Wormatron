# [Imports]
import re
import os
import json
import tkinter as tk
import platform
import inspect
import random
import requests
from PIL import Image, ImageTk
from assets.libs.libtabledraw import drawTable
from assets.sceneSystem import *
import hashlib
from assets.libs.GamehubAPI.libs.libcrypto.aes import *

# =================================[DEBUG]=================================
def isDebugMode():
    return os.path.exists( os.path.abspath(f"{os.path.dirname( inspect.getabsfile(inspect.currentframe()) )}{os.sep}..{os.sep}debug.state") )
def getConsoleLast():
    p = os.path.abspath(f"{os.path.dirname( inspect.getabsfile(inspect.currentframe()) )}{os.sep}..{os.sep}threadedconsole.content")
    if os.path.exists(p):
        return open(p,"r").read()
    else:
        return None
def getDebugCon():
    if isDebugMode() == True:
        return getConsoleLast()
    else:
        return None
def actDebugCon(csStore):
    if isDebugMode() == True:
        content = getConsoleLast()
        if content != None:
            content = content.strip()
            if "sc:" in content:
                csStore["spawnEnemies"] = False
                csStore["gameRunning"] = False
                csStore["soundSys"].stopAll()
                content = content.replace("sc:","")
                switch_scene(csStore, content)
                runCurrentScene(csStore)
            elif content == "ex":
                csStore["window"].destroy()
                exit()
            elif content == "soundOf":
                if csStore.get("soundSys") != None:
                    csStore["soundSys"].stopAll()
if isDebugMode() == True:
    orgPrint = print
    lines_shifted = 0
    import sys
    def print(*args, **kwargs):
        global lines_shifted
        # Move the cursor one line up for each printed line
        lines_to_print = str(*args, **kwargs).split('\n')
        offset = len(lines_to_print) - 1
        sys.stdout.write("\033[{}A".format(offset))
        sys.stdout.flush()
        # Clear the line below the shifted lines
        sys.stdout.write("\033[1B\033[2K")
        sys.stdout.flush()
        # Call the original print function
        orgPrint(*args, **kwargs)
        lines_shifted += offset

# =================================[UI]=================================
def winBack_resizeImage_caller(window,oImg,label,csStore,updateRate,event=None):
    if csStore["windowBackground_resizeEventID"]:
        window.after_cancel(csStore["windowBackground_resizeEventID"])
    csStore["windowBackground_resizeEventID"] = window.after(updateRate,lambda:winBack_resizeImage(window,oImg,label,event))
def winBack_resizeImage(window,oImg,label,event=None):
    if event:
        new_width = event.width
        new_height = event.height
    else:
        new_width = window.winfo_width()
        new_height = window.winfo_height()
    resized_image = oImg.resize((new_width, new_height))
    new_image = ImageTk.PhotoImage(resized_image)
    label.configure(image=new_image)
    label.image = new_image  # Update the reference to prevent garbage collection

def get_average_color(image):
    # Convert the image to RGB mode if it's not already
    image = image.convert("RGB")
    # Get the image data
    pixels = image.getdata()
    # Calculate the total sum of red, green, and blue values
    total_r, total_g, total_b = 0, 0, 0
    count = 0
    for pixel in pixels:
        r, g, b = pixel
        total_r += r
        total_g += g
        total_b += b
        count += 1
    # Calculate the average values
    avg_r = int(total_r / count)
    avg_g = int(total_g / count)
    avg_b = int(total_b / count)
    # Convert the average RGB values to hexadecimal format
    hex_color = "#{:02x}{:02x}{:02x}".format(avg_r, avg_g, avg_b)
    return hex_color

class clickStateStorage():
    def __init__(self):
        self.stateStorage = dict()
    def toggle(self,id):
        state = self.stateStorage.get(id)
        if state == True:
            state = False
        else: state = True
        self.stateStorage[id] = state
    def get(self,id):
        return self.stateStorage.get(id)
    def set(self,id,value):
        self.stateStorage[id] = value
    def anyClicked(self):
        states = list()
        for _id in list(self.stateStorage.keys()):
            states.append(self.stateStorage[_id])
        return True in states

def createBtnBack(canvas,posX,posY,width,height,fill):
    return canvas.create_rectangle(posX-(width/2),posY-(height/2),posX+(width/2),posY+(height/2),fill=fill)

def generateLevelList(levels,pathtags):
    levelList = []
    for key,value in levels.items():
        level = {"name":str(key),"edgeBackgroundPath":pathtag(pathtags,value["levelSelect"]["edge"]),"iconPath":pathtag(pathtags,value["levelSelect"]["icon"]),"description":value["levelSelect"]["desc"],"difficulty":value["Difficulty"],"lockedByDefault":value["levelSelect"]["lockedByDefault"],"unlock":value["levelSelect"]["unlock"]}
        levelList.append(level)
    return levelList

def getGridWidth(winWidth=int(),winPadX=int(),horizPad=int(),objSizeX=int()):
    x = (winWidth-(horizPad*2))/(objSizeX+horizPad)
    return int( (str(x).split("."))[0] )

def isLvl(value=str(),player_xp=int(),player_lvl=int()):
    locked = True
    # Level lock
    if "lvl." in value:
        value = value.replace("lvl.","")
        value = int(value)
        if player_lvl >= value: locked = False
    # XP lock
    elif "xp." in value:
        value = value.replace("xp.","")
        value = int(value)
        if player_xp >= value: locked = False
    return locked

def isLvlText(value=str()):
    msg = True
    overwrite = False
    # Level lock
    if "lvl." in value:
        value = value.replace("lvl.","")
        value = int(value)
        msg = f"level {value}"
    # XP lock
    elif "xp." in value:
        value = value.replace("xp.","")
        value = int(value)
        msg = f"xp {value}"
    # MSG lock
    elif "msg:" in value:
        value = value.replace("msg:","")
        msg = value
        overwrite = True
    return msg,overwrite

def generateGrid_empty(levelList,gridWidth):
    grid = {"selectedRow":None,"rows":[]}
    # Sort into boxes of len() = gridWidth
    boxes = dict()
    index = 0
    for level in levelList:
        level["objects"] = {"edge":None,"icon":None,"name":None,"desc":None,"diff":None}
        level["lock"] = {"locked":level["lockedByDefault"],"unlock":level["unlock"]}
        if boxes.get(index) == None: boxes[index] = []
        if len(boxes[index]) < gridWidth:
            boxes[index].append(level)
        else:
            index += 1
            if boxes.get(index) == None: boxes[index] = []
            boxes[index].append(level)
    # Add header
    grid["rows"].append({"type":"header"})
    # Boxes to rows
    for _,val in boxes.items():
        grid["rows"].append({"type":"none", "placks":val})
    # Fix missing row 1
    if len(grid["rows"]) < 2:
        grid["rows"].append({"type":"none", "placks":[]})
    # Asign types
    if len(grid["rows"]) > 2:
        if grid["rows"][1]["type"] != "header" and grid["rows"][1]["type"] != "footer":
            grid["rows"][1]["type"] = "main"
            grid["selectedRow"] = 1
    if len(grid["rows"]) > 3:
        if grid["rows"][2]["type"] != "header" and grid["rows"][2]["type"] != "footer":
            grid["rows"][2]["type"] = "lower"
    # Add footer
    grid["rows"].append({"type":"footer"})
    # Return value
    return grid

def updateButtonShows(rGrid,canvas,upBtn,dwBtn):
    last = len(rGrid["rows"])-2
    if canvas.coords(rGrid["rows"][last]["placks"][0]["objects"]["edge"])[1] != rGrid["maxY"]:
        if rGrid["shiftEvent"]["type"] == None:
            canvas.itemconfigure(dwBtn, state='normal')
    else:
        canvas.itemconfigure(dwBtn, state='hidden')
    if canvas.coords(rGrid["rows"][1]["placks"][0]["objects"]["edge"])[1] != rGrid["maxY"]:
        if rGrid["shiftEvent"]["type"] == None:
            canvas.itemconfigure(upBtn, state='normal')
    else:
        canvas.itemconfigure(upBtn, state='hidden')
    
def gridUp(rGrid,oSize,vPad,canvas):
    # Check for current shiftEvent
    if rGrid["shiftEvent"]["type"] == None:
        # Check if allowed
        last = len(rGrid["rows"])-2
        if canvas.coords(rGrid["rows"][last]["placks"][0]["objects"]["edge"])[1] != rGrid["maxY"]:
            # Setup shift event
            currentY = rGrid["shiftEvent"]["currentY"]
            finalY = currentY - (oSize[1]+vPad)
            type = "shiftUp"
            rGrid["shiftEvent"] = {"type":type,"currentY":currentY,"finalY":finalY}
    # Return grid
    return rGrid
def gridDown(rGrid,oSize,vPad,canvas):
    # Check for current shiftEvent
    if rGrid["shiftEvent"]["type"] == None:
        # Check if allowed
        if canvas.coords(rGrid["rows"][1]["placks"][0]["objects"]["edge"])[1] != rGrid["maxY"]:
            # Setup shift event
            currentY = rGrid["shiftEvent"]["currentY"]
            finalY = currentY + (oSize[1]+vPad)
            type = "shiftDown"
            rGrid["shiftEvent"] = {"type":type,"currentY":currentY,"finalY":finalY}
    # Return grid
    return rGrid
def getStepDiff(v1=int(),v2=int()):
    diff = 0
    v1 = str(v1)
    v1 = v1.strip("-")
    v1 = v1.replace(".0","")
    v1 = int(v1)
    v2 = str(v2)
    v2 = v2.strip("-")
    v2 = v2.replace(".0","")
    v2 = int(v2)
    if v1 > v2:
        diff = v1 - v2
    elif v1 < v2:
        diff = v2 - v1
    else:
        diff = 0
    return diff

def moveGrid(rGrid,canvas,speed):
    # Check if shiftEvent is set:
    if rGrid["shiftEvent"]["type"] != None:
        # Check if done or should continue
        done = False
        if rGrid["shiftEvent"]["type"] == "shiftUp":
            if rGrid["shiftEvent"]["currentY"] <= rGrid["shiftEvent"]["finalY"]:
                done = True
        elif rGrid["shiftEvent"]["type"] == "shiftDown":
            if rGrid["shiftEvent"]["currentY"] >= rGrid["shiftEvent"]["finalY"]:
                done = True
        if done == True:
            # Done so unregister
            rGrid["shiftEvent"] = {"type":None,"currentY":rGrid["shiftEvent"]["currentY"],"finalY":None}
        # Continue...
        else:
            # ShiftUp
            if rGrid["shiftEvent"]["type"] == "shiftUp":
                # update currentY
                oldY = rGrid["shiftEvent"]["currentY"]
                newY = oldY - speed
                # Snap to max
                if newY <= rGrid["shiftEvent"]["finalY"]:
                    newY_snapped = rGrid["shiftEvent"]["finalY"]
                    howMuchSnapped = getStepDiff(newY,newY_snapped)
                    speed -= howMuchSnapped
                    newY = newY_snapped
                # Save newY
                rGrid["shiftEvent"]["currentY"] = newY
                # move objects
                for row in rGrid["rows"]:
                    for plack in row["placks"]:
                        for obj in plack["objects"]:
                            tkObj = plack["objects"][obj]
                            x,y = canvas.coords(tkObj)
                            y = y - speed
                            canvas.coords(tkObj,x,y)
            # ShiftDown
            if rGrid["shiftEvent"]["type"] == "shiftDown":
                # update currentY
                oldY = rGrid["shiftEvent"]["currentY"]
                newY = oldY + speed
                # Snap to max
                if newY >= rGrid["shiftEvent"]["finalY"]:
                    newY_snapped = rGrid["shiftEvent"]["finalY"]
                    howMuchSnapped = getStepDiff(newY,newY_snapped)
                    speed -= howMuchSnapped
                    newY = newY_snapped
                # Save newY
                rGrid["shiftEvent"]["currentY"] = newY
                # move objects
                for row in rGrid["rows"]:
                    for plack in row["placks"]:
                        for obj in plack["objects"]:
                            tkObj = plack["objects"][obj]
                            x,y = canvas.coords(tkObj)
                            y = y + speed
                            canvas.coords(tkObj,x,y)
    # Return grid
    return rGrid

# =================================[Sound]=================================
# SoundMap class based on platform
platformv = platform.system()
# Linux and macOS using simpleaudio
if platformv in ["Linux", "Darwin"]:
    from pydub import AudioSegment
    from pydub.playback import play
    import threading
    import subprocess
    class SoundMap():
        def __init__(self, csStore):
            self.csStore = csStore
            self.play_thread = None
            self.stop_event = threading.Event()
        def playSound(self, mFile, loop=False):
            if self.play_thread and self.play_thread.is_alive():
                return  # Ignore if a sound is already playing
            audio = AudioSegment.from_file(pathtag(self.csStore["pathtags"], mFile))
            self.stop_event.clear()  # Reset the stop event
            self.play_thread = threading.Thread(target=self._play_sound, args=(audio, loop))
            self.play_thread.start()
        def _play_sound(self, audio, loop):
            audio.export('/tmp/tmpaudio.wav', format='wav')  # Export the audio to a temporary WAV file
            command = ['ffplay', '-nodisp', '-autoexit', '/tmp/tmpaudio.wav']
            while loop and not self.stop_event.is_set():
                if self.stop_event.is_set():
                    break
                subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if not loop and not self.stop_event.is_set():
                subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        def stopAll(self):
            self.stop_event.set()  # Set the stop event to exit the loop immediately
            if self.play_thread and self.play_thread.is_alive():
                self.play_thread.join(1)  # Wait for 1 second for the thread to finish gracefully
            self.play_thread = None
# Window using winsound
elif platformv == "Windows":
    import winsound
    class SoundMap():
        def __init__(self,csStore):
            self.csStore = csStore
        def playSound(self,mFile,loop=False):
            if loop == True:
                winsound.PlaySound(pathtag(self.csStore["pathtags"],mFile),winsound.SND_ASYNC | winsound.SND_LOOP)
            else:
                winsound.PlaySound(pathtag(self.csStore["pathtags"],mFile),winsound.SND_ASYNC)
        def stopAll(self):
            winsound.PlaySound(None, winsound.SND_PURGE)

# =================================[General]=================================
# 256 Hasher
def calculate_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as file:
        # Read the file in small chunks to conserve memory
        for chunk in iter(lambda: file.read(4096), b''):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

# Between value checker
def isBetween(value, min, max):
    return value > min and value < max
# Between value checker (INCLUSIVE)
def isBetweenI(value, min, max):
    return value >= min and value <= max

# Function to strip comments out of json
def removeComments(json_string):
    '''function to strip comments from a raw json string and returns the stripped string'''
    # Match and remove single-line comments that start with //
    pattern = r"(^|\s)//.*$"
    without_comments = re.sub(pattern, "", json_string, flags=re.MULTILINE)
    return without_comments

# Original dictionary merger from https://stackoverflow.com/questions/7204805/how-to-merge-dictionaries-of-dictionaries
def merge(a, b, path=None):
    '''merges dictionary a into dictionary b, apon conflict favoring the value from b'''
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            else:
                a[key] = b[key]  # always favor the value from b
        else:
            a[key] = b[key]
    return a

# handlePaths in dictionary
def pathtag(definitions=dict(),inPath=str()) -> str:
    '''Takes a dictionary of key,value pairs and modifies the inPath string by replaceing %<key>% with <value>'''
    for key,value in definitions.items():
        tag = key
        path = value
        oString = "%" + str(tag) + "%"
        inPath = inPath.replace(oString,path)
        inPath = inPath.replace("\\",os.sep)
    return inPath
# =================================[Data]=================================

def _safeLoadListString(listString):
    try:
        _list = json.loads(listString)
    except:
        _str = listString.replace('"',"\000").replace("'",'"').replace("\000","'")
        _list = json.loads(_str)
    return _list

_ServerEncryptionKey = GenerateKey("GAMEHUBSERVERKEY_Wormatron_Server:b543dfb3-61bb-4ead-962b-3b9ce329ac93:DONTSHARE!!!")

def _getHashFile(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
    except: pass
    return None

def _assembleHashKeyList(currentHash,keyFile=None):
    hashList = [currentHash]
    if keyFile != None:
        keyFileContent = open(keyFile,"r").read()
        decryptedKeyFileContent = encdec(inputs=keyFileContent,key=_ServerEncryptionKey,mode="dec")
        keys = _safeLoadListString(decryptedKeyFileContent)
        hashList.extend(keys)
    return hashList

def _tryHash(hash,content,mode):
    try:
        content = encdec(key=hash,input=content,mode=mode)
        return content
    except:
        return False

def decryptHashLock(content,currentHash,keyFile=None):
    hashes = _assembleHashKeyList(currentHash,keyFile)
    for hash in hashes:
        tryResult = _tryHash(hash,content,"dec")
        if tryResult != False:
            return tryResult
    return None

def decryptHashLockAuto(content,currentHash,csStore):
    keyFileContent = None
    if csStore.get("LocalDataSecureKeyFileURL") != None:
        keyFileContent = _getHashFile(csStore.get("LocalDataSecureKeyFileURL"))
    return decryptHashLock(content,currentHash,keyFile)

def encryptServer(toEncrypt):
    if toEncrypt != None:
        for user in toEncrypt:
            userData_str = json.dumps(toEncrypt[user])
            userData_enc = encdec(inputs=userData_str,key=_ServerEncryptionKey,mode="enc")
            toEncrypt[user] = userData_enc
    return toEncrypt

def decryptServer(toDecrypt):
    if toDecrypt != None:
        for user in toDecrypt:
            userData_str = encdec(inputs=toDecrypt[user],key=_ServerEncryptionKey,mode="dec")
            userData = json.loads(userData_str)
            toDecrypt[user] = userData
    return toDecrypt

def updateLocalData(csStore,file,newData=dict()):
    # Check if file not exist
    exi = os.path.exists(file)
    # Get content with json
    if exi == True:
        rawContent_enc = open(file,'r').read()
        _LocalDataKey = GenerateKey(calculate_sha256(f"{csStore['GAME_PARENTPATH']}\\wormatron.py"))
        rawContent = encdec(key=_LocalDataKey,mode="dec",inputs=rawContent_enc)
        #rawContent = decryptHashLockAuto(rawContent_enc,_LocalDataKey,csStore)
        try:
            content = json.loads(rawContent)
        except:
            raise Exception("\033[31mFailed to load localdata, probably generated in diffrent wormatron version, please delete /assets/local.data to continue\033[0m")
        # Update content
        content.update(newData)
    else:
        content = newData
    # Save content and remove old file if exi
    if exi == True: os.remove(file)
    jsonstring = json.dumps(content)
    _LocalDataKey = GenerateKey(calculate_sha256(f"{csStore['GAME_PARENTPATH']}\\wormatron.py"))
    jsonstring_enc = encdec(key=_LocalDataKey,mode="enc",inputs=jsonstring)
    open(file,'w').write(jsonstring_enc)
    # give back updated content
    return content

def getLocalData(csStore,file):
    content = dict()
    # Check if file not exist
    exi = os.path.exists(file)
    # Get content with json
    if exi == True:
        rawContent_enc = open(file,'r').read()
        _LocalDataKey = GenerateKey(calculate_sha256(f"{csStore['GAME_PARENTPATH']}\\wormatron.py"))
        rawContent = encdec(key=_LocalDataKey,mode="dec",inputs=rawContent_enc)
        try:
            content = json.loads(rawContent)
        except:
            raise Exception("\033[31mFailed to load localdata, probably generated in diffrent wormatron version, please delete /assets/local.data to continue\033[0m")
    return content

def updateCopyOfLocal(csStore):
    csStore["localData"] = getLocalData(csStore,csStore["PATH_LOCALDATAFILE"])

def clearLocalData(file):
    if os.path.exists(file): os.remove(file)

def syncLocalData(csStore):
    if csStore["hasInternet"] != False:
        username   = csStore["player_username"]
        localData  = getLocalData(csStore,csStore["PATH_LOCALDATAFILE"])
        serverData = csStore["scoreboardConnector"].get("wormatron")
        serverData = decryptServer(serverData)
        userExistsOnServer = False if (serverData.get(username) == None) else True
        userExistsOnLocal  = False if (localData.get(username)  == None) else True
        serverUserData = serverData.get(username) if userExistsOnServer == True else {"xp":0,"level":0,"badges":[]}
        localUserData  = localData.get(username)  if userExistsOnLocal  == True else {"player_xp":0,"player_lvl":0}
        serverXp = int(serverUserData["xp"])
        serverLvl = int(serverUserData["level"])
        localXp = int(localUserData["player_xp"])
        localLvl = int(localUserData["player_lvl"])
        newXp = 0
        newLvl = 0
        if serverXp > localXp:   newXp = serverXp
        else:                    newXp = localXp
        if serverLvl > localLvl: newLvl = serverLvl
        else:                    newLvl = localLvl
        serverData.update({username:{"xp":newXp,"level":newLvl,"badges":serverUserData["badges"]}})
        csStore["scoreboardConnector"].replace("wormatron",encryptServer(serverData))

def removeUser(csStore,username):
    # Local user
    localData = getLocalData(csStore,csStore["PATH_LOCALDATAFILE"])
    if localData.get(username) != None:
        localData.pop(username)
        os.remove(csStore["PATH_LOCALDATAFILE"])
        updateLocalData(csStore,csStore["PATH_LOCALDATAFILE"],newData=localData)
    # Server user
    if csStore["hasInternet"] != False:
        serverData = csStore["scoreboardConnector"].get("wormatron")
        serverData = decryptServer(serverData)
        userExistsOnServer = False if (serverData.get(username) == None) else True
        if userExistsOnServer == True:
            serverData.pop(username)
            csStore["scoreboardConnector"].replace("wormatron",encryptServer(serverData))

def gainBadge(csStore,badgeId):
    username = csStore["player_username"]
    if csStore["hasInternet"] != False:
        # Get current server data
        serverData = csStore["scoreboardConnector"].get("wormatron")
        serverData = decryptServer(serverData)
        userExistsOnServer = False if (serverData.get(username) == None) else True
        # Add field if not exists
        if userExistsOnServer == True:
            if serverData[username].get("badges") == None: serverData[username]["badges"] = []
        # Add badgeId
        if badgeId not in serverData[username]["badges"]:
            serverData[username]["badges"].append(badgeId)
        # Upload
        csStore["scoreboardConnector"].replace("wormatron",encryptServer(serverData))

def loseBadge(csStore,badgeId):
    username = csStore["player_username"]
    if csStore["hasInternet"] != False:
        # Get current server data
        serverData = csStore["scoreboardConnector"].get("wormatron")
        serverData = decryptServer(serverData)
        userExistsOnServer = False if (serverData.get(username) == None) else True
        # Add field if not exists
        if userExistsOnServer == True:
            if serverData[username].get("badges") == None: serverData[username]["badges"] = []
        # Add badgeId
        if badgeId in serverData[username]["badges"]:
            for i,b in enumerate(serverData[username]["badges"]):
                if b == badgeId:
                    serverData[username]["badges"].pop(i)
        # Upload
        csStore["scoreboardConnector"].replace("wormatron",encryptServer(serverData))

# =================================[GameFallbacks]=================================
# Show Map selector
def showMapSelector(gameData=dict(),preset=str(),lockingSys=None) -> str:
    '''Shows the map selector'''
    maps = list(gameData["Maps"].keys())
    mods = gameData["LoadedMods"]
    table = dict()
    table["Maps"] = []
    table["Id"] = []
    table["Difficulty"] = []
    table["Loaded Mods"] = []
    table["Unlock"] = []
    for i,_map in enumerate(maps):
        table["Maps"].append(_map)
        text,overwrite = isLvlText(value=gameData["Maps"][_map]["levelSelect"]["unlock"])
        if overwrite == True: text = str(gameData["Maps"][_map]["levelSelect"]["unlock"])
        else: text = f"\033[33mUnlocks at {text}\033[0m"
        locked = isLvl(value=gameData["Maps"][_map]["levelSelect"]["unlock"],player_xp=lockingSys["lvl"],player_lvl=lockingSys["hp"])
        if locked == False:
            table["Id"].append(i)
            text = "\033[32mUnlocked\033[0m"
        else:
            table["Id"].append(" ")
        table["Unlock"].append(text)
        table["Difficulty"].append(gameData["Maps"][_map]["Difficulty"])
        table["Loaded Mods"].append(((str(mods).replace("[","")).replace("]","")).replace("'",""))
    if preset != None: _id = preset
    else:
        drawTable(table)
        _id = input("Id: ")
        if _id.lower() == "exit": return "CODE:EXIT"
    if _id in maps:
        if isLvl(value=gameData["Maps"][_id]["levelSelect"]["unlock"],player_xp=lockingSys["lvl"],player_lvl=lockingSys["hp"]) == False:
            selMap = _id
        else:
            print(f"\033[31mInput '{_id}' is not unlocked!\033[0m")
            return "CODE:ERR_INVALID_ID"
    else:
        try:
            if isLvl(value=gameData["Maps"][maps[int(_id)]]["levelSelect"]["unlock"],player_xp=lockingSys["lvl"],player_lvl=lockingSys["hp"]) == False:
                selMap = maps[int(_id)]
            else:
                print(f"\033[31mInput '{_id}' is not unlocked!\033[0m")
                return "CODE:ERR_INVALID_ID"
        except:
            print(f"\033[31mInput '{_id}' is not a valid id or name!\033[0m")
            return "CODE:ERR_INVALID_ID"
    return selMap


# =================================[GamePrep]=================================
# Function to list out mods avaliable
def listMods(modFolder=str(),gameVer=str(),formatVer=str()):
    modsList = dict()
    entries = os.listdir(modFolder)
    for entry in entries:
        # Get modData
        lpath = os.path.join(modFolder,entry)
        modPath = f"{lpath}{os.sep}mod.jsonc"
        rawModData = open(modPath,'r').read()
        rawModData = removeComments(rawModData)
        valid = True
        compatible = True
        try:
            modData = json.loads(rawModData)
        except:
            valid = False
            compatible = False
            modData = {}
        # check compat
        if valid:
            mod_reqGameVer = str( modData["ModData"]["REQGameVersion"] )
            mod_formatVer  = str( modData["ModData"]["FormatVersion"]  )
            if mod_reqGameVer.lower() != "none" and mod_reqGameVer != gameVer:
                print(f"[\033[33mMODLOADER\033[0m]: \033[95mMod '{entry}' requires gameVersion '{mod_reqGameVer}' but only '{gameVer}' was present, modList.MarkedIncompat!\033[0m")
                compatible = False
            elif int(mod_formatVer) != int(formatVer):
                print(f"[\033[33mMODLOADER\033[0m]: \033[95mMod '{entry}' requires formatVersion '{mod_formatVer}' but the game uses '{formatVer}', modList.MarkedIncompat!\033[0m")
                compatible = False
        # Add mod to list
        amnt = len(list(modsList.keys()))
        modsList[str(amnt+1)] = {"ModName":str(entry),"ModPath":str(lpath),"ModFilePath":str(modPath),"Compatible":compatible,"Valid":valid,"ModData":modData}
    # Return modlist
    return modsList

# Function to load mods
def loadMods(csStore):
    modsList = csStore["game_modsList"]
    # Load mods and apply
    for modId in list(modsList.keys()):
        modListData = modsList[modId]
        if modListData["Valid"] != True:
            print(f"[\033[31mMODLOADER\033[0m]: \033[95mMod '{modListData['ModName']}' with id '{modId}' had an invalid format and could't be loaded, modLoad.Aborted!\033[0m")
        else:
            if modListData["Compatible"] != True:
                print(f"[\033[31mMODLOADER\033[0m]: \033[95mMod '{modListData['ModName']}' with id '{modId}' is incompatible, modLoad.Aborted!\033[0m")
            else:
                csStore["game_Data"]["LoadedMods"].append(modListData["ModName"])
                csStore["game_Data"] = merge(csStore["game_Data"],modListData["ModData"])
                # Add pathtag definition
                csStore["pathtags"].update( {modListData["ModName"]: modListData["ModPath"]} )


# =================================[Game]=================================
# WaitCycleSystem
class waitCycle():
  def __init__(self):
    self.register = dict()
  def create(self,name=str(),max=int()):
    self.register[name] = {"current":0, "max":max}
  def remove(self,name=str()):
    self.register.pop(name)
  def increment(self,name=str()) -> bool:
    if self.register[name]["current"] >= self.register[name]["max"]:
      self.register[name]["current"] = 0
      return True
    else:
      self.register[name]["current"] += 1
      return False
  def setMax(self, name, max):
      self.register[name]["max"] = max
  def getMax(self, name):
      return self.register[name]["max"]
  def incremMax(self, name, incr=1):
      self.register[name]["max"] += incr
  def decresMax(self, name, decr=1, floor=False):
      self.register[name]["max"] -= decr
      if floor == True:
        if self.register[name]["max"] < 1: self.register[name]["max"] = 1
  def reset(self, name):
      self.register[name]["current"] = 0

def doMiss(missChance=int()):
    miss = False
    rI = random.randint(0,99)
    if missChance > 0:
        if rI < missChance:
            miss = False
        else:
            miss = True
    return miss

# Function to calculate xp given
def calcXP(csStore,currentHealth=int()):
    xp = 0
    totalDmg = 0
    startingHealth = int(csStore["game_mapData"]["PlayerStartHealth"])
    baseXp = int(csStore["game_mapData"]["xp"]["base"])
    dmgFactor = int(csStore["game_mapData"]["xp"]["dmgFactor"])
    if currentHealth < startingHealth:
        totalDmg = startingHealth - currentHealth
    xp = baseXp-(totalDmg*dmgFactor)
    return xp

def calcLvl_factor(xp,factor):
    base = 100
    factor = factor
    level = 0
    while xp > 0:
        level += 1
        xp -= base
        base = int(base * factor)
    return level

def calcLvl_exp(xp,exp):
    import math
    lvl = -10 + abs(math.sqrt(100+xp/exp))
    lvl = math.floor(lvl)
    if lvl < 0: return 0
    else:       return lvl

# Function to get a keyname from a keybind config
def keyOnly(tkinterBindString=str()) -> str:
    key = tkinterBindString.replace("<","")
    key = key.replace(">","")
    key = key.replace("KeyPress-","")
    return key

# Function to check if a tile was clicked
def wasClickedTile(tile,lastClickCoords):
    return isBetween(lastClickCoords[0], tile["gridCoordsTL"][0],tile["gridCoordsTR"][0]) and isBetween(lastClickCoords[1], tile["gridCoordsTL"][1],tile["gridCoordsBL"][1])
# Function to check if a position was clicked taking two corners
def wasClickedGen(TL,TR,BL,lastClickCoords):
    return isBetween(lastClickCoords[0], TL[0],TR[0]) and isBetween(lastClickCoords[1], TL[1],BL[1])

# Function to get the tileData of tileCoords
def getTile(tilePosX,tilePosY,gridData):
    for xRow in gridData:
        for yRow in gridData[str(xRow)]:
            tile = gridData[str(xRow)][str(yRow)]
            if int(tile["gridPlacement"][0]) == int(tilePosX):
                if int(tilePosY) == int(tile["gridPlacement"][1]):
                    return tile

# Function to get the screenCoords of tileCoords
def getTileCoords(gameGrid,tilePos=list()):
    '''
    Takes tilepos and returns coords in order TL,TR,BR,BL
    '''
    tilePosX = tilePos[0]
    tilePosY = tilePos[1]
    tileObj = getTile(tilePosX, tilePosY, gameGrid)
    return tileObj["gridCoordsTL"],tileObj["gridCoordsTR"],tileObj["gridCoordsBR"],tileObj["gridCoordsBL"]

# Function to get the tileCoords from screenCoords
def getCoordsTile(tileCoords,windowSize,gridSize):
    # Get tile width/height
    tileWidthPX = round(windowSize[0]/gridSize[0])
    tileHeightPX = round(windowSize[1]/gridSize[1])
    # get tile coords
    x,y = tileCoords
    # Getting tiles from 0 to coords
    stepsX = int(x)/tileWidthPX
    stepsY = int(y)/tileHeightPX
    return [stepsX,stepsY]

# Grid generator
def generateGrid(windowSize, gridSize) -> dict:
    tileWidthPX = round(windowSize[0]/gridSize[0])
    tileHeightPX = round(windowSize[1]/gridSize[1])
    tileWidthAmnt = gridSize[0]
    tileHeightAmnt = gridSize[1]
    # Generate grid
    grid = dict()
    for xRow in range(tileWidthAmnt):
        # Create a row along the X-axis of the grid
        row = {}
        # Generate yRow
        for yRow in range(tileHeightAmnt):
            # Generate tile
            tile = {}
            tile["placedOn"] = bool()
            tile["gridPlacement"] = [xRow,yRow]
            tile["gridCoordsTL"] = [ xRow*tileWidthPX, yRow*tileHeightPX ]
            tile["gridCoordsTR"] = [ (xRow+1)*tileWidthPX, yRow*tileHeightPX ]
            tile["gridCoordsBR"] = [ (xRow+1)*tileWidthPX, (yRow+1)*tileHeightPX ]
            tile["gridCoordsBL"] = [ xRow*tileWidthPX, (yRow+1)*tileHeightPX ]
            # Add tile to row
            row[str(yRow)] = tile
        # Poplate xRow with yRow
        grid[str(xRow)] = row
    # Return grid
    return grid,{"PX":tileWidthPX,"Amnt":tileWidthAmnt},{"PX":tileHeightPX,"Amnt":tileHeightAmnt}

# Function to convert an enemy track from x|y to [x,y]
def convertEnemyTrack(enemyTrack,coords=None,gameGrid=None):
    convertedTrack = list()
    for tile in enemyTrack:
        x = tile.split("|")[0]
        y = tile.split("|")[1]
        if coords == True:
            convertedTrack.append( [*getTileCoords(gameGrid,[x,y])] )
        else:
            convertedTrack.append([x,y])
    return convertedTrack

# Function to convert a track of tileCoords (fourPoint-coords) to cornerCoords
def asumeSimpleTrack(track=list(),corner=str()) -> list:
    #tileObj["gridCoordsTL"],tileObj["gridCoordsTR"],tileObj["gridCoordsBR"],tileObj["gridCoordsBL"]
    nTrack = list()
    for step in track:
        if corner.lower() == "tl":
            nTrack.append( step[0] ) # 0 for gridCoordsTL
        elif corner.lower() == "tr":
            nTrack.append( step[1] ) # 1 for gridCoordsTR
        elif corner.lower() == "br":
            nTrack.append( step[2] ) # 2 for gridCoordsBR
        elif corner.lower() == "bl":
            nTrack.append( step[3] ) # 3 for gridCoordsBL
    return nTrack

# Function to calculate the direction of a complexTrack step
def getTrackDirection(old=list(),new=list()) -> str:
    x,y = "x","y"
    old = { x:int(old[0]), y:int(old[1]) }
    new = { x:int(new[0]), y:int(new[1]) }
    direction = str()
    #0,0 at top right, so more is farther away from it
    if new[x] == old[x]:
        if new[y] == old[y]: direction = "None"
        elif new[y] > old[y]: direction = "down"
        elif new[y] < old[y]: direction = "up"
    elif new[x] > old[x]:
        if new[y] == old[y]: direction = "fwd"
        elif new[y] > old[y]: direction = "fwd-down"
        elif new[y] < old[y]: direction = "fwd-up"
    elif new[x] < old[x]:
        if new[y] == old[y]: direction = "bck"
        elif new[y] > old[y]: direction = "bck-down"
        elif new[y] < old[y]: direction = "bck-up"
    return direction

# Function to calculate the type of a complexTrack step
def getTrackType(oldCoords=list(),newCoords=list(),windowSize=list(),gridSize=list()) -> str:
    _type = str()
    # Check if new inside (back-up of old):top-left <-> (fwd-down of old):bottom-right
    ## start by getting olds gridCoords
    old_gridCoords = getCoordsTile(oldCoords, windowSize, gridSize)
    new_gridCoords = getCoordsTile(newCoords, windowSize, gridSize)
    ## Get gridCoords of (back-up of old) and (fwd-down of old)
    backUp_ofOld =  [ old_gridCoords[0]-1, old_gridCoords[1]-1 ]
    fwdDown_ofOld = [ old_gridCoords[0]+1, old_gridCoords[1]+1 ]
    ## Check if new is between cuz then inside of one distance
    xIsb = isBetweenI(new_gridCoords[0], backUp_ofOld[0], fwdDown_ofOld[0])
    yIsb = isBetweenI(new_gridCoords[1], backUp_ofOld[1], fwdDown_ofOld[1])
    #print(old_gridCoords,new_gridCoords,backUp_ofOld,fwdDown_ofOld,xIsb,yIsb)
    #print(old_gridCoords,backUp_ofOld,new_gridCoords,fwdDown_ofOld,xIsb,yIsb)
    if xIsb == True and yIsb == True:
        _type = "move"
    else:
        _type = "jump"
    return _type

# Function to handle precise jumps on stepType:"jump" on complexTracks (jump >> move,jump,move # to smooth out) 
def handlePreciseJump(complexTrack=list(),windowSize=list(),gridSize=list()) -> list():
    tileWidthPX = round(windowSize[0]/gridSize[0])
    tileHeightPX = round(windowSize[1]/gridSize[1])
    numOffset = 0
    for index,step in enumerate(complexTrack):
        index = index+numOffset
        if step["type"] == "jump":
            sPos = step["sPos"]
            ePos = step["ePos"]
            dire = step["direction"]
            # get presteps
            prestep_ePos = sPos.copy()
            xPlus = ["fwd","fwd-down","fwd-up"]
            xMins = ["bck","bck-down","bck-up"]
            yPlus = ["down","fwd-down","bck-down"]
            yMins = ["up","fwd-up","bck-up"]
            if dire in xPlus:
                prestep_ePos[0] = prestep_ePos[0]+tileWidthPX/2
            if dire in xMins:
                prestep_ePos[0] = prestep_ePos[0]-tileWidthPX/2
            if dire in yPlus:
                prestep_ePos[1] = prestep_ePos[1]+tileHeightPX/2
            if dire in yMins:
                prestep_ePos[1] = prestep_ePos[1]-tileHeightPX/2
            # get endsteps
            endstep_sPos = ePos.copy()
            xPlus = ["fwd","fwd-down","fwd-up"]
            xMins = ["bck","bck-down","bck-up"]
            yPlus = ["down","fwd-down","bck-down"]
            yMins = ["up","fwd-up","bck-up"]
            if dire in xPlus:
                endstep_sPos[0] = endstep_sPos[0]-tileWidthPX/3
            if dire in xMins:
                endstep_sPos[0] = endstep_sPos[0]+tileWidthPX/3
            if dire in yPlus:
                endstep_sPos[1] = endstep_sPos[1]-tileHeightPX/3
            if dire in yMins:
                endstep_sPos[1] = endstep_sPos[1]+tileHeightPX/3
            # define substeps
            prestep = {"sPos":sPos,"ePos":prestep_ePos,"direction":dire,"type":"move"}
            subjump = {"sPos":prestep_ePos,"ePos":endstep_sPos,"direction":dire,"type":"jump"}
            endjump = {"sPos":endstep_sPos,"ePos":ePos,"direction":dire,"type":"move"}
            # Removing old step
            complexTrack.pop(index)
            complexTrack = complexTrack.copy()
            complexTrack.insert(index, prestep)
            complexTrack.insert(index+1, subjump)
            complexTrack.insert(index+2, endjump)
            numOffset += 3
    return complexTrack

# Function to turn a normal track into a complexTrack: [ [x,y], [x,y] ] >> {"sPos":[x,y], "ePos":[x,y], "direction":"<direction>", "type":"<type>"}
def generateComplexTrack(track=list(),windowSize=list(),gridSize=list()) -> list:
    track = asumeSimpleTrack(track,"TL")
    complexTrack = list()
    # Go through each step
    for index,step in enumerate(track):
        sPos = step
        if len(track)-1 == index:
            ePos = sPos
        else:
            ePos = track[index+1]
        # Get info on this step
        stepInfo = {"sPos":sPos, "ePos":ePos, "direction":getTrackDirection(sPos,ePos), "type":getTrackType(sPos,ePos,windowSize,gridSize)}
        complexTrack.append( stepInfo )
    # Remove empty end
    if complexTrack[-1]["sPos"] == complexTrack[-1]["ePos"] and complexTrack[-1]["direction"] == "None": complexTrack.pop(-1)
    complexTrack = handlePreciseJump(complexTrack,windowSize,gridSize)
    return complexTrack

# Function to compress/simplify complexTracks and turn multile steps in the same direction and of the same type into a bigger piece
def compressComplexTrack(uncompressedComplexTrack=list()) -> list():
    complexTrack_combines = dict()
    complexTrack = list()
    pieceIndex = -1
    lastStep = {"direction":None, "type":None}
    # Asign piece index to steps, and increment if new one is found
    for index,step in enumerate(uncompressedComplexTrack):
        if step["direction"] != lastStep["direction"] or step["type"] != lastStep["type"]:
            pieceIndex += 1
            lastStep = step
        uncompressedComplexTrack[index]["pieceIndex"] = pieceIndex
    # Combine steps to the same piece
    for step in uncompressedComplexTrack:
        if complexTrack_combines.get( step["pieceIndex"] ) == None: complexTrack_combines[ step["pieceIndex"] ] = list()
        complexTrack_combines[ step["pieceIndex"] ].append(step)
    # Compress steps into pieces
    for combine in complexTrack_combines:
        combine = complexTrack_combines[combine]
        firstStep = combine[0]
        lastStep = combine[-1]
        piece = {"sPos":firstStep["sPos"], "ePos":lastStep["ePos"], "direction":firstStep["direction"], "type":firstStep["type"]}
        complexTrack.append( piece )
    return complexTrack

# Function to get the new/next coordinates
def getNewCoords(CoordsPerMove,canvas,enemy,complexTrack=list(),IndexOfTrack=int(),currentPosUnoffseted=list()):
    '''
    return newIndexOfTrack,newPos
    '''
    if IndexOfTrack < len(complexTrack):
        # Get current piece
        piece = complexTrack[IndexOfTrack]
        direction = piece["direction"]
        ePos = piece["ePos"]
        # Move towards ePos and handle change of piece
        if enemy["hidden"] == False:
            if piece["type"] == "jump":
                enemy["hidden"] = True
                enemy["hiddenUntil"] = IndexOfTrack+1
                canvas.itemconfig(enemy["Object"], state='hidden')
        elif enemy["hidden"] == True:
            if IndexOfTrack == enemy["hiddenUntil"]:
                enemy["hidden"] = False
                enemy["hiddenUntil"] = 0
                canvas.itemconfig(enemy["Object"], state='normal')
        ## Define newPos
        newPos = currentPosUnoffseted
        ## DirectionDefiners
        xPlus = ["fwd","fwd-down","fwd-up"]
        xMins = ["bck","bck-down","bck-up"]
        yPlus = ["down","fwd-down","bck-down"]
        yMins = ["up","fwd-up","bck-up"]
        if direction in xPlus:
            newPos[0] = newPos[0]+CoordsPerMove
        if direction in xMins:
            newPos[0] = newPos[0]-CoordsPerMove
        if direction in yPlus:
            newPos[1] = newPos[1]+CoordsPerMove
        if direction in yMins:
            newPos[1] = newPos[1]-CoordsPerMove
        ## Check if done with piece
        isOver = False
        if direction == "fwd":
            if newPos[0] >= ePos[0]: isOver = True
        elif direction == "bck":
            if newPos[0] <= ePos[0]: isOver = True
        elif direction == "down":
            if newPos[1] >= ePos[1]: isOver = True
        elif direction == "up":
            if newPos[1] <= ePos[1]: isOver = True
        elif direction == "fwd-up":
            if newPos[0] >= ePos[0] and newPos[1] <= ePos[1]: isOver = True
        elif direction == "fwd-down":
            if newPos[0] >= ePos[0] and newPos[1] >= ePos[1]: isOver = True
        elif direction == "bck-up":
            if newPos[0] <= ePos[0] and newPos[1] <= ePos[1]: isOver = True
        elif direction == "bck-down":
            if newPos[0] <= ePos[0] and newPos[1] >= ePos[1]: isOver = True
        ## if over check piece and snap to ePos
        if isOver == True:
            newPos = ePos
            newIndexOfTrack = IndexOfTrack+1
        else:
            newIndexOfTrack = IndexOfTrack
        # Return new coords
        return enemy,newIndexOfTrack,newPos
    else:
        return enemy,IndexOfTrack,currentPosUnoffseted

# Function to get midPoint of anchor.NW textures
def getNWsize(canvas,object):
    bbox = canvas.bbox(object)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return width,height