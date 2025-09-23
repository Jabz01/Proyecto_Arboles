from typing import List, Dict, Optional, Tuple
from src.model.avlTree import avlTree
from src.game.car import Car
from src.utils.configLoader import load_config
import pygame

class GameState:
    RUNNING = "running"
    GAME_OVER = "game_over"

class GameEngine:
    """
    Minimal game engine:
    - Updates the car every frame
    - Detects collisions using bounding boxes (hitboxes)
    - Manages obstacle lifecycle (remove after collision or when passed)
    - Provides visible obstacles for rendering
    """

    def __init__(self,
                 config_path: str = "config/config.json",
                 car_sprite_path: str = "assets/sprites/chiva.png",
                 start_x: int = 0,
                 start_y: int = 31,
                 screen_width: int = 1024): #road.png width px 
        """
        Initialize engine: load config, create car and fill the AVL.

        Args:
            config_path: path to the JSON config file.
            car_sprite_path: path to the car sprite.
            start_x, start_y: initial car position.
            screen_width: camera/screen width in pixels.
        """
        self.config, self.obstacles_data = load_config(config_path)
        self.car = Car(start_x, start_y, car_sprite_path, self.config)
        self.tree = avlTree()
        self.screen_width = screen_width
        self.total_distance = self.config.get("totalDistance", 1000)
        self.state = GameState.RUNNING

        # simple sprite cache used to compute hitbox sizes
        self._sprite_cache: Dict[str, pygame.Surface] = {}

        # active obstacles list kept in sync with AVL for easy linear scans
        self._active_obstacles: List[Dict] = []

        self._load_obstacles()

    # --- Loading and insertion --------------------------------------------
    def _load_obstacles(self):
        """
        Insert all config obstacles into the AVL and the active list.
        Tries to preload sprites if pygame is initialized.
        """
        for obs in self.obstacles_data:
            self.tree.insert(obs["x"], obs["y"], obs)
            self._active_obstacles.append(obs)
            sprite_path = obs.get("sprite")
            if sprite_path and pygame.get_init():
                try:
                    surf = pygame.image.load(sprite_path).convert_alpha()
                    self._sprite_cache[sprite_path] = surf
                except Exception:
                    pass

    # --- Per-frame update -------------------------------------------------
    def update(self, delta_time: float = 0.0):
        """
        Update game state for the current frame.
        - Moves the car (car.update handles movement)
        - Checks collisions and manages obstacle lifecycle
        - Sets GAME_OVER if conditions met

        Args:
            delta_time: seconds since last frame (optional).
        """
        if self.state != GameState.RUNNING:
            return

        # update car (Car.update may use config speed)
        self.car.update()

        # collision checks and cleanup
        self._process_collisions_and_cleanup()

        # end conditions
        if not self.car.is_alive() or self.car.x >= self.total_distance:
            self.state = GameState.GAME_OVER

    # --- Collisions and lifecycle -----------------------------------------
    def _process_collisions_and_cleanup(self):
        """Only remove obstacles that actually caused damage."""
        visible = self.get_visible_obstacles()
        to_remove = []
        
        car_rect = self._get_car_hitbox()
        
        for obs in visible:
            obs_rect = self._get_obstacle_hitbox(obs)
            if obs_rect and car_rect.colliderect(obs_rect):
                # Store energy before collision
                energy_before = self.car.energy
                self.car.collide(obs)
                # Only remove if damage was actually dealt
                if self.car.energy < energy_before:
                    to_remove.append((obs["x"], obs["y"]))
            elif obs["x"] < self.car.x - self.config.get("cleanup_margin", 50):
                to_remove.append((obs["x"], obs["y"]))


    def remove_obstacle_by_coords(self, x: float, y: int):
        """
        Remove obstacle by coordinates from AVL and active list.
        """
        self.tree.delete(x, y)
        self._active_obstacles = [o for o in self._active_obstacles if not (o["x"] == x and o["y"] == y)]

    # --- Hitbox helpers ---------------------------------------------------
    def _get_car_hitbox(self) -> pygame.Rect:
        """Use the car's actual sprite for hitbox calculation."""
        try:
            w, h = self.car.sprite.get_size()
        except:
            w, h = (64, 32)  # fallback
        return pygame.Rect(int(self.car.x), int(self.car.y), w, h)

    def _get_obstacle_hitbox(self, obs: Dict) -> Optional[pygame.Rect]:
        """
        Build a collision rect for an obstacle using preloaded sprite if available,
        otherwise use a default size map.
        """
        x = int(obs["x"])
        y = int(obs["y"])
        sprite_path = obs.get("sprite")
        if sprite_path and sprite_path in self._sprite_cache:
            surf = self._sprite_cache[sprite_path]
            w, h = surf.get_size()
            return pygame.Rect(x, y, w, h)

        default_size_map = {
            "cone": (24, 24),
            "hole": (40, 16),
        }
        w, h = default_size_map.get(obs.get("type"), (48, 48))
        return pygame.Rect(x, y, w, h)

    # --- Visibility and utilities -----------------------------------------
    def get_visible_obstacles(self) -> List[Dict]:
        """
        Return obstacles in the visible X range: [car.x, car.x + screen_width].
        Uses linear filter over active list (sufficient for prototype).
        """
        min_x = self.car.x
        max_x = self.car.x + self.screen_width
        return [o for o in self._active_obstacles if min_x <= o["x"] <= max_x]

    def spawn_obstacle(self, obs: Dict):
        """
        Dynamically insert an obstacle at runtime: AVL + active list + preload sprite.
        """
        self.tree.insert(obs["x"], obs["y"], obs)
        self._active_obstacles.append(obs)
        sprite = obs.get("sprite")
        if sprite and pygame.get_init() and sprite not in self._sprite_cache:
            try:
                self._sprite_cache[sprite] = pygame.image.load(sprite).convert_alpha()
            except Exception:
                pass

    # --- State helpers ---------------------------------------------------
    def is_game_over(self) -> bool:
        """Return True if the game is over."""
        return self.state == GameState.GAME_OVER

    def serialize_state(self) -> Dict:
        """Small snapshot useful for debugging or quick save."""
        return {
            "car_x": self.car.x,
            "car_y": self.car.y,
            "energy": self.car.energy,
            "remaining_obstacles": len(self._active_obstacles),
            "state": self.state
        }
