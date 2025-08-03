# pathfinding.py
"""Pathfinding algorithms for maze solving"""

import heapq
import random
import time
from collections import deque
from config import GameConfig


class PathFinder:
    def __init__(self):
        """Initialize PathFinder without maze dependency"""
        pass

    def find_path(self, start, end, algorithm, maze):
        """Main pathfinding function that calls the selected algorithm"""
        # Get maze dimensions
        height = len(maze)
        width = len(maze[0]) if maze else 0

        start_time = time.time()

        if algorithm == "BFS":
            result, nodes_explored = self._bfs(start, end, maze, width, height)
        elif algorithm == "UCS":
            result, nodes_explored = self._ucs(start, end, maze, width, height)
        elif algorithm == "DFS":
            result, nodes_explored = self._dfs(start, end, maze, width, height)
        elif algorithm == "DLS":
            result, nodes_explored = self._dls(start, end, maze, width, height)
        elif algorithm == "IDS":
            result, nodes_explored = self._ids(start, end, maze, width, height)
        elif algorithm == "Bidirectional":
            result, nodes_explored = self._bidirectional(
                start, end, maze, width, height
            )
        else:
            result, nodes_explored = self._bfs(
                start, end, maze, width, height
            )  # Default to BFS

        search_time = time.time() - start_time
        return result, nodes_explored, search_time

    def _bfs(self, start, end, maze, width, height):
        """Breadth-First Search - Guarantees shortest path"""
        queue = deque([(start, [start])])
        visited = set([tuple(start)])
        nodes_explored = 0

        while queue:
            (x, y), path = queue.popleft()
            nodes_explored += 1

            if [x, y] == end:
                return path, nodes_explored

            for dx, dy in GameConfig.DIRECTIONS:
                nx, ny = x + dx, y + dy
                if (
                    0 <= nx < width
                    and 0 <= ny < height
                    and maze[ny][nx] == 0
                    and (nx, ny) not in visited
                ):
                    visited.add((nx, ny))
                    queue.append(([nx, ny], path + [[nx, ny]]))

        return None, nodes_explored

    def _ucs(self, start, end, maze, width, height):
        """Uniform-Cost Search - Like BFS but with priority queue"""
        heap = [(0, start, [start])]  # (cost, position, path)
        visited = set()
        nodes_explored = 0

        while heap:
            cost, (x, y), path = heapq.heappop(heap)
            nodes_explored += 1

            if (x, y) in visited:
                continue
            visited.add((x, y))

            if [x, y] == end:
                return path, nodes_explored

            for dx, dy in GameConfig.DIRECTIONS:
                nx, ny = x + dx, y + dy
                if (
                    0 <= nx < width
                    and 0 <= ny < height
                    and maze[ny][nx] == 0
                    and (nx, ny) not in visited
                ):
                    new_cost = cost + 1  # Each step costs 1
                    heapq.heappush(heap, (new_cost, [nx, ny], path + [[nx, ny]]))

        return None, nodes_explored

    def _dfs(self, start, end, maze, width, height):
        """Depth-First Search - May not find shortest path"""
        stack = [(start, [start])]
        visited = set()
        nodes_explored = 0
        directions = GameConfig.DIRECTIONS[:]

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
                if (
                    0 <= nx < width
                    and 0 <= ny < height
                    and maze[ny][nx] == 0
                    and (nx, ny) not in visited
                ):
                    stack.append(([nx, ny], path + [[nx, ny]]))

        return None, nodes_explored

    def _dls_recursive(
        self, x, y, end, path, visited, remaining_depth, maze, width, height
    ):
        """Recursive helper for Depth-Limited Search"""
        if remaining_depth < 0:
            return None, 0

        if [x, y] == end:
            return path, 1

        visited.add((x, y))
        nodes_explored = 1

        for dx, dy in GameConfig.DIRECTIONS:
            nx, ny = x + dx, y + dy
            if (
                0 <= nx < width
                and 0 <= ny < height
                and maze[ny][nx] == 0
                and (nx, ny) not in visited
            ):
                result, explored = self._dls_recursive(
                    nx,
                    ny,
                    end,
                    path + [[nx, ny]],
                    visited.copy(),
                    remaining_depth - 1,
                    maze,
                    width,
                    height,
                )
                nodes_explored += explored
                if result:
                    return result, nodes_explored

        return None, nodes_explored

    def _dls(self, start, end, maze, width, height, depth_limit=50):
        """Depth-Limited Search - DFS with depth limit"""
        return self._dls_recursive(
            start[0], start[1], end, [start], set(), depth_limit, maze, width, height
        )

    def _ids(self, start, end, maze, width, height, max_depth=100):
        """Iterative Deepening Search - Combines benefits of BFS and DFS"""
        total_nodes_explored = 0

        for depth in range(max_depth):
            result, nodes_explored = self._dls(start, end, maze, width, height, depth)
            total_nodes_explored += nodes_explored
            if result:
                return result, total_nodes_explored

        return None, total_nodes_explored

    def _bidirectional(self, start, end, maze, width, height):
        """Bidirectional Search - Search from both start and end"""
        if start == end:
            return [start], 1

        # Forward search from start
        forward_queue = deque([(start, [start])])
        forward_visited = {tuple(start): [start]}

        # Backward search from end
        backward_queue = deque([(end, [end])])
        backward_visited = {tuple(end): [end]}

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

                for dx, dy in GameConfig.DIRECTIONS:
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < width
                        and 0 <= ny < height
                        and maze[ny][nx] == 0
                        and (nx, ny) not in forward_visited
                    ):
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

                for dx, dy in GameConfig.DIRECTIONS:
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < width
                        and 0 <= ny < height
                        and maze[ny][nx] == 0
                        and (nx, ny) not in backward_visited
                    ):
                        new_path = path + [[nx, ny]]
                        backward_visited[(nx, ny)] = new_path
                        backward_queue.append(([nx, ny], new_path))

        return None, nodes_explored
