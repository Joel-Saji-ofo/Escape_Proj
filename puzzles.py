# puzzles.py
# ---------------------------------------------------------------
# PUZZLE DUMP — every puzzle type lives here as a function.
# Each function returns an on_interact callable.
#
# HOW TO USE IN A ROOM FILE:
#   from puzzles import password_puzzle, symbol_puzzle
#   { "img": "computer", "tx": 6, "ty": 3,
#     "on_interact": password_puzzle("1234", "Terminal A") }
#
# HOW TO ADD A NEW PUZZLE TYPE:
#   1. Write a new function below following the same pattern.
#   2. It must return a function with signature:
#        def _interact(obj, root, hud): ...
#   3. Import and use it in any room file.
#   Nothing else in the codebase needs to change.
# ---------------------------------------------------------------

import tkinter as tk
import random
from game_state import STATE


# ==============================================================
# INTERNAL HELPER
# Call this inside any puzzle when the player solves it.
# Handles all counter updates automatically.
# ==============================================================
def _on_solve(obj, hud, label, room_manager=None):
    obj["solved"]        = True
    obj["interactable"]  = False
    STATE["room_puzzles_solved"]  += 1
    STATE["total_puzzles_solved"] += 1
    hud.flash(f"{label} solved!  ({STATE['room_puzzles_solved']} this room)")

    # Tell room_manager to check if a key should be awarded
    # room_manager reference is injected by engine — see engine.py
    if room_manager and hasattr(room_manager, "check_key_reward"):
        room_manager.check_key_reward(hud)


# ==============================================================
# PUZZLE TYPE 1 — PASSWORD / TERMINAL
# The classic: type a code into a popup window.
#
# Usage:
#   password_puzzle("1234", "Terminal A")
#   password_puzzle("secret99", "Lab Console")
# ==============================================================
def password_puzzle(code, label="Terminal"):
    def _interact(obj, root, hud, room_manager=None):
        if obj["solved"]:
            hud.flash(f"{label} already solved!")
            return

        win = tk.Toplevel(root)
        win.title(label)
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win,
                 text=f"{label}",
                 font=("Courier", 14, "bold")).pack(pady=(16, 2))
        tk.Label(win,
                 text="Enter access code:",
                 font=("Courier", 11)).pack(pady=(0, 8))

        entry = tk.Entry(win, font=("Courier", 14), show="*", width=16)
        entry.pack(padx=24)
        entry.focus()

        result_lbl = tk.Label(win, text="", font=("Courier", 12))
        result_lbl.pack(pady=8)

        def _submit():
            if obj["solved"]:
                win.destroy()
                return
            if entry.get() == code:
                result_lbl.config(text="✓  ACCESS GRANTED", fg="green")
                _on_solve(obj, hud, label, room_manager)
                win.after(900, win.destroy)
            else:
                result_lbl.config(text="✗  ACCESS DENIED", fg="red")
                entry.delete(0, tk.END)

        entry.bind("<Return>", lambda _e: _submit())
        tk.Button(win, text="Submit", command=_submit,
                  font=("Courier", 11), width=10).pack(pady=(0, 16))

    return _interact


# ==============================================================
# PUZZLE TYPE 2 — SYMBOL MATCH
# Player picks symbols in the correct order from a grid.
# Placeholder UI — replace the symbols list with your own.
#
# Usage:
#   symbol_puzzle(["moon", "star", "sun"], "Altar Panel")
#   symbol_puzzle(["A", "C", "B", "D"],   "Keypad")
# ==============================================================
def symbol_puzzle(solution, label="Symbol Lock"):
    """
    solution — list of strings defining the correct order.
               Can be any strings; they show as buttons.
    """
    def _interact(obj, root, hud, room_manager=None):
        if obj["solved"]:
            hud.flash(f"{label} already solved!")
            return

        win = tk.Toplevel(root)
        win.title(label)
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text=label,
                 font=("Courier", 14, "bold")).pack(pady=(14, 4))
        tk.Label(win, text="Select symbols in correct order:",
                 font=("Courier", 11)).pack()

        selected = []
        selected_lbl = tk.Label(win, text="Selected: —",
                                font=("Courier", 11))
        selected_lbl.pack(pady=6)

        result_lbl = tk.Label(win, text="", font=("Courier", 12))
        result_lbl.pack()

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=8, padx=16)

        # Shuffled display so buttons aren't in solution order
        import random
        display = solution[:]
        random.shuffle(display)

        def _pick(sym):
            selected.append(sym)
            selected_lbl.config(
                text="Selected: " + "  ".join(selected))
            if len(selected) == len(solution):
                if selected == solution:
                    result_lbl.config(
                        text="✓  CORRECT", fg="green")
                    _on_solve(obj, hud, label, room_manager)
                    win.after(900, win.destroy)
                else:
                    result_lbl.config(
                        text="✗  WRONG ORDER — try again", fg="red")
                    selected.clear()
                    selected_lbl.config(text="Selected: —")

        for sym in display:
            tk.Button(btn_frame, text=sym, width=8,
                      font=("Courier", 12),
                      command=lambda s=sym: _pick(s)).pack(
                side=tk.LEFT, padx=4)

        tk.Button(win, text="Reset", font=("Courier", 10),
                  command=lambda: (
                      selected.clear(),
                      selected_lbl.config(text="Selected: —"),
                      result_lbl.config(text="")
                  )).pack(pady=(0, 12))

    return _interact


