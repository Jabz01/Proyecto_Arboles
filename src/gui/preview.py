# src/gui/preview.py
from typing import Tuple, Optional, Dict
import pygame

DEFAULT_LANES = 8


def screenToWorld(mouse_x: int, mouse_y: int, engine, hud_height: int, car_screen_x: int) -> Tuple[Tuple[float, int], bool]:
    x_min, x_max, y_min, y_max = engine.get_road_bounds()
    game_area_h = int(y_max - y_min)
    if mouse_y < hud_height or mouse_y >= hud_height + game_area_h:
        return ((0.0, 0), False)

    world_x = float(engine.car.x) + float(mouse_x - car_screen_x)
    world_y = int(mouse_y - hud_height + y_min)
    return ((world_x, world_y), True)


def getSnappedPosition(world_pos: Tuple[float, int], engine, lanes: int = DEFAULT_LANES) -> Tuple[float, int]:
    wx, wy = world_pos
    x_min, x_max, y_min, y_max = engine.get_road_bounds()
    total_h = float(y_max - y_min)
    if total_h <= 0 or lanes <= 0:
        return (float(wx), int(round(wy)))

    lane_h = total_h / float(lanes)
    rel = float(wy - y_min) / lane_h
    lane_index = int(round(rel))
    lane_index = max(0, min(lanes, lane_index))
    snapped_y = int(round(y_min + lane_index * lane_h))
    return (float(wx), snapped_y)


def validatePreview(world_pos: Tuple[float, int], engine, template: Optional[Dict] = None, margin: float = 4.0) -> bool:
    tpl_type = template.get("type") if template else "cone"
    snapped = getSnappedPosition(world_pos, engine)
    return engine.can_place_obstacle(float(snapped[0]), int(snapped[1]), margin=margin, obstacle_type=tpl_type)


def drawPreview(surface: pygame.Surface,
                world_pos: Tuple[float, int],
                engine,
                preview_sprite: Optional[pygame.Surface],
                valid: bool,
                hud_height: int,
                car_screen_x: int,
                alpha: int = 160) -> None:
    snapped_x, snapped_y = getSnappedPosition(world_pos, engine)

    # clamp to road bounds
    x_min, x_max, y_min, y_max = engine.get_road_bounds()
    snapped_x = max(float(x_min), min(float(x_max), snapped_x))
    snapped_y = max(int(y_min), min(int(y_max), snapped_y))

    # world -> screen
    screen_x = int(snapped_x - float(engine.car.x) + car_screen_x)
    screen_y = int(snapped_y - y_min + hud_height)

    color = (40, 200, 40) if valid else (200, 40, 40)
    if preview_sprite:
        try:
            sw, sh = preview_sprite.get_size()
            surface.blit(preview_sprite, (screen_x, screen_y))
            overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            overlay.fill((*color, alpha))
            surface.blit(overlay, (screen_x, screen_y))
        except Exception:
            w, h = 48, 48
            rect = pygame.Rect(screen_x, screen_y, w, h)
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((*color, alpha))
            surface.blit(overlay, rect.topleft)
            pygame.draw.rect(surface, (0, 0, 0), rect, 1)
    else:
        w, h = 48, 48
        rect = pygame.Rect(screen_x, screen_y, w, h)
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((*color, alpha))
        surface.blit(overlay, rect.topleft)
        pygame.draw.rect(surface, (0, 0, 0), rect, 1)