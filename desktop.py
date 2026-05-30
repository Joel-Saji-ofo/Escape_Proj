# desktop.py
# ---------------------------------------------------------------
# RetroOS Desktop screen shown after login.
# - XP-style wallpaper (drawn procedurally as placeholder)
# - Taskbar at bottom with clock and start button
# - Desktop icons: File Explorer, The Game, (more later)
# - Progress widget (shows real progress_pct from DB)
# - Double-click icons to open windows
# - File Explorer opens a blank explorer window
# - Game icon launches the game via main.launch_game()
# ---------------------------------------------------------------

import tkinter as tk
from tkinter import font as tkfont
import datetime
import db

# ── Colours ───────────────────────────────────────────────────
C = {
    "wallpaper_top":  "#2b6cb0",
    "wallpaper_bot":  "#1a4080",
    "taskbar":        "#0f2a5e",
    "taskbar_light":  "#1a3f8a",
    "start_green":    "#3a7a3a",
    "start_green_dk": "#285228",
    "white":          "#ffffff",
    "off_white":      "#d6eaf8",
    "text_dim":       "#7fb3d3",
    "text_dark":      "#0d1f3c",
    "accent":         "#5dade2",
    "gold":           "#f0b429",
    "red":            "#e04040",      # FIX: was missing, caused crash on ✕ hover
    "win_title":      "#0a3080",
    "win_bg":         "#f0f4f8",
    "win_border":     "#1a3f8a",
    "progress_bg":    "#1c3f7a",
    "progress_bar":   "#3cb94a",
    "panel_dark":     "#0d2040",
    "shadow":         "#0a1830",
    "hill_light":     "#3a8a3a",
    "hill_dark":      "#2a6a2a",
    "cloud":          "#ddeeff",
    # NOTE: removed "icon_bg": "rgba(...)" — tkinter doesn't support rgba
}

FONT = {
    "taskbar":   ("Tahoma", 10, "bold"),
    "clock":     ("Tahoma", 10),
    "icon":      ("Tahoma", 9),
    "icon_sel":  ("Tahoma", 9, "bold"),
    "win_title": ("Tahoma", 11, "bold"),
    "win_body":  ("Tahoma", 10),
    "progress":  ("Tahoma", 9, "bold"),
    "user":      ("Tahoma", 11, "bold"),
    "start":     ("Tahoma", 11, "bold"),
    "tooltip":   ("Tahoma", 8),
}

W, H        = 960, 620
TASKBAR_H   = 40
DESKTOP_H   = H - TASKBAR_H
ICON_SIZE   = 48


