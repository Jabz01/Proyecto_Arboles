import pygame
import time
from typing import Optional


class Car:
    """
    Player car using baseline semantics:
      - self.x is the world left coordinate
      - self.y is the world baseline (ground) coordinate
    Rects used for collision are in world coordinates: top = baseline - sprite_height.
    _sync_rect_with_baseline keeps self.rect consistent without applying HUD offsets.
    """
    INVULNERABILITY_SECONDS = 0.5

    def __init__(self, x: int, y: int, sprite_path: str, config: dict, energy_max: int = 100):
        self.x = float(x)
        self.y = float(y)  # baseline world coordinate
        self.speed = float(config.get("speed", 0.0))
        self.jump_distance = float(config.get("jumpDistance", 0.0))
        self.color = config.get("carColor", (255, 255, 255))
        self.energy = int(energy_max)
        self.energy_max = int(energy_max)

        # Load sprites (normal and jump)
        try:
            self.normal_sprite = pygame.image.load(sprite_path).convert_alpha()
        except Exception:
            self.normal_sprite = pygame.Surface((64, 32), flags=pygame.SRCALPHA)
            self.normal_sprite.fill((0, 120, 200))
        self.jump_sprite = self._create_brighter_sprite_subtle(self.normal_sprite)
        self.sprite = self.normal_sprite

        # rect stored in world coords (top-left). Initialize and sync with baseline.
        w, h = self.normal_sprite.get_size()
        top = int(self.y - h)
        self.rect = pygame.Rect(int(self.x), top, w, h)
        self._sync_rect_with_baseline()

        # Jump state
        self.is_jumping = False
        self.jump_remaining = 0.0

        # invulnerability timer
        self._last_hit_time = 0.0

    def _create_brighter_sprite_subtle(self, base_sprite: pygame.Surface) -> pygame.Surface:
        """
        Create a subtle brighter version of the base sprite preserving alpha.
        Returns a surface that can be blitted in place of the normal sprite when jumping.
        """
        try:
            w, h = base_sprite.get_size()
            bright = pygame.Surface((w, h), flags=pygame.SRCALPHA)
            base = base_sprite.copy()
            for px in range(w):
                for py in range(h):
                    pr, pg, pb, pa = base.get_at((px, py))
                    if pa == 0:
                        continue
                    nr = min(255, pr + 40)
                    ng = min(255, pg + 40)
                    nb = min(255, pb + 40)
                    bright.set_at((px, py), (nr, ng, nb, pa))
            return bright
        except Exception:
            return base_sprite.copy()

    def _sync_rect_with_baseline(self) -> None:
        """
        Ensure self.rect matches self.x (left) and self.y (baseline) using sprite height.
        IMPORTANT: rect is in world coordinates (do NOT add HUD offsets here).
        Uses rounding to avoid visual jitter and only updates rect if necessary.
        """
        sprite = getattr(self, "sprite", None) or getattr(self, "normal_sprite", None)
        if sprite:
            w, h = sprite.get_size()
        else:
            w, h = (64, 32)

        new_x = round(self.x)
        new_y = round(self.y - h)

        if hasattr(self, "rect") and isinstance(self.rect, pygame.Rect):
            if self.rect.x != new_x or self.rect.y != new_y or self.rect.width != w or self.rect.height != h:
                self.rect.x = new_x
                self.rect.y = new_y
                self.rect.width = w
                self.rect.height = h
        else:
            self.rect = pygame.Rect(new_x, new_y, w, h)

    def move_up(self, lane_height: int, min_y: int = 0) -> None:
        new_y = max(min_y, self.y - lane_height)
        if new_y % lane_height == 0:
            self.y = new_y
            self._sync_rect_with_baseline()

    def move_down(self, lane_height: int, max_y: int = 500) -> None:
        new_y = min(max_y, self.y + lane_height)
        if new_y % lane_height == 0:
            self.y = new_y
            self._sync_rect_with_baseline()
    def jump(self) -> None:
        """
        Begin a jump: sets horizontal jump distance to cover.
        """
        if not self.is_jumping:
            self.is_jumping = True
            self.jump_remaining = float(self.jump_distance)

    def update(self, delta_time: float = 0.0) -> None:
        """
        Advance car horizontally. delta_time is seconds; if zero, use speed as step.
        Keep rect synced to world baseline coordinates.
        """
        if self.is_jumping:
            step = (self.speed * delta_time) if delta_time > 0 else min(self.jump_remaining, self.speed)
            self.x += step
            self.jump_remaining -= step
            if self.jump_remaining <= 0:
                self.is_jumping = False
        else:
            step = (self.speed * delta_time) if delta_time > 0 else self.speed
            self.x += step

        self._sync_rect_with_baseline()

    def collide(self, obstacle: dict) -> bool:
        """
        Apply damage from obstacle if collision counts.
        Returns True if energy decreased.
        Ignores collisions while jumping or during invulnerability window.
        """
        now = time.time()
        if self.is_jumping and self.jump_remaining > 0:
            return False
        if now - getattr(self, "_last_hit_time", 0.0) < self.INVULNERABILITY_SECONDS:
            return False

        damage = int(obstacle.get("damage", 0))
        energy_before = int(self.energy)
        self.energy = max(0, int(self.energy) - damage)
        damaged = self.energy < energy_before
        if damaged:
            self._last_hit_time = now
            print(f"💥 Collision with {obstacle.get('type', 'unknown')}, energy left: {self.energy}")
        return damaged

    def draw(self, surface: pygame.Surface, hud_height: int = 0, road_y_min: float = 0.0, screen_x: Optional[int] = None) -> None:
        """
        Draw the car on the given surface.
        Converts world coords -> screen coords here: screen_y = (top_world - road_y_min + hud_height).
        If screen_x is provided it is used as x on screen (camera offset / anchor); otherwise uses self.x.
        """
        if self.is_jumping and self.jump_remaining > 0 and self.jump_sprite:
            current_sprite = self.jump_sprite
        else:
            current_sprite = self.normal_sprite

        if current_sprite:
            w, h = current_sprite.get_size()
            top_world = self.y - h
            draw_x = int(screen_x if screen_x is not None else self.x)
            draw_y = int(top_world - float(road_y_min) + int(hud_height))
            # clamp to not draw above HUD (optional)
            min_draw_y = int(hud_height)
            draw_y = max(min_draw_y, draw_y)
            surface.blit(current_sprite, (draw_x, draw_y))
        else:
            # fallback rectangle drawn using same convention
            h = getattr(self.rect, "height", 32)
            top_world = self.y - h
            draw_x = int(screen_x if screen_x is not None else self.x)
            draw_y = int(top_world - float(road_y_min) + int(hud_height))
            draw_y = max(int(hud_height), draw_y)
            pygame.draw.rect(surface, (0, 120, 200), pygame.Rect(draw_x, draw_y, 64, h))

    def is_alive(self) -> bool:
        return int(self.energy) > 0