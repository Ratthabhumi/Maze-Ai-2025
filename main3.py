import tkinter as tk
from tkinter import messagebox
import random
from collections import deque
import time
import math
import platform


class HardMazeGame:
    def __init__(self, width=35, height=35):
        self.solution_path = None  # <-- Move this to the top!
        self.width = width
        self.height = height
        
        # Platform-specific adjustments
        self.platform = platform.system()
        self.setup_platform_settings()
        
        self.maze = []
        self.player_pos = [1, 1]
        self.end_pos = [width - 2, height - 2]

        # Difficulty features
        self.visibility_radius = 4  # Limited vision
        self.time_limit = 300  # 5 minutes in seconds
        self.start_time = None
        self.moves_count = 0
        self.max_moves = None  # Will be set based on optimal path
        self.has_flashlight = False
        self.flashlight_duration = 30  # seconds
        self.flashlight_start = None
        self.map_revealed = False  # Map reveal state
        self.reveal_duration = 999  # seconds
        self.reveal_start = None

        # Traps and hazards
        self.traps = []
        self.moving_walls = []
        self.wall_move_timer = 0
        self.teleporters = []

        # Power-ups
        self.keys = []  # Golden keys to collect
        self.keys_collected = 0
        self.required_keys = 3

        # Enemy (moving obstacle)
        self.enemy_pos = None
        self.enemy_path = []
        self.enemy_move_counter = 0

        # Create the main window
        self.root = tk.Tk()
        self.root.title("HARD Maze Game - Survival Mode")
        self.root.resizable(False, False)
        
        # Configure DPI awareness for Windows
        self.configure_dpi_awareness()

        # Create canvas with platform-adjusted sizes
        canvas_width = self.width * self.cell_size
        canvas_height = self.height * self.cell_size

        self.canvas = tk.Canvas(
            self.root,
            width=canvas_width,
            height=canvas_height,
            bg="black",  # Dark background for limited visibility
            highlightthickness=0,  # Remove border highlight
        )
        self.canvas.pack()

        # Create compact info display
        self.create_ui_elements()

        # Bind keyboard events
        self.root.bind("<Key>", self.on_key_press)
        self.root.focus_set()

        # Center window on screen
        self.center_window()

        self.zoom_window = 9  # Number of cells to show in zoom mode (must be odd)

        # Generate initial maze
        self.generate_maze()
        self.setup_difficulty_features()
        self.start_time = time.time()
        self.draw_maze()
        self.update_info()
        self.game_loop()

    def setup_platform_settings(self):
        """Configure platform-specific settings for consistent display"""
        if self.platform == "Darwin":  # macOS
            self.cell_size = 20
            self.font_size_large = 12
            self.font_size_medium = 10
            self.font_size_small = 9
            self.button_font_size = 9
            self.emoji_font_size = 14
            self.player_radius_factor = 0.35
        elif self.platform == "Windows":
            self.cell_size = 29  # Increase this value for a bigger screen
            self.font_size_large = 24
            self.font_size_medium = 18
            self.font_size_small = 15
            self.button_font_size = 22
            self.emoji_font_size = 18
            self.player_radius_factor = 0.32
        else:  # Linux and others
            self.cell_size = 19
            self.font_size_large = 11
            self.font_size_medium = 9
            self.font_size_small = 8
            self.button_font_size = 8
            self.emoji_font_size = 13
            self.player_radius_factor = 0.33

    def configure_dpi_awareness(self):
        """Configure DPI awareness for better scaling on Windows"""
        if self.platform == "Windows":
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except:
                pass  # Ignore if not available
            
            # Try to get DPI scaling factor
            try:
                self.root.tk.call('tk', 'scaling', 1.0)
            except:
                pass

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_ui_elements(self):
        """Create UI elements with platform-appropriate sizes"""
        info_frame = tk.Frame(self.root)
        info_frame.pack(pady=2, fill=tk.X)

        # Left side info
        left_info = tk.Frame(info_frame)
        left_info.pack(side=tk.LEFT, padx=5)

        self.time_label = tk.Label(
            left_info, 
            text="Time: 5:00", 
            font=("Arial", self.font_size_medium), 
            fg="red"
        )
        self.time_label.pack(side=tk.LEFT, padx=8)

        self.moves_label = tk.Label(
            left_info, 
            text="Moves: 0", 
            font=("Arial", self.font_size_medium)
        )
        self.moves_label.pack(side=tk.LEFT, padx=8)

        self.keys_label = tk.Label(
            left_info, 
            text="Keys: 0/3", 
            font=("Arial", self.font_size_medium), 
            fg="gold"
        )
        self.keys_label.pack(side=tk.LEFT, padx=8)

        # Right side controls
        right_info = tk.Frame(info_frame)
        right_info.pack(side=tk.RIGHT, padx=5)

        self.flashlight_label = tk.Label(
            right_info, 
            text="F: Flashlight", 
            font=("Arial", self.font_size_small), 
            fg="yellow"
        )
        self.flashlight_label.pack(side=tk.RIGHT, padx=4)

        self.reveal_label = tk.Label(
            right_info, 
            text="R: Reveal Map", 
            font=("Arial", self.font_size_small), 
            fg="cyan"
        )
        self.reveal_label.pack(side=tk.RIGHT, padx=4)

        solver_label = tk.Label(
            right_info, 
            text="S: Solve | C: Compare", 
            font=("Arial", self.font_size_small), 
            fg="orange"
        )
        solver_label.pack(side=tk.RIGHT, padx=4)

        # Create compact control buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=2)

        # Button styling for consistency
        button_config = {
            'font': ("Arial", self.button_font_size),
            'padx': 4,
            'pady': 2
        }

        tk.Button(
            button_frame,
            text="New Maze",
            command=self.generate_new_maze,
            **button_config
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            button_frame, 
            text="Reset", 
            command=self.reset_game, 
            **button_config
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            button_frame,
            text="Hint (-10 moves)",
            command=self.show_hint,
            **button_config
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            button_frame,
            text="Reveal Map (R)",
            command=self.toggle_reveal_map,
            **button_config
        ).pack(side=tk.LEFT, padx=2)

        # Solver controls
        tk.Label(
            button_frame, 
            text="Algorithm:", 
            font=("Arial", self.button_font_size)
        ).pack(side=tk.LEFT, padx=(8, 2))
        
        self.solver_var = tk.StringVar(value="BFS")
        solver_options = ["BFS", "UCS", "DFS", "DLS", "IDS", "Bidirectional"]
        self.solver_menu = tk.OptionMenu(button_frame, self.solver_var, *solver_options)
        self.solver_menu.config(font=("Arial", self.button_font_size))
        self.solver_menu.pack(side=tk.LEFT, padx=2)

        tk.Button(
            button_frame,
            text="Solve (S)",
            command=self.show_solution,
            **button_config
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            button_frame,
            text="Compare (C)",
            command=self.compare_algorithms,
            **button_config
        ).pack(side=tk.LEFT, padx=2)

    def generate_maze(self):
        """Generate a more complex maze with multiple paths and dead ends"""
        self.maze = [[1 for _ in range(self.width)] for _ in range(self.height)]

        # Create main path using recursive backtracking
        stack = []
        start_x, start_y = 1, 1
        self.maze[start_y][start_x] = 0
        stack.append((start_x, start_y))

        directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]

        while stack:
            current_x, current_y = stack[-1]
            neighbors = []

            for dx, dy in directions:
                nx, ny = current_x + dx, current_y + dy
                if (
                    0 < nx < self.width - 1
                    and 0 < ny < self.height - 1
                    and self.maze[ny][nx] == 1
                ):
                    neighbors.append((nx, ny, dx // 2, dy // 2))

            if neighbors:
                nx, ny, wall_x, wall_y = random.choice(neighbors)
                self.maze[current_y + wall_y][current_x + wall_x] = 0
                self.maze[ny][nx] = 0
                stack.append((nx, ny))
            else:
                stack.pop()

        # Add extra connections to create loops (makes it harder)
        for _ in range(self.width // 2):
            x = random.randrange(1, self.width - 1, 2)
            y = random.randrange(1, self.height - 1, 2)
            if self.maze[y][x] == 0:
                # Try to break a wall to create a loop
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if (
                        0 < nx < self.width - 1
                        and 0 < ny < self.height - 1
                        and self.maze[ny][nx] == 1
                        and random.random() < 0.3
                    ):
                        self.maze[ny][nx] = 0
                        break

        # Ensure start and end are clear
        self.maze[1][1] = 0
        self.maze[self.height - 2][self.width - 2] = 0

    def setup_difficulty_features(self):
        """Set up traps, keys, teleporters, and other difficulty features, ensuring solvability"""
        max_attempts = 20
        for attempt in range(max_attempts):
            self.traps = []
            self.keys = []
            self.teleporters = []
            self.moving_walls = []

            # Find all empty spaces
            empty_spaces = []
            for y in range(1, self.height - 1):
                for x in range(1, self.width - 1):
                    if self.maze[y][x] == 0 and [x, y] not in [[1, 1], self.end_pos]:
                        empty_spaces.append([x, y])

            # Place golden keys
            keys = []
            available = empty_spaces[:]
            for _ in range(self.required_keys):
                if available:
                    pos = random.choice(available)
                    keys.append(pos)
                    available.remove(pos)
            self.keys = [k[:] for k in keys]

            # Place traps (avoid keys, start, end)
            traps = []
            trap_candidates = [pos for pos in empty_spaces if pos not in self.keys]
            num_traps = min(8, len(trap_candidates) // 10)
            for _ in range(num_traps):
                if trap_candidates:
                    pos = random.choice(trap_candidates)
                    traps.append(pos)
                    trap_candidates.remove(pos)
            self.traps = [t[:] for t in traps]

            # Place teleporter pairs (avoid keys, traps, start, end)
            tele_candidates = [pos for pos in empty_spaces if pos not in self.keys and pos not in self.traps]
            teleporters = []
            if len(tele_candidates) >= 4:
                for _ in range(2):  # 2 pairs of teleporters
                    pos1 = random.choice(tele_candidates)
                    tele_candidates.remove(pos1)
                    pos2 = random.choice(tele_candidates)
                    tele_candidates.remove(pos2)
                    teleporters.append((pos1[:], pos2[:]))
            self.teleporters = [ (a[:], b[:]) for a, b in teleporters ]

            # Set up enemy
            enemy_candidates = [pos for pos in empty_spaces if pos not in self.keys and pos not in self.traps]
            self.enemy_pos = random.choice(enemy_candidates) if enemy_candidates else None
            self.create_enemy_path()

            # --- NEW: Check solvability with enemy as a moving obstacle ---
            def is_solvable_with_enemy():
                # Treat all enemy patrol positions as blocked
                blocked = set(tuple(pos) for pos in self.enemy_path)
                # Helper for BFS that avoids enemy
                def bfs_avoid_enemy(start, end):
                    queue = deque([(start, [start])])
                    visited = set([tuple(start)])
                    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
                    while queue:
                        (x, y), path = queue.popleft()
                        if [x, y] == end:
                            return True
                        for dx, dy in directions:
                            nx, ny = x + dx, y + dy
                            if (
                                0 <= nx < self.width and 0 <= ny < self.height
                                and self.maze[ny][nx] == 0
                                and (nx, ny) not in visited
                                and (nx, ny) not in blocked
                            ):
                                visited.add((nx, ny))
                                queue.append(([nx, ny], path + [[nx, ny]]))
                    return False

                # Check path to each key and from last key to exit
                test_pos = [1, 1]
                test_keys = [k[:] for k in self.keys]
                while test_keys:
                    nearest = min(test_keys, key=lambda k: abs(k[0] - test_pos[0]) + abs(k[1] - test_pos[1]))
                    if not bfs_avoid_enemy(test_pos, nearest):
                        return False
                    test_pos = nearest[:]
                    test_keys.remove(nearest)
                # Path from last key to exit
                if not bfs_avoid_enemy(test_pos, self.end_pos):
                    return False
                return True

            if is_solvable_with_enemy():
                # Set move limit based on optimal path + buffer
                optimal_path, _, _ = self.find_path([1, 1], self.end_pos, "BFS")
                if optimal_path:
                    self.max_moves = len(optimal_path) * 3  # 3x the optimal moves
                return  # Success: solvable maze with features

        # If teleporters are present and maze is unsolvable, try again with different placement
        # (This is the key fix: don't keep unsolvable teleporters)

        # If we get here, fallback: no traps/teleporters
        self.traps = []
        self.teleporters = []
        self.keys = []
        empty_spaces = []
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.maze[y][x] == 0 and [x, y] not in [[1, 1], self.end_pos]:
                    empty_spaces.append([x, y])
        for _ in range(self.required_keys):
            if empty_spaces:
                pos = random.choice(empty_spaces)
                self.keys.append(pos)
                empty_spaces.remove(pos)
        self.enemy_pos = random.choice(empty_spaces) if empty_spaces else None
        self.create_enemy_path()
        optimal_path, _, _ = self.find_path([1, 1], self.end_pos, "BFS")
        if optimal_path:
            self.max_moves = len(optimal_path) * 3

    def create_enemy_path(self):
        """Create a patrol path for the enemy"""
        if not self.enemy_pos:
            return

        # Find nearby empty spaces for patrol
        self.enemy_path = [self.enemy_pos[:]]
        current = self.enemy_pos[:]

        # Create a simple back-and-forth patrol
        for _ in range(6):
            for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                nx, ny = current[0] + dx, current[1] + dy
                if (
                    0 <= nx < self.width
                    and 0 <= ny < self.height
                    and self.maze[ny][nx] == 0
                    and [nx, ny] not in self.enemy_path
                ):
                    self.enemy_path.append([nx, ny])
                    current = [nx, ny]
                    break

    def draw_maze(self):
        """Draw the maze with limited visibility or full reveal"""
        self.canvas.delete("all")

        px, py = self.player_pos
        vision_range = self.visibility_radius

        # Check if map is revealed
        map_fully_visible = False
        if self.map_revealed and self.reveal_start:
            elapsed = time.time() - self.reveal_start
            if elapsed < self.reveal_duration:
                map_fully_visible = True
            else:
                self.map_revealed = False
                self.reveal_start = None

        # Extend vision if flashlight is active
        if self.has_flashlight and self.flashlight_start:
            elapsed = time.time() - self.flashlight_start
            if elapsed < self.flashlight_duration:
                vision_range = 8
            else:
                self.has_flashlight = False
                self.flashlight_start = None

        # --- ZOOM LOGIC ---
        if not map_fully_visible:
            # Zoomed-in: only draw a window around the player
            half = self.zoom_window // 2
            start_x = max(0, px - half)
            end_x = min(self.width, px + half + 1)
            start_y = max(0, py - half)
            end_y = min(self.height, py + half + 1)

            # Adjust canvas size for zoom
            zoom_cell_size = self.cell_size * 2  # Make cells bigger when zoomed in
            self.canvas.config(
                width=(end_x - start_x) * zoom_cell_size,
                height=(end_y - start_y) * zoom_cell_size,
            )

            for y in range(start_y, end_y):
                for x in range(start_x, end_x):
                    distance = math.sqrt((x - px) ** 2 + (y - py) ** 2)
                    cell_visible = distance <= vision_range

                    x1 = (x - start_x) * zoom_cell_size
                    y1 = (y - start_y) * zoom_cell_size
                    x2 = x1 + zoom_cell_size
                    y2 = y1 + zoom_cell_size

                    if cell_visible:
                        if self.maze[y][x] == 1:
                            self.canvas.create_rectangle(
                                x1, y1, x2, y2, fill="#444444", outline="#666666", width=1
                            )
                        else:
                            self.canvas.create_rectangle(
                                x1, y1, x2, y2, fill="#f0f0f0", outline="#cccccc", width=1
                            )
                    else:
                        self.canvas.create_rectangle(
                            x1, y1, x2, y2, fill="black", outline="black", width=0
                        )

            # Draw special items, player, and solution path in zoomed coordinates
            effective_vision = float('inf') if map_fully_visible else vision_range
            self.draw_special_items_zoom(px, py, effective_vision, start_x, start_y, zoom_cell_size)
            self.draw_player_zoom(start_x, start_y, zoom_cell_size)

            # Draw solution path if it exists (zoomed)
            if self.solution_path:
                line_width = max(2, zoom_cell_size // 6)
                for i in range(len(self.solution_path) - 1):
                    x1, y1 = self.solution_path[i]
                    x2, y2 = self.solution_path[i + 1]
                    if start_x <= x1 < end_x and start_y <= y1 < end_y and start_x <= x2 < end_x and start_y <= y2 < end_y:
                        center1_x = (x1 - start_x) * zoom_cell_size + zoom_cell_size // 2
                        center1_y = (y1 - start_y) * zoom_cell_size + zoom_cell_size // 2
                        center2_x = (x2 - start_x) * zoom_cell_size + zoom_cell_size // 2
                        center2_y = (y2 - start_y) * zoom_cell_size + zoom_cell_size // 2
                        self.canvas.create_line(
                            center1_x, center1_y, center2_x, center2_y,
                            fill="orange", width=line_width, tags="solution"
                        )
            return

        # --- Normal (full) view ---
        # Restore canvas size
        self.canvas.config(
            width=self.width * self.cell_size,
            height=self.height * self.cell_size,
        )

        for y in range(self.height):
            for x in range(self.width):
                # Calculate distance from player
                distance = math.sqrt((x - px) ** 2 + (y - py) ** 2)

                x1, y1 = x * self.cell_size, y * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size

                # Determine if cell should be visible
                cell_visible = map_fully_visible or distance <= vision_range

                if cell_visible:
                    if self.maze[y][x] == 1:  # Wall
                        # Dim walls if map is revealed to distinguish from normal vision
                        wall_color = "#333333" if map_fully_visible and distance > vision_range else "#444444"
                        outline_color = "#555555" if map_fully_visible and distance > vision_range else "#666666"
                        self.canvas.create_rectangle(
                            x1, y1, x2, y2, fill=wall_color, outline=outline_color, width=1
                        )
                    else:  # Path
                        # Dim paths if map is revealed to distinguish from normal vision
                        path_color = "#d0d0d0" if map_fully_visible and distance > vision_range else "#f0f0f0"
                        outline_color = "#aaaaaa" if map_fully_visible and distance > vision_range else "#cccccc"
                        self.canvas.create_rectangle(
                            x1, y1, x2, y2, fill=path_color, outline=outline_color, width=1
                        )
                else:
                    # Outside vision - pure black
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2, fill="black", outline="black", width=0
                    )

        # Draw visible special items
        effective_vision = float('inf') if map_fully_visible else vision_range
        self.draw_special_items(px, py, effective_vision)
        
        # Draw player
        self.draw_player()

        # Defensive: ensure solution_path exists
        if not hasattr(self, "solution_path"):
            self.solution_path = None

        # Draw solution path if it exists
        if self.solution_path:
            line_width = max(2, self.cell_size // 6)
            for i in range(len(self.solution_path) - 1):
                x1, y1 = self.solution_path[i]
                x2, y2 = self.solution_path[i + 1]
                center1_x = x1 * self.cell_size + self.cell_size // 2
                center1_y = y1 * self.cell_size + self.cell_size // 2
                center2_x = x2 * self.cell_size + self.cell_size // 2
                center2_y = y2 * self.cell_size + self.cell_size // 2
                self.canvas.create_line(
                    center1_x,
                    center1_y,
                    center2_x,
                    center2_y,
                    fill="orange",
                    width=line_width,
                    tags="solution",
                )

    def draw_special_items(self, px, py, vision_range):
        """Draw keys, teleporters, enemy, etc. within vision range"""
        # Draw traps if map is revealed (normally invisible)
        if vision_range == float('inf'):  # Map is fully revealed
            for trap_x, trap_y in self.traps:
                margin = max(2, self.cell_size // 8)
                x1, y1 = trap_x * self.cell_size + margin, trap_y * self.cell_size + margin
                x2, y2 = x1 + self.cell_size - 2*margin, y1 + self.cell_size - 2*margin
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill="darkred", outline="red", width=1
                )
                self.canvas.create_text(
                    trap_x * self.cell_size + self.cell_size // 2,
                    trap_y * self.cell_size + self.cell_size // 2,
                    text="!",
                    fill="white",
                    font=("Arial", self.font_size_small, "bold"),
                )

        # Draw keys
        for kx, ky in self.keys:
            if math.sqrt((kx - px) ** 2 + (ky - py) ** 2) <= vision_range:
                margin = max(3, self.cell_size // 6)
                x1, y1 = kx * self.cell_size + margin, ky * self.cell_size + margin
                x2, y2 = x1 + self.cell_size - 2*margin, y1 + self.cell_size - 2*margin
                self.canvas.create_oval(x1, y1, x2, y2, fill="gold", outline="orange", width=2)
                
                # Use platform-appropriate text/symbol
                key_symbol = "K" if self.platform == "Windows" else "🗝"
                self.canvas.create_text(
                    kx * self.cell_size + self.cell_size // 2,
                    ky * self.cell_size + self.cell_size // 2,
                    text=key_symbol,
                    font=("Arial", self.font_size_small, "bold"),
                    fill="darkgoldenrod"
                )

        # Draw teleporters
        for pos1, pos2 in self.teleporters:
            for tx, ty in [pos1, pos2]:
                if math.sqrt((tx - px) ** 2 + (ty - py) ** 2) <= vision_range:
                    margin = max(2, self.cell_size // 8)
                    x1, y1 = tx * self.cell_size + margin, ty * self.cell_size + margin
                    x2, y2 = x1 + self.cell_size - 2*margin, y1 + self.cell_size - 2*margin
                    self.canvas.create_oval(
                        x1, y1, x2, y2, fill="purple", outline="magenta", width=2
                    )
                    self.canvas.create_text(
                        tx * self.cell_size + self.cell_size // 2,
                        ty * self.cell_size + self.cell_size // 2,
                        text="T",
                        fill="white",
                        font=("Arial", self.font_size_small, "bold"),
                    )

        # Draw enemy
        if self.enemy_pos:
            ex, ey = self.enemy_pos
            if math.sqrt((ex - px) ** 2 + (ey - py) ** 2) <= vision_range:
                margin = max(1, self.cell_size // 10)
                x1, y1 = ex * self.cell_size + margin, ey * self.cell_size + margin
                x2, y2 = x1 + self.cell_size - 2*margin, y1 + self.cell_size - 2*margin
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill="red", outline="darkred", width=2
                )
                
                # Use platform-appropriate enemy symbol
                enemy_symbol = "E" if self.platform == "Windows" else "👹"
                self.canvas.create_text(
                    ex * self.cell_size + self.cell_size // 2,
                    ey * self.cell_size + self.cell_size // 2,
                    text=enemy_symbol,
                    font=("Arial", self.font_size_medium, "bold"),
                    fill="white"
                )

        # Draw start position (only if visible)
        if math.sqrt((1 - px) ** 2 + (1 - py) ** 2) <= vision_range:
            margin = max(2, self.cell_size // 8)
            x1 = 1 * self.cell_size + margin
            y1 = 1 * self.cell_size + margin
            x2 = x1 + self.cell_size - 2*margin
            y2 = y1 + self.cell_size - 2*margin
            self.canvas.create_rectangle(
                x1, y1, x2, y2, fill="lightgreen", outline="green", width=2
            )

        # Draw end position (only if visible and all keys collected)
        end_x, end_y = self.end_pos
        if math.sqrt((end_x - px) ** 2 + (end_y - py) ** 2) <= vision_range:
            margin = max(2, self.cell_size // 8)
            x1 = end_x * self.cell_size + margin
            y1 = end_y * self.cell_size + margin
            x2 = x1 + self.cell_size - 2*margin
            y2 = y1 + self.cell_size - 2*margin
            
            if self.keys_collected >= self.required_keys:
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill="lightcoral", outline="red", width=2
                )
                door_symbol = "EXIT" if self.platform == "Windows" else "🚪"
                self.canvas.create_text(
                    end_x * self.cell_size + self.cell_size // 2,
                    end_y * self.cell_size + self.cell_size // 2,
                    text=door_symbol,
                    font=("Arial", self.font_size_small, "bold"),
                    fill="darkred"
                )
            else:
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill="gray", outline="darkgray", width=2
                )
                lock_symbol = "LOCK" if self.platform == "Windows" else "🔒"
                self.canvas.create_text(
                    end_x * self.cell_size + self.cell_size // 2,
                    end_y * self.cell_size + self.cell_size // 2,
                    text=lock_symbol,
                    font=("Arial", self.font_size_small, "bold"),
                    fill="white"
                )

    def draw_special_items_zoom(self, px, py, vision_range, start_x, start_y, cell_size):
        """Draw keys, teleporters, enemy, etc. within vision range for zoomed-in view"""
        # Draw traps if map is revealed (normally invisible)
        if vision_range == float('inf'):  # Map is fully revealed
            for trap_x, trap_y in self.traps:
                margin = max(2, cell_size // 8)
                x1, y1 = (trap_x - start_x) * cell_size + margin, (trap_y - start_y) * cell_size + margin
                x2, y2 = x1 + cell_size - 2*margin, y1 + cell_size - 2*margin
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill="darkred", outline="red", width=1
                )
                self.canvas.create_text(
                    (trap_x - start_x) * cell_size + cell_size // 2,
                    (trap_y - start_y) * cell_size + cell_size // 2,
                    text="!",
                    fill="white",
                    font=("Arial", self.font_size_small, "bold"),
                )

        # Draw keys
        for kx, ky in self.keys:
            if math.sqrt((kx - px) ** 2 + (ky - py) ** 2) <= vision_range:
                margin = max(3, cell_size // 6)
                x1 = (kx - start_x) * cell_size + margin
                y1 = (ky - start_y) * cell_size + margin
                x2 = x1 + cell_size - 2*margin
                y2 = y1 + cell_size - 2*margin
                self.canvas.create_oval(x1, y1, x2, y2, fill="gold", outline="orange", width=2)
                key_symbol = "K" if self.platform == "Windows" else "🗝"
                self.canvas.create_text(
                    (kx - start_x) * cell_size + cell_size // 2,
                    (ky - start_y) * cell_size + cell_size // 2,
                    text=key_symbol,
                    font=("Arial", self.font_size_small, "bold"),
                    fill="darkgoldenrod"
                )

        # Draw teleporters
        for pos1, pos2 in self.teleporters:
            for tx, ty in [pos1, pos2]:
                if math.sqrt((tx - px) ** 2 + (ty - py) ** 2) <= vision_range:
                    margin = max(2, cell_size // 8)
                    x1 = (tx - start_x) * cell_size + margin
                    y1 = (ty - start_y) * cell_size + margin
                    x2 = x1 + cell_size - 2*margin
                    y2 = y1 + cell_size - 2*margin
                    self.canvas.create_oval(
                        x1, y1, x2, y2, fill="purple", outline="magenta", width=2
                    )
                    self.canvas.create_text(
                        (tx - start_x) * cell_size + cell_size // 2,
                        (ty - start_y) * cell_size + cell_size // 2,
                        text="T",
                        fill="white",
                        font=("Arial", self.font_size_small, "bold"),
                    )

        # Draw enemy
        if self.enemy_pos:
            ex, ey = self.enemy_pos
            if math.sqrt((ex - px) ** 2 + (ey - py) ** 2) <= vision_range:
                margin = max(1, cell_size // 10)
                x1 = (ex - start_x) * cell_size + margin
                y1 = (ey - start_y) * cell_size + margin
                x2 = x1 + cell_size - 2*margin
                y2 = y1 + cell_size - 2*margin
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill="red", outline="darkred", width=2
                )
                enemy_symbol = "E" if self.platform == "Windows" else "👹"
                self.canvas.create_text(
                    (ex - start_x) * cell_size + cell_size // 2,
                    (ey - start_y) * cell_size + cell_size // 2,
                    text=enemy_symbol,
                    font=("Arial", self.font_size_medium, "bold"),
                    fill="white"
                )

        # Draw start position (only if visible)
        if math.sqrt((1 - px) ** 2 + (1 - py) ** 2) <= vision_range:
            margin = max(2, cell_size // 8)
            x1 = (1 - start_x) * cell_size + margin
            y1 = (1 - start_y) * cell_size + margin
            x2 = x1 + cell_size - 2*margin
            y2 = y1 + cell_size - 2*margin
            self.canvas.create_rectangle(
                x1, y1, x2, y2, fill="lightgreen", outline="green", width=2
            )

        # Draw end position (only if visible and all keys collected)
        end_x, end_y = self.end_pos
        if math.sqrt((end_x - px) ** 2 + (end_y - py) ** 2) <= vision_range:
            margin = max(2, cell_size // 8)
            x1 = (end_x - start_x) * cell_size + margin
            y1 = (end_y - start_y) * cell_size + margin
            x2 = x1 + cell_size - 2*margin
            y2 = y1 + cell_size - 2*margin
            
            if self.keys_collected >= self.required_keys:
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill="lightcoral", outline="red", width=2
                )
                door_symbol = "EXIT" if self.platform == "Windows" else "🚪"
                self.canvas.create_text(
                    (end_x - start_x) * cell_size + cell_size // 2,
                    (end_y - start_y) * cell_size + cell_size // 2,
                    text=door_symbol,
                    font=("Arial", self.font_size_small, "bold"),
                    fill="darkred"
                )
            else:
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill="gray", outline="darkgray", width=2
                )
                lock_symbol = "LOCK" if self.platform == "Windows" else "🔒"
                self.canvas.create_text(
                    (end_x - start_x) * cell_size + cell_size // 2,
                    (end_y - start_y) * cell_size + cell_size // 2,
                    text=lock_symbol,
                    font=("Arial", self.font_size_small, "bold"),
                    fill="white"
                )

    def draw_player(self):
        """Draw player at current position"""
        self.canvas.delete("player")
        px, py = self.player_pos
        center_x = px * self.cell_size + self.cell_size // 2
        center_y = py * self.cell_size + self.cell_size // 2
        radius = int(self.cell_size * self.player_radius_factor)

        self.canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            fill="blue",
            outline="darkblue",
            width=2,
            tags="player",
        )

    def draw_player_zoom(self, start_x, start_y, cell_size):
        """Draw the player in zoomed-in coordinates"""
        px, py = self.player_pos
        center_x = (px - start_x) * cell_size + cell_size // 2
        center_y = (py - start_y) * cell_size + cell_size // 2
        radius = int(cell_size * self.player_radius_factor)
        self.canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            fill="blue",
            outline="darkblue",
            width=2,
            tags="player",
        )

    def on_key_press(self, event):
        """Handle keyboard input with additional features"""
        if not self.start_time:
            return

        key = event.keysym.lower()
        new_x, new_y = self.player_pos

        # Movement keys
        if key == "up" or key == "w":
            new_y -= 1
        elif key == "down" or key == "s":
            new_y += 1
        elif key == "left" or key == "a":
            new_x -= 1
        elif key == "right" or key == "d":
            new_x += 1
        # Utility keys
        elif key == "f":  # Flashlight
            if not self.has_flashlight:
                self.has_flashlight = True
                self.flashlight_start = time.time()
                self.draw_maze()
            return
        elif key == "s" and event.state == 0:  # S key for solver (without modifier)
            self.show_solution()
            return
        elif key == "c":  # C key for compare
            self.compare_algorithms()
            return
        elif key == "h":  # H key for hint
            self.show_hint()
            return
        elif key == "r":  # R key for reveal map
            self.toggle_reveal_map()
            return
        else:
            return

        # Check if move is valid
        if (
            0 <= new_x < self.width
            and 0 <= new_y < self.height
            and self.maze[new_y][new_x] == 0
        ):

            self.player_pos = [new_x, new_y]
            self.moves_count += 1

            # Check for trap
            if self.player_pos in self.traps:
                messagebox.showwarning("Trap!", "You stepped on a trap! Game Over!")
                self.reset_game()
                return

            # Check for enemy collision
            if self.player_pos == self.enemy_pos:
                messagebox.showwarning("Caught!", "The enemy caught you! Game Over!")
                self.reset_game()
                return

            # Check for key collection
            if self.player_pos in self.keys:
                self.keys.remove(self.player_pos)
                self.keys_collected += 1
                messagebox.showinfo(
                    "Key Found!",
                    f"You found a key! ({self.keys_collected}/{self.required_keys})",
                )

            # Check for teleporter
            for pos1, pos2 in self.teleporters:
                if self.player_pos == pos1:
                    self.player_pos = pos2[:]
                    messagebox.showinfo("Teleported!", "You've been teleported!")
                    break
                elif self.player_pos == pos2:
                    self.player_pos = pos1[:]
                    messagebox.showinfo("Teleported!", "You've been teleported!")
                    break

            self.draw_maze()

            # Check win condition
            if (
                self.player_pos == self.end_pos
                and self.keys_collected >= self.required_keys
            ):
                elapsed_time = time.time() - self.start_time
                messagebox.showinfo(
                    "Victory!",
                    f"Congratulations! You escaped!\nTime: {elapsed_time:.1f}s\nMoves: {self.moves_count}",
                )
                self.start_time = None

    def move_enemy(self):
        """Move the enemy along its patrol path"""
        if not self.enemy_pos or not self.enemy_path:
            return

        self.enemy_move_counter += 1
        if self.enemy_move_counter >= 5:  # Move every 5 game loops
            current_index = (
                self.enemy_path.index(self.enemy_pos)
                if self.enemy_pos in self.enemy_path
                else 0
            )
            next_index = (current_index + 1) % len(self.enemy_path)
            self.enemy_pos = self.enemy_path[next_index][:]
            self.enemy_move_counter = 0

    def update_info(self):
        """Update the information display"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            remaining = max(0, self.time_limit - elapsed)
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            self.time_label.config(text=f"Time: {minutes}:{seconds:02d}")

            if remaining <= 0:
                messagebox.showwarning("Time's Up!", "You ran out of time! Game Over!")
                self.reset_game()
                return

        moves_text = f"Moves: {self.moves_count}"
        if self.max_moves:
            moves_text += f"/{self.max_moves}"
        self.moves_label.config(text=moves_text)

        if self.max_moves and self.moves_count >= self.max_moves:
            messagebox.showwarning(
                "Too Many Moves!", "You've used too many moves! Game Over!"
            )
            self.reset_game()
            return

        self.keys_label.config(text=f"Keys: {self.keys_collected}/{self.required_keys}")

        # Flashlight status
        if self.has_flashlight and self.flashlight_start:
            remaining_flash = max(
                0, self.flashlight_duration - (time.time() - self.flashlight_start)
            )
            self.flashlight_label.config(
                text=f"F: Flash {remaining_flash:.0f}s", fg="yellow"
            )
        else:
            self.flashlight_label.config(text="F: Flashlight", fg="gray")

        # Reveal map status
        if self.map_revealed and self.reveal_start:
            remaining_reveal = max(
                0, self.reveal_duration - (time.time() - self.reveal_start)
            )
            self.reveal_label.config(
                text=f"R: Reveal {remaining_reveal:.0f}s", fg="cyan"
            )
        else:
            self.reveal_label.config(text="R: Reveal Map", fg="gray")

    def show_solution(self):
        """Show the solution path using selected algorithm"""
        algorithm = self.solver_var.get()
        start_pos = [1, 1]

        # If player needs keys, find path to nearest key first
        if self.keys_collected < self.required_keys and self.keys:
            target = min(
                self.keys,
                key=lambda k: abs(k[0] - self.player_pos[0])
                + abs(k[1] - self.player_pos[1]),
            )
            path_result = self.find_path(self.player_pos, target, algorithm)
        else:
            path_result = self.find_path(self.player_pos, self.end_pos, algorithm)

        if len(path_result) == 3:
            path, nodes_explored, search_time = path_result
        else:
            path, nodes_explored, search_time = path_result[0], path_result[1], 0

        if path:
            self.solution_path = path  # Store the solution path
            self.draw_maze()           # Redraw maze, which will now show the solution
            # Show algorithm performance
            target_type = (
                "nearest key"
                if (self.keys_collected < self.required_keys and self.keys)
                else "exit"
            )
            messagebox.showinfo(
                "Solution Found",
                f"Algorithm: {algorithm}\n"
                f"Path to {target_type}\n"
                f"Path length: {len(path)} steps\n"
                f"Nodes explored: {nodes_explored}\n"
                f"Search time: {search_time:.4f}s",
            )
        else:
            self.solution_path = None
            self.draw_maze()
            messagebox.showwarning("No Solution", f"No path found using {algorithm}!")

    def compare_algorithms(self):
        """Compare all search algorithms"""
        algorithms = ["BFS", "UCS", "DFS", "DLS", "IDS", "Bidirectional"]
        start_pos = self.player_pos[:]
        end_pos = self.end_pos[:]

        # If player needs keys, compare paths to nearest key
        if self.keys_collected < self.required_keys and self.keys:
            end_pos = min(
                self.keys,
                key=lambda k: abs(k[0] - start_pos[0]) + abs(k[1] - start_pos[1]),
            )

        results = []

        for algorithm in algorithms:
            try:
                path_result = self.find_path(start_pos, end_pos, algorithm)
                if len(path_result) == 3:
                    path, nodes_explored, search_time = path_result
                else:
                    path, nodes_explored, search_time = (
                        path_result[0],
                        path_result[1],
                        0,
                    )

                if path:
                    results.append(
                        f"{algorithm}: {len(path)} steps, {nodes_explored} nodes, {search_time:.4f}s"
                    )
                else:
                    results.append(f"{algorithm}: No solution found")
            except Exception as e:
                results.append(f"{algorithm}: Error - {str(e)}")

        comparison_text = "Algorithm Comparison:\n" + "\n".join(results)

        # Create a new window for detailed comparison
        comparison_window = tk.Toplevel(self.root)
        comparison_window.title("Search Algorithm Comparison")
        comparison_window.geometry("600x400")
        comparison_window.resizable(True, True)

        # Create scrollable text widget
        frame = tk.Frame(comparison_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(
            frame, 
            wrap=tk.WORD, 
            font=("Courier", self.font_size_small),
            yscrollcommand=scrollbar.set
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)

        text_widget.insert(tk.END, comparison_text)

        # Add explanations
        explanations = """

Algorithm Explanations:
• BFS: Breadth-First Search - Guarantees shortest path, explores level by level
• UCS: Uniform-Cost Search - Like BFS but for weighted graphs (same as BFS here)
• DFS: Depth-First Search - Goes deep first, may not find shortest path
• DLS: Depth-Limited Search - DFS with depth limit to avoid infinite paths
• IDS: Iterative Deepening Search - Combines BFS optimality with DFS memory efficiency
• Bidirectional: Searches from both start and end simultaneously

Performance Notes:
- Path length: Number of moves required (lower is better for shortest path)
- Nodes explored: Computational efficiency (lower is more efficient)
- Search time: Actual time taken to find the solution
- BFS and Bidirectional typically find optimal solutions
- DFS may find longer paths but can be faster in some cases
- IDS combines the benefits of both BFS and DFS
"""
        text_widget.insert(tk.END, explanations)
        text_widget.config(state=tk.DISABLED)

        # Center the comparison window
        comparison_window.update_idletasks()
        x = (comparison_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (comparison_window.winfo_screenheight() // 2) - (400 // 2)
        comparison_window.geometry(f"600x400+{x}+{y}")

    def show_hint(self):
        """Show a hint at the cost of moves"""
        if self.moves_count + 10 > self.max_moves:
            messagebox.showwarning(
                "Not enough moves!", "You don't have enough moves left for a hint!"
            )
            return

        self.moves_count += 10

        # Find direction to nearest key or exit
        target = None
        if self.keys:
            target = min(
                self.keys,
                key=lambda k: abs(k[0] - self.player_pos[0])
                + abs(k[1] - self.player_pos[1]),
            )
        elif self.keys_collected >= self.required_keys:
            target = self.end_pos

        if target:
            dx = target[0] - self.player_pos[0]
            dy = target[1] - self.player_pos[1]

            if abs(dx) > abs(dy):
                direction = "RIGHT" if dx > 0 else "LEFT"
            else:
                direction = "DOWN" if dy > 0 else "UP"

            messagebox.showinfo("Hint", f"Try going {direction}!")

    def toggle_reveal_map(self):
        """Toggle the map reveal feature"""
        if not self.map_revealed:
            self.map_revealed = True
            self.reveal_start = time.time()
            self.draw_maze()
            messagebox.showinfo("Map Revealed!", f"Full map visible for {self.reveal_duration} seconds!\nTraps are shown as red squares with '!' symbols.")
        else:
            # If already revealed, show remaining time
            if self.reveal_start:
                remaining = max(0, self.reveal_duration - (time.time() - self.reveal_start))
                messagebox.showinfo("Map Status", f"Map reveal active for {remaining:.1f} more seconds")

    def game_loop(self):
        """Main game loop"""
        if self.start_time:
            self.move_enemy()
            self.update_info()
            if self.player_pos == self.enemy_pos:
                messagebox.showwarning("Caught!", "The enemy caught you! Game Over!")
                self.reset_game()
                return

        self.root.after(200, self.game_loop)  # Run every 200ms

    def is_safe_cell(self, x, y):
        """Check if a cell is safe to move to (not a wall, trap, or enemy)"""
        # Check bounds
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False

        # Check if it's a wall
        if self.maze[y][x] == 1:
            return False

        # Check if it's a trap
        if [x, y] in self.traps:
            return False

        return True

    def get_teleport(self, x, y):
        """Return teleported position if (x, y) is a teleporter, else None"""
        for pos1, pos2 in self.teleporters:
            if [x, y] == pos1:
                return pos2[:]
            if [x, y] == pos2:
                return pos1[:]
        return None

    def find_path_bfs(self, start, end):
        """Breadth-First Search - Guarantees shortest path, avoiding traps and using teleporters"""
        queue = deque([(start, [start])])
        visited = set([tuple(start)])
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        nodes_explored = 0

        while queue:
            (x, y), path = queue.popleft()
            nodes_explored += 1

            if [x, y] == end:
                return path, nodes_explored

            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if self.is_safe_cell(nx, ny) and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append(([nx, ny], path + [[nx, ny]]))
                    # Check teleport
                    tele = self.get_teleport(nx, ny)
                    if tele and tuple(tele) not in visited:
                        visited.add(tuple(tele))
                        queue.append((tele, path + [[nx, ny], tele]))
        return None, nodes_explored

    def find_path_ucs(self, start, end):
        """Uniform-Cost Search - Like BFS but with priority queue for weighted graphs, avoiding traps"""
        import heapq

        heap = [(0, start, [start])]  # (cost, position, path)
        visited = set()
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        nodes_explored = 0

        while heap:
            cost, (x, y), path = heapq.heappop(heap)
            nodes_explored += 1

            if (x, y) in visited:
                continue
            visited.add((x, y))

            if [x, y] == end:
                return path, nodes_explored

            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if self.is_safe_cell(nx, ny) and (nx, ny) not in visited:
                    new_cost = cost + 1  # Each step costs 1
                    heapq.heappush(heap, (new_cost, [nx, ny], path + [[nx, ny]]))
        return None, nodes_explored

    def find_path_dfs(self, start, end):
        """Depth-First Search - May not find shortest path, avoiding traps"""
        stack = [(start, [start])]
        visited = set()
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        nodes_explored = 0

        while stack:
            (x, y), path = stack.pop()
            nodes_explored += 1

            if (x, y) in visited:
                continue
            visited.add((x, y))

            if [x, y] == end:
                return path, nodes_explored

            # Shuffle directions for variety in DFS
            random.shuffle(directions)
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if self.is_safe_cell(nx, ny) and (nx, ny) not in visited:
                    stack.append(([nx, ny], path + [[nx, ny]]))
        return None, nodes_explored

    def find_path_dls(self, start, end, depth_limit=50):
        """Depth-Limited Search - DFS with depth limit, avoiding traps"""

        def dls_recursive(x, y, path, visited, remaining_depth):
            if remaining_depth < 0:
                return None, 0

            if [x, y] == end:
                return path, 1

            visited.add((x, y))
            nodes_explored = 1
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if self.is_safe_cell(nx, ny) and (nx, ny) not in visited:
                    result, explored = dls_recursive(
                        nx, ny, path + [[nx, ny]], visited.copy(), remaining_depth - 1
                    )
                    nodes_explored += explored
                    if result:
                        return result, nodes_explored

            return None, nodes_explored

        return dls_recursive(start[0], start[1], [start], set(), depth_limit)

    def find_path_ids(self, start, end, max_depth=100):
        """Iterative Deepening Search - Combines benefits of BFS and DFS, avoiding traps"""
        total_nodes_explored = 0

        for depth in range(max_depth):
            result, nodes_explored = self.find_path_dls(start, end, depth)
            total_nodes_explored += nodes_explored
            if result:
                return result, total_nodes_explored

        return None, total_nodes_explored

    def find_path_bidirectional(self, start, end):
        """Bidirectional Search - Search from both start and end, avoiding traps"""
        if start == end:
            return [start], 1

        # Forward search from start
        forward_queue = deque([(start, [start])])
        forward_visited = {tuple(start): [start]}

        # Backward search from end
        backward_queue = deque([(end, [end])])
        backward_visited = {tuple(end): [end]}

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        nodes_explored = 0

        while forward_queue or backward_queue:
            # Forward search step
            if forward_queue:
                (x, y), path = forward_queue.popleft()
                nodes_explored += 1

                # Check if we've met the backward search
                if (x, y) in backward_visited:
                    backward_path = backward_visited[(x, y)]
                    # Reverse the backward path and combine
                    full_path = path + backward_path[-2::-1]
                    return full_path, nodes_explored

                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if self.is_safe_cell(nx, ny) and (nx, ny) not in forward_visited:
                        new_path = path + [[nx, ny]]
                        forward_visited[(nx, ny)] = new_path
                        forward_queue.append(([nx, ny], new_path))

            # Backward search step
            if backward_queue:
                (x, y), path = backward_queue.popleft()
                nodes_explored += 1

                # Check if we've met the forward search
                if (x, y) in forward_visited:
                    forward_path = forward_visited[(x, y)]
                    # Reverse the backward path and combine
                    full_path = forward_path + path[-2::-1]
                    return full_path, nodes_explored

                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if self.is_safe_cell(nx, ny) and (nx, ny) not in backward_visited:
                        new_path = path + [[nx, ny]]
                        backward_visited[(nx, ny)] = new_path
                        backward_queue.append(([nx, ny], new_path))

        return None, nodes_explored

    def find_path(self, start, end, algorithm="BFS"):
        """Main pathfinding function that calls the selected algorithm"""
        start_time = time.time()

        if algorithm == "BFS":
            result, nodes_explored = self.find_path_bfs(start, end)
        elif algorithm == "UCS":
            result, nodes_explored = self.find_path_ucs(start, end)
        elif algorithm == "DFS":
            result, nodes_explored = self.find_path_dfs(start, end)
        elif algorithm == "DLS":
            result, nodes_explored = self.find_path_dls(start, end)
        elif algorithm == "IDS":
            result, nodes_explored = self.find_path_ids(start, end)
        elif algorithm == "Bidirectional":
            result, nodes_explored = self.find_path_bidirectional(start, end)
        else:
            result, nodes_explored = self.find_path_bfs(start, end)  # Default to BFS

        search_time = time.time() - start_time
        return result, nodes_explored, search_time

    def generate_new_maze(self):
        self.solution_path = None
        """Generate a new maze and reset everything"""
        self.generate_maze()
        self.reset_game()

    def reset_game(self):
        self.solution_path = None
        """Reset the game to initial state"""
        self.player_pos = [1, 1]
        self.moves_count = 0
        self.keys_collected = 0
        self.has_flashlight = False
        self.flashlight_start = None
        self.map_revealed = False
        self.reveal_start = None
        self.setup_difficulty_features()
        self.start_time = time.time()
        self.draw_maze()

    def run(self):
        """Start the game"""
        print("HARD Maze Game - Survival Mode with Multiple Search Algorithms")
        print("Controls:")
        print("- WASD/Arrow keys: Move")
        print("- F: Activate flashlight (30s)")
        print("- R: Reveal full map (15s)")
        print("- S: Show solution path")
        print("- C: Compare all algorithms")
        print("- H: Get hint (costs 10 moves)")
        print("- Goal: Collect all 3 keys and reach the exit!")
        print("- Avoid traps (invisible) and the red enemy!")
        print("- Purple circles are teleporters")
        print("- You have limited time and moves!")
        print(f"Running on: {self.platform}")
        self.root.mainloop()


if __name__ == "__main__":
    game = HardMazeGame(width=35, height=35)
    game.run()