from typing import List, Dict, Optional, Tuple
from game.car import Car
from utils.configLoader import load_config
from game.obstacleManager import ObstacleManager
import pygame

class GameState:
    INIT = "init"
    RUNNING = "running"
    PAUSED = "paused"
    GOD_MODE = "god_mode"
    GAME_OVER = "game_over"

class GameEngine:
    """
    GameEngine with explicit GameState including GOD_MODE.
    - enter_god_mode puts engine in GOD_MODE (simulation paused for UI placement)
    - exit_god_mode returns engine to PAUSED (does not auto-resume)
    - engine.start() must be invoked to set RUNNING again
    """

    def __init__(self,
                 config_path: str = "config/config.json",
                 car_sprite_path: str = "assets/sprites/chiva.png",
                 start_x: int = 0,
                 start_y: int = 31,
                 screen_width: int = 1024):
        self.config_path = config_path
        self.car_sprite_path = car_sprite_path  # Store sprite path
        self.config, self.obstacles_data = load_config(config_path)
        self.car = Car(start_x, start_y, car_sprite_path, self.config)
        self.screen_width = screen_width
        self.total_distance = self.config.get("totalDistance", 1000)

        # state, prev state and hooks
        self.state = GameState.INIT
        self._prev_state: Optional[str] = None
        self._state_changing = False  # Prevent recursion in state changes
        self.on_state_change = None         # optional callback(new_state)
        self.on_obstacle_placed = None      # optional callback(obs)

        # road bounds from config (world coords)
        road_cfg = self.config.get("road", {})
        self.road_x_min = road_cfg.get("x_min", 0.0)
        self.road_x_max = road_cfg.get("x_max", self.total_distance)
        self.road_y_min = road_cfg.get("y_min", 0)      # top of road in game-area coords
        self.road_y_max = road_cfg.get("y_max", 500)    # default game area height

        # obstacle management: central manager holds AVL, list and sprite cache
        self.obstacle_manager = ObstacleManager()
        self.obstacle_manager.load_from_list(self.obstacles_data)


    # ---------------- State management ---------------------------------
    def _set_state(self, new_state: str):
        """Set state with recursion prevention."""
        if self._state_changing:
            return  # Prevent recursion
        
        self._state_changing = True
        try:
            self._prev_state = self.state
            self.state = new_state
            if callable(self.on_state_change):
                try:
                    self.on_state_change(new_state)
                except Exception as e:
                    print(f"Warning: State change callback error: {e}")
        finally:
            self._state_changing = False

    def start(self):
        """Transition to RUNNING from INIT or PAUSED. Does not resume directly from GOD_MODE."""
        if self.state in (GameState.INIT, GameState.PAUSED):
            self._set_state(GameState.RUNNING)

    def pause(self):
        if self.state == GameState.RUNNING:
            self._set_state(GameState.PAUSED)

    def resume(self):
        if self.state == GameState.PAUSED:
            self._set_state(GameState.RUNNING)

    def toggle_pause(self):
        if self.state == GameState.RUNNING:
            self.pause()
        elif self.state == GameState.PAUSED:
            self.resume()

    def reset(self):
        """Reset engine and return to INIT."""
        self.config, self.obstacles_data = load_config(self.config_path)
        # Use stored sprite path instead of getattr
        self.car = Car(0, 31, self.car_sprite_path, self.config)
        road_cfg = self.config.get("road", {})
        self.road_x_min = road_cfg.get("x_min", 0.0)
        self.road_x_max = road_cfg.get("x_max", self.total_distance)
        self.road_y_min = road_cfg.get("y_min", 0)
        self.road_y_max = road_cfg.get("y_max", 500)
        # recreate manager and reload obstacles
        self.obstacle_manager = ObstacleManager()
        self.obstacle_manager.load_from_list(self.obstacles_data)
        self._set_state(GameState.INIT)

    # ---------------- God Mode -----------------------------------------
    def enter_god_mode(self):
        """Enter GOD_MODE. Simulation is paused; UI can place obstacles."""
        if self.state != GameState.GOD_MODE:
            self._set_state(GameState.GOD_MODE)

    def exit_god_mode(self):
        """
        Exit GOD_MODE and leave the engine in PAUSED.
        User must press Start to go to RUNNING.
        """
        if self.state == GameState.GOD_MODE:
            self._set_state(GameState.PAUSED)

    # ---------------- Validation and placement API ---------------------
    def get_road_bounds(self) -> Tuple[float, float, int, int]:
        return (self.road_x_min, self.road_x_max, self.road_y_min, self.road_y_max)

    def can_place_obstacle(self, x: float, y: int, margin: float = 4.0) -> bool:
        """
        Check road bounds and overlap with existing obstacles.
        Intended for UI preview while in GOD_MODE.
        """
        if not (self.road_x_min <= x <= self.road_x_max and self.road_y_min <= y <= self.road_y_max):
            return False

        # conservative candidate rect (cone-size)
        default_size_map = {"cone": (24, 24), "hole": (40, 16)}
        cw, ch = default_size_map.get("cone", (24, 24))  # Add fallback
        cand_rect = pygame.Rect(int(x - margin), int(y - margin), cw + int(margin*2), ch + int(margin*2))

        for o in self._active_obstacles:
            o_rect = self._get_obstacle_hitbox(o)
            if o_rect and cand_rect.colliderect(o_rect):
                return False
        return True

    def place_obstacle(self, obs: Dict) -> bool:
        """
        Validate and insert obstacle. Acceptable to call while in GOD_MODE.
        Returns True if inserted; False otherwise.
        """
        if "x" not in obs or "y" not in obs:
            return False
        x = float(obs["x"])
        y = int(obs["y"])

        # Only allow placement when in GOD_MODE (UI pattern enforced)
        if self.state != GameState.GOD_MODE:
            return False

        if not self.can_place_obstacle(x, y):
            return False

        try:
            if not self.obstacle_manager.spawn_obstacle(obs):
                return False
            if callable(self.on_obstacle_placed):
                try:
                    self.on_obstacle_placed(obs)
                except Exception as e:
                    print(f"Warning: Obstacle placed callback error: {e}")
            
            return True
            
        except Exception as e:
            print(f"Error placing obstacle: {e}")
            # rollback best-effort via manager
            try:
                # try to remove if partially inserted
                self.obstacle_manager.remove_by_coords(x, y)
            except Exception:
                pass
            return False

    # ---------------- Per-frame update ---------------------------------
    def update(self, delta_time: float = 0.0):
        # Only run simulation when RUNNING. GOD_MODE and PAUSED skip updates.
        if self.state != GameState.RUNNING:
            return

        self.car.update()
        self._process_collisions_and_cleanup()

        if not self.car.is_alive() or self.car.x >= self.total_distance:
            self._set_state(GameState.GAME_OVER)

    # ---------------- Collisions and lifecycle --------------------------
    def _process_collisions_and_cleanup(self):
        visible = self.get_visible_obstacles()
        to_remove: List[Tuple[float, int]] = []

        car_rect = self._get_car_hitbox()

        for obs in visible:
            obs_rect = self._get_obstacle_hitbox(obs)
            if obs_rect and car_rect.colliderect(obs_rect):
                energy_before = self.car.energy
                try:
                    ret = self.car.collide(obs)
                except Exception as e:
                    print(f"Warning: Collision error: {e}")
                    ret = False
                if getattr(self.car, "energy", None) is not None and self.car.energy < energy_before:
                    to_remove.append((obs["x"], obs["y"]))
                elif ret is True:
                    to_remove.append((obs["x"], obs["y"]))
            elif obs["x"] < self.car.x - self.config.get("cleanup_margin", 50):
                to_remove.append((obs["x"], obs["y"]))

        for x, y in to_remove:
            self.remove_obstacle_by_coords(x, y)

    def remove_obstacle_by_coords(self, x: float, y: int):
        self.obstacle_manager.remove_by_coords(x, y)

    # ---------------- Hitbox helpers -----------------------------------
    def _get_car_hitbox(self) -> pygame.Rect:
        try:
            if hasattr(self.car, 'sprite') and self.car.sprite:
                w, h = self.car.sprite.get_size()
            else:
                w, h = (64, 32)
        except Exception:
            w, h = (64, 32)
        return pygame.Rect(int(self.car.x), int(self.car.y), w, h)

    def _get_obstacle_hitbox(self, obs: Dict) -> Optional[pygame.Rect]:
        x = int(obs["x"])
        y = int(obs["y"])
        sprite_path = obs.get("sprite")
        cache = self.obstacle_manager.get_sprite_cache()
        if sprite_path and sprite_path in cache:
            surf = cache[sprite_path]
            w, h = surf.get_size()
            return pygame.Rect(x, y, w, h)

        default_size_map = {"cone": (24, 24), "hole": (40, 16)}
        w, h = default_size_map.get(obs.get("type"), (48, 48))
        return pygame.Rect(x, y, w, h)

    # ---------------- Visibility and utilities -------------------------
    def get_visible_obstacles(self) -> List[Dict]:
        return self.obstacle_manager.get_visible(self.car.x, self.screen_width)

    def spawn_obstacle(self, obs: Dict):
        """
        Backwards-compatible spawn (no validation). Prefer place_obstacle when placing via UI.
        """
        try:
            self.obstacle_manager.spawn_obstacle(obs)
        except Exception as e:
            print(f"Warning: Could not spawn obstacle: {e}")

    # ---------------- State helpers ------------------------------------
    def is_game_over(self) -> bool:
        return self.state == GameState.GAME_OVER

    def serialize_state(self) -> Dict:
        return {
            "car_x": getattr(self.car, 'x', 0),
            "car_y": getattr(self.car, 'y', 0),
            "energy": getattr(self.car, 'energy', 0),
            "remaining_obstacles": len(self._active_obstacles),
            "state": self.state
        }