# hud.py
from game_state import STATE

class HUD:
    def __init__(self, canvas, W, H):
        self.canvas   = canvas
        self._job     = None

        self._counter = canvas.create_text(
            10, 10, anchor="nw", text="",
            fill="yellow", font=("Courier", 13, "bold"))

        self._guide   = canvas.create_text(
            W // 2, 28, text="",
            fill="white", font=("Arial", 15, "bold"))

        self._msg     = canvas.create_text(
            W // 2, 56, text="",
            fill="tomato", font=("Arial", 13, "bold"))

    def flash(self, text, ms=2500):
        self.canvas.itemconfig(self._msg, text=text)
        if self._job:
            self.canvas.after_cancel(self._job)
        self._job = self.canvas.after(
            ms, lambda: self.canvas.itemconfig(self._msg, text=""))

    def set_guide(self, text):
        self.canvas.itemconfig(self._guide, text=text)

    def update(self):
        self.canvas.itemconfig(
            self._counter,
            
            text=f"Puzzles: {STATE['room_puzzles_solved']}  |  Total: {STATE['total_puzzles_solved']}")

    def raise_all(self):
        for item in (self._counter, self._guide, self._msg):
            self.canvas.tag_raise(item)