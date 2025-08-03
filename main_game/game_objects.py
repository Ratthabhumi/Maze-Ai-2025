# game_objects.py
"""Game objects and entities"""

import random
from config import GameConfig


class Player:
    def __init__(self, start_pos=[1, 1]):
        self.pos = start_pos[:]
        self.moves_count = 0
        self.keys_collected = 0

    def move(self, new_pos):
        """Move player to new position"""
        self.pos = new_pos[:]
        self.moves_count += 1

    def collect_key(self):
        """Collect a key"""
        self.keys_collected += 1

    def reset(self, start_pos=[1, 1]):
        """Reset player to initial state"""
        self.pos = start_pos[:]
        self.moves_count = 0
        self.keys_collected = 0


class Enemy:
    def __init__(self, pos=None):
        self.pos = pos[:] if pos else None
        self.path = []
        self.move_counter = 0
        self.initial_pos = pos[:] if pos else None

    def create_patrol_path(self, maze, width, height):
        """Create a patrol path for the enemy"""
        if not self.pos:
            return

        self.path = [self.pos[:]]
        current = self.pos[:]
        visited = set()
        visited.add(tuple(current))

        # Create a more robust patrol path
        directions = getattr(
            GameConfig, "DIRECTIONS", [(0, 1), (1, 0), (0, -1), (-1, 0)]
        )

        for _ in range(10):  # Try to create a longer path
            found_next = False
            # Shuffle directions for more varied paths
            random.shuffle(directions)

            for dx, dy in directions:
                nx, ny = current[0] + dx, current[1] + dy
                if (
                    0 <= nx < width
                    and 0 <= ny < height
                    and maze[ny][nx] == 0
                    and (nx, ny) not in visited
                ):
                    self.path.append([nx, ny])
                    current = [nx, ny]
                    visited.add((nx, ny))
                    found_next = True
                    break

            if not found_next:
                break

        # If path is too short, create a simple back-and-forth
        if len(self.path) < 3:
            self.path = [self.pos[:]]
            for dx, dy in directions:
                nx, ny = self.pos[0] + dx, self.pos[1] + dy
                if 0 <= nx < width and 0 <= ny < height and maze[ny][nx] == 0:
                    self.path.append([nx, ny])
                    break

    def move(self):
        """Move enemy along patrol path"""
        if not self.pos or not self.path or len(self.path) < 2:
            return

        move_interval = getattr(GameConfig, "ENEMY_MOVE_INTERVAL", 3)
        self.move_counter += 1

        if self.move_counter >= move_interval:
            try:
                current_index = self.path.index(self.pos)
            except ValueError:
                current_index = 0
                self.pos = self.path[0][:]

            next_index = (current_index + 1) % len(self.path)
            self.pos = self.path[next_index][:]
            self.move_counter = 0

    def reset(self):
        """Reset enemy to initial state"""
        self.pos = self.initial_pos[:] if self.initial_pos else None
        self.path = []
        self.move_counter = 0


