# login_screen.py
# ---------------------------------------------------------------
# Windows XP-style login screen.
# Left/right arrows traverse profiles.
# Click a profile → password entry appears below.
# Admin profile is always present (locked with "lorem ipsum").
# New users can create a profile from the + card.
# ---------------------------------------------------------------

import tkinter as tk
from tkinter import font as tkfont
import db

# ---------------------------------------------------------------
# COLOUR PALETTE — XP inspired
# ---------------------------------------------------------------
C = {
    "sky_top":    "#1a5fa8",   # deep XP blue
    "sky_bot":    "#3a8fd4",   # lighter blue
    "panel":      "#245eab",   # taskbar/panel blue
    "panel_dark": "#1a3f78",
    "white":      "#ffffff",
    "off_white":  "#d8e8f8",
    "text_dark":  "#0a1a3a",
    "text_light": "#e8f0ff",
    "text_dim":   "#8aaad0",
    "accent":     "#7ec8f0",
    "green":      "#3cb94a",
    "red":        "#e04040",
    "card_bg":    "#1e4f96",
    "card_hl":    "#4a90d9",
    "input_bg":   "#e8f0ff",
    "shadow":     "#0d2d5a",
}

FONT_TITLE  = ("Tahoma", 28, "bold")
FONT_NAME   = ("Tahoma", 13, "bold")
FONT_SMALL  = ("Tahoma", 10)
FONT_TINY   = ("Tahoma", 9)
FONT_INPUT  = ("Tahoma", 12)
FONT_MONO   = ("Courier New", 11)

W, H = 960, 620


