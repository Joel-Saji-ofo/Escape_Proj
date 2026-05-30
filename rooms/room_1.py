# rooms/room_1.py
# 
# Modularised room making. To make a room, use the given functions to make objects meant to be in the room
#
# for ref:
#
#   a plain solid object:
#     { "img": "desk", "tx": 3, "ty": 2 }
#
#   huge object or objects with size change (size scales image AND collision box):
#     { "img": "shelf", "tx": 8, "ty": 2, "size": 2 }
#
#   decor (player walks through it so default solid state changed to false):
#     { "img": "plant", "tx": 2, "ty": 8, "solid": False }
#
#   Invisible wall (blocks player, no image):
#     { "type": "wall", "tx": 9, "ty": 5, "size": 3 }
#
#   Puzzle object:
#     { "img": "computer", "tx": 6, "ty": 3,
#       "on_interact": password_puzzle("1234", "Terminal A") }
#
#   Door (in "doors" list, not "objects"):
#     { "tx": 16, "ty": 7, "key_id": "lab_exit_key",
#       "leads_to": "room_2", "spawn": (2, 7), "label": "Exit" }
#
# a kind of note - 
#   When correct amount of puzzles_needed puzzles are solved in this room,
#   the key named in "grants" is silent added to the player.
#   Change puzzles_needed to match how many puzzles are in the room.
#   To open the door the key_id must match what "grants" gives.
# ---------------------------------------------------------------

from puzzles import password_puzzle, dice_hack, symbol_puzzle, note_clue

ROOM = {
    "bg": "bg_lab",

    #Important because no of puzzles is here
    "key_reward": {
        "puzzles_needed": 3,
        "grants": "lab_exit_key",
    },

    "objects": [
        #eg furniture
        
        # { "img": "desk",    "tx": 3,  "ty": 2, "size": 2 },
        # { "img": "shelf",   "tx": 10, "ty": 2, "size": 2 },
        # { "img": "chair",   "tx": 4,  "ty": 3, "solid": False },
        # { "img": "plant",   "tx": 2,  "ty": 8, "solid": False },

        # invisible walls (shape the path) 
        # { "type": "wall", "tx": 7, "ty": 4, "size": 3 },

        # puzzle terminals (laptops pics for now)
        { "img": "computer", "tx": 6,  "ty": 3, "size": 2,
          "on_interact": password_puzzle("1234", "Terminal A") },

        { "img": "computer", "tx": 10, "ty": 6, "size": 2,
          "on_interact": dice_hack(20,20,20) },

        { "img": "computer", "tx": 14, "ty": 10, "size": 2,
          "on_interact": password_puzzle("1234", "Terminal C") },

        #if you want the terminal to show a note
        # { "img": "paper", "tx": 5, "ty": 5, "size": 1,
        #   "on_interact": note_clue("enter your note here") },
    ],

    "doors": [
        {
            "tx":       16,
            "ty":       7,
            "key_id":   "lab_exit_key",   # must match "grants" above
            "leads_to": "room_2",
            "spawn":    (2, 7),            # tile player appears in room_2
            "label":    "Exit Door",
        },
    ],
}