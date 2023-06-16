import tkinter as tk

def pack_canvas(canvas):
    canvas.pack(expand=True, anchor="center")

def create_canvas_item(window, canvas_data):
    canvas = tk.Canvas(window, width=canvas_data["width"], height=canvas_data["height"])
    canvas.configure(highlightthickness=canvas_data["highlightThickness"], bg=canvas_data["backgroundColor"])
    return canvas

def create_scenes(csStore):
    scenes_dict = csStore["scenes"]
    for scene_name, scene_data in scenes_dict.items():
        # Overwrite
        if scene_data["overwrite"] and scene_data["overwrite"] != "None":
            overwrite_scene = scenes_dict.get(scene_data["overwrite"])
            if overwrite_scene:
                scene_data.update(overwrite_scene)
        # LoadData
        scene_data["canvas"] = create_canvas_item(csStore["window"], scene_data)
        # Get reset
        scene_data["orgData"] = scene_data.copy()
        # Pack if not hidden
        if not scene_data["hiddenOnCreate"]:
            pack_canvas(scene_data["canvas"])
        # Give name
        scene_data["name"] = scene_name
        csStore["scenes"][scene_name] = scene_data

def switch_scene(csStore,scene_name,dontRecreate=None):
    # Update title
    csStore["window"].title( f"{csStore['GAME_STDTITLE']} - {scene_name.replace('scene_','').capitalize()}" )
    current_scene = csStore.get("current_scene")
    csStore["last_scene"] = current_scene
    scenes = csStore.get("scenes")
    if current_scene and current_scene.get("canvas"):
        current_scene["canvas"].pack_forget()

    for scene_data in scenes.values():
        if scene_data.get("canvas") and scene_data["canvas"] != current_scene.get("canvas"):
            scene_data["canvas"].pack_forget()

    current_scene = scenes.get(scene_name)
    if current_scene.get("resizeWindow") == True: csStore["window"].geometry(f"{current_scene['width']}x{current_scene['height']}")
    if current_scene and current_scene.get("reconstructOnSwitch") and dontRecreate != True:
        current_scene["canvas"].destroy()
        csStore["current_scene"] = current_scene
        current_scene["canvas"] = create_canvas_item(csStore["window"],current_scene)
        pack_canvas(current_scene["canvas"])
    else: 
        pack_canvas(current_scene["canvas"])
    csStore["current_scene"] = current_scene

def runCurrentScene(csStore):
    csStore["current_scene"]["function"](csStore)

def switchAndRun(csStore,scene_name):
    switch_scene(csStore, scene_name)
    runCurrentScene(csStore)

class crossSceneStorage():
    def __init__(self):
        self.storage = dict()

    def __setitem__(self, key, value):
        self.storage.__setitem__(key, value)
    def __ior__(self, other):
        if isinstance(other, dict):
            self.storage.update(other)
        return self
    def __repr__(self):
        return repr(self.storage)
    def __getitem__(self, key):
        return self.storage.__getitem__(key)

    def append(self,data):
        self.storage.append(data)
    def update(self,data):
        self.storage.update(data)
    def get(self,key=None):
        if key != None:
            return self.storage.get(key)
        else:
            return self.storage
    def clear(self):
        self.storage.clear()
    def copy(self):
        return copy.copy(self)