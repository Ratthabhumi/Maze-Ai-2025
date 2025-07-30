import tkinter as tk
from tkinter import messagebox
import random
from collections import deque


class MazeGame:
    def __init__(self, width=25, height=25):
        self.width = width
        self.height = height
        self.cell_size = 20
        self.maze = []
        self.player_pos = [1, 1]  # Starting position
        self.end_pos = [width - 2, height - 2]  # End position

        # Create the main window
        self.root = tk.Tk()
        self.root.title("Maze Game")
        self.root.resizable(False, False)

        # Create canvas
        canvas_width = self.width * self.cell_size
        canvas_height = self.height * self.cell_size + 60  # Extra space for buttons

        self.canvas = tk.Canvas(
            self.root,
            width=canvas_width,
            height=canvas_height,
            bg='white'
        )
        self.canvas.pack()

        # Create control buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="New Maze", command=self.generate_new_maze).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Reset Player", command=self.reset_player).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Solve", command=self.show_solution).pack(side=tk.LEFT, padx=5)

        # Bind keyboard events
        self.root.bind('<Key>', self.on_key_press)
        self.root.focus_set()

        # Generate initial maze
        self.generate_maze()
        self.draw_maze()

    def generate_maze(self):
        """Generate maze using recursive backtracking algorithm"""
        # Initialize maze with walls (1) and paths (0)
        self.maze = [[1 for _ in range(self.width)] for _ in range(self.height)]

        # Stack for backtracking
        stack = []

        # Start from position (1,1)
        start_x, start_y = 1, 1
        self.maze[start_y][start_x] = 0
        stack.append((start_x, start_y))

        directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]  # Right, Down, Left, Up

        while stack:
            current_x, current_y = stack[-1]
            neighbors = []

            # Find unvisited neighbors
            for dx, dy in directions:
                nx, ny = current_x + dx, current_y + dy
                if (0 < nx < self.width - 1 and 0 < ny < self.height - 1 and
                        self.maze[ny][nx] == 1):
                    neighbors.append((nx, ny, dx // 2, dy // 2))

            if neighbors:
                # Choose random neighbor
                nx, ny, wall_x, wall_y = random.choice(neighbors)

                # Remove wall between current cell and chosen neighbor
                self.maze[current_y + wall_y][current_x + wall_x] = 0
                self.maze[ny][nx] = 0

                stack.append((nx, ny))
            else:
                stack.pop()

        # Ensure start and end positions are clear
        self.maze[1][1] = 0  # Start
        self.maze[self.height - 2][self.width - 2] = 0  # End

    def draw_maze(self):
        """Draw the maze on canvas"""
        self.canvas.delete("all")

        for y in range(self.height):
            for x in range(self.width):
                x1, y1 = x * self.cell_size, y * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size

                if self.maze[y][x] == 1:  # Wall
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill='black', outline='black')
                else:  # Path
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill='white', outline='lightgray')

        # Draw start position (green)
        start_x, start_y = 1, 1
        x1, y1 = start_x * self.cell_size + 2, start_y * self.cell_size + 2
        x2, y2 = x1 + self.cell_size - 4, y1 + self.cell_size - 4
        self.canvas.create_rectangle(x1, y1, x2, y2, fill='lightgreen', outline='green')

        # Draw end position (red)
        end_x, end_y = self.end_pos
        x1, y1 = end_x * self.cell_size + 2, end_y * self.cell_size + 2
        x2, y2 = x1 + self.cell_size - 4, y1 + self.cell_size - 4
        self.canvas.create_rectangle(x1, y1, x2, y2, fill='lightcoral', outline='red')

        # Draw player (blue circle)
        self.draw_player()

    def draw_player(self):
        """Draw player at current position"""
        self.canvas.delete("player")
        px, py = self.player_pos
        center_x = px * self.cell_size + self.cell_size // 2
        center_y = py * self.cell_size + self.cell_size // 2
        radius = self.cell_size // 3

        self.canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            fill='blue', outline='darkblue', tags="player"
        )

    def on_key_press(self, event):
        """Handle keyboard input for player movement"""
        key = event.keysym.lower()

        new_x, new_y = self.player_pos

        if key == 'up' or key == 'w':
            new_y -= 1
        elif key == 'down' or key == 's':
            new_y += 1
        elif key == 'left' or key == 'a':
            new_x -= 1
        elif key == 'right' or key == 'd':
            new_x += 1
        else:
            return

        # Check if move is valid
        if (0 <= new_x < self.width and 0 <= new_y < self.height and
                self.maze[new_y][new_x] == 0):
            self.player_pos = [new_x, new_y]
            self.draw_player()

            # Check if player reached the end
            if self.player_pos == self.end_pos:
                messagebox.showinfo("Congratulations!", "You solved the maze!")

    def generate_new_maze(self):
        """Generate a new random maze"""
        self.generate_maze()
        self.reset_player()
        self.draw_maze()

    def reset_player(self):
        """Reset player to starting position"""
        self.player_pos = [1, 1]
        self.draw_player()

    def find_path(self, start, end):
        """Use BFS to find path from start to end"""
        queue = deque([(start, [start])])
        visited = set([tuple(start)])

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        while queue:
            (x, y), path = queue.popleft()

            if [x, y] == end:
                return path

            for dx, dy in directions:
                nx, ny = x + dx, y + dy

                if (0 <= nx < self.width and 0 <= ny < self.height and
                        self.maze[ny][nx] == 0 and (nx, ny) not in visited):
                    visited.add((nx, ny))
                    queue.append(([nx, ny], path + [[nx, ny]]))

        return None

    def show_solution(self):
        """Show the solution path"""
        path = self.find_path([1, 1], self.end_pos)

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
                    center1_x, center1_y, center2_x, center2_y,
                    fill='orange', width=3, tags="solution"
                )
        else:
            messagebox.showwarning("No Solution", "No path found!")

    def run(self):
        """Start the game"""
        self.root.mainloop()


if __name__ == "__main__":
    # Create and run the maze game
    game = MazeGame(width=31, height=31)  # Odd numbers work better for maze generation

    print("Maze Game Controls:")
    print("- Use arrow keys or WASD to move")
    print("- 'New Maze' button to generate a new maze")
    print("- 'Reset Player' button to return to start")
    print("- 'Solve' button to show the solution path")
    print("- Goal: Reach the red square!")

    game.run()