# ==============================================================
# PUZZLE TYPE 3 — NUMBER SEQUENCE
# Player enters a sequence of numbers in order by clicking.
# Good for combination locks, PIN pads, etc.
#
# Usage:
#   sequence_puzzle([3, 1, 4, 1], "PIN Pad")
#   sequence_puzzle([7, 2, 9],    "Safe Dial")
# ==============================================================
def sequence_puzzle(sequence, label="Keypad"):
    def _interact(obj, root, hud, room_manager=None):
        if obj["solved"]:
            hud.flash(f"{label} already solved!")
            return

        win = tk.Toplevel(root)
        win.title(label)
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text=label,
                 font=("Courier", 14, "bold")).pack(pady=(14, 4))
        tk.Label(win, text="Enter the correct sequence:",
                 font=("Courier", 11)).pack()

        display_var = tk.StringVar(value="")
        tk.Label(win, textvariable=display_var,
                 font=("Courier", 18), width=14,
                 relief="sunken").pack(pady=8, padx=20)

        result_lbl = tk.Label(win, text="", font=("Courier", 12))
        result_lbl.pack()

        entered = []

        def _press(n):
            entered.append(n)
            display_var.set("  ".join(str(x) for x in entered))
            # Check after enough digits entered
            if len(entered) == len(sequence):
                if entered == sequence:
                    result_lbl.config(text="✓  CORRECT", fg="green")
                    _on_solve(obj, hud, label, room_manager)
                    win.after(900, win.destroy)
                else:
                    result_lbl.config(text="✗  WRONG — cleared", fg="red")
                    entered.clear()
                    win.after(600, lambda: (
                        display_var.set(""),
                        result_lbl.config(text="")))

        def _clear():
            entered.clear()
            display_var.set("")
            result_lbl.config(text="")

        # Numpad buttons 0-9
        pad = tk.Frame(win)
        pad.pack(pady=6, padx=16)
        nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]
        for i, n in enumerate(nums):
            tk.Button(pad, text=str(n), width=4, height=2,
                      font=("Courier", 12),
                      command=lambda x=n: _press(x)).grid(
                row=i // 3, column=i % 3, padx=2, pady=2)

        tk.Button(win, text="Clear", font=("Courier", 10),
                  command=_clear).pack(pady=(4, 12))

    return _interact


# ==============================================================
# PUZZLE TYPE 4 — READ-ONLY NOTE / CLUE
# Not really a puzzle — just displays text when interacted with.
# Use for lore, clues that hint at other puzzle codes, etc.
#
# Usage:
#   note_clue("The code is the year this lab was founded.\n— Dr. K",
#             "Torn Note")
# ==============================================================
def note_clue(text, label="Note"):
    def _interact(obj, root, hud, room_manager=None):
        win = tk.Toplevel(root)
        win.title(label)
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text=label,
                 font=("Courier", 13, "bold")).pack(pady=(14, 6))
        tk.Label(win, text=text,
                 font=("Courier", 11),
                 justify=tk.LEFT,
                 wraplength=300).pack(padx=20, pady=6)
        tk.Button(win, text="Close", font=("Courier", 11),
                  command=win.destroy).pack(pady=(4, 14))
        # Notes don't count as puzzles and don't call _on_solve

    return _interact


