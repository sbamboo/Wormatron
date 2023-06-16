# [Imports]
import tkinter as tk
from assets.sceneSystem import *
from assets.generalFuncs import *
from assets.libs.libSimpleAnim import *

# [Options]
def scene_gameLoading(csStore):
    actDebugCon(csStore) # DEBUG
    if csStore["game_Data"]["HeldSettings"]["skipStartVid"].lower() == "true":
        switchAndRun(csStore,"scene_sync")
        return 0
    # Get Canvas and Window
    current_scene = csStore["current_scene"]
    canvas = current_scene["canvas"]
    window = csStore["window"]
    # Init objects
    addAnims(csStore)
    identifier = "gameLoading_backgroundAnimation"
    backgroundAnim_id = getAvId(csStore,identifier)
    backgroundAnim = createAnim(
        csStore=csStore,
        globalData = globals,
        canvas = canvas,
        x=0,y=0,anchor=tk.NW,animID = backgroundAnim_id,
        filename = f"{csStore['GAME_PARENTPATH']}\\assets\\ui\\loadingBackground.anim",
        identifier=identifier
    )
    csStore["gameLoading_doLoop"] = True
    # Define menu loop
    def internal_loop():
        # Update the canvas
        canvas.update()
        # Update animations
        isLast = isLastFrame(csStore,backgroundAnim_id)
        if isLast == False:
            updateAnims(globals, csStore)
            # Re-Scedule
            if csStore["gameLoading_doLoop"] == True:
                canvas.after(10, internal_loop)
        else:
            if isLast != "ERROR:NoAnimPropertyOnScene":
                switchAndRun(csStore,"scene_sync")
    # Execute first cycle
    internal_loop()