from typing import List, Dict, Tuple, Optional
import pygame
from src.model.avlTree import avlTree

class ObstacleManager:
    """
    Manages obstacles for the game.
    - Keeps an AVL tree for fast search
    - Keeps an active list of dicts (compatible with GameEngine)
    - Uses a sprite cache to avoid reloading images
    """

    def __init__(self, sprite_cache: Optional[Dict[str, pygame.Surface]] = None):
        self.tree = avlTree()
        self._active_obstacles: List[Dict] = []
        self._sprite_cache: Dict[str, pygame.Surface] = sprite_cache if sprite_cache is not None else {}

    # ---------------- Loading ----------------
    def load_from_list(self, obstacles: List[Dict]):
        """Bulk load obstacles from a list of dicts (from config.json)."""
        for obs in obstacles:
            self.spawn_obstacle(obs)

    # ---------------- Insert/Remove ----------------
    def spawn_obstacle(self, obs: Dict) -> bool:
        """
        Insert a new obstacle into the AVL and active list.
        Returns True if inserted successfully, False otherwise.
        """
        try:
            x, y = obs["x"], obs["y"]
            # Check duplicates in AVL
            if self.tree.search(x, y) is not None:
                print(f"[ObstacleManager] Duplicate obstacle at ({x},{y}), skipping")
                return False

            # Insert into AVL
            self.tree.insert(x, y, obs)
            # Add to active list
            self._active_obstacles.append(obs)

            # Preload sprite into cache if available
            sprite = obs.get("sprite")
            if sprite and pygame.get_init() and sprite not in self._sprite_cache:
                try:
                    self._sprite_cache[sprite] = pygame.image.load(sprite).convert_alpha()
                except Exception as e:
                    print(f"[ObstacleManager] Could not load sprite {sprite}: {e}")

            return True
        except Exception as e:
            print(f"[ObstacleManager] Failed to spawn obstacle {obs}: {e}")
            return False

    def remove_by_coords(self, x: float, y: int) -> bool:
        """
        Remove obstacle by coordinates from AVL and active list.
        Returns True if removed, False otherwise.
        """
        removed = False
        try:
            self.tree.delete(x, y)
            removed = True
        except Exception as e:
            print(f"[ObstacleManager] Could not delete from AVL: {e}")

        # Update active list
        before = len(self._active_obstacles)
        self._active_obstacles = [o for o in self._active_obstacles if not (o["x"] == x and o["y"] == y)]
        after = len(self._active_obstacles)

        return removed or (before != after)

    # ---------------- Queries ----------------
    def get_visible(self, camera_x: float, screen_width: int) -> List[Dict]:
        """
        Return all active obstacles visible on screen (x within [camera_x, camera_x+screen_width]).
        """
        min_x = camera_x
        max_x = camera_x + screen_width
        return [o for o in self._active_obstacles if min_x <= o["x"] <= max_x]

    def get_active_obstacles(self) -> List[Dict]:
        """Return all active obstacles (list of dicts)."""
        return self._active_obstacles

    def get_sprite_cache(self) -> Dict[str, pygame.Surface]:
        """Expose sprite cache for hitbox calculations."""
        return self._sprite_cache