class Desktop:
    def __init__(self, root, profile_id, username, is_admin, on_logout, on_launch_game):
        """
        profile_id  — DB id
        username    — display name
        is_admin    — bool
        on_logout   — called when user logs out (returns to login screen)
        """
        self.root       = root
        self.profile_id = profile_id
        self.username   = username
        self.is_admin   = is_admin
        self.on_logout  = on_logout
        self.on_launch_game = on_launch_game
        self.windows    = []     # track open sub-windows for cleanup

        self.root.title(f"RetroOS — {username}")
        self.root.geometry(f"{W}x{H}")
        self.root.resizable(False, False)
        self.root.configure(bg=C["taskbar"])

        # Load game state for progress display
        gs = db.get_game_state(profile_id)
        self.progress = gs["progress_pct"] if gs else 0

        self._build_wallpaper()
        self._build_icons()
        self._build_progress_widget()
        self._build_taskbar()
        self._tick_clock()

    # ── Wallpaper ─────────────────────────────────────────────
    def _build_wallpaper(self):
        """Draw an XP-style rolling hills wallpaper procedurally."""
        self.cv = tk.Canvas(self.root, width=W, height=DESKTOP_H,
                             highlightthickness=0)
        self.cv.place(x=0, y=0)

        # Sky gradient
        sky_steps = 60
        for i in range(sky_steps):
            t  = i / sky_steps
            r  = int(0x2b + t * (0x87 - 0x2b))
            g  = int(0x6c + t * (0xce - 0x6c))
            b  = int(0xb0 + t * (0xff - 0xb0))
            self.cv.create_rectangle(
                0, i * DESKTOP_H // sky_steps,
                W, (i + 1) * DESKTOP_H // sky_steps,
                fill=f"#{r:02x}{g:02x}{b:02x}", outline="")

        # Clouds (simple ellipses)
        clouds = [
            (120, 80, 110, 38),
            (340, 55, 90,  30),
            (600, 90, 130, 42),
            (800, 60, 100, 34),
        ]
        for cx, cy, cw, ch in clouds:
            self.cv.create_oval(cx - cw, cy - ch, cx + cw, cy + ch,
                                 fill=C["cloud"], outline="")
            self.cv.create_oval(cx - cw // 2, cy - ch - 10,
                                 cx + cw // 2, cy + ch - 10,
                                 fill=C["cloud"], outline="")

        # Hills (dark green base)
        hill_pts_dark = [
            0, DESKTOP_H,
            0, DESKTOP_H - 140,
            80, DESKTOP_H - 180,
            200, DESKTOP_H - 220,
            320, DESKTOP_H - 200,
            400, DESKTOP_H - 160,
            W, DESKTOP_H - 100,
            W, DESKTOP_H,
        ]
        self.cv.create_polygon(hill_pts_dark, fill=C["hill_dark"], outline="")

        # Hills (light green on top)
        hill_pts = [
            0, DESKTOP_H,
            0, DESKTOP_H - 100,
            100, DESKTOP_H - 150,
            250, DESKTOP_H - 190,
            W // 2, DESKTOP_H - 170,
            W - 200, DESKTOP_H - 130,
            W - 50,  DESKTOP_H - 80,
            W, DESKTOP_H - 70,
            W, DESKTOP_H,
        ]
        self.cv.create_polygon(hill_pts, fill=C["hill_light"], outline="")

        # Sun
        self.cv.create_oval(W - 130, 30, W - 50, 110,
                             fill="#fff8c0", outline="#ffe070", width=2)

    # ── Icons ─────────────────────────────────────────────────
    def _build_icons(self):
        """Place desktop icons. Double-click triggers action."""
        icons = [
            {
                "label":  "File Explorer",
                "emoji":  "📁",
                "x":      60,
                "y":      60,
                "action": self._open_file_explorer,
            },
            {
                "label":  "The Game",
                "emoji":  "🎮",
                "x":      60,
                "y":      160,
                "action": self._launch_game,
            },
        ]

        self._icon_items = {}   # tag → action

        for ic in icons:
            tag = ic["label"].replace(" ", "_")
            self._draw_icon(ic["x"], ic["y"],
                             ic["emoji"], ic["label"],
                             tag, ic["action"])

    def _draw_icon(self, x, y, emoji, label, tag, action):
        """Draw one desktop icon with emoji + label, bind double-click."""
        # Shadow box
        self.cv.create_rectangle(
            x - ICON_SIZE // 2 + 3, y - ICON_SIZE // 2 + 3,
            x + ICON_SIZE // 2 + 3, y + ICON_SIZE // 2 + 3,
            fill=C["shadow"], outline="",
            tags=(tag, "icon_shadow"))

        # Icon box (highlight on hover)
        self.cv.create_rectangle(
            x - ICON_SIZE // 2, y - ICON_SIZE // 2,
            x + ICON_SIZE // 2, y + ICON_SIZE // 2,
            fill="", outline="",
            tags=(tag, "icon_box"))

        # Emoji text
        self.cv.create_text(x, y, text=emoji,
                             font=("Segoe UI Emoji", 28),
                             tags=(tag, "icon_emoji"))

        # Label below icon
        self.cv.create_text(x, y + ICON_SIZE // 2 + 12,
                             text=label,
                             font=FONT["icon"],
                             fill=C["white"],
                             tags=(tag, "icon_label"))

        # Hover highlight
        def _enter(e, t=tag):
            self.cv.itemconfig(t, fill=C["off_white"])
            # only colour the box itself
            for item in self.cv.find_withtag(t):
                if "icon_box" in self.cv.gettags(item):
                    self.cv.itemconfig(item,
                                       fill="#4a90d9",
                                       outline=C["accent"])

        def _leave(e, t=tag):
            self.cv.itemconfig(t, fill=C["white"])
            for item in self.cv.find_withtag(t):
                if "icon_box" in self.cv.gettags(item):
                    self.cv.itemconfig(item, fill="", outline="")
            # restore label colour explicitly
            for item in self.cv.find_withtag(t):
                if "icon_label" in self.cv.gettags(item):
                    self.cv.itemconfig(item, fill=C["white"])

        self.cv.tag_bind(tag, "<Enter>", _enter)
        self.cv.tag_bind(tag, "<Leave>", _leave)
        self.cv.tag_bind(tag, "<Double-Button-1>",
                          lambda e, a=action: a())

        self._icon_items[tag] = action

    # ── Progress widget ───────────────────────────────────────
    def _build_progress_widget(self):
        """Small progress card in bottom-right of desktop."""
        pw, ph = 200, 90
        px     = W - pw - 20
        py     = DESKTOP_H - ph - 20

        # Card background
        self.cv.create_rectangle(px, py, px + pw, py + ph,
                                  fill=C["progress_bg"],
                                  outline=C["accent"], width=1)

        # Title
        self.cv.create_text(px + pw // 2, py + 16,
                             text="Game Progress",
                             font=FONT["progress"],
                             fill=C["off_white"])

        # Percentage
        pct = self.progress
        self.cv.create_text(px + pw // 2, py + 36,
                             text=f"{pct}%",
                             font=("Tahoma", 20, "bold"),
                             fill=C["gold"])

        # Progress bar background
        bar_x = px + 14
        bar_y = py + 56
        bar_w = pw - 28
        bar_h = 14
        self.cv.create_rectangle(bar_x, bar_y,
                                  bar_x + bar_w, bar_y + bar_h,
                                  fill=C["panel_dark"],
                                  outline=C["accent"], width=1)

        # Progress bar fill
        fill_w = int(bar_w * pct / 100)
        if fill_w > 0:
            self.cv.create_rectangle(bar_x, bar_y,
                                      bar_x + fill_w, bar_y + bar_h,
                                      fill=C["progress_bar"],
                                      outline="")

        # Sub-label
        self.cv.create_text(px + pw // 2, py + 78,
                             text="Keep going!",
                             font=FONT["tooltip"],
                             fill=C["text_dim"])

    # ── Taskbar ───────────────────────────────────────────────
    def _build_taskbar(self):
        tb_y = DESKTOP_H

        # Taskbar canvas
        self.tb = tk.Canvas(self.root, width=W, height=TASKBAR_H,
                             bg=C["taskbar"], highlightthickness=0)
        self.tb.place(x=0, y=tb_y)

        # Top highlight line
        self.tb.create_line(0, 0, W, 0, fill=C["taskbar_light"], width=2)

        # Start button
        self.start_btn = tk.Button(self.root,
                                    text="⊞  Start",
                                    font=FONT["start"],
                                    bg=C["start_green"],
                                    fg=C["white"],
                                    activebackground=C["start_green_dk"],
                                    activeforeground=C["white"],
                                    relief="raised", bd=2,
                                    cursor="hand2",
                                    command=self._show_start_menu)
        self.start_btn.place(x=4, y=tb_y + 4, width=100, height=32)

        # Separator
        self.tb.create_line(112, 6, 112, TASKBAR_H - 6,
                             fill=C["taskbar_light"], width=1)

        # Logged-in username
        self.tb.create_text(130, TASKBAR_H // 2,
                             text=f"👤  {self.username}",
                             font=FONT["user"],
                             fill=C["off_white"],
                             anchor="w")

        # Clock label (right side)
        self.clock_lbl = tk.Label(self.root,
                                   text="",
                                   font=FONT["clock"],
                                   fg=C["off_white"],
                                   bg=C["taskbar"])
        self.clock_lbl.place(x=W - 90, y=tb_y + 11)

        # System tray separator
        self.tb.create_line(W - 100, 6, W - 100, TASKBAR_H - 6,
                             fill=C["taskbar_light"], width=1)

    def _tick_clock(self):
        now = datetime.datetime.now().strftime("%I:%M %p")
        try:
            self.clock_lbl.config(text=now)
        except Exception:
            return   # widget destroyed (e.g. after logout), stop ticking
        self.root.after(10000, self._tick_clock)

    # ── Start menu ────────────────────────────────────────────
    def _show_start_menu(self):
        """Simple popup start menu."""
        menu = tk.Menu(self.root, tearoff=0,
                        bg=C["taskbar_light"],
                        fg=C["white"],
                        activebackground=C["accent"],
                        activeforeground=C["text_dark"],
                        font=FONT["win_body"],
                        relief="flat")
        menu.add_command(label=f"  👤  {self.username}",
                          state="disabled")
        menu.add_separator()
        menu.add_command(label="  📁  File Explorer",
                          command=self._open_file_explorer)
        menu.add_command(label="  🎮  The Game",
                          command=self._launch_game)
        menu.add_separator()
        menu.add_command(label="  🔒  Log Out",
                          command=self._logout)
        try:
            menu.tk_popup(4, DESKTOP_H - 4)
        finally:
            menu.grab_release()

    # ── File Explorer window ──────────────────────────────────
    def _open_file_explorer(self):
        """Opens a placeholder file explorer window."""
        win = tk.Toplevel(self.root)
        win.title("File Explorer")
        win.geometry("580x380")
        win.resizable(True, True)
        win.configure(bg=C["win_bg"])
        self.windows.append(win)
        win.protocol("WM_DELETE_WINDOW",
                      lambda: (self.windows.remove(win), win.destroy()))

        # Title bar strip
        title_bar = tk.Frame(win, bg=C["win_title"], height=30)
        title_bar.pack(fill=tk.X)
        tk.Label(title_bar, text="📁  File Explorer",
                  font=FONT["win_title"],
                  fg=C["white"], bg=C["win_title"]).pack(
                      side=tk.LEFT, padx=8, pady=4)
        tk.Button(title_bar, text="✕",
                   font=FONT["win_body"],
                   fg=C["white"], bg=C["win_title"],
                   activebackground=C["red"],   # FIX: "red" now exists in C
                   activeforeground=C["white"],
                   relief="flat", bd=0, cursor="hand2",
                   command=win.destroy).pack(
                       side=tk.RIGHT, padx=4, pady=4)

        # Address bar
        addr = tk.Frame(win, bg=C["win_bg"], pady=4)
        addr.pack(fill=tk.X, padx=6)
        tk.Label(addr, text="Address: ", font=FONT["win_body"],
                  bg=C["win_bg"]).pack(side=tk.LEFT)
        tk.Entry(addr, font=FONT["win_body"],
                  relief="sunken", bd=1,
                  width=40).pack(side=tk.LEFT, padx=4)

        # Divider
        tk.Frame(win, bg=C["win_border"], height=1).pack(fill=tk.X)

        # Body
        body = tk.Frame(win, bg=C["win_bg"])
        body.pack(fill=tk.BOTH, expand=True)

        # Left panel (folder tree placeholder)
        left = tk.Frame(body, bg="#e8eef4", width=160)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)
        tk.Label(left, text="Folders",
                  font=FONT["win_body"],
                  bg="#e8eef4", anchor="w").pack(
                      fill=tk.X, padx=8, pady=6)
        for folder in ["Desktop", "My Documents", "System"]:
            tk.Label(left, text=f"  📂  {folder}",
                      font=FONT["win_body"],
                      bg="#e8eef4", anchor="w",
                      cursor="hand2").pack(
                          fill=tk.X, padx=4, pady=2)

        # Right panel (content area)
        right = tk.Frame(body, bg=C["win_bg"])
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(right,
                  text="This folder is empty.",
                  font=FONT["win_body"],
                  fg=C["text_dim"],
                  bg=C["win_bg"]).place(relx=0.5, rely=0.5, anchor="center")

        # Status bar
        tk.Label(win, text="0 items",
                  font=FONT["tooltip"],
                  fg=C["text_dim"],
                  bg="#dde4ec",
                  anchor="w",
                  relief="sunken").pack(
                      fill=tk.X, side=tk.BOTTOM, ipady=2, padx=2)

    # ── Launch game ───────────────────────────────────────────
    def _launch_game(self):
        for w in list(self.windows):
            try:
                w.destroy()
            except Exception:
                pass
        self.windows.clear()
        self.on_launch_game(self.profile_id)


    # ── Logout ────────────────────────────────────────────────
    def _logout(self):
        """Close sub-windows, cancel the clock, return to login screen."""
        for w in list(self.windows):
            try:
                w.destroy()
            except Exception:
                pass
        self.windows.clear()
        self.on_logout()