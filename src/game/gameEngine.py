# src/game/gameEngine.py
from typing import List, Dict, Optional, Tuple
from game.car import Car
from utils.configLoader import load_config
from game.obstacleManager import ObstacleManager
from gui.spriteUtils import SPRITE_CACHE
import pygame


class GameState:
    INIT = "init"
    RUNNING = "running"
    PAUSED = "paused"
    GOD_MODE = "god_mode"
    GAME_OVER = "game_over"


class GameEngine:
    def __init__(self,
                 config_path: str = "config/config.json",
                 car_sprite_path: str = "assets/sprites/chiva.png",
                 start_x: int = 0,
                 start_y: int = 31,
                 screen_width: int = 1024,
                 camera_offset: int = 64):
        self.config_path = config_path
        self.car_sprite_path = car_sprite_path
        self.config, self.obstacles_data = load_config(config_path)
        self.car = Car(start_x, start_y, car_sprite_path, self.config)
        self.screen_width = screen_width
        self.camera_offset = camera_offset
        self.total_distance = self.config.get("totalDistance", 1000)
        # state, prev state and hooks
        self.state = GameState.INIT
        self._prev_state: Optional[str] = None
        self._state_changing = False
        self.on_state_change = None
        self.on_obstacle_placed = None

        # road bounds
        road_cfg = self.config.get("road", {})
        self.road_x_min = road_cfg.get("x_min", 0.0)
        self.road_x_max = road_cfg.get("x_max", self.total_distance)
        self.road_y_min = road_cfg.get("y_min", 31)
        self.road_y_max = road_cfg.get("y_max", 500)
        self.lane_height = int((self.road_y_max - self.road_y_min) // 8)

        # obstacle manager
        self.obstacle_manager = ObstacleManager(sprite_cache=SPRITE_CACHE)
        self.obstacle_manager.load_from_list(self.obstacles_data)

    def _set_state(self, new_state: str):
        if self._state_changing:
            return
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
        if self.state == GameState.GAME_OVER:
            self.reset()
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
        self.config, self.obstacles_data = load_config(self.config_path)
        self.car = Car(0, 31, self.car_sprite_path, self.config)
        road_cfg = self.config.get("road", {})
        self.road_x_min = road_cfg.get("x_min", 0.0)
        self.road_x_max = road_cfg.get("x_max", self.total_distance)
        self.road_y_min = road_cfg.get("y_min", 0)
        self.road_y_max = road_cfg.get("y_max", 500)
        self.obstacle_manager = ObstacleManager(sprite_cache=SPRITE_CACHE)
        self.obstacle_manager.load_from_list(self.obstacles_data)
        self._set_state(GameState.INIT)

    def enter_god_mode(self):
        if self.state != GameState.GOD_MODE:
            self._set_state(GameState.GOD_MODE)

    def exit_god_mode(self):
        if self.state == GameState.GOD_MODE:
            self._set_state(GameState.PAUSED)

    def get_road_bounds(self) -> Tuple[float, float, int, int]:
        return (self.road_x_min, self.road_x_max, self.road_y_min, self.road_y_max)

    def can_place_obstacle(self, x: float, y: int, margin: float = 4.0, obstacle_type: str = "cone") -> bool:
        # y is baseline; ensure baseline is within road bounds
        if not (self.road_x_min <= x <= self.road_x_max and self.road_y_min <= y <= self.road_y_max):
            return False

        default_size_map = {"cone": (24, 24), "hole": (40, 16)}
        cw, ch = default_size_map.get(obstacle_type, (24, 24))

        # candidate rect top in world coords
        cand_top = int(y - ch - margin)
        cand_rect = pygame.Rect(int(x - margin), cand_top, cw + int(margin * 2), ch + int(margin * 2))

        for o in self.obstacle_manager.get_active_obstacles():
            o_rect = self._get_obstacle_hitbox(o)
            if o_rect and cand_rect.colliderect(o_rect):
                return False
        return True

    def place_obstacle(self, obs: Dict) -> bool:
        if "x" not in obs or "y" not in obs:
            return False
        x = float(obs["x"])
        y = int(obs["y"])

        if self.state != GameState.GOD_MODE:
            return False

        if not self.can_place_obstacle(x, y, obstacle_type=obs.get("type", "cone")):
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
            try:
                self.obstacle_manager.remove_by_coords(x, y)
            except Exception:
                pass
            return False

    def update(self, delta_time: float = 0.0):
        if self.state != GameState.RUNNING:
            return

        pre_x = float(getattr(self.car, "x", 0.0))

        # Try to call car.update(delta_time). If the Car API does not accept dt,
        # advance using speed * delta_time to ensure speed is units per second.
        try:
            self.car.update(delta_time)
        except TypeError:
            speed = float(getattr(self.car, "speed", 0.0))
            self.car.x = pre_x + speed * float(delta_time)
        except Exception:
            speed = float(getattr(self.car, "speed", 0.0))
            self.car.x = pre_x + speed * float(delta_time)

        # Keep rect consistent when Car doesn't update it internally
# Ensure car.x stays within road bounds (avoid leaving world view)
        try:
            self.car.x = max(float(self.road_x_min), min(float(self.road_x_max), float(self.car.x)))
        except Exception:
            pass

        # Keep rect consistent when Car doesn't update it internally
        try:
            if hasattr(self.car, "rect"):
                self.car.rect.x = int(self.car.x)
                self.car.rect.y = int(self.car.y)
        except Exception:
            pass


        self._process_collisions_and_cleanup()

        if not self.car.is_alive() or self.car.x >= self.total_distance:
            self._set_state(GameState.GAME_OVER)

    def _process_collisions_and_cleanup(self):
        visible = self.get_visible_obstacles()
        to_remove: List[Tuple[float, int]] = []

        car_rect = self._get_car_hitbox()

        for obs in visible:
            obs_rect = self._get_obstacle_hitbox(obs)
            if obs_rect and car_rect.colliderect(obs_rect):
                energy_before = getattr(self.car, "energy", None)
                try:
                    ret = self.car.collide(obs)
                except Exception as e:
                    print(f"Warning: Collision error: {e}")
                    ret = False
                if getattr(self.car, "energy", None) is not None and energy_before is not None and self.car.energy < energy_before:
                    to_remove.append((obs["x"], obs["y"]))
                elif ret is True:
                    to_remove.append((obs["x"], obs["y"]))
            else:
                # Remove obstacle only after it has fully left the left side of the screen.
                # Compute obstacle screen x and width.
                sprite_path = obs.get("sprite")
                cache = self.obstacle_manager.get_sprite_cache()
                if sprite_path and sprite_path in cache:
                    surf = cache[sprite_path]
                    w = surf.get_width()
                else:
                    default_size_map = {"cone": (24, 24), "hole": (40, 16)}
                    w, _ = default_size_map.get(obs.get("type"), (48, 48))

                screen_x = float(obs["x"]) - float(self.car.x) + float(self.camera_offset)
                # if right edge is left of screen 0, it's fully out of view
                if (screen_x + w) < 0:
                    to_remove.append((obs["x"], obs["y"]))

        for x, y in to_remove:
            self.remove_obstacle_by_coords(x, y)

    def remove_obstacle_by_coords(self, x: float, y: int):
        self.obstacle_manager.remove_by_coords(x, y)

    def _get_car_hitbox(self) -> pygame.Rect:
        try:
            if hasattr(self.car, 'sprite') and self.car.sprite:
                w, h = self.car.sprite.get_size()
            else:
                w, h = (64, 32)
        except Exception:
            w, h = (64, 32)
        top_world = float(getattr(self.car, "y", 0)) - h
        top_world = max(top_world, float(self.road_y_min))
        top = int(top_world)
        return pygame.Rect(int(self.car.x), top, w, h)

    def _get_obstacle_hitbox(self, obs: Dict) -> Optional[pygame.Rect]:
        try:
            x = int(obs["x"])
            baseline = float(obs["y"])
        except Exception:
            return None
        sprite_path = obs.get("sprite")
        cache = self.obstacle_manager.get_sprite_cache()
        if sprite_path and sprite_path in cache:
            surf = cache[sprite_path]
            w, h = surf.get_size()
        else:
            default_size_map = {"cone": (24, 24), "hole": (40, 16)}
            w, h = default_size_map.get(obs.get("type"), (48, 48))
        top_world = baseline - h
        top_world = max(top_world, float(self.road_y_min))
        return pygame.Rect(x, int(top_world), w, h)
    def get_visible_obstacles(self) -> List[Dict]:
        return self.obstacle_manager.get_visible(self.car.x, self.screen_width)

    def spawn_obstacle(self, obs: Dict):
        try:
            self.obstacle_manager.spawn_obstacle(obs)
        except Exception as e:
            print(f"Warning: Could not spawn obstacle: {e}")

    def get_sprite_cache(self) -> Dict[str, pygame.Surface]:
        return self.obstacle_manager.get_sprite_cache()

    def is_game_over(self) -> bool:
        return self.state == GameState.GAME_OVER

    def serialize_state(self) -> Dict:
        return {
            "car_x": getattr(self.car, "x", 0),
            "car_y": getattr(self.car, "y", 0),
            "energy": getattr(self.car, "energy", 0),
            "remaining_obstacles": len(self.obstacle_manager.get_active_obstacles()),
            "state": self.state
        }