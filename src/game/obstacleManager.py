# src/game/obstacleManager.py
import pygame
from typing import List, Dict, Optional, Tuple
from model.avlTree import avlTree
from gui.spriteUtils import loadSprite, SPRITE_CACHE


class ObstacleManager:
    """
    Manage obstacles: AVL tree for spatial lookup, active list for iteration,
    and a sprite cache for obstacle sprites.

    Args:
        sprite_cache: optional dict used as shared sprite cache. If None, uses
                      gui.spriteUtils.SPRITE_CACHE as the canonical cache.
    """

    def __init__(self, sprite_cache: Optional[Dict[str, pygame.Surface]] = None):
        self.tree = avlTree()
        self._active_obstacles: List[Dict] = []
        self._sprite_cache: Dict[str, pygame.Surface] = sprite_cache if sprite_cache is not None else SPRITE_CACHE

    # ---------------- Loading ----------------
    def load_from_list(self, obstacles: List[Dict]) -> None:
        """
        Bulk load obstacles from a list of dicts (e.g., from config).

        Args:
            obstacles: list of obstacle dicts with keys at least 'x' and 'y'.
        """
        for obs in obstacles:
            try:
                self.spawn_obstacle(obs)
            except Exception as e:
                print(f"[ObstacleManager] Error loading obstacle {obs}: {e}")

    # ---------------- Insert / Remove ----------------
    def spawn_obstacle(self, obs: Dict) -> bool:
        """
        Insert a new obstacle into the AVL and active list.
        Uses the shared sprite cache via spriteUtils.

        Args:
            obs: obstacle dict with required keys 'x' (float) and 'y' (int). Optional 'sprite'.

        Returns:
            True if inserted successfully, False otherwise.
        """
        try:
            x = float(obs["x"])
            y = int(obs["y"])
        except Exception as e:
            print(f"[ObstacleManager] Invalid obstacle coords {obs}: {e}")
            return False

        # Check duplicates in AVL
        try:
            existing = self.tree.search(x, y)
            if existing is not None:
                print(f"[ObstacleManager] Duplicate obstacle at ({x},{y}), skipping")
                return False
        except Exception:
            # If search fails for some reason, continue cautiously and try to insert
            pass

        # Insert into AVL and active list
        try:
            self.tree.insert(x, y, obs)
            self._active_obstacles.append(obs)
        except Exception as e:
            print(f"[ObstacleManager] Failed to insert obstacle into AVL/list: {e}")
            # best-effort cleanup: remove from active list if partially appended
            try:
                self._active_obstacles = [o for o in self._active_obstacles if o is not obs]
            except Exception:
                pass
            return False

        # Preload sprite into shared cache using spriteUtils
        sprite_path = obs.get("sprite")
        if sprite_path and sprite_path not in self._sprite_cache:
            try:
                surf = loadSprite(sprite_path, fallbackSize=None)
                if surf:
                    # store canonical key as normalized path inside spriteUtils
                    self._sprite_cache[sprite_path] = surf
                else:
                    print(f"[ObstacleManager] Could not load sprite {sprite_path}")
            except Exception as e:
                print(f"[ObstacleManager] Exception loading sprite {sprite_path}: {e}")

        return True

    def remove_by_coords(self, x: float, y: int) -> bool:
        """
        Remove obstacle by coordinates from AVL and active list.

        Args:
            x: world x coordinate.
            y: world y coordinate.

        Returns:
            True if an obstacle was removed, False otherwise.
        """
        removed = False
        try:
            self.tree.delete(float(x), int(y))
            removed = True
        except Exception:
            # deletion from AVL might fail if not present - we'll still filter active list
            removed = False

        before = len(self._active_obstacles)
        self._active_obstacles = [o for o in self._active_obstacles if not (float(o.get("x", -999999)) == float(x) and int(o.get("y", -999999)) == int(y))]
        after = len(self._active_obstacles)

        return removed or (before != after)

    # ---------------- Queries ----------------
    def get_visible(self, camera_x: float, screen_width: int) -> List[Dict]:
        """
        Return active obstacles visible on screen.

        Args:
            camera_x: current camera/car x in world coords.
            screen_width: width of the screen in pixels.

        Returns:
            List of obstacle dicts whose x is within [camera_x, camera_x + screen_width].
        """
        min_x = camera_x
        max_x = camera_x + screen_width
        return [o for o in self._active_obstacles if min_x <= float(o.get("x", -999999)) <= max_x]

    def get_active_obstacles(self) -> List[Dict]:
        """
        Return the active obstacles list.

        Returns:
            List[Dict] of active obstacles.
        """
        return self._active_obstacles

    def get_sprite_cache(self) -> Dict[str, pygame.Surface]:
        """
        Expose the internal sprite cache.

        Returns:
            Dict mapping sprite path -> pygame.Surface.
        """
        return self._sprite_cache