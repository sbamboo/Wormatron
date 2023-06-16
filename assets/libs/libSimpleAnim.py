# Simple animation library by Simon Kalmi Claesson
# Version: 1.0

import os
import tkinter as tk

class waitCycleProvider(): # Code by Simon Kalmi Claesson
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
  def reset(self, name):
      self.register[name]["current"] = 0

def _commentRemove(multiLineString):
    cleared = ""
    for line in multiLineString.split('\n'):
        if line.strip()[0] != "#":
            line = str(line.split("#")[0]).strip()
            cleared += f"\n{line}"
    return cleared

def _getProp(line,elemName):
    if line.startswith(elemName):
        line = line.replace(f"{elemName}:","")
        line = line.strip()
        return line

def _getConfFile(filename):
  if "anim.conf" not in filename:
    filename = f"{filename}\\anim.conf"
  return filename

def _addSlash(folderpath):
  if not folderpath.endswith("\\"):
    folderpath += "\\"
  return folderpath

def _getFrames(animData):
  frames = []
  # Specific
  if animData["type"].lower() == "specific":
    framesT = animData["_frames"].strip('"').split(",")
    for frame in framesT:
      frame = frame.strip("'").strip('"')
      if frame.startswith("."):
        frame = frame[1:]
        frame = frame.replace("\\\\","\\")
        frame = f"{animData['source']}\\{frame}"
        frame = frame.replace(f"{animData['source']}\\\\",f"{animData['source']}\\")
      frames.append({"file":frame,"object":None})
  # Dynamic
  elif animData["type"].lower() == "dynamic":
    files = os.listdir(animData["source"])
    files.pop(files.index("anim.conf"))
    files = sorted(files, key=lambda x: int(x.split('.')[0]))
    for file in files:
      frames.append({"file":f"{animData['source']}\\{file}","object":None})
  return frames

def _createObjects(globalData,animData,animID):
  for index,frame in enumerate(animData["frames"]):
    globalData()[f"{animID}_frame{index}_img"] = tk.PhotoImage(file=frame["file"])
    animData["frames"][index]["object"] = globalData()[f"{animID}_frame{index}_img"]
  return animData

def _sceneHasAnims(csStore):
  has = False
  if csStore["current_scene"].get("Animations") != None: has = True
  return has

def createAnim(csStore,globalData,canvas,x,y,anchor,animID,filename,identifier=None):
    filename = _getConfFile(filename)
    raw = open(filename, 'r').read()
    text = _commentRemove(raw)
    _frameDelay = None
    _selection = None
    _type = None
    _frames = None
    _loop = False
    _repeats = None
    # Get settings
    for line in text.split('\n'):
        line = line.strip()
        if "frameDelay" in line:
            _frameDelay = _getProp(line,"frameDelay")
        elif "selection" in line:
            _selection = _getProp(line,"selection")
        elif "type" in line:
            _type = _getProp(line,"type")
        elif "frames" in line:
           _frames = _getProp(line,"frames")
        elif "loop" in line:
           _loop = _getProp(line,"loop")
        elif "repeats" in line:
           _repeats = _getProp(line,"repeats")
        elif "autoShow" in line:
           _autoShow = _getProp(line,"autoShow")
        elif "extendLastFrame" in line:
           _extendLastFrame = _getProp(line,"extendLastFrame")
    # Setup
    _provider = waitCycleProvider()
    _provider.create("frameCycler",max=int(_frameDelay))
    _source = os.path.dirname(filename)
    anim = {"_provider":_provider, "_frames":_frames, "source":_source, "config":filename, "frameDelay":_frameDelay, "selection":_selection, "type":_type, "loop":_loop, "repeats":_repeats, "autoShow":_autoShow, "extendLastFrame":_extendLastFrame}
    anim["frames"] = _getFrames(anim)
    if anim["extendLastFrame"].lower() == "true":
      anim["frames"].append(anim["frames"][-1])
    anim = _createObjects(globalData=globalData,animData=anim,animID=animID)
    if anim["autoShow"].lower() == "true":
      anim["object"] = canvas.create_image(x,y,anchor=anchor,image=globalData()[f"{animID}_frame0_img"])
      anim["currentFrame"] = 1
    else:
      anim["object"] = canvas.create_image(x,y,anchor=anchor)
      anim["currentFrame"] = 0
    anim["currentRepeat"] = 1
    anim["animID"] = animID
    anim["stop"] = False
    anim["identifier"] = identifier
    # Return animation
    if csStore["current_scene"].get("Animations") != None:
      currentIdentifiers = []
      for _anim in csStore["current_scene"]["Animations"]:
        if _anim.get("identifier") != None:
          currentIdentifiers.append(_anim["identifier"])
      if identifier in currentIdentifiers: pass
      else:
        csStore["current_scene"]["Animations"].append(anim)

