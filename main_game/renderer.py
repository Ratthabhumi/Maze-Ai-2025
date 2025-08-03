import math
import tkinter as tk


class MazeRenderer:
    def __init__(self, canvas, width, height, cell_size):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.original_cell_size = cell_size
        self.cell_size = cell_size

        # Camera/viewport for zoomed gameplay
        self.camera_x = 0
        self.camera_y = 0
        self.zoom_factor = 2.0  # 2x zoom for gameplay

        # View modes
        self.is_full_map_view = False
        self.canvas_width = canvas.winfo_reqwidth()
        self.canvas_height = canvas.winfo_reqheight()

    def toggle_view_mode(self):
        """Toggle between zoomed gameplay and full map view"""
        self.is_full_map_view = not self.is_full_map_view

        if self.is_full_map_view:
            # Calculate cell size to fit entire maze in canvas
            max_cell_width = self.canvas_width // self.width
            max_cell_height = self.canvas_height // self.height
            self.cell_size = min(
                max_cell_width, max_cell_height, self.original_cell_size
            )
        else:
            # Return to original cell size for zoomed gameplay
            self.cell_size = self.original_cell_size

        return self.is_full_map_view

    def draw_maze(
        self,
        maze,
        player_pos,
        visibility_radius,
        map_revealed,
        has_flashlight,
        flashlight_start,
        flashlight_duration,
        keys,
        teleporters,
        traps,
        enemy_pos,
        end_pos,
        keys_collected,
        required_keys,
    ):
        """Draw the maze with dynamic zoom system"""
        self.canvas.delete("all")

        px, py = player_pos
        vision_range = visibility_radius

        # Extend vision if flashlight is active
        if has_flashlight and flashlight_start:
            import time

            elapsed = time.time() - flashlight_start
            if elapsed < flashlight_duration:
                vision_range = 8

        if self.is_full_map_view:
            # Full map view - show everything
            self._draw_full_map(
                maze,
                player_pos,
                keys,
                teleporters,
                traps,
                enemy_pos,
                end_pos,
                keys_collected,
                required_keys,
            )
        else:
            # Zoomed gameplay view
            self._draw_zoomed_view(
                maze,
                player_pos,
                vision_range,
                map_revealed,
                keys,
                teleporters,
                traps,
                enemy_pos,
                end_pos,
                keys_collected,
                required_keys,
            )

    def _draw_full_map(
        self,
        maze,
        player_pos,
        keys,
        teleporters,
        traps,
        enemy_pos,
        end_pos,
        keys_collected,
        required_keys,
    ):
        """Draw the complete maze in full map view"""
        px, py = player_pos

        # Calculate offset to center the maze in canvas
        maze_width = self.width * self.cell_size
        maze_height = self.height * self.cell_size
        offset_x = (self.canvas_width - maze_width) // 2
        offset_y = (self.canvas_height - maze_height) // 2

        # Draw all maze cells
        for y in range(self.height):
            for x in range(self.width):
                screen_x = offset_x + x * self.cell_size
                screen_y = offset_y + y * self.cell_size
                x1, y1 = screen_x, screen_y
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size

                if maze[y][x] == 1:  # Wall
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2, fill="#666666", outline="#888888"
                    )
                else:  # Path
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2, fill="#e8e8e8", outline="#d0d0d0"
                    )

        # Draw all special items in full map view
        self._draw_special_items_full_map(
            offset_x,
            offset_y,
            keys,
            teleporters,
            traps,
            enemy_pos,
            end_pos,
            keys_collected,
            required_keys,
        )

        # Draw player
        self._draw_player_full_map(player_pos, offset_x, offset_y)

    def _draw_zoomed_view(
        self,
        maze,
        player_pos,
        vision_range,
        map_revealed,
        keys,
        teleporters,
        traps,
        enemy_pos,
        end_pos,
        keys_collected,
        required_keys,
    ):
        """Draw the zoomed gameplay view"""
        px, py = player_pos

        # Camera/viewport calculations for zoom
        viewport_width = int(self.canvas_width / (self.cell_size * self.zoom_factor))
        viewport_height = int(self.canvas_height / (self.cell_size * self.zoom_factor))

        # Center camera on player
        self.camera_x = max(
            0, min(self.width - viewport_width, px - viewport_width // 2)
        )
        self.camera_y = max(
            0, min(self.height - viewport_height, py - viewport_height // 2)
        )

        # Draw the maze based on visibility mode and camera viewport
        for y in range(
            self.camera_y, min(self.camera_y + viewport_height, self.height)
        ):
            for x in range(
                self.camera_x, min(self.camera_x + viewport_width, self.width)
            ):
                # Calculate screen coordinates
                screen_x = (x - self.camera_x) * self.cell_size
                screen_y = (y - self.camera_y) * self.cell_size
                x1, y1 = screen_x, screen_y
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size

                # Check if cell should be visible
                distance = math.sqrt((x - px) ** 2 + (y - py) ** 2)
                is_visible = map_revealed or distance <= vision_range

                if is_visible:
                    if maze[y][x] == 1:  # Wall
                        color = "#444444" if not map_revealed else "#666666"
                        outline = "#666666" if not map_revealed else "#888888"
                        self.canvas.create_rectangle(
                            x1, y1, x2, y2, fill=color, outline=outline
                        )
                    else:  # Path
                        color = "#f0f0f0" if not map_revealed else "#e8e8e8"
                        outline = "#cccccc" if not map_revealed else "#d0d0d0"
                        self.canvas.create_rectangle(
                            x1, y1, x2, y2, fill=color, outline=outline
                        )
                else:
                    # Outside vision - pure black
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2, fill="black", outline="black"
                    )

        # Draw visible special items in zoomed view
        self._draw_special_items_zoomed(
            px,
            py,
            vision_range,
            map_revealed,
            keys,
            teleporters,
            traps,
            enemy_pos,
            end_pos,
            keys_collected,
            required_keys,
        )

        # Draw player
        self._draw_player_zoomed(player_pos)

    def _draw_special_items_full_map(
        self,
        offset_x,
        offset_y,
        keys,
        teleporters,
        traps,
        enemy_pos,
        end_pos,
        keys_collected,
        required_keys,
    ):
        """Draw all special items in full map view"""

        # Draw keys
        for kx, ky in keys:
            screen_x = offset_x + kx * self.cell_size
            screen_y = offset_y + ky * self.cell_size
            x1, y1 = screen_x + 2, screen_y + 2
            x2, y2 = x1 + self.cell_size - 4, y1 + self.cell_size - 4
            self.canvas.create_oval(x1, y1, x2, y2, fill="gold", outline="orange")

            # Adjust font size for smaller cells
            font_size = max(6, self.cell_size // 5)
            self.canvas.create_text(
                screen_x + self.cell_size // 2,
                screen_y + self.cell_size // 2,
                text="🗝",
                font=("Arial", font_size),
            )

        # Draw teleporters
        for pos1, pos2 in teleporters:
            for tx, ty in [pos1, pos2]:
                screen_x = offset_x + tx * self.cell_size
                screen_y = offset_y + ty * self.cell_size
                x1, y1 = screen_x + 1, screen_y + 1
                x2, y2 = x1 + self.cell_size - 2, y1 + self.cell_size - 2
                self.canvas.create_oval(
                    x1, y1, x2, y2, fill="purple", outline="magenta"
                )

                font_size = max(6, self.cell_size // 5)
                self.canvas.create_text(
                    screen_x + self.cell_size // 2,
                    screen_y + self.cell_size // 2,
                    text="◉",
                    fill="white",
                    font=("Arial", font_size),
                )

        # Draw traps (always visible in full map view)
        for trap_x, trap_y in traps:
            screen_x = offset_x + trap_x * self.cell_size
            screen_y = offset_y + trap_y * self.cell_size
            x1, y1 = screen_x + 1, screen_y + 1
            x2, y2 = x1 + self.cell_size - 2, y1 + self.cell_size - 2
            self.canvas.create_rectangle(
                x1, y1, x2, y2, fill="darkred", outline="red", stipple="gray50"
            )

            font_size = max(6, self.cell_size // 5)
            self.canvas.create_text(
                screen_x + self.cell_size // 2,
                screen_y + self.cell_size // 2,
                text="⚠",
                fill="red",
                font=("Arial", font_size),
            )

        # Draw enemy
        if enemy_pos:
            ex, ey = enemy_pos
            screen_x = offset_x + ex * self.cell_size
            screen_y = offset_y + ey * self.cell_size
            x1, y1 = screen_x + 1, screen_y + 1
            x2, y2 = x1 + self.cell_size - 2, y1 + self.cell_size - 2
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="red", outline="darkred")

            font_size = max(8, self.cell_size // 4)
            self.canvas.create_text(
                screen_x + self.cell_size // 2,
                screen_y + self.cell_size // 2,
                text="👹",
                font=("Arial", font_size),
            )

        # Draw start position
        screen_x = offset_x + 1 * self.cell_size
        screen_y = offset_y + 1 * self.cell_size
        x1, y1 = screen_x + 1, screen_y + 1
        x2, y2 = x1 + self.cell_size - 2, y1 + self.cell_size - 2
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="lightgreen", outline="green")

        font_size = max(4, self.cell_size // 8)
        self.canvas.create_text(
            screen_x + self.cell_size // 2,
            screen_y + self.cell_size // 2,
            text="START",
            fill="darkgreen",
            font=("Arial", font_size),
        )

        # Draw end position
        end_x, end_y = end_pos
        screen_x = offset_x + end_x * self.cell_size
        screen_y = offset_y + end_y * self.cell_size
        x1, y1 = screen_x + 1, screen_y + 1
        x2, y2 = x1 + self.cell_size - 2, y1 + self.cell_size - 2

        font_size = max(4, self.cell_size // 8)
        if keys_collected >= required_keys:
            self.canvas.create_rectangle(
                x1, y1, x2, y2, fill="lightcoral", outline="red"
            )
            self.canvas.create_text(
                screen_x + self.cell_size // 2,
                screen_y + self.cell_size // 2,
                text="EXIT",
                fill="darkred",
                font=("Arial", font_size),
            )
        else:
            self.canvas.create_rectangle(
                x1, y1, x2, y2, fill="gray", outline="darkgray"
            )
            self.canvas.create_text(
                screen_x + self.cell_size // 2,
                screen_y + self.cell_size // 2,
                text="LOCKED",
                fill="white",
                font=("Arial", font_size),
            )

    def _draw_special_items_zoomed(
        self,
        px,
        py,
        vision_range,
        map_revealed,
        keys,
        teleporters,
        traps,
        enemy_pos,
        end_pos,
        keys_collected,
        required_keys,
    ):
        """Draw keys, teleporters, enemy, and other special items with zoom"""

        # Draw keys
        for kx, ky in keys:
            # Check if key is in viewport
            if self.camera_x <= kx < self.camera_x + int(
                self.canvas_width / (self.cell_size * self.zoom_factor)
            ) and self.camera_y <= ky < self.camera_y + int(
                self.canvas_height / (self.cell_size * self.zoom_factor)
            ):

                distance = math.sqrt((kx - px) ** 2 + (ky - py) ** 2)
                if map_revealed or distance <= vision_range:
                    screen_x = (kx - self.camera_x) * self.cell_size
                    screen_y = (ky - self.camera_y) * self.cell_size
                    x1, y1 = screen_x + 4, screen_y + 4
                    x2, y2 = x1 + self.cell_size - 8, y1 + self.cell_size - 8
                    self.canvas.create_oval(
                        x1, y1, x2, y2, fill="gold", outline="orange"
                    )
                    self.canvas.create_text(
                        screen_x + self.cell_size // 2,
                        screen_y + self.cell_size // 2,
                        text="🗝",
                        font=("Arial", 8),
                    )

        # Draw teleporters
        for pos1, pos2 in teleporters:
            for tx, ty in [pos1, pos2]:
                if self.camera_x <= tx < self.camera_x + int(
                    self.canvas_width / (self.cell_size * self.zoom_factor)
                ) and self.camera_y <= ty < self.camera_y + int(
                    self.canvas_height / (self.cell_size * self.zoom_factor)
                ):

                    distance = math.sqrt((tx - px) ** 2 + (ty - py) ** 2)
                    if map_revealed or distance <= vision_range:
                        screen_x = (tx - self.camera_x) * self.cell_size
                        screen_y = (ty - self.camera_y) * self.cell_size
                        x1, y1 = screen_x + 2, screen_y + 2
                        x2, y2 = x1 + self.cell_size - 4, y1 + self.cell_size - 4
                        self.canvas.create_oval(
                            x1, y1, x2, y2, fill="purple", outline="magenta"
                        )
                        self.canvas.create_text(
                            screen_x + self.cell_size // 2,
                            screen_y + self.cell_size // 2,
                            text="◉",
                            fill="white",
                            font=("Arial", 8),
                        )

        # Draw traps (only if map is revealed - they're normally invisible!)
        if map_revealed:
            for trap_x, trap_y in traps:
                if self.camera_x <= trap_x < self.camera_x + int(
                    self.canvas_width / (self.cell_size * self.zoom_factor)
                ) and self.camera_y <= trap_y < self.camera_y + int(
                    self.canvas_height / (self.cell_size * self.zoom_factor)
                ):

                    screen_x = (trap_x - self.camera_x) * self.cell_size
                    screen_y = (trap_y - self.camera_y) * self.cell_size
                    x1, y1 = screen_x + 3, screen_y + 3
                    x2, y2 = x1 + self.cell_size - 6, y1 + self.cell_size - 6
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2, fill="darkred", outline="red", stipple="gray50"
                    )
                    self.canvas.create_text(
                        screen_x + self.cell_size // 2,
                        screen_y + self.cell_size // 2,
                        text="⚠",
                        fill="red",
                        font=("Arial", 8),
                    )

        # Draw enemy
        if enemy_pos:
            ex, ey = enemy_pos
            if self.camera_x <= ex < self.camera_x + int(
                self.canvas_width / (self.cell_size * self.zoom_factor)
            ) and self.camera_y <= ey < self.camera_y + int(
                self.canvas_height / (self.cell_size * self.zoom_factor)
            ):

                distance = math.sqrt((ex - px) ** 2 + (ey - py) ** 2)
                if map_revealed or distance <= vision_range:
                    screen_x = (ex - self.camera_x) * self.cell_size
                    screen_y = (ey - self.camera_y) * self.cell_size
                    x1, y1 = screen_x + 1, screen_y + 1
                    x2, y2 = x1 + self.cell_size - 2, y1 + self.cell_size - 2
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2, fill="red", outline="darkred"
                    )
                    self.canvas.create_text(
                        screen_x + self.cell_size // 2,
                        screen_y + self.cell_size // 2,
                        text="👹",
                        font=("Arial", 10),
                    )

        # Draw start position
        if self.camera_x <= 1 < self.camera_x + int(
            self.canvas_width / (self.cell_size * self.zoom_factor)
        ) and self.camera_y <= 1 < self.camera_y + int(
            self.canvas_height / (self.cell_size * self.zoom_factor)
        ):

            distance = math.sqrt((1 - px) ** 2 + (1 - py) ** 2)
            if map_revealed or distance <= vision_range:
                screen_x = (1 - self.camera_x) * self.cell_size
                screen_y = (1 - self.camera_y) * self.cell_size
                x1, y1 = screen_x + 2, screen_y + 2
                x2, y2 = x1 + self.cell_size - 4, y1 + self.cell_size - 4
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill="lightgreen", outline="green"
                )
                self.canvas.create_text(
                    screen_x + self.cell_size // 2,
                    screen_y + self.cell_size // 2,
                    text="START",
                    fill="darkgreen",
                    font=("Arial", 6),
                )

        # Draw end position
        end_x, end_y = end_pos
        if self.camera_x <= end_x < self.camera_x + int(
            self.canvas_width / (self.cell_size * self.zoom_factor)
        ) and self.camera_y <= end_y < self.camera_y + int(
            self.canvas_height / (self.cell_size * self.zoom_factor)
        ):

            distance = math.sqrt((end_x - px) ** 2 + (end_y - py) ** 2)
            if map_revealed or distance <= vision_range:
                screen_x = (end_x - self.camera_x) * self.cell_size
                screen_y = (end_y - self.camera_y) * self.cell_size
                x1, y1 = screen_x + 2, screen_y + 2
                x2, y2 = x1 + self.cell_size - 4, y1 + self.cell_size - 4
                if keys_collected >= required_keys:
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2, fill="lightcoral", outline="red"
                    )
                    self.canvas.create_text(
                        screen_x + self.cell_size // 2,
                        screen_y + self.cell_size // 2,
                        text="EXIT",
                        fill="darkred",
                        font=("Arial", 6),
                    )
                else:
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2, fill="gray", outline="darkgray"
                    )
                    self.canvas.create_text(
                        screen_x + self.cell_size // 2,
                        screen_y + self.cell_size // 2,
                        text="LOCKED",
                        fill="white",
                        font=("Arial", 5),
                    )

    def _draw_player_zoomed(self, player_pos):
        """Draw player at current position with zoom"""
        self.canvas.delete("player")
        px, py = player_pos

        # Convert world coordinates to screen coordinates
        screen_x = (px - self.camera_x) * self.cell_size
        screen_y = (py - self.camera_y) * self.cell_size

        center_x = screen_x + self.cell_size // 2
        center_y = screen_y + self.cell_size // 2
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

    def _draw_player_full_map(self, player_pos, offset_x, offset_y):
        """Draw player in full map view"""
        self.canvas.delete("player")
        px, py = player_pos

        screen_x = offset_x + px * self.cell_size
        screen_y = offset_y + py * self.cell_size

        center_x = screen_x + self.cell_size // 2
        center_y = screen_y + self.cell_size // 2
        radius = max(2, self.cell_size // 3)

        self.canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            fill="blue",
            outline="darkblue",
            tags="player",
        )

    def draw_solution_path(self, path):
        """Draw the solution path - only visible in full map view"""
        if not path or not self.is_full_map_view:
            return

        # Clear previous solution
        self.canvas.delete("solution")
        self.canvas.delete("solution_arrow")

        # Calculate offset to center the maze in canvas
        maze_width = self.width * self.cell_size
        maze_height = self.height * self.cell_size
        offset_x = (self.canvas_width - maze_width) // 2
        offset_y = (self.canvas_height - maze_height) // 2

        # Draw solution path
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]

            # Convert to screen coordinates
            center1_x = offset_x + x1 * self.cell_size + self.cell_size // 2
            center1_y = offset_y + y1 * self.cell_size + self.cell_size // 2
            center2_x = offset_x + x2 * self.cell_size + self.cell_size // 2
            center2_y = offset_y + y2 * self.cell_size + self.cell_size // 2

            # Main solution line (thick orange)
            line_width = max(2, self.cell_size // 10)
            self.canvas.create_line(
                center1_x,
                center1_y,
                center2_x,
                center2_y,
                fill="orange",
                width=line_width,
                tags="solution",
            )

            # Direction arrows every few steps
            if (
                i % max(1, len(path) // 10) == 0
            ):  # Adjust arrow frequency based on path length
                # Calculate arrow direction
                dx = x2 - x1
                dy = y2 - y1
                arrow_char = (
                    "→" if dx > 0 else "←" if dx < 0 else "↓" if dy > 0 else "↑"
                )

                arrow_font_size = max(6, self.cell_size // 4)
                self.canvas.create_text(
                    center1_x,
                    center1_y,
                    text=arrow_char,
                    fill="red",
                    font=("Arial", arrow_font_size, "bold"),
                    tags="solution_arrow",
                )

        # Highlight start and end points
        start_x, start_y = path[0]
        end_x, end_y = path[-1]

        # Start point highlight
        start_screen_x = offset_x + start_x * self.cell_size
        start_screen_y = offset_y + start_y * self.cell_size
        highlight_width = max(2, self.cell_size // 15)

        self.canvas.create_oval(
            start_screen_x + 1,
            start_screen_y + 1,
            start_screen_x + self.cell_size - 1,
            start_screen_y + self.cell_size - 1,
            outline="lime",
            width=highlight_width,
            tags="solution",
        )

        # End point highlight
        end_screen_x = offset_x + end_x * self.cell_size
        end_screen_y = offset_y + end_y * self.cell_size

        self.canvas.create_oval(
            end_screen_x + 1,
            end_screen_y + 1,
            end_screen_x + self.cell_size - 1,
            end_screen_y + self.cell_size - 1,
            outline="red",
            width=highlight_width,
            tags="solution",
        )

    def clear_solution(self):
        """Clear the solution path from display"""
        self.canvas.delete("solution")
        self.canvas.delete("solution_arrow")

    def set_zoom_factor(self, zoom_factor):
        """Set the zoom factor for the renderer"""
        self.zoom_factor = zoom_factor

    def get_canvas_dimensions(self):
        """Get current canvas dimensions"""
        self.canvas.update()
        self.canvas_width = self.canvas.winfo_width()
        self.canvas_height = self.canvas.winfo_height()
        return self.canvas_width, self.canvas_height
