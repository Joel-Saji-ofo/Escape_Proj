# objects.py
from PIL import Image, ImageTk
from assets import make_photo
from game_state import STATE

TILE = 40


def T(tile):
    """Tile index → pixel centre."""
    return tile * TILE + TILE // 2


def _spawn_image(canvas, key, px, py, size):
    """Spawns a correctly-sized image. Returns (canvas_id, photo)."""
    pixel_size = int(TILE * size)
    photo      = make_photo(key, pixel_size)
    cid        = canvas.create_image(px, py, image=photo, anchor="center")
    return cid, photo


# ==============================================================
# CORE OBJECT FACTORY
# ==============================================================
def make_object(canvas, img_key, tx, ty,
                size=1,
                solid=True,
                interactable=False,
                on_interact=None,
                kind="generic"):
    """
    size — tiles. Image AND collision box scale together.
    size=1 → 40px,  size=2 → 80px,  size=3 → 120px
    """
    px, py     = T(tx), T(ty)
    pixel_size = int(TILE * size)
    half       = pixel_size / 2

    cid, photo = _spawn_image(canvas, img_key, px, py, size)

    return {
        "id":           cid,
        "photo":        photo,
        "x":            float(px),
        "y":            float(py),
        "half":         half,
        "solid":        solid,
        "interactable": interactable,
        "on_interact":  on_interact,
        "kind":         kind,
        "solved":       False,
        "door_state":   "closed",
    }


# ==============================================================
# INVISIBLE WALL
# ==============================================================
def make_wall(canvas, tx, ty, size=1):
    px   = T(tx)
    py   = T(ty)
    half = (TILE * size) / 2
    cid  = canvas.create_rectangle(
        px - half, py - half, px + half, py + half,
        outline="", fill="")
    return {
        "id":           cid,
        "photo":        None,
        "x":            float(px),
        "y":            float(py),
        "half":         half,
        "solid":        True,
        "interactable": False,
        "on_interact":  None,
        "kind":         "wall",
        "solved":       False,
        "door_state":   "closed",
    }


# ==============================================================
# DOOR FACTORY
# ==============================================================
def make_door(canvas, tx, ty,
              key_id="default_key",
              leads_to="room_2",
              spawn=(2, 7),
              label="Exit Door"):
    DOOR_SIZE  = 2
    px, py     = T(tx), T(ty)
    pixel_size = int(TILE * DOOR_SIZE)
    half       = pixel_size / 2

    cid, photo = _spawn_image(canvas, "door_closed", px, py, DOOR_SIZE)

    obj = {
        "id":           cid,
        "photo":        photo,
        "x":            float(px),
        "y":            float(py),
        "half":         half,
        "solid":        True,
        "interactable": True,
        "on_interact":  None,
        "kind":         "door",
        "solved":       False,
        "door_state":   "closed",
        "key_id":       key_id,
        "leads_to":     leads_to,
        "spawn":        spawn,
        "trigger_tx":   tx,
        "trigger_ty":   ty,
    }

    def _interact(obj, root, hud, room_manager=None):
        if obj["door_state"] == "open":
            return
        if obj["key_id"] in STATE["keys"]:
            obj["door_state"]   = "open"
            obj["solid"]        = False
            obj["interactable"] = False
            obj["x"]            = -9999.0
            obj["y"]            = -9999.0
            open_photo          = make_photo("door_open", pixel_size)
            obj["photo"]        = open_photo
            canvas.itemconfig(obj["id"], image=open_photo)
            hud.flash(f"{label} is OPEN — walk through!")
        else:
            hud.flash(f"{label} is locked. Find the key first.")

    obj["on_interact"] = _interact
    return obj