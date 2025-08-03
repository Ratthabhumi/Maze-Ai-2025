import tkinter as tk
from tkinter import messagebox
import time

# Import your separated modules
from config import GameConfig
from game_objects import GameObjects
from maze_generator import MazeGenerator
from path_finding import PathFinder
from renderer import MazeRenderer  # This will be our enhanced renderer


class HardMazeGame:
    def __init__(self, width=35, height=35):
        # Initialize core game properties
        self.width = width
        self.height = height
        self.cell_size = GameConfig.CELL_SIZE

        # Initialize game modules
        self.maze_generator = MazeGenerator(width, height)
        self.path_finder = PathFinder()
        self.game_objects = GameObjects(width, height)

        # Game state
        self.maze = []
        self.start_time = None
        self.moves_count = 0
        self.max_moves = None

        # Create the main window
        self.root = tk.Tk()
        self.root.title("HARD Maze Game - Survival Mode with Dynamic Zoom")
        self.root.geometry("800x900")

        # Create canvas
        canvas_width = 600  # Fixed canvas size
        canvas_height = 600

        self.canvas = tk.Canvas(
            self.root,
            width=canvas_width,
            height=canvas_height,
            bg="black",
        )
        self.canvas.pack()

        # Initialize renderer with enhanced zoom system
        self.renderer = MazeRenderer(
            self.canvas, self.width, self.height, self.cell_size
        )

        # Update renderer with actual canvas dimensions
        self.canvas.update()
        self.renderer.get_canvas_dimensions()

        # Create UI
        self.create_ui()

        # Bind keyboard events
        self.root.bind("<Key>", self.on_key_press)
        self.root.focus_set()

        # Initialize game
        self.generate_maze()
        self.setup_difficulty_features()
        self.start_time = time.time()
        self.draw_maze()
        self.update_info()
        self.game_loop()

    def create_ui(self):
        """Create the user interface"""
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
            right_info,
            text="M: Map | S: Solve | C: Compare",
            font=("Arial", 8),
            fg="orange",
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

        # Map and solver controls
        self.map_button = tk.Button(
            button_frame,
            text="📍 Full Map (M)",
            command=self.toggle_map_view,
            font=("Arial", 8),
            bg="lightblue",
        )
        self.map_button.pack(side=tk.LEFT, padx=2)

        tk.Button(
            button_frame,
            text="🔍 SOLVE (S)",
            command=self.show_solution,
            font=("Arial", 8),
            bg="lightgreen",
        ).pack(side=tk.LEFT, padx=2)

        # Algorithm selector
        tk.Label(button_frame, text="Algo:", font=("Arial", 8)).pack(
            side=tk.LEFT, padx=(10, 2)
        )
        self.solver_var = tk.StringVar(value="BFS")
        solver_options = ["BFS", "UCS", "DFS", "DLS", "IDS", "Bidirectional"]
        self.solver_menu = tk.OptionMenu(button_frame, self.solver_var, *solver_options)
        self.solver_menu.config(font=("Arial", 7), width=8)
        self.solver_menu.pack(side=tk.LEFT, padx=2)

        tk.Button(
            button_frame,
            text="Compare (C)",
            command=self.compare_algorithms,
            font=("Arial", 8),
        ).pack(side=tk.LEFT, padx=2)

    def generate_maze(self):
        """Generate a new maze"""
        self.maze = self.maze_generator.generate_maze()

    def setup_difficulty_features(self):
        """Set up game objects and difficulty features"""
        self.game_objects.setup_objects(self.maze)

        # Set move limit based on optimal path + buffer
        optimal_path, _, _ = self.path_finder.find_path(
            self.game_objects.player_pos, self.game_objects.end_pos, "BFS", self.maze
        )
        if optimal_path:
            self.max_moves = len(optimal_path) * 3

    def draw_maze(self):
        """Draw the maze using the renderer"""
        self.renderer.draw_maze(
            self.maze,
            self.game_objects.player_pos,
            self.game_objects.visibility_radius,
            self.game_objects.map_revealed,
            self.game_objects.has_flashlight,
            self.game_objects.flashlight_start,
            GameConfig.FLASHLIGHT_DURATION,
            self.game_objects.keys,
            self.game_objects.teleporters,
            self.game_objects.traps,
            self.game_objects.enemy_pos,
            self.game_objects.end_pos,
            self.game_objects.keys_collected,
            GameConfig.REQUIRED_KEYS,
        )

    def on_key_press(self, event):
        """Handle keyboard input"""
        if not self.start_time:
            return

        key = event.keysym.lower()
        new_x, new_y = self.game_objects.player_pos

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
            self.game_objects.activate_flashlight()
            self.draw_maze()
            return
        elif key == "m":  # Toggle map view
            self.toggle_map_view()
            return
        elif key == "s" and event.state == 0:  # S key for solver
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
            # Update player position
            self.game_objects.player_pos = [new_x, new_y]
            self.moves_count += 1

            # Handle game events
            event_result = self.game_objects.handle_player_move(self.maze)

            if event_result == "trap":
                messagebox.showwarning("Trap!", "You stepped on a trap! Game Over!")
                self.reset_game()
                return
            elif event_result == "enemy":
                messagebox.showwarning("Caught!", "The enemy caught you! Game Over!")
                self.reset_game()
                return
            elif event_result.startswith("key"):
                messagebox.showinfo("Key Found!", event_result)
            elif event_result.startswith("teleport"):
                messagebox.showinfo("Teleported!", "You've been teleported!")

            self.draw_maze()

            # Check win condition
            if (
                self.game_objects.player_pos == self.game_objects.end_pos
                and self.game_objects.keys_collected >= GameConfig.REQUIRED_KEYS
            ):
                elapsed_time = time.time() - self.start_time
                messagebox.showinfo(
                    "Victory!",
                    f"Congratulations! You escaped!\nTime: {elapsed_time:.1f}s\nMoves: {self.moves_count}",
                )
                self.start_time = None

    def toggle_map_view(self):
        """Toggle between zoomed gameplay and full map view"""
        is_full_map = self.renderer.toggle_view_mode()

        # Update button text based on current view
        if is_full_map:
            self.map_button.config(text="🔍 Zoom In (M)", bg="lightcoral")
            # Automatically reveal map when switching to full view
            self.game_objects.map_revealed = True
            messagebox.showinfo(
                "Full Map View",
                "🗺️ FULL MAP VIEW ACTIVATED!\n\n"
                "• Entire maze visible with all elements\n"
                "• Red ⚠ squares are deadly traps!\n"
                "• Purple ◉ are teleporters\n"
                "• Gold 🗝 are keys to collect\n"
                "• Red 👹 is the moving enemy\n"
                "• Solution paths will show here\n"
                "• Press M again to return to zoomed gameplay",
            )
        else:
            self.map_button.config(text="📍 Full Map (M)", bg="lightblue")
            # Return to limited vision for gameplay
            self.game_objects.map_revealed = False
            messagebox.showinfo("Zoomed View", "Returned to zoomed gameplay mode")

        # Clear any existing solution when changing views
        self.renderer.clear_solution()
        self.draw_maze()

    def show_solution(self):
        """Show the solution path - only works in full map view"""
        if not self.renderer.is_full_map_view:
            messagebox.showinfo(
                "Solution Display",
                "🗺️ Switch to Full Map view (press M) to see solution paths!\n\n"
                "Solution visualization is only available in full map mode.",
            )
            return

        algorithm = self.solver_var.get()
        start_pos = self.game_objects.player_pos[:]

        # Find target (key or exit)
        if (
            self.game_objects.keys_collected < GameConfig.REQUIRED_KEYS
            and self.game_objects.keys
        ):
            target = min(
                self.game_objects.keys,
                key=lambda k: abs(k[0] - start_pos[0]) + abs(k[1] - start_pos[1]),
            )
            target_name = "nearest key"
        else:
            target = self.game_objects.end_pos
            target_name = "exit"

        # Get solution path
        path, nodes_explored, search_time = self.path_finder.find_path(
            start_pos, target, algorithm, self.maze
        )

        # Redraw maze (should be in full map view)
        self.draw_maze()

        if path:
            # Draw solution path
            self.renderer.draw_solution_path(path)

            # Show solution info
            messagebox.showinfo(
                "🔍 SOLUTION FOUND!",
                f"🎯 Target: {target_name.title()}\n"
                f"🧠 Algorithm: {algorithm}\n"
                f"📏 Path Length: {len(path)} steps\n"
                f"🔍 Nodes Explored: {nodes_explored}\n"
                f"⏱️ Search Time: {search_time:.4f}s\n\n"
                f"🟠 Orange line shows the optimal path\n"
                f"→ Red arrows show direction\n"
                f"🟢 Green circle marks start\n"
                f"🔴 Red circle marks destination",
            )
        else:
            messagebox.showwarning(
                "❌ No Solution", f"No path found using {algorithm}!"
            )

    def compare_algorithms(self):
        """Compare all search algorithms"""
        algorithms = ["BFS", "UCS", "DFS", "DLS", "IDS", "Bidirectional"]
        start_pos = self.game_objects.player_pos[:]
        end_pos = self.game_objects.end_pos[:]

        # If player needs keys, compare paths to nearest key
        if (
            self.game_objects.keys_collected < GameConfig.REQUIRED_KEYS
            and self.game_objects.keys
        ):
            end_pos = min(
                self.game_objects.keys,
                key=lambda k: abs(k[0] - start_pos[0]) + abs(k[1] - start_pos[1]),
            )

        results = []
        for algorithm in algorithms:
            try:
                path, nodes_explored, search_time = self.path_finder.find_path(
                    start_pos, end_pos, algorithm, self.maze
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

        # Create comparison window
        comparison_window = tk.Toplevel(self.root)
        comparison_window.title("Search Algorithm Comparison")
        comparison_window.geometry("500x300")

        text_widget = tk.Text(comparison_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, comparison_text)
        text_widget.config(state=tk.DISABLED)

    def show_hint(self):
        """Show a hint at the cost of moves"""
        if self.moves_count + 10 > self.max_moves:
            messagebox.showwarning(
                "Not enough moves!", "You don't have enough moves left for a hint!"
            )
            return

        self.moves_count += 10

        # Find direction to target
        target = None
        if self.game_objects.keys:
            target = min(
                self.game_objects.keys,
                key=lambda k: abs(k[0] - self.game_objects.player_pos[0])
                + abs(k[1] - self.game_objects.player_pos[1]),
            )
        elif self.game_objects.keys_collected >= GameConfig.REQUIRED_KEYS:
            target = self.game_objects.end_pos

        if target:
            dx = target[0] - self.game_objects.player_pos[0]
            dy = target[1] - self.game_objects.player_pos[1]

            if abs(dx) > abs(dy):
                direction = "RIGHT" if dx > 0 else "LEFT"
            else:
                direction = "DOWN" if dy > 0 else "UP"

            messagebox.showinfo("Hint", f"Try going {direction}!")

    def update_info(self):
        """Update the information display"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            remaining = max(0, GameConfig.TIME_LIMIT - elapsed)
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

        self.keys_label.config(
            text=f"Keys: {self.game_objects.keys_collected}/{GameConfig.REQUIRED_KEYS}"
        )

        # Flashlight status - pass current time as argument
        current_time = time.time()
        flashlight_remaining = self.game_objects.get_flashlight_remaining(current_time)
        if flashlight_remaining > 0:
            self.flashlight_label.config(
                text=f"F: Flash {flashlight_remaining/1000:.1f}s",
                fg="yellow",  # Convert ms to seconds
            )
        else:
            self.flashlight_label.config(text="F: Flashlight", fg="gray")

    def game_loop(self):
        """Main game loop"""
        if self.start_time:
            self.game_objects.move_enemy()
            self.update_info()
            if self.game_objects.player_pos == self.game_objects.enemy_pos:
                messagebox.showwarning("Caught!", "The enemy caught you! Game Over!")
                self.reset_game()
                return

        self.root.after(200, self.game_loop)

    def generate_new_maze(self):
        """Generate a new maze and reset everything"""
        self.generate_maze()
        self.reset_game()

    def reset_game(self):
        """Reset the game to initial state"""
        self.game_objects.reset()
        self.moves_count = 0
        self.setup_difficulty_features()
        self.start_time = time.time()

        # Clear any solution paths
        self.renderer.clear_solution()

        # Reset to zoomed view if in full map mode
        if self.renderer.is_full_map_view:
            self.renderer.toggle_view_mode()
            self.map_button.config(text="📍 Full Map (M)", bg="lightblue")
            self.game_objects.map_revealed = False

        self.draw_maze()

    def run(self):
        """Start the game"""
        print("HARD Maze Game - Survival Mode with Dynamic Zoom System")
        print("Controls:")
        print("- WASD/Arrow keys: Move")
        print("- F: Activate flashlight (30s)")
        print("- M: Toggle between zoomed gameplay and full map view")
        print("- S: Show solution path (full map view only)")
        print("- C: Compare all algorithms")
        print("- H: Get hint (costs 10 moves)")
        print("- Goal: Collect all 3 keys and reach the exit!")
        print("- Avoid traps (invisible) and the red enemy!")
        print("- Purple circles are teleporters")
        print("- You have limited time and moves!")
        print("\nZoom System:")
        print("- Default: Zoomed in view for gameplay")
        print("- Press M: Switch to full map view to see everything")
        print("- Solution paths only visible in full map view")
        self.root.mainloop()


if __name__ == "__main__":
    game = HardMazeGame(width=35, height=35)
    game.run()
