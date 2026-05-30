# room_manager.py
# ---------------------------------------------------------------
# Loads room dicts, spawns all objects, manages fade transitions,
# and handles the key reward system.
# You only touch this file if you add a brand new object type
# that doesn't exist yet (e.g. inventory pickups later).
# ---------------------------------------------------------------

import importlib
from objects    import make_object, make_wall, make_door, T, TILE
from assets     import img, load_bg
from game_state import STATE


class RoomManager:
    def __init__(self, canvas, engine, hud, W, H):
        self.canvas   = canvas
        self.engine   = engine
        self.hud      = hud
        self.W        = W
        self.H        = H
        self.objects  = []
        self._bg_id   = None
        self._overlay = None

        # Stores the current room's key_reward spec while room is active
        # { "puzzles_needed": 3, "grants": "lab_exit_key" }
        self._key_reward = None

    # ----------------------------------------------------------
    # PUBLIC: load a room by name string
    # ----------------------------------------------------------
    def load(self, room_key, spawn_tx, spawn_ty):
        """
        room_key       — matches a file in rooms/ e.g. "room_1"
        spawn_tx/ty    — tile where the player appears
        """
        self._clear()
        STATE["current_room"]        = room_key
        STATE["room_puzzles_solved"] = 0   # reset per-room count

        # Dynamically import rooms/room_key.py
        module = importlib.import_module(f"rooms.{room_key}")
        room   = module.ROOM

        # Store key reward spec for this room (may be None)
        self._key_reward = room.get("key_reward", None)

        # Background
        bg_photo    = load_bg(room["bg"], self.W, self.H)
        self._bg_id = self.canvas.create_image(
            0, 0, anchor="nw", image=bg_photo)

        # Border walls — always automatic, every room
        self._add_border_walls()

        # Spawn objects from the room's "objects" list
        for spec in room.get("objects", []):
            obj = self._build_object(spec)
            if obj:
                self.objects.append(obj)

        # Spawn doors from the room's "doors" list
        for spec in room.get("doors", []):
            obj = make_door(
                self.canvas,
                tx       = spec["tx"],
                ty       = spec["ty"],
                key_id   = spec.get("key_id", "default_key"),
                leads_to = spec["leads_to"],
                spawn    = spec["spawn"],
                label    = spec.get("label", "Exit Door"),
            )
            self.objects.append(obj)

        # Spawn player
        player = make_object(
            self.canvas, "player_down",
            spawn_tx, spawn_ty,
            size=1, solid=False, kind="player")
        self.objects.append(player)

        # Hand the new object list and player to the engine
        self.engine.set_objects(self.objects, player)

    # ----------------------------------------------------------
    # KEY REWARD — called by puzzles._on_solve after every solve
    # Checks if the room's puzzle target has been hit and if so
    # silently adds the key to STATE["keys"].
    # ----------------------------------------------------------
    def check_key_reward(self, hud):
        if not self._key_reward:
            return

        needed  = self._key_reward["puzzles_needed"]
        grants  = self._key_reward["grants"]

        if (STATE["room_puzzles_solved"] >= needed
                and grants not in STATE["keys"]):
            STATE["keys"].add(grants)
            # Flash a message — when inventory is added, show item here too
            hud.flash(f"Key obtained: {grants.replace('_', ' ').title()}!")

    # ----------------------------------------------------------
    # TRANSITION — fade out → swap room → fade in
    # ----------------------------------------------------------
    def transition(self, leads_to, spawn):
        if STATE["transitioning"]:
            return
        STATE["transitioning"] = True
        self._ensure_overlay()
        self._fade_out(leads_to, spawn, step=0)

    def _ensure_overlay(self):
        if not self._overlay:
            self._overlay = self.canvas.create_rectangle(
                0, 0, self.W, self.H,
                fill="", outline="")

    # tkinter doesn't support real alpha — stipple is the closest
    _STIPPLES = ["", "gray12", "gray25", "gray50", "gray75", "gray75"]

    def _fade_out(self, leads_to, spawn, step):
        self.canvas.itemconfig(
            self._overlay,
            fill="black",
            stipple=self._STIPPLES[step])
        self.canvas.tag_raise(self._overlay)

        if step < len(self._STIPPLES) - 1:
            self.canvas.after(
                55, lambda: self._fade_out(leads_to, spawn, step + 1))
        else:
            # Fully dark — swap rooms
            self.canvas.after(80, lambda: self._do_swap(leads_to, spawn))

    def _do_swap(self, leads_to, spawn):
        self.load(leads_to, spawn[0], spawn[1])
        self.canvas.tag_raise(self._overlay)
        self.canvas.after(80, lambda: self._fade_in(
            step=len(self._STIPPLES) - 1))

    def _fade_in(self, step):
        if step >= 0:
            self.canvas.itemconfig(
                self._overlay,
                fill="black" if step > 0 else "",
                stipple=self._STIPPLES[step] if step > 0 else "")
            self.canvas.after(
                55, lambda: self._fade_in(step - 1))
        else:
            self.canvas.itemconfig(self._overlay, fill="", stipple="")
            self.canvas.tag_lower(self._overlay)
            STATE["transitioning"] = False

    # ----------------------------------------------------------
    # INTERNAL HELPERS
    # ----------------------------------------------------------
    def _clear(self):
        """Delete all canvas items for the current room."""
        overlay_id = self._overlay  # keep the overlay alive
        for obj in self.objects:
            if obj["id"] != overlay_id:
                try:
                    self.canvas.delete(obj["id"])
                except Exception:
                    pass
        if self._bg_id:
            try:
                self.canvas.delete(self._bg_id)
            except Exception:
                pass
        self.objects = []

    def _add_border_walls(self):
        """
        Invisible solid walls along all four edges.
        Added automatically — you never write these in room files.
        """
        cols = self.W // TILE
        rows = self.H // TILE
        for tx in range(cols):
            self.objects.append(make_wall(self.canvas, tx, 0))
            self.objects.append(make_wall(self.canvas, tx, rows - 1))
        for ty in range(1, rows - 1):
            self.objects.append(make_wall(self.canvas, 0,       ty))
            self.objects.append(make_wall(self.canvas, cols - 1, ty))

    def _build_object(self, spec):
        """
        Turns one line from a room dict into a live canvas object.

        To add a new object type in the future, add an elif here.
        """
        kind = spec.get("type", "object")
        size = spec.get("size", 1)   # default size = 1 tile

        # -- invisible wall --
        if kind == "wall":
            return make_wall(self.canvas,
                             spec["tx"], spec["ty"],
                             size=size)

        # -- puzzle object --
        if "on_interact" in spec:
            return make_object(
                self.canvas,
                img_key     = spec["img"],
                tx          = spec["tx"],
                ty          = spec["ty"],
                size        = size,
                solid       = spec.get("solid", True),
                interactable= True,
                on_interact = self._wrap_interact(spec["on_interact"]),
                kind        = "puzzle")

        # -- plain object (solid or decoration) --
        return make_object(
            self.canvas,
            img_key = spec["img"],
            tx      = spec["tx"],
            ty      = spec["ty"],
            size    = size,
            solid   = spec.get("solid", True),
            kind    = kind)

    def _wrap_interact(self, raw_fn):
        """
        Puzzle functions from puzzles.py have signature:
            _interact(obj, root, hud, room_manager)
        Engine calls them as:
            fn(obj, root, hud)
        This wrapper injects room_manager automatically so puzzles
        can call check_key_reward without the room file knowing about it.
        """
        rm = self
        def _wrapped(obj, root, hud):
            raw_fn(obj, root, hud, room_manager=rm)
        return _wrapped