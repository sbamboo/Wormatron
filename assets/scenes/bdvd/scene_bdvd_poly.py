# [Imports]
import tkinter as tk
from PIL import Image, ImageTk
import random
from assets.sceneSystem import *
from assets.generalFuncs import isBetweenI

# [Bouncing DVD Logo]
def scene_bdvd(csStore):
    bdvd_pause = False
    hits = 0
    fxEnabled = False
    if csStore.get("game_Data") != None:
        fxEnabled = csStore.get("game_Data")["HeldSettings"]["easterEggFX"]
    # OnClick Function
    def onClick(event):
        nonlocal bdvd_pause,window
        window.unbind(gameData["Settings"]["Keybinds"]["click"])
        bdvd_pause = True
        switch_scene(csStore,"scene_mainMenu")
        runCurrentScene(csStore)
    # Collision checker
    def collides():
        nonlocal bdvd_vel,hits
        hits += 1
        collides = False
        if (bdvd_pos[0] < 0) or ((bdvd_pos[0] + bdvd_logo_images[bdvd_logo_index].width()) > current_scene["width"]):
            bdvd_vel[0] *= -1
            collides = True
        if (bdvd_pos[1] < 0) or ((bdvd_pos[1] + bdvd_logo_images[bdvd_logo_index].height()) > current_scene["height"]):
            bdvd_vel[1] *= -1
            collides = True
        return collides
    def isCorner(offset=None):
        nonlocal canvas
        inCorner = False
        width = int(csStore["current_scene"]["width"])
        height = int(csStore["current_scene"]["height"])
        if offset == None:
            # Top Left
            if bdvd_pos[0] == 0 and bdvd_pos[1] == 0:  inCorner = True
            # Top Right
            if bdvd_pos[0]+bdvd_logo_images[bdvd_logo_index].width() == width and bdvd_pos[1] == 0:  inCorner = True
            # Bottom Left
            if bdvd_pos[0] == 0 and bdvd_pos[1]+bdvd_logo_images[bdvd_logo_index].height() == height:  inCorner = True
            # Bottom Right
            if bdvd_pos[0]+bdvd_logo_images[bdvd_logo_index].width() == width and bdvd_pos[1]+bdvd_logo_images[bdvd_logo_index].height() == height:  inCorner = True
        else:
            offset = int(offset)
            # Top Left
            if isBetweenI(bdvd_pos[0],0,offset) and isBetweenI(bdvd_pos[1],0,offset): inCorner = True
            # Top Right
            if isBetweenI(bdvd_pos[0]+bdvd_logo_images[bdvd_logo_index].width(),width-offset,width) and isBetweenI(bdvd_pos[1],0,offset):  inCorner = True
            # Bottom Left
            if isBetweenI(bdvd_pos[0],0,offset) and isBetweenI(bdvd_pos[1]+bdvd_logo_images[bdvd_logo_index].height(),height-offset,height):  inCorner = True
            # Bottom Right
            if isBetweenI(bdvd_pos[0]+bdvd_logo_images[bdvd_logo_index].width(),width-offset,width) and isBetweenI(bdvd_pos[1]+bdvd_logo_images[bdvd_logo_index].height(),height-offset,height):  inCorner = True
        return inCorner
    # Get Canvas and Window
    current_scene = csStore["current_scene"]
    canvas = current_scene["canvas"]
    window = csStore["window"]
    window.title( window.title().replace("Bdvd","Press any key to return... (Progress not saved)") )
    # Start loop
    if fxEnabled == True:
        csStore["soundSys"].playSound(f"{csStore['GAME_PARENTPATH']}\\assets\\scenes\\bdvd\\background.wav",loop=True)
    # Define variables
    bdvd_pos = [0,0]
    bdvd_logo_images = []
    bdvd_logo_index = 0
    bdvd_vel = [1,1]
    # Load images
    for i in range(8): # 8 being the amount of images
        bvdv_image = Image.open(f"{csStore['GAME_PARENTPATH']}\\assets\\scenes\\bdvd\\dvd{i+1}.png")
        bdvd_logo_images.append(ImageTk.PhotoImage(bvdv_image))
    # Define objects
    bdvd_logo = canvas.create_image(bdvd_pos[0],bdvd_pos[1],image=bdvd_logo_images[bdvd_logo_index],anchor=tk.NW)
    bdvd_trail_verts = [0,0,0,0,0,0]
    bdvd_trail = canvas.create_polygon(bdvd_trail_verts,fill="blue")
    # Define menu loop
    def internal_loop():
        nonlocal bdvd_pause,canvas,bdvd_logo_images,bdvd_logo_index,bdvd_logo,bdvd_trail,hits
        # Update the canvas
        canvas.update()
        # Move loop
        canvas.move(bdvd_logo,bdvd_vel[0],bdvd_vel[1])
        bdvd_pos[0] += bdvd_vel[0]
        bdvd_pos[1] += bdvd_vel[1]
        if collides() == True:
            # Colide math
            bdvd_logo_index += 1
            if bdvd_logo_index >= len(bdvd_logo_images):
                bdvd_logo_index = 0
            canvas.itemconfig(bdvd_logo,image=bdvd_logo_images[bdvd_logo_index])
            # Draw trail
            bdvd_trail_coords = canvas.coords(bdvd_trail)
            bdvd_trail_coords.extend([bdvd_pos[0],bdvd_pos[1]])
            canvas.coords(bdvd_trail, bdvd_trail_coords)
        # Check corner
        if isCorner() == True and (hits >= 2 and bdvd_pos[0] > 2):
            if fxEnabled == True:
                canvas.configure(bg="yellow")
                globals()["bdvd_wonBackground"] = tk.PhotoImage(file=f"{csStore['GAME_PARENTPATH']}\\assets\\scenes\\bdvd\\won.png")
                canvas.create_image(0,0,image=bdvd_wonBackground,anchor=tk.NW)
                csStore["soundSys"].playSound(f"{csStore['GAME_PARENTPATH']}\\assets\\scenes\\bdvd\\Victory.wav")
                bdvd_pause = True
        # Update if was not clicked
        if bdvd_pause == False:
            canvas.after(10, internal_loop)
    # Execute first cycle
    canvas.after(0,internal_loop)
    gameData = csStore["game_Data"]
    window.bind(gameData["Settings"]["Keybinds"]["click"],onClick)