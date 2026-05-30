# main.py
import tkinter as tk
import db
from login_screen import LoginScreen
from desktop import Desktop

# ── Constants ─────────────────────────────────────────────────
GAME_W, GAME_H = 800, 600
LOGIN_W, LOGIN_H = 960, 620
TILE = 40

APP_RUNNING = True


def launch_game(root, profile_id):
    """
    Called from Desktop when the user double-clicks The Game icon.
    Tears down the desktop and starts the game engine.
    Receives root so it doesn't need to import main at all.
    """
    from assets import load_all
    from engine import Engine
    from hud import HUD
    from room_manager import RoomManager

    # Clear all desktop widgets
    for widget in root.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass

    root.geometry(f"{GAME_W}x{GAME_H}")
    root.title("Lab Escape")

    canvas = tk.Canvas(root, width=GAME_W, height=GAME_H, bg="black")
    canvas.pack()

    load_all(TILE)

    hud    = HUD(canvas, GAME_W, GAME_H)
    engine = Engine(root, canvas, hud, None)
    rm     = RoomManager(canvas, engine, hud, GAME_W, GAME_H)
    engine.rm = rm

    rm.load("room_1", spawn_tx=2, spawn_ty=7)
    engine.update()


# ── Only runs when you do: python main.py ─────────────────────
# NOT when desktop.py does: import main
if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(False, False)

    # Initialise database
    try:
        db.init_db()
    except Exception as e:
        import tkinter.messagebox as mb
        mb.showerror("Database Error",
                     f"Could not connect to MySQL.\n\n{e}\n\n"
                     "Make sure MySQL is running and your password\n"
                     "in db.py is correct.")
        root.destroy()
        raise SystemExit

    def clear_root():
        for widget in root.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass

    def show_login():
        clear_root()
        root.geometry(f"{LOGIN_W}x{LOGIN_H}")
        LoginScreen(root, on_login=show_desktop)

    def show_desktop(profile_id, username, is_admin):
        clear_root()
        root.geometry(f"{LOGIN_W}x{LOGIN_H}")
        # Pass launch_game as a lambda so Desktop never needs to import main
        Desktop(root, profile_id, username, is_admin,
                on_logout=show_login,
                on_launch_game=lambda pid: launch_game(root, pid))

    show_login()
    root.mainloop()
# main.py
import tkinter as tk
import db
from login_screen import LoginScreen
from desktop import Desktop

# ── Constants ─────────────────────────────────────────────────
GAME_W, GAME_H = 800, 600
LOGIN_W, LOGIN_H = 960, 620
TILE = 40


def launch_game(root, profile_id):
    """
    Called from Desktop when the user double-clicks The Game icon.
    Tears down the desktop and starts the game engine.
    Receives root so it doesn't need to import main at all.
    """
    from assets import load_all
    from engine import Engine
    from hud import HUD
    from room_manager import RoomManager

    # Clear all desktop widgets
    for widget in root.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass

    root.geometry(f"{GAME_W}x{GAME_H}")
    root.title("Lab Escape")

    canvas = tk.Canvas(root, width=GAME_W, height=GAME_H, bg="black")
    canvas.pack()

    load_all(TILE)

    hud    = HUD(canvas, GAME_W, GAME_H)
    engine = Engine(root, canvas, hud, None)
    rm     = RoomManager(canvas, engine, hud, GAME_W, GAME_H)
    engine.rm = rm

    rm.load("room_1", spawn_tx=2, spawn_ty=7)
    engine.update()


# ── Only runs when you do: python main.py ─────────────────────
# NOT when desktop.py does: import main
if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(False, False)

    # Initialise database
    try:
        db.init_db()
    except Exception as e:
        import tkinter.messagebox as mb
        mb.showerror("Database Error",
                     f"Could not connect to MySQL.\n\n{e}\n\n"
                     "Make sure MySQL is running and your password\n"
                     "in db.py is correct.")
        root.destroy()
        raise SystemExit

    def clear_root():
        for widget in root.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass

    def show_login():
        clear_root()
        root.geometry(f"{LOGIN_W}x{LOGIN_H}")
        LoginScreen(root, on_login=show_desktop)

    def show_desktop(profile_id, username, is_admin):
        clear_root()
        root.geometry(f"{LOGIN_W}x{LOGIN_H}")
        # Pass launch_game as a lambda so Desktop never needs to import main
        Desktop(root, profile_id, username, is_admin,
                on_logout=show_login,
                on_launch_game=lambda pid: launch_game(root, pid))

    show_login()
    root.mainloop()