def addAnims(csStore):
  if csStore["current_scene"].get("Animations") == None:
    csStore["current_scene"]["Animations"] = []

def getAvId(csStore,identifier=None,verbose=None):
  if identifier != None:
    if verbose == True: print(f"\033[34mIdentifierGiven:{identifier}\033[0m")
    exists = [False,0]
    for index,_anim in enumerate(csStore["current_scene"]["Animations"]):
      if _anim.get("identifier") != None:
        if identifier == _anim["identifier"]:
          exists = [True,index]
    if verbose == True: print(f"\033[33mIdentifierExists:{exists}\033[0m")
    if exists[0] == False:
      if verbose == True: print(f"\033[31mCreatingNewIdentifier:{len(csStore['current_scene']['Animations'])}\033[0m")
      return len(csStore["current_scene"]["Animations"])
    else:
      if verbose == True: print(f"\033[32mGivingExisitingIdentifier:{exists[1]}\033[0m")
      return exists[1]
  else:
    if verbose == True: print(f"\033[34mNoIdentifier\033[0m")
    if verbose == True: print(f"\033[31mCreatingNewIdentifier:{len(csStore['current_scene']['Animations'])}\033[0m")
    return len(csStore["current_scene"]["Animations"])

def getAnims(csStore):
  return csStore["current_scene"]["Animations"]

def updateAnims(globalData,csStore):
  for index,animation in enumerate(csStore["current_scene"]["Animations"]):
    if animation["_provider"].increment("frameCycler") == True:
      if animation['currentFrame'] != len(animation["frames"]):
        pic = globalData()[f"{animation['animID']}_frame{animation['currentFrame']}_img"]
        csStore["current_scene"]["canvas"].itemconfig(animation["object"],image=pic)
        csStore["current_scene"]["Animations"][index]["currentFrame"] += 1
      else:
        if animation["loop"].lower() == "true":
          if animation["stop"] != True:
            csStore["current_scene"]["Animations"][index]["currentFrame"] = 0
        elif animation["repeats"] != None:
          if animation["stop"] != True:
            if csStore["current_scene"]["Animations"][index]["currentRepeat"] != int(csStore["current_scene"]["Animations"][index]["repeats"]):
              csStore["current_scene"]["Animations"][index]["currentRepeat"] += 1
              csStore["current_scene"]["Animations"][index]["currentFrame"] = 0
            else:
              csStore["current_scene"]["Animations"][index]["currentRepeat"] = 0
              if csStore["current_scene"]["Animations"][index]["loop"].lower() != "true":
                csStore["current_scene"]["Animations"][index]["stop"] = True



def removeAnim(csStore,animID):
  frames = csStore["current_scene"]["Animations"][animID]["frames"]
  for frame in frames:
    csStore["current_scene"]["canvas"].delete(frame["object"])
  csStore["current_scene"]["Animations"].pop(animID)

def stopAnim(csStore,animID):
  csStore["current_scene"]["Animations"][animID]["stop"] = True

def playAnim(csStore,animID):
  csStore["current_scene"]["Animations"][animID]["stop"] = False

def resetAnim(csStore,animID):
  csStore["current_scene"]["Animations"][animID]["currentFrame"] = 0

def isLastFrame(csStore,animID):
  if _sceneHasAnims(csStore) == True:
    animation = csStore["current_scene"]["Animations"][animID]
    if animation["repeats"] != None:
      return animation['currentFrame'] == len(animation["frames"])
    else:
      return (animation['currentFrame'] == len(animation["frames"])) == (animation["currentRepeat"] == int(csStore["current_scene"]["Animations"][index]["repeats"]))
  else:
    return "ERROR:NoAnimPropertyOnScene"