class GameItems:
    def __init__(self):
        self.keys = []
        self.traps = []
        self.teleporters = []
        self.moving_walls = []

    def setup_items(self, empty_spaces, required_keys):
        """Set up all game items on the maze"""
        available_spaces = empty_spaces[:]

        # Place golden keys
        keys_to_place = min(required_keys, len(available_spaces))
        for _ in range(keys_to_place):
            if available_spaces:
                pos = random.choice(available_spaces)
                self.keys.append(pos)
                available_spaces.remove(pos)

        # Place traps (invisible death squares)
        num_traps = min(8, len(available_spaces) // 10, len(available_spaces))
        for _ in range(num_traps):
            if available_spaces:
                pos = random.choice(available_spaces)
                self.traps.append(pos)
                available_spaces.remove(pos)

        # Place teleporter pairs
        if len(available_spaces) >= 4:
            pairs_to_create = min(2, len(available_spaces) // 2)
            for _ in range(pairs_to_create):
                if len(available_spaces) >= 2:
                    pos1 = random.choice(available_spaces)
                    available_spaces.remove(pos1)
                    pos2 = random.choice(available_spaces)
                    available_spaces.remove(pos2)
                    self.teleporters.append((pos1, pos2))

        return available_spaces

    def remove_key(self, pos):
        """Remove a key from the specified position"""
        if pos in self.keys:
            self.keys.remove(pos)
            return True
        return False

    def get_teleporter_destination(self, pos):
        """Get teleporter destination for given position"""
        for pos1, pos2 in self.teleporters:
            if pos == pos1:
                return pos2[:]
            elif pos == pos2:
                return pos1[:]
        return None

    def is_trap(self, pos):
        """Check if position is a trap"""
        return pos in self.traps

    def reset(self):
        """Reset all game items"""
        self.keys = []
        self.traps = []
        self.teleporters = []
        self.moving_walls = []


class PowerUps:
    def __init__(self):
        self.has_flashlight = False
        self.flashlight_duration = getattr(
            GameConfig, "FLASHLIGHT_DURATION", 10000
        )  # Default 10 seconds
        self.flashlight_start = None

    def activate_flashlight(self, current_time):
        """Activate flashlight power-up"""
        if not self.has_flashlight:
            self.has_flashlight = True
            self.flashlight_start = current_time

    def update_flashlight(self, current_time):
        """Update flashlight status"""
        if (
            self.has_flashlight
            and self.flashlight_start
            and current_time - self.flashlight_start >= self.flashlight_duration
        ):
            self.has_flashlight = False
            self.flashlight_start = None

    def get_flashlight_remaining(self, current_time):
        """Get remaining flashlight time"""
        if self.has_flashlight and self.flashlight_start:
            return max(
                0, self.flashlight_duration - (current_time - self.flashlight_start)
            )
        return 0

    def reset(self):
        """Reset power-ups"""
        self.has_flashlight = False
        self.flashlight_start = None


class GameObjects:
    """A manager class to hold all game objects and state."""

    def __init__(self, width, height):
        self.width = width
        self.height = height

        # Create instances of all game object classes
        self.player = Player()
        self.enemy = Enemy()
        self.items = GameItems()
        self.power_ups = PowerUps()

        # Game state variables
        self.start_pos = [1, 1]
        self.end_pos = [width - 2, height - 2]
        self.map_revealed = False
        self.visibility_radius = getattr(GameConfig, "VISIBILITY_RADIUS", 3)

    def setup_objects(self, maze):
        """Sets up the initial positions and states of all game objects."""
        # Find all empty spaces (value 0)
        empty_spaces = []
        for y in range(self.height):
            for x in range(self.width):
                if maze[y][x] == 0:
                    empty_spaces.append([x, y])

        # Ensure start and end positions are not used for items
        if self.start_pos in empty_spaces:
            empty_spaces.remove(self.start_pos)
        if self.end_pos in empty_spaces:
            empty_spaces.remove(self.end_pos)

        # Set up player
        self.player.reset(self.start_pos)

        # Set up enemy
        # Place enemy far from the player's start
        if empty_spaces:
            far_spaces = sorted(
                empty_spaces,
                key=lambda p: abs(p[0] - self.start_pos[0])
                + abs(p[1] - self.start_pos[1]),
                reverse=True,
            )
            enemy_start_pos = far_spaces[0]
            self.enemy.pos = enemy_start_pos[:]
            self.enemy.initial_pos = enemy_start_pos[:]
            empty_spaces.remove(enemy_start_pos)
            self.enemy.create_patrol_path(maze, self.width, self.height)

        # Set up keys, traps, teleporters
        required_keys = getattr(GameConfig, "REQUIRED_KEYS", 3)
        self.items.setup_items(empty_spaces, required_keys)

    def handle_player_move(self, maze):
        """Check for and handle events at the player's new position."""
        player_pos = self.player.pos

        # Check for trap
        if self.items.is_trap(player_pos):
            return "trap"

        # Check for enemy collision
        if self.enemy.pos and player_pos == self.enemy.pos:
            return "enemy"

        # Check for key collection
        if self.items.remove_key(player_pos):
            self.player.collect_key()
            required_keys = getattr(GameConfig, "REQUIRED_KEYS", 3)
            return f"key collected! You now have {self.player.keys_collected}/{required_keys} keys."

        # Check for teleporter
        destination = self.items.get_teleporter_destination(player_pos)
        if destination:
            self.player.move(destination)
            return f"teleport to {destination}!"

        return "move"

    def reset(self):
        """Resets all game objects to their initial state."""
        self.player.reset(self.start_pos)
        self.enemy.reset()
        self.items.reset()
        self.power_ups.reset()
        self.map_revealed = False

    # --- Properties to provide a clean interface to the main game ---

    @property
    def player_pos(self):
        return self.player.pos

    @player_pos.setter
    def player_pos(self, value):
        self.player.move(value)

    @property
    def keys_collected(self):
        return self.player.keys_collected

    @property
    def enemy_pos(self):
        return self.enemy.pos

    @property
    def keys(self):
        return self.items.keys

    @property
    def traps(self):
        return self.items.traps

    @property
    def teleporters(self):
        return self.items.teleporters

    @property
    def has_flashlight(self):
        return self.power_ups.has_flashlight

    @property
    def flashlight_start(self):
        return self.power_ups.flashlight_start

    # --- Methods to delegate calls ---

    def move_enemy(self):
        self.enemy.move()

    def activate_flashlight(self, current_time):
        self.power_ups.activate_flashlight(current_time)

    def update_flashlight(self, current_time):
        self.power_ups.update_flashlight(current_time)

    def get_flashlight_remaining(self, current_time):
        return self.power_ups.get_flashlight_remaining(current_time)
