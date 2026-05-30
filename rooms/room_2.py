# rooms/room_2.py


from puzzles import password_puzzle, maze_puzzle, red_light_puzzle, bullet_dodge_puzzle, symbol_puzzle

ROOM = {
    "bg": "bg_hallway",

    
    "key_reward": {
        "puzzles_needed": 3,
        "grants": "hallway_exit_key",
    },

    "objects": [
        # Add room 2 objects here exactly like room 1
        # { "img": "locker", "tx": 3, "ty": 3, "size": 2 },

        

        { "img": "computer", "tx": 10, "ty": 6, "size": 2,
          "on_interact": maze_puzzle("Lab Maze") },
          
        { "img": "computer", "tx": 14, "ty": 10, "size": 2,
          "on_interact": red_light_puzzle("Red Light Green Light") },

        { "img": "computer", "tx": 6, "ty": 3, "size": 2,
          "on_interact": bullet_dodge_puzzle("Bullet Chamber") },

        
    ],

    "doors": [
        {
            "tx":       16,
            "ty":       7,
            "key_id":   "hallway_exit_key",
            "leads_to": "room_3",          # create room_3.py when ready
            "spawn":    (2, 7),
            "label":    "Next Room",
        },
    ],
}