class LoginScreen:
    def __init__(self, root, on_login):
        """
        on_login(profile_id, username, is_admin) called on successful login.
        """
        self.root     = root
        self.on_login = on_login
        self.profiles = []   # [(id, username, is_admin), ...]
        self.index    = 0    # current profile index shown

        self._build_ui()
        self._load_profiles()

    # ----------------------------------------------------------
    # UI CONSTRUCTION
    # ----------------------------------------------------------
    def _build_ui(self):
        self.root.configure(bg=C["sky_top"])
        self.root.geometry(f"{W}x{H}")
        self.root.resizable(False, False)
        self.root.title("Welcome")

        # Main canvas — everything drawn here
        self.cv = tk.Canvas(self.root, width=W, height=H,
                            highlightthickness=0, bg=C["sky_top"])
        self.cv.pack()

        # Gradient sky background (simulated with rectangles)
        steps = 40
        for i in range(steps):
            t   = i / steps
            r   = int(0x1a + t * (0x3a - 0x1a))
            g   = int(0x5f + t * (0x8f - 0x5f))
            b   = int(0xa8 + t * (0xd4 - 0xa8))
            col = f"#{r:02x}{g:02x}{b:02x}"
            y0  = int(i * H / steps)
            y1  = int((i + 1) * H / steps)
            self.cv.create_rectangle(0, y0, W, y1, fill=col, outline="")

        # Top bar
        self.cv.create_rectangle(0, 0, W, 52, fill=C["panel_dark"], outline="")
        self.cv.create_rectangle(0, 50, W, 54, fill=C["accent"], outline="")
        self.cv.create_text(W // 2, 26, text="Welcome to EscapeOS",
                            font=FONT_TITLE, fill=C["white"])

        # Bottom bar
        self.cv.create_rectangle(0, H - 48, W, H,
                                 fill=C["panel_dark"], outline="")
        self.cv.create_rectangle(0, H - 50, W, H - 47,
                                 fill=C["accent"], outline="")
        self.cv.create_text(W // 2, H - 24,
                            text="To begin, select your profile",
                            font=FONT_SMALL, fill=C["text_dim"])

        # Instruction text
        self.cv.create_text(W // 2, 82,
                            text="Select a user account",
                            font=("Tahoma", 14), fill=C["off_white"])

        # Left arrow button
        self.btn_left = self.cv.create_text(
            52, H // 2, text="◀", font=("Tahoma", 36, "bold"),
            fill=C["white"], tags="arrow_left")
        self.cv.tag_bind("arrow_left", "<Button-1>",
                         lambda e: self._shift(-1))
        self.cv.tag_bind("arrow_left", "<Enter>",
                         lambda e: self.cv.itemconfig(
                             self.btn_left, fill=C["accent"]))
        self.cv.tag_bind("arrow_left", "<Leave>",
                         lambda e: self.cv.itemconfig(
                             self.btn_left, fill=C["white"]))

        # Right arrow button
        self.btn_right = self.cv.create_text(
            W - 52, H // 2, text="▶", font=("Tahoma", 36, "bold"),
            fill=C["white"], tags="arrow_right")
        self.cv.tag_bind("arrow_right", "<Button-1>",
                         lambda e: self._shift(1))
        self.cv.tag_bind("arrow_right", "<Enter>",
                         lambda e: self.cv.itemconfig(
                             self.btn_right, fill=C["accent"]))
        self.cv.tag_bind("arrow_right", "<Leave>",
                         lambda e: self.cv.itemconfig(
                             self.btn_right, fill=C["white"]))

        # Keyboard navigation
        self.root.bind("<Left>",  lambda e: self._shift(-1))
        self.root.bind("<Right>", lambda e: self._shift(1))
        self.root.bind("<Return>", lambda e: self._try_login())

        # Profile card frame (centre of screen)
        # All card content is drawn into this sub-canvas
        card_w, card_h = 320, 360
        cx = (W - card_w) // 2
        cy = 110
        self.card_cv = tk.Canvas(self.cv, width=card_w, height=card_h,
                                  bg=C["card_bg"], highlightthickness=2,
                                  highlightbackground=C["accent"])
        self.card_win = self.cv.create_window(
            W // 2, cy + card_h // 2,
            window=self.card_cv, width=card_w, height=card_h)

        self._build_card()

        # Error / status message
       # Error / status message
        self.msg_var = tk.StringVar(value="")

        self.msg_id = self.cv.create_text(
            W // 2,
            cy + card_h + 30,
            text="",
            font=FONT_SMALL,
            fill=C["red"],
            tags="msg_text"
        )

    def _build_card(self):
        """Build the interior of the profile card."""
        self.card_cv.delete("all")
        cw, ch = 320, 360

        # Avatar circle background
        self.card_cv.create_oval(95, 30, 225, 160,
                                  fill=C["panel_dark"],
                                  outline=C["accent"], width=3)

        # Avatar letter / placeholder — updated by _refresh_card
        self.avatar_text = self.card_cv.create_text(
            160, 95, text="?", font=("Tahoma", 52, "bold"),
            fill=C["white"])

        # Admin lock icon placeholder
        self.lock_icon = self.card_cv.create_text(
            205, 145, text="", font=("Tahoma", 18),
            fill=C["accent"])

        # Profile name
        self.name_text = self.card_cv.create_text(
            160, 178, text="",
            font=FONT_NAME, fill=C["white"])

        # Divider
        self.card_cv.create_line(40, 200, 280, 200,
                                  fill=C["panel_dark"], width=1)

        # Password label
        self.pw_label = self.card_cv.create_text(
            160, 220, text="Password",
            font=FONT_TINY, fill=C["text_dim"])

        # Password entry widget (inside card canvas)
        self.pw_var = tk.StringVar()
        self.pw_entry = tk.Entry(self.card_cv,
                                  textvariable=self.pw_var,
                                  font=FONT_INPUT,
                                  show="●",
                                  bg=C["input_bg"],
                                  fg=C["text_dark"],
                                  insertbackground=C["text_dark"],
                                  relief="flat",
                                  bd=0,
                                  width=18)
        self.card_cv.create_window(160, 245, window=self.pw_entry,
                                    height=32)
        self.pw_entry.bind("<Return>", lambda e: self._try_login())

        # Login button
        self.login_btn = tk.Button(self.card_cv,
                                    text="Log In  →",
                                    font=("Tahoma", 11, "bold"),
                                    bg=C["green"], fg=C["white"],
                                    activebackground="#2da03a",
                                    activeforeground=C["white"],
                                    relief="flat", bd=0,
                                    cursor="hand2",
                                    command=self._try_login)
        self.card_cv.create_window(160, 295, window=self.login_btn,
                                    width=160, height=34)

        # "New profile" button — shown on the + card
        self.new_btn = tk.Button(self.card_cv,
                                  text="Create Profile",
                                  font=("Tahoma", 11, "bold"),
                                  bg=C["card_hl"], fg=C["white"],
                                  activebackground=C["accent"],
                                  activeforeground=C["white"],
                                  relief="flat", bd=0,
                                  cursor="hand2",
                                  command=self._show_create_dialog)
        self.card_cv.create_window(160, 295, window=self.new_btn,
                                    width=160, height=34)

        # Profile dots (navigation indicator)
        self.dots_frame = tk.Frame(self.card_cv, bg=C["card_bg"])
        self.card_cv.create_window(160, 340, window=self.dots_frame)

    # ----------------------------------------------------------
    # DATA
    # ----------------------------------------------------------
    def _load_profiles(self):
        """Fetch profiles from DB and add the + (new profile) card at end."""
        rows = db.get_all_profiles()
        # Each entry: (id, username, is_admin)
        # Append a sentinel for the "new profile" card
        self.profiles = list(rows) + [(-1, "+", 0)]
        self.index    = 0
        self._refresh_card()

    def _shift(self, direction):
        if not self.profiles:
            return
        self.index = (self.index + direction) % len(self.profiles)
        self.pw_var.set("")
        self.cv.itemconfig(self.msg_id, text="")
        self._refresh_card()

    # ----------------------------------------------------------
    # CARD RENDERING
    # ----------------------------------------------------------
    def _refresh_card(self):
        if not self.profiles:
            return
        pid, uname, is_admin = self.profiles[self.index]
        is_new = (pid == -1)

        # Avatar letter
        letter  = "+" if is_new else uname[0].upper()
        av_col  = C["accent"] if is_admin else (
                  C["text_dim"] if is_new else C["white"])
        self.card_cv.itemconfig(self.avatar_text,
                                 text=letter, fill=av_col)

        # Lock icon
        self.card_cv.itemconfig(
            self.lock_icon,
            text="🔒" if is_admin else "")

        # Name
        display = "ADMIN" if is_admin else ("New Profile" if is_new else uname)
        self.card_cv.itemconfig(self.name_text, text=display)

        # Show/hide password entry vs create button
        if is_new:
            self.pw_entry.place_forget()
            self.pw_label_visible = False
            self.card_cv.itemconfig(self.pw_label, text="")
            self.login_btn.place_forget()
            self.new_btn.lift()
            self.card_cv.itemconfig(
                self.card_cv.find_withtag("all")[0],   # background
                fill=C["card_bg"])
        else:
            self.card_cv.itemconfig(self.pw_label, text="Password")
            self.pw_entry.lift()
            self.login_btn.lift()
            self.pw_entry.focus()

        # Navigation dots
        for widget in self.dots_frame.winfo_children():
            widget.destroy()
        for i, _ in enumerate(self.profiles):
            col = C["white"] if i == self.index else C["panel_dark"]
            tk.Label(self.dots_frame, text="●",
                     font=("Tahoma", 8),
                     fg=col, bg=C["card_bg"]).pack(side=tk.LEFT, padx=2)

    # ----------------------------------------------------------
    # LOGIN
    # ----------------------------------------------------------
    def _try_login(self):
        if not self.profiles:
            return
        pid, uname, is_admin = self.profiles[self.index]
        if pid == -1:
            return   # new profile card — login button hidden

        password = self.pw_var.get()
        if not password:
            self._show_msg("Please enter a password.", C["red"])
            return

        ok, profile_id, admin_flag = db.verify_login(uname, password)
        if ok:
            self._show_msg("Welcome back!", C["green"])
            self.root.after(600, lambda: self.on_login(
                profile_id, uname, bool(admin_flag)))
        else:
            self._show_msg("Incorrect password. Try again.", C["red"])
            self.pw_var.set("")
            self.pw_entry.focus()

    def _show_msg(self, text, colour=None):
        self.cv.itemconfig(self.msg_id, text=text)

        if colour:
            self.cv.itemconfig(self.msg_id, fill=colour)

    # ----------------------------------------------------------
    # CREATE PROFILE DIALOG
    # ----------------------------------------------------------
    def _show_create_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Create Profile")
        dlg.geometry("340x240")
        dlg.resizable(False, False)
        dlg.configure(bg=C["panel_dark"])
        dlg.grab_set()
        dlg.transient(self.root)

        tk.Label(dlg, text="Create New Profile",
                 font=("Tahoma", 14, "bold"),
                 bg=C["panel_dark"], fg=C["white"]).pack(pady=(20, 4))

        tk.Label(dlg, text="Username",
                 font=FONT_TINY, bg=C["panel_dark"],
                 fg=C["text_dim"]).pack()
        uname_var = tk.StringVar()
        uname_entry = tk.Entry(dlg, textvariable=uname_var,
                                font=FONT_INPUT,
                                bg=C["input_bg"], fg=C["text_dark"],
                                relief="flat", width=22)
        uname_entry.pack(pady=(2, 10))
        uname_entry.focus()

        tk.Label(dlg, text="Password",
                 font=FONT_TINY, bg=C["panel_dark"],
                 fg=C["text_dim"]).pack()
        pw_var   = tk.StringVar()
        pw_entry = tk.Entry(dlg, textvariable=pw_var,
                             font=FONT_INPUT, show="●",
                             bg=C["input_bg"], fg=C["text_dark"],
                             relief="flat", width=22)
        pw_entry.pack(pady=(2, 12))

        err_lbl = tk.Label(dlg, text="",
                            font=FONT_TINY, bg=C["panel_dark"],
                            fg=C["red"])
        err_lbl.pack()

        def _submit():
            uname = uname_var.get().strip()
            pw    = pw_var.get().strip()
            if not uname:
                err_lbl.config(text="Username cannot be empty.")
                return
            if len(uname) > 20:
                err_lbl.config(text="Username max 20 characters.")
                return
            if not pw:
                err_lbl.config(text="Password cannot be empty.")
                return
            ok, result = db.create_profile(uname, pw)
            if ok:
                dlg.destroy()
                self._load_profiles()
                # Jump to newly created profile
                for i, (pid, un, _) in enumerate(self.profiles):
                    if un == uname:
                        self.index = i
                        break
                self._refresh_card()
                self._show_msg(f"Profile '{uname}' created!", C["green"])
            else:
                err_lbl.config(text=result)

        pw_entry.bind("<Return>", lambda e: _submit())
        tk.Button(dlg, text="Create Profile",
                  font=("Tahoma", 11, "bold"),
                  bg=C["green"], fg=C["white"],
                  activebackground="#2da03a",
                  relief="flat", bd=0, cursor="hand2",
                  command=_submit).pack(pady=(4, 0),
                                        ipadx=12, ipady=6)


# ---------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------
if __name__ == "__main__":
    db.init_db()
    root = tk.Tk()

    def on_login(profile_id, username, is_admin):
        print(f"Logged in: {username}  admin={is_admin}  id={profile_id}")
        root.destroy()

    LoginScreen(root, on_login)
    root.mainloop()