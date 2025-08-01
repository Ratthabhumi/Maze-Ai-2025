import tkinter as tk
from tkinter import messagebox
import random
from collections import deque
import time
import math


class HardMazeGame:
    def __init__(self, width=35, height=35):
        self.width = width
        self.height = height
        self.cell_size = 18
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

        # Create canvas
        canvas_width = self.width * self.cell_size
        canvas_height = self.height * self.cell_size

        self.canvas = tk.Canvas(
            self.root,
            width=canvas_width,
            height=canvas_height,
            bg="black",  # Dark background for limited visibility
        )
        self.canvas.pack()

        # Create compact info display
        info_frame = tk.Frame(self.root)
        info_frame.pack(pady=2, fill=tk.X)

        # Left side info
        left_info = tk.Frame(info_frame)
        left_info.pack(side=tk.LEFT, padx=5)

        self.time_label = tk.Label(
            left_info, text="Time: 5:00", font=("Arial", 10), fg="red"
        )
        self.time_label.pack(side=tk.LEFT, padx=10)

        self.moves_label = tk.Label(left_info, text="Moves: 0", font=("Arial", 10))
        self.moves_label.pack(side=tk.LEFT, padx=10)

        self.keys_label = tk.Label(
            left_info, text="Keys: 0/3", font=("Arial", 10), fg="gold"
        )
        self.keys_label.pack(side=tk.LEFT, padx=10)

        # Right side controls
        right_info = tk.Frame(info_frame)
        right_info.pack(side=tk.RIGHT, padx=5)

        self.flashlight_label = tk.Label(
            right_info, text="F: Flashlight", font=("Arial", 9), fg="yellow"
        )
        self.flashlight_label.pack(side=tk.RIGHT, padx=5)

        solver_label = tk.Label(
            right_info, text="S: Solve | C: Compare", font=("Arial", 9), fg="orange"
        )
        solver_label.pack(side=tk.RIGHT, padx=5)

        # Create compact control buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=2)

        tk.Button(
            button_frame,
            text="New Maze",
            command=self.generate_new_maze,
            font=("Arial", 8),
        ).pack(side=tk.LEFT, padx=2)
        tk.Button(
            button_frame, text="Reset", command=self.reset_game, font=("Arial", 8)
        ).pack(side=tk.LEFT, padx=2)
        tk.Button(
            button_frame,
            text="Hint (-10 moves)",
            command=self.show_hint,
            font=("Arial", 8),
        ).pack(side=tk.LEFT, padx=2)

        # Solver controls
        tk.Label(button_frame, text="Algorithm:", font=("Arial", 8)).pack(
            side=tk.LEFT, padx=(10, 2)
        )
        self.solver_var = tk.StringVar(value="BFS")
        solver_options = ["BFS", "UCS", "DFS", "DLS", "IDS", "Bidirectional"]
        self.solver_menu = tk.OptionMenu(button_frame, self.solver_var, *solver_options)
        self.solver_menu.config(font=("Arial", 8))
        self.solver_menu.pack(side=tk.LEFT, padx=2)

        tk.Button(
            button_frame,
            text="Solve (S)",
            command=self.show_solution,
            font=("Arial", 8),
        ).pack(side=tk.LEFT, padx=2)
        tk.Button(
            button_frame,
            text="Compare (C)",
            command=self.compare_algorithms,
            font=("Arial", 8),
        ).pack(side=tk.LEFT, padx=2)

        # Bind keyboard events
        self.root.bind("<Key>", self.on_key_press)
        self.root.focus_set()

        # Generate initial maze
        self.generate_maze()
        self.setup_difficulty_features()
        self.start_time = time.time()
        self.draw_maze()
        self.update_info()
        self.game_loop()

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
        """Set up traps, keys, teleporters, and other difficulty features"""
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
        for _ in range(self.required_keys):
            if empty_spaces:
                pos = random.choice(empty_spaces)
                self.keys.append(pos)
                empty_spaces.remove(pos)

        # Place traps (invisible death squares)
        num_traps = min(8, len(empty_spaces) // 10)
        for _ in range(num_traps):
            if empty_spaces:
                pos = random.choice(empty_spaces)
                self.traps.append(pos)
                empty_spaces.remove(pos)

        # Place teleporter pairs
        if len(empty_spaces) >= 4:
            for _ in range(2):  # 2 pairs of teleporters
                pos1 = random.choice(empty_spaces)
                empty_spaces.remove(pos1)
                pos2 = random.choice(empty_spaces)
                empty_spaces.remove(pos2)
                self.teleporters.append((pos1, pos2))

        # Set up enemy
        if empty_spaces:
            self.enemy_pos = random.choice(empty_spaces)
            # Create a patrol path for the enemy
            self.create_enemy_path()

        # Set move limit based on optimal path + buffer
        optimal_path, _, _ = self.find_path([1, 1], self.end_pos, "BFS")
        if optimal_path:
            self.max_moves = len(optimal_path) * 3  # 3x the optimal moves

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
        """Draw the maze with limited visibility"""
        self.canvas.delete("all")

        px, py = self.player_pos
        vision_range = self.visibility_radius

        # Extend vision if flashlight is active
        if self.has_flashlight and self.flashlight_start:
            elapsed = time.time() - self.flashlight_start
            if elapsed < self.flashlight_duration:
                vision_range = 8
            else:
                self.has_flashlight = False
                self.flashlight_start = None

        for y in range(self.height):
            for x in range(self.width):
                # Calculate distance from player
                distance = math.sqrt((x - px) ** 2 + (y - py) ** 2)

                x1, y1 = x * self.cell_size, y * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size

                if distance <= vision_range:
                    if self.maze[y][x] == 1:  # Wall
                        self.canvas.create_rectangle(
                            x1, y1, x2, y2, fill="#444444", outline="#666666"
                        )
                    else:  # Path
                        self.canvas.create_rectangle(
                            x1, y1, x2, y2, fill="#f0f0f0", outline="#cccccc"
                        )
                else:
                    # Outside vision - pure black
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2, fill="black", outline="black"
                    )

        # Draw visible special items
        px, py = self.player_pos

        # Draw keys
        for kx, ky in self.keys:
            if math.sqrt((kx - px) ** 2 + (ky - py) ** 2) <= vision_range:
                x1, y1 = kx * self.cell_size + 4, ky * self.cell_size + 4
                x2, y2 = x1 + self.cell_size - 8, y1 + self.cell_size - 8
                self.canvas.create_oval(x1, y1, x2, y2, fill="gold", outline="orange")
                # Key symbol
                self.canvas.create_text(
                    kx * self.cell_size + self.cell_size // 2,
                    ky * self.cell_size + self.cell_size // 2,
                    text="🗝",
                    font=("Arial", 8),
                )

        # Draw teleporters
        for pos1, pos2 in self.teleporters:
            for tx, ty in [pos1, pos2]:
                if math.sqrt((tx - px) ** 2 + (ty - py) ** 2) <= vision_range:
                    x1, y1 = tx * self.cell_size + 2, ty * self.cell_size + 2
                    x2, y2 = x1 + self.cell_size - 4, y1 + self.cell_size - 4
                    self.canvas.create_oval(
                        x1, y1, x2, y2, fill="purple", outline="magenta"
                    )
                    self.canvas.create_text(
                        tx * self.cell_size + self.cell_size // 2,
                        ty * self.cell_size + self.cell_size // 2,
                        text="◉",
                        fill="white",
                        font=("Arial", 8),
                    )

        # Draw enemy
        if self.enemy_pos:
            ex, ey = self.enemy_pos
            if math.sqrt((ex - px) ** 2 + (ey - py) ** 2) <= vision_range:
                x1, y1 = ex * self.cell_size + 1, ey * self.cell_size + 1
                x2, y2 = x1 + self.cell_size - 2, y1 + self.cell_size - 2
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill="red", outline="darkred"
                )
                self.canvas.create_text(
                    ex * self.cell_size + self.cell_size // 2,
                    ey * self.cell_size + self.cell_size // 2,
                    text="👹",
                    font=("Arial", 10),
                )

        # Draw start position (only if visible)
        if math.sqrt((1 - px) ** 2 + (1 - py) ** 2) <= vision_range:
            x1, y1 = 1 * self.cell_size + 2, 1 * self.cell_size + 2
            x2, y2 = x1 + self.cell_size - 4, y1 + self.cell_size - 4
            self.canvas.create_rectangle(
                x1, y1, x2, y2, fill="lightgreen", outline="green"
            )

        # Draw end position (only if visible and all keys collected)
        end_x, end_y = self.end_pos
        if math.sqrt((end_x - px) ** 2 + (end_y - py) ** 2) <= vision_range:
            x1, y1 = end_x * self.cell_size + 2, end_y * self.cell_size + 2
            x2, y2 = x1 + self.cell_size - 4, y1 + self.cell_size - 4
            if self.keys_collected >= self.required_keys:
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill="lightcoral", outline="red"
                )
                self.canvas.create_text(
                    end_x * self.cell_size + self.cell_size // 2,
                    end_y * self.cell_size + self.cell_size // 2,
                    text="🚪",
                    font=("Arial", 12),
                )
            else:
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill="gray", outline="darkgray"
                )
                self.canvas.create_text(
                    end_x * self.cell_size + self.cell_size // 2,
                    end_y * self.cell_size + self.cell_size // 2,
                    text="🔒",
                    font=("Arial", 12),
                )

        # Draw player
        self.draw_player()

    def draw_player(self):
        """Draw player at current position"""
        self.canvas.delete("player")
        px, py = self.player_pos
        center_x = px * self.cell_size + self.cell_size // 2
        center_y = py * self.cell_size + self.cell_size // 2
        radius = self.cell_size // 3

        self.canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            fill="blue",
            outline="darkblue",
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
            self.canvas.delete("solution")

            for i in range(len(path) - 1):
                x1, y1 = path[i]
                x2, y2 = path[i + 1]

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
                    width=3,
                    tags="solution",
                )

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
        comparison_window.geometry("500x300")

        text_widget = tk.Text(comparison_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, comparison_text)
        text_widget.config(state=tk.DISABLED)

        # Add explanations
        explanations = """

Algorithm Explanations:
• BFS: Breadth-First Search - Guarantees shortest path, explores level by level
• UCS: Uniform-Cost Search - Like BFS but for weighted graphs (same as BFS here)
• DFS: Depth-First Search - Goes deep first, may not find shortest path
• DLS: Depth-Limited Search - DFS with depth limit to avoid infinite paths
• IDS: Iterative Deepening Search - Combines BFS optimality with DFS memory efficiency
• Bidirectional: Searches from both start and end simultaneously
"""
        text_widget.config(state=tk.NORMAL)
        text_widget.insert(tk.END, explanations)
        text_widget.config(state=tk.DISABLED)

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

        # Check if it's the enemy position (optional - you might want to allow this)
        # if [x, y] == self.enemy_pos:
        #     return False

        return True

    def find_path_bfs(self, start, end):
        """Breadth-First Search - Guarantees shortest path, avoiding traps"""
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
        """Generate a new maze and reset everything"""
        self.generate_maze()
        self.reset_game()

    def reset_game(self):
        """Reset the game to initial state"""
        self.player_pos = [1, 1]
        self.moves_count = 0
        self.keys_collected = 0
        self.has_flashlight = False
        self.flashlight_start = None
        self.setup_difficulty_features()
        self.start_time = time.time()
        self.draw_maze()

    def run(self):
        """Start the game"""
        print("HARD Maze Game - Survival Mode with Multiple Search Algorithms")
        print("Controls:")
        print("- WASD/Arrow keys: Move")
        print("- F: Activate flashlight (30s)")
        print("- S: Show solution path")
        print("- C: Compare all algorithms")
        print("- H: Get hint (costs 10 moves)")
        print("- Goal: Collect all 3 keys and reach the exit!")
        print("- Avoid traps (invisible) and the red enemy!")
        print("- Purple circles are teleporters")
        print("- You have limited time and moves!")
        self.root.mainloop()


if __name__ == "__main__":
    game = HardMazeGame(width=35, height=35)
    game.run()
