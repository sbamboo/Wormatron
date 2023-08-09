# [Imports]
import tkinter as tk
from PIL import Image, ImageTk
from assets.sceneSystem import *
from assets.generalFuncs import clickStateStorage, actDebugCon, removeUser, decryptServer
import json,base64,io,requests

def get_lowest_object_position(event):
    lowest_widget = event.widget
    x_relative_to_top = 0
    y_relative_to_top = 0
    while str(lowest_widget) != ".":
        x_relative_to_top += lowest_widget.winfo_x()
        y_relative_to_top += lowest_widget.winfo_y()
        lowest_widget = lowest_widget.nametowidget(lowest_widget.winfo_parent())
    return [x_relative_to_top,y_relative_to_top]

# [Options]
def scene_scoreboard(csStore):
    # Get Canvas and Window
    current_scene = csStore["current_scene"]
    canvas = current_scene["canvas"]
    window = csStore["window"]
    actDebugCon(csStore)  # DEBUG

    # Define a clickStateStorage
    clickStates = clickStateStorage()

    # Define buttons
    btn_gotoMenu_obj = tk.Button(window, text="🔙", command=lambda: clickStates.toggle("gotoMenu"), font=('Consolas', 18))
    btn_gotoMenu = canvas.create_window(0, 0, anchor=tk.NW, window=btn_gotoMenu_obj)

    # Get badgeStore
    badgeStore = json.load(open(f"{csStore['GAME_PARENTPATH']}\\assets\\badgeStore.json",'r'))

    # Get scoreboard
    try:
        _scoreboard = csStore["scoreboardConnector"].get("wormatron")
        _scoreboard = decryptServer(_scoreboard)
    except:
        _scoreboard = {"Connection to scoreboard could not be initialized!":{}}

    # Create title
    canvas.create_text((current_scene["width"] / 2, 40), text="Scoreboard", font=("Consolas", 45))

    # Create a frame for the scoreboard
    scoreboard_frame = tk.Frame(canvas)
    canvas.create_window((current_scene["width"] / 2, 250), window=scoreboard_frame)

    # Create a canvas inside the scoreboard frame
    scoreboard_canvas = tk.Canvas(scoreboard_frame, width=700, height=300)  # Set the desired width of the canvas
    scoreboard_canvas.pack(side=tk.LEFT, fill=tk.X)

    # Add a scrollbar to the scoreboard frame
    scrollbar = tk.Scrollbar(scoreboard_frame, orient=tk.VERTICAL, command=scoreboard_canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    scoreboard_canvas.configure(yscrollcommand=scrollbar.set)

    # Configure canvas scrolling region
    scoreboard_content_frame = tk.Frame(scoreboard_canvas)
    scoreboard_content_frame_canvasObj = scoreboard_canvas.create_window((0, 0), window=scoreboard_content_frame, anchor=tk.NW)
    scoreboard_content_frame.bind("<Configure>", lambda event: scoreboard_canvas.configure(scrollregion=scoreboard_canvas.bbox("all")))

    # Define hovering effects object dict
    hoveringLabels = []
    text_label = tk.Label(csStore["current_scene"]["canvas"])
    text_label.pack_forget()

    # Define accountRemover
    y = current_scene["height"]
    accr_title = canvas.create_text(5,y-45,anchor=tk.W,text="Delete your account: (Irreversible)",font=("Consolas",10))
    accr_button = tk.Button(window, text="Remove account",fg="red", command=lambda:clickStates.toggle("removeAccount"),font=("Consolas",10))
    accr_button_window = canvas.create_window(5,y-20,anchor=tk.W, window=accr_button)

    # Define accountSignout
    accs_title = canvas.create_text(5,y-95,anchor=tk.W,text="Sign out",font=("Consolas",10))
    accs_button = tk.Button(window, text="Signout", command=lambda:clickStates.toggle("signoutAccount"),font=("Consolas",10))
    accs_button_window = canvas.create_window(5,y-70,anchor=tk.W, window=accs_button)

    # Define signed in as
    offset = 46
    canvas.create_rectangle(0+offset,0,270+offset,30,fill="lightblue")
    canvas.create_text(5+offset,5, anchor=tk.NW, text=f"Signed in as: ",font=("Consolas", 12),fill="Black")
    canvas.create_text(130+offset,5, anchor=tk.NW, text=csStore['player_username'],font=("Consolas", 12),fill="Orange")

    # Define functions
    def show_text(event):
        c = get_lowest_object_position(event)
        x = c[0]
        y = c[1]
        text_label.config(text=event.widget.hover_text)
        text_label.place(x=x, y=y - event.widget.winfo_height() + (event.widget.winfo_height()/2))

    def hide_text(event):
        text_label.place_forget()

    # Add elements to the scoreboard
    for index, (name, details) in enumerate(_scoreboard.items()):
        # Name Label
        if details.get("xp") != None: 
            label_name = tk.Label(scoreboard_content_frame, text=f"{name}:", font=("Consolas", 15))
        else:
            label_name = tk.Label(scoreboard_content_frame, text=f"{name}", font=("Consolas", 15), fg="red")
        label_name.grid(row=index, column=0, sticky="w")

        # Add badge item
        badges_frame = tk.Frame(scoreboard_content_frame)
        badges_frame.grid(row=index, column=1, sticky="w")

        # Populate badges
        if details.get("badges") != None:
            for i, badge in enumerate(details['badges']):
                # Decode the base64 image string and open the image using PIL
                image_bytes = base64.b64decode(badgeStore[badge][0])
                image = Image.open(io.BytesIO(image_bytes))
                # Create a PhotoImage from the image
                photo = ImageTk.PhotoImage(image)
                #image = Image.open("badge.png")  # Replace with your badge image
                image = image.resize((40, 40))  # Adjust badge image size as needed
                badge_img = ImageTk.PhotoImage(image)
                badge_label = tk.Label(badges_frame, image=badge_img)
                badge_label.image = badge_img
                # Fix with hovering label
                badge_label.hover_text = badgeStore[badge][1]
                badge_label.bind("<Enter>",show_text)
                badge_label.bind("<Leave>",hide_text)
                hoveringLabels.append(badge_label)
                # Fix to grid
                badge_label.grid(row=0, column=i, padx=2)
        # XP label
        if details.get("xp") != None:
            xp_label_text = f"XP: {details['xp']}, Level: {details['level']}"
            # Code for tabIn text if length to great
            pixel_charsInFrame = len(xp_label_text)*15
            if pixel_charsInFrame > 700:
                xp_label_text = f"XP: {details['xp']},\n Level: {details['level']}"
            xp_label = tk.Label(scoreboard_content_frame, text=xp_label_text, font=("Consolas", 15))
            xp_label.grid(row=index, column=2, sticky="w")


    # Define menu loop
    def internal_loop():
        # Update the canvas
        canvas.update_idletasks()

        # GotoMenu
        if clickStates.get("gotoMenu") == True:
            switchAndRun(csStore, "scene_mainMenu")
        elif clickStates.get("removeAccount") == True:
            acc = csStore["player_username"]
            if acc != "" and acc != None:
                removeUser(csStore,acc)
                switchAndRun(csStore, "scene_sync")
        elif clickStates.get("signoutAccount") == True:
            csStore["cliArguments"]["usr"] = None
            switchAndRun(csStore, "scene_sync")
        # Schedule if no buttons were clicked
        else:
            canvas.after(100, internal_loop)

    # Execute first cycle
    internal_loop()
