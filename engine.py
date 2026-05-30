# engine.py
import math
from game_state import STATE

TILE          = 40
SPEED         = 5
INTERACT_DIST = TILE * 2.0

DIR_IMG = {
    "up":    "player_up",
    "down":  "player_down",
    "left":  "player_left",
    "right": "player_right",
}

class Engine:
    def __init__(self, root, canvas, hud, room_manager):
        self.root         = root
        self.canvas       = canvas
        self.hud          = hud
        self.rm           = room_manager
        self.objects      = []
        self.player       = None
        self.keys         = set()

        root.bind("<KeyPress>",   lambda e: self.keys.add(e.keysym.lower()))
        root.bind("<KeyRelease>", lambda e: self.keys.discard(e.keysym.lower()))

    def set_objects(self, objects, player):
        """Called by room_manager every time a room loads."""
        self.objects = objects
        self.player  = player

    # ----------------------------------------------------------
    # MAIN LOOP — called every 16ms
    # ----------------------------------------------------------
    def update(self):
        if not STATE["transitioning"] and self.player:
            self._move()
            self._interact()
            self._check_door_walk()
            self.hud.update()
            self.hud.raise_all()
            self.canvas.tag_raise(self.player["id"])

        self.root.after(16, self.update)

    # ----------------------------------------------------------
    # MOVEMENT + COLLISION
    # ----------------------------------------------------------
    def _move(self):
        dx, dy = 0.0, 0.0
        if "w" in self.keys or "up"    in self.keys:
            dy -= 1; STATE["player_dir"] = "up"
        if "s" in self.keys or "down"  in self.keys:
            dy += 1; STATE["player_dir"] = "down"
        if "a" in self.keys or "left"  in self.keys:
            dx -= 1; STATE["player_dir"] = "left"
        if "d" in self.keys or "right" in self.keys:
            dx += 1; STATE["player_dir"] = "right"

        mag = math.hypot(dx, dy)
        if not mag:
            self._update_sprite()
            return

        dx = dx / mag * SPEED
        dy = dy / mag * SPEED

        # Try X and Y separately so player slides along walls
        self._try_move(dx, 0)
        self._try_move(0, dy)
        self._update_sprite()

    def _try_move(self, dx, dy):
        p   = self.player
        nx  = p["x"] + dx
        ny  = p["y"] + dy
        ph  = TILE / 2

        for o in self.objects:
            if not o["solid"] or o is p:
                continue
            hw = o.get("half_w", o["half"])
            hh = o.get("half_h", o["half"])
            if (abs(nx - o["x"]) < ph + hw and
                    abs(ny - o["y"]) < ph + hh):
                return   # blocked — don't apply move

        p["x"] = nx
        p["y"] = ny
        self.canvas.coords(p["id"], nx, ny)

    def _update_sprite(self):
        from assets import img
        self.canvas.itemconfig(
            self.player["id"],
            image=img(DIR_IMG[STATE["player_dir"]]))

    # ----------------------------------------------------------
    # INTERACTION (E key)
    # ----------------------------------------------------------
    def _interact(self):
        p = self.player
        closest, best = None, INTERACT_DIST

        for o in self.objects:
            if not o["interactable"]:
                continue
            d = math.hypot(p["x"] - o["x"], p["y"] - o["y"])
            if d < best:
                best, closest = d, o

        if closest:
            self.hud.set_guide("[E]  Interact")
            if "e" in self.keys:
                self.keys.discard("e")
                closest["on_interact"](closest, self.root, self.hud)
        else:
            self.hud.set_guide("")

    # ----------------------------------------------------------
    # DOOR WALK-THROUGH DETECTION
    # Player steps into open door tile → trigger transition
    # ----------------------------------------------------------
    def _check_door_walk(self):
        p = self.player
        for o in self.objects:
            if o["kind"] != "door" or o["door_state"] != "open":
                continue
            # Use original tile position for trigger zone
            tx, ty = o.get("trigger_tx", 0), o.get("trigger_ty", 0)
            door_px = tx * TILE + TILE // 2
            door_py = ty * TILE + TILE // 2
            if (abs(p["x"] - door_px) < TILE * 1.5 and
                    abs(p["y"] - door_py) < TILE * 1.5):
                self.rm.transition(o["leads_to"], o["spawn"])