#THIS IS MEANT FOR THE FINAL ADMIN LEVEL PASSWORD CAPTURE. A SYSTEM HACK BASICALLY

def dice_hack(target_str, target_wis, target_mag, label="Dice Forge"):
    """
    An escape room puzzle where players must roll dice to build attributes 
    to hack the device.
    
    Targets required are passed into the factory function.
    """
    def _interact(obj, root, hud, room_manager=None):
        if obj.get("solved", False):
            hud.flash(f"{label} already solved!")
            return

        # --- Window Setup ---
        win = tk.Toplevel(root)
        win.title(label)
        win.resizable(False, False)
        win.grab_set()
        win.configure(bg="#1e1e2e") # Sleek dark theme

        # --- State Variables ---
        stats = {"Breach": 0, "Decrypt": 0, "Bypass": 0}
        targets = {"Breach": target_str, "Decrypt": target_wis, "Bypass": target_mag}
        rolls_left = {"Breach": 3, "Decrypt": 3, "Bypass": 3}
        current_attr = tk.StringVar(value="Breach")
        
        # Track active animation to prevent overlapping clicks
        is_rolling = False 

        # --- Core Logic Functions ---
        def _roll_dice():
            nonlocal is_rolling
            attr = current_attr.get()
            if rolls_left[attr] <= 0 or is_rolling:
                return

            is_rolling = True
            roll_btn.config(state="disabled")
            
            # Simple, clean "rolling" animation using .after()
            def animate(count):
                if count > 0:
                    d1, d2 = random.randint(1, 6), random.randint(1, 6)
                    dice_lbl.config(text=f"⚄ [{d1}]  ⚂ [{d2}]")
                    win.after(100, lambda: animate(count - 1))
                else:
                    # Final result
                    d1, d2 = random.randint(1, 6), random.randint(1, 6)
                    total = d1 + d2
                    stats[attr] += total
                    rolls_left[attr] -= 1
                    
                    dice_lbl.config(text=f"🎲 [{d1}] + [{d2}] = {total}")
                    _update_ui()

            animate(6)

        def _update_ui():
            nonlocal is_rolling
            is_rolling = False
            
            # Update the SQL-like table labels
            for attr in ["Breach", "Decrypt", "Bypass"]:
                table_cells[attr]["current"].config(
                    text=str(stats[attr]),
                    fg="#a6e3a1" if stats[attr] >= targets[attr] else "#cdd6f4"
                )
                table_cells[attr]["left"].config(text=str(rolls_left[attr]))
            
            # Update contextual button states
            attr = current_attr.get()
            if rolls_left[attr] > 0:
                roll_btn.config(state="normal", text=f"Roll for {attr} ({rolls_left[attr]} Left)")
            else:
                roll_btn.config(state="disabled", text=f"No Rolls Left for {attr}")

        def _execute_fight():
            if is_rolling:
                return
                
            # Victory Check: Must meet or exceed all targets
            victory = all(stats[a] >= targets[a] for a in targets)
            
            if victory:
                result_lbl.config(text="✓ VICTORY — COMPUTER HACKED", fg="#a6e3a1")
                # Trigger the room's solving mechanics
                if room_manager and hasattr(room_manager, "on_solve"):
                    room_manager.on_solve(obj, hud, label)
                elif '_on_solve' in globals():
                    _on_solve(obj, hud, label, room_manager)
                else:
                    obj["solved"] = True
                    hud.flash(f"{label} solved!")
                
                win.after(1200, win.destroy)
            else:
                result_lbl.config(text="✗ DEFEAT — STATS TOO LOW! RESETTING...", fg="#f38ba8")
                # Reset state on failure
                win.after(1500, _reset_puzzle)

        def _reset_puzzle():
            nonlocal is_rolling
            is_rolling = False
            for a in stats:
                stats[a] = 0
                rolls_left[a] = 3
            result_lbl.config(text="")
            dice_lbl.config(text="🎲 [?]  [?]")
            _update_ui()

        # --- UI Layout ---
        
        # Header
        tk.Label(win, text=label, font=("Courier", 16, "bold"), bg="#1e1e2e", fg="#cdd6f4").pack(pady=(12, 2))
        tk.Label(win, text="Build your stats to hack the computer.", font=("Courier", 10), bg="#1e1e2e", fg="#bac2de").pack(pady=(0, 10))

        # Main Split Frame (Left: Controls, Right: SQL Table)
        main_frame = tk.Frame(win, bg="#1e1e2e")
        main_frame.pack(padx=15, pady=5, fill="both", expand=True)

        # LEFT SIDE: Selector & Dice Roller
        left_frame = tk.Frame(main_frame, bg="#1e1e2e")
        left_frame.pack(side="left", padx=(0, 15), anchor="n")

        tk.Label(left_frame, text="Select Target Attribute:", font=("Courier", 10, "bold"), bg="#1e1e2e", fg="#b4befe").pack(anchor="w", pady=2)
        
        # Radio buttons to change target attribute focus
        for attr in ["Breach", "Decrypt", "Bypass"]:
            tk.Radiobutton(
                left_frame, text=attr, variable=current_attr, value=attr,
                font=("Courier", 11), bg="#1e1e2e", fg="#cdd6f4",
                selectcolor="#313244", activebackground="#1e1e2e", activeforeground="#cdd6f4",
                command=_update_ui
            ).pack(anchor="w", padx=5)

        dice_lbl = tk.Label(left_frame, text="🎲 [?]  [?]", font=("Courier", 16, "bold"), bg="#313244", fg="#f5c2e7", width=14, height=2, relief="groove", bd=2)
        dice_lbl.pack(pady=12)

        roll_btn = tk.Button(left_frame, text="Roll Dice", font=("Courier", 10, "bold"), bg="#89b4fa", fg="#11111b", activebackground="#b4befe", width=22, height=2, command=_roll_dice)
        roll_btn.pack()

        # RIGHT SIDE: The SQL Database style table
        right_frame = tk.Frame(main_frame, bg="#11111b", bd=2, relief="ridge")
        right_frame.pack(side="right", anchor="n")

        # SQL Table Header
        headers = ["ATTRIBUTE_NAME", "CURRENT_VAL", "TARGET_REQ", "ROLLS_LEFT"]
        for col_idx, text in enumerate(headers):
            lbl = tk.Label(right_frame, text=text, font=("Courier", 9, "bold"), bg="#313244", fg="#f5e0dc", padx=8, pady=6, bd=1, relief="solid")
            lbl.grid(row=0, column=col_idx, sticky="nsew")

        # SQL Table Rows Populating dynamically
        table_cells = {}
        for row_idx, attr in enumerate(["Breach", "Decrypt", "Bypass"], start=1):
            table_cells[attr] = {}
            
            # Col 0: Attr Name
            lbl_name = tk.Label(right_frame, text=attr.upper(), font=("Courier", 10), bg="#181825", fg="#cdd6f4", anchor="w", padx=8, pady=6, bd=1, relief="solid")
            lbl_name.grid(row=row_idx, column=0, sticky="nsew")
            
            # Col 1: Current value
            lbl_curr = tk.Label(right_frame, text="0", font=("Courier", 10, "bold"), bg="#181825", fg="#cdd6f4", padx=8, pady=6, bd=1, relief="solid")
            lbl_curr.grid(row=row_idx, column=1, sticky="nsew")
            table_cells[attr]["current"] = lbl_curr
            
            # Col 2: Target requirements
            lbl_targ = tk.Label(right_frame, text=str(targets[attr]), font=("Courier", 10), bg="#181825", fg="#f38ba8", padx=8, pady=6, bd=1, relief="solid")
            lbl_targ.grid(row=row_idx, column=2, sticky="nsew")
            
            # Col 3: Rolls remaining
            lbl_left = tk.Label(right_frame, text="3", font=("Courier", 10), bg="#181825", fg="#bac2de", padx=8, pady=6, bd=1, relief="solid")
            lbl_left.grid(row=row_idx, column=3, sticky="nsew")
            table_cells[attr]["left"] = lbl_left

        # --- Lower Action Section ---
        action_frame = tk.Frame(win, bg="#1e1e2e")
        action_frame.pack(fill="x", padx=15, pady=(10, 15))

        result_lbl = tk.Label(action_frame, text="", font=("Courier", 12, "bold"), bg="#1e1e2e", fg="#cdd6f4")
        result_lbl.pack(pady=4)

        fight_btn = tk.Button(
            action_frame, text="⚔ INITIATE HACK ⚔", font=("Courier", 12, "bold"),
            bg="#f38ba8", fg="#11111b", activebackground="#f5e0dc",
            height=2, command=_execute_fight
        )
        fight_btn.pack(fill="x")

        # Initialize views
        _update_ui()

    return _interact