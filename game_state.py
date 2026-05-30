# game_state.py
# ---------------------------------------------------------------
# Single source of truth shared across every file.
# Import anywhere with:  from game_state import STATE
# ---------------------------------------------------------------

STATE = {
    # puzzles solved in the CURRENT room only — resets on room load
    "room_puzzles_solved": 0,

    # puzzles solved across the entire game — never resets
    "total_puzzles_solved": 0,

    # set of key strings the player currently holds
    # e.g. {"lab_exit_key", "storage_room_key"}
    # when inventory is added, this drives the UI
    "keys": set(),

    # room tracking
    "current_room": "room_1",

    # player facing direction
    "player_dir": "down",

    # True while fade transition is running — freezes player
    "transitioning": False,
}