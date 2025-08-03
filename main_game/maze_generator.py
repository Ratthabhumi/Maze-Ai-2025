# maze_generator.py
"""Maze generation and setup functionality"""

import random
from config import GameConfig


class MazeGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def generate_maze(self):
        """Generate a complex maze with multiple paths and dead ends"""
        maze = [[1 for _ in range(self.width)] for _ in range(self.height)]

        # Create main path using recursive backtracking
        stack = []
        start_x, start_y = 1, 1
        maze[start_y][start_x] = 0
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
                    and maze[ny][nx] == 1
                ):
                    neighbors.append((nx, ny, dx // 2, dy // 2))

            if neighbors:
                nx, ny, wall_x, wall_y = random.choice(neighbors)
                maze[current_y + wall_y][current_x + wall_x] = 0
                maze[ny][nx] = 0
                stack.append((nx, ny))
            else:
                stack.pop()

        # Add extra connections to create loops (makes it harder)
        for _ in range(self.width // 2):
            x = random.randrange(1, self.width - 1, 2)
            y = random.randrange(1, self.height - 1, 2)
            if maze[y][x] == 0:
                # Try to break a wall to create a loop
                for dx, dy in GameConfig.DIRECTIONS:
                    nx, ny = x + dx, y + dy
                    if (
                        0 < nx < self.width - 1
                        and 0 < ny < self.height - 1
                        and maze[ny][nx] == 1
                        and random.random() < 0.3
                    ):
                        maze[ny][nx] = 0
                        break

        # Ensure start and end are clear
        maze[1][1] = 0
        maze[self.height - 2][self.width - 2] = 0

        return maze

    def get_empty_spaces(self, maze, exclude_positions=None):
        """Get all empty spaces in the maze, excluding specified positions"""
        if exclude_positions is None:
            exclude_positions = [[1, 1], [self.width - 2, self.height - 2]]

        empty_spaces = []
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if maze[y][x] == 0 and [x, y] not in exclude_positions:
                    empty_spaces.append([x, y])
        return empty_spaces
