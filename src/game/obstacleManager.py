from typing import Dict, List, Tuple, Optional
import pygame

"""
ObstacleManager:
- Wraps the AVL tree (provided by your avlTree implementation)
- Keeps:
    * AVL (original dicts stored in AVL to keep compatibility with existing engine)
    * active_list: list of dicts (same structure as JSON) for linear scanning and for GameEngine compatibility
    * objects_map: (x,y) -> Obstacle instance for rendering and collisions
- Provides conveniences: load_from_list, spawn_from_dict, remove_by_coords, get_visible_*
"""

from src.model.obstacle import Obstacle

class ObstacleManager:
    def __init__(self, avl_tree, sprite_cache: Optional[Dict[str, pygame.Surface]] = None):
        self.tree = avl_tree
        self.sprite_cache = sprite_cache if sprite_cache is not None else {}
        # key -> dict (original JSON dict)
        self.obstacles_map: Dict[Tuple[int,int], Dict] = {}
        # key -> Obstacle object (for rendering)
        self.objects_map: Dict[Tuple[int,int], Obstacle] = {}
        # ordered list of dicts (keeps insertion order; compatible with earlier GameEngine._active_obstacles)
        self.active_list: List[Dict] = []

    # ---------------- loading / spawning ----------------
    def load_from_list(self, list_of_dicts: List[Dict]):
        """Bulk load obstacles (used at startup)."""
        for entry in list_of_dicts:
            self.spawn_from_dict(entry)

    def spawn_from_dict(self, d: Dict) -> bool:
        """
        Insert obstacle both into AVL (storing original dict) and into internal object map.
        Returns True if inserted, False if coordinates already exist.
        """
        x = int(d["x"])
        y = int(d["y"])
        key = (x, y)
        if key in self.obstacles_map:
            print(f"[ObstacleManager] obstacle at {key} already present, skipping.")
            return False

        # insert into AVL using the same API your code expects
        try:
            self.tree.insert(x, y, d)  # keep AVL storing dicts for compatibility
        except Exception as e:
            # Many AVL implementations don't throw, but guard anyway
            print(f"[WARN] AVL insert failed for {key}: {e}")

        # keep active list and maps
        self.obstacles_map[key] = d
        self.active_list.append(d)

        # create Obstacle object for rendering/collisions
        obj = Obstacle.from_dict(d)
        # preload sprite if pygame initialized
        if pygame.get_init():
            obj.load_image(sprite_cache=self.sprite_cache)
        self.objects_map[key] = obj
        return True

    # ---------------- removal ----------------
    def remove_by_coords(self, x: int, y: int) -> bool:
        """Remove obstacle from AVL, active list and objects map."""
        key = (int(x), int(y))
        if key not in self.obstacles_map:
            return False

        try:
            self.tree.delete(x, y)
        except Exception as e:
            print(f"[WARN] AVL delete failed for {key}: {e}")
        # remove from internal structures
        del self.obstacles_map[key]
        # remove first matching element in active_list (dict compare)
        self.active_list = [o for o in self.active_list if not (int(o["x"]) == key[0] and int(o["y"]) == key[1])]
        self.objects_map.pop(key, None)
        return True

    # ---------------- queries ----------------
    def get_visible_dicts(self, camera_x: int, screen_width: int) -> List[Dict]:
        """
        Return list of dicts of obstacles whose x in [camera_x, camera_x + screen_width].
        Maintains compatibility with existing GameEngine which expects dicts.
        """
        min_x = int(camera_x)
        max_x = int(camera_x + screen_width)
        return [d for d in self.active_list if min_x <= int(d["x"]) <= max_x]

    def get_visible_objects(self, camera_x: int, screen_width: int) -> List[Obstacle]:
        """
        Return Obstacle objects for rendering that are visible in the screen range.
        """
        min_x = int(camera_x)
        max_x = int(camera_x + screen_width)
        visible = []
        for (kx, ky), obj in self.objects_map.items():
            if min_x <= obj.x <= max_x:
                visible.append(obj)
        return visible

    # ---------------- helpers ----------------
    def find_by_coords(self, x: int, y: int) -> Optional[Dict]:
        """Return the original dict if present."""
        return self.obstacles_map.get((int(x), int(y)))

    def insert_manual(self, x: int, y: int, tipo: str, damage: int, sprite: Optional[str] = None) -> bool:
        """Create a dict and spawn it (helper used by GUI insert forms)."""
        d = {"x": int(x), "y": int(y), "type": tipo, "damage": int(damage), "sprite": sprite}
        return self.spawn_from_dict(d)

    def debug_summary(self) -> Dict:
        return {
            "total_active": len(self.active_list),
            "total_objects": len(self.objects_map),
            "total_avl_nodes": "unknown"  # could implement a count() in avlTree
        }
