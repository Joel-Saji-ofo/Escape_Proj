# assets.py
import os
from PIL import Image, ImageTk

# ── This makes the path relative to wherever assets.py lives ──
# Works on any machine regardless of username or folder location
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

ASSET_FILES = {
    "bg_lab":        "bgggplace.png",
    "bg_hallway":    "bgggplace.png",
    "player_up":     "upplace.png",
    "player_down":   "downpplace.png",
    "player_left":   "leftplace.png",
    "player_right":  "rightplace.png",
    "door_closed":   "door_closed.png",
    "door_open":     "door_open.png",
    "computer":      "placeholder computer.png",
}

_pil   = {}   # raw PIL images (resizable)
_cache = {}   # finalised PhotoImages (kept alive to prevent GC)


def load_all(tile_size):
    for key, filename in ASSET_FILES.items():
        path         = os.path.join(BASE, filename)
        pil_img      = Image.open(path).convert("RGBA")
        _pil[key]    = pil_img
        _cache[key]  = ImageTk.PhotoImage(
            pil_img.resize((tile_size, tile_size), Image.NEAREST))


def make_photo(key, pixel_size):
    """Return a PhotoImage for key at pixel_size × pixel_size. Cached."""
    cache_key = (key, pixel_size)
    if cache_key not in _cache:
        if key not in _pil:
            raise KeyError(f"Image '{key}' not in assets. Add to ASSET_FILES.")
        _cache[cache_key] = ImageTk.PhotoImage(
            _pil[key].resize((pixel_size, pixel_size), Image.NEAREST))
    return _cache[cache_key]


def load_bg(key, w, h):
    """Load background at canvas size."""
    cache_key = (key, w, h)
    if cache_key not in _cache:
        path = os.path.join(BASE, ASSET_FILES[key])
        _cache[cache_key] = ImageTk.PhotoImage(
            Image.open(path).convert("RGBA").resize((w, h), Image.NEAREST))
    return _cache[cache_key]


def img(key):
    """Default 1-tile PhotoImage — used by engine for player sprites."""
    if key not in _cache:
        raise KeyError(f"Image '{key}' not loaded. Add to ASSET_FILES.")
    return _cache[key]