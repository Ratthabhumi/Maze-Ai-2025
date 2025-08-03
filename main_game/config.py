# config.py
"""Game configuration and constants"""


class GameConfig:
    # Maze dimensions
    DEFAULT_WIDTH = 35
    DEFAULT_HEIGHT = 35
    CELL_SIZE = 40

    # Difficulty settings
    VISIBILITY_RADIUS = 4
    TIME_LIMIT = 300  # 5 minutes in seconds
    REQUIRED_KEYS = 3
    FLASHLIGHT_DURATION = 30  # seconds

    # Camera settings
    ZOOM_FACTOR = 2.0

    # Game mechanics
    ENEMY_MOVE_INTERVAL = 5  # Move every 5 game loops
    GAME_LOOP_DELAY = 200  # milliseconds

    # UI settings
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 900

    # Colors
    COLORS = {
        "wall": "#444444",
        "wall_revealed": "#666666",
        "wall_outline": "#666666",
        "wall_outline_revealed": "#888888",
        "path": "#f0f0f0",
        "path_revealed": "#e8e8e8",
        "path_outline": "#cccccc",
        "path_outline_revealed": "#d0d0d0",
        "black": "black",
        "player": "blue",
        "player_outline": "darkblue",
        "key": "gold",
        "key_outline": "orange",
        "teleporter": "purple",
        "teleporter_outline": "magenta",
        "trap": "darkred",
        "trap_outline": "red",
        "enemy": "red",
        "enemy_outline": "darkred",
        "start": "lightgreen",
        "start_outline": "green",
        "exit_open": "lightcoral",
        "exit_open_outline": "red",
        "exit_locked": "gray",
        "exit_locked_outline": "darkgray",
        "solution_path": "orange",
        "solution_arrow": "red",
        "solution_start": "lime",
        "solution_end": "red",
    }

    # Movement directions
    DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    # Search algorithms
    ALGORITHMS = ["BFS", "UCS", "DFS", "DLS", "IDS", "Bidirectional"]
