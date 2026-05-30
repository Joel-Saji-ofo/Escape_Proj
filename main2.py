# main2.py
# ---------------------------------------------------
# Direct game launcher for demo/testing
# Skips login + desktop completely
# ---------------------------------------------------

import tkinter as tk

from assets import load_all
from engine import Engine
from hud import HUD
from room_manager import RoomManager

# ── Constants ──────────────────────────────────────
GAME_W = 800
GAME_H = 600
TILE   = 40

# ── Root Window ────────────────────────────────────
root = tk.Tk()
root.title("Lab Escape")
root.geometry(f"{GAME_W}x{GAME_H}")
root.resizable(False, False)

# ── Canvas ─────────────────────────────────────────
canvas = tk.Canvas(
    root,
    width=GAME_W,
    height=GAME_H,
    bg="black",
    highlightthickness=0
)
canvas.pack()

# ── Load Assets ────────────────────────────────────
load_all(TILE)

# ── Initialise Systems ─────────────────────────────
hud    = HUD(canvas, GAME_W, GAME_H)
engine = Engine(root, canvas, hud, None)

rm = RoomManager(
    canvas,
    engine,
    hud,
    GAME_W,
    GAME_H
)

engine.rm = rm

# ── Load Starting Room ─────────────────────────────
rm.load("room_1", spawn_tx=2, spawn_ty=7)

# ── Start Game Loop ────────────────────────────────
engine.update()

# ── Run ────────────────────────────────────────────
root.mainloop()