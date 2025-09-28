# src/gui/hud.py
from typing import Dict, Optional, Tuple
import pygame
from gui.spriteUtils import getCachedSprite
from game.gameEngine import GameState

HUD_BG_COLOR = (36, 40, 60)
STAT_TEXT_COLOR = (230, 230, 230)
PALETTE_BG = (28, 28, 36)
PALETTE_BORDER = (200, 200, 200)


def drawEnergyBar(surface: pygame.Surface, x: int, y: int, w: int, h: int, value: float, max_value: float) -> None:
    """
    Draw a horizontal energy bar with color-coded levels.

    Args:
        surface: destination surface.
        x,y,w,h: rectangle where the bar is drawn.
        value: current energy level (0..max_value).
        max_value: maximum energy.
    """
    # Fondo gris
    pygame.draw.rect(surface, (80, 80, 80), pygame.Rect(x, y, w, h))

    # Calcular porcentaje
    pct = max(0.0, min(1.0, (value / float(max_value) if max_value else 0.0)))
    fill_w = int(round(w * pct))

    # Determinar color según nivel
    if pct >= 0.7:
        fill_color = (60, 220, 100)   # verde claro
    elif pct >= 0.4:
        fill_color = (240, 200, 40)   # amarillo
    else:
        fill_color = (220, 60, 60)    # rojo

    # Dibujar barra de energía
    pygame.draw.rect(surface, fill_color, pygame.Rect(x, y, fill_w, h))
    pygame.draw.rect(surface, (0, 0, 0), pygame.Rect(x, y, w, h), 1)

def drawGameStats(surface: pygame.Surface, engine, font: pygame.font.Font, x: int, y: int) -> None:
    """
    Draw compact game statistics.

    Args:
        surface: destination surface.
        engine: GameEngine instance.
        font: pygame Font for text.
        x,y: top-left location to start drawing stats.
    """
    estado = f"Estado: {engine.state}"
    distancia = f"Distancia: {int(getattr(engine.car, 'x', 0))}/{engine.total_distance}"

    surface.blit(font.render(estado, True, STAT_TEXT_COLOR), (x, y))
    surface.blit(font.render(distancia, True, STAT_TEXT_COLOR), (x + 200, y))


def drawPalette(surface: pygame.Surface,
                ui_state: Dict,
                font: pygame.font.Font,
                x: int,
                y: int,
                slot_size: Tuple[int, int] = (48, 48)) -> None:
    """
    Draw the selected template palette UI for GOD_MODE.

    Args:
        surface: destination surface.
        ui_state: dict containing 'palette', 'palette_index', 'selected_template'.
        font: pygame Font used for labels.
        x,y: top-left of the palette panel.
        slot_size: (w,h) size used to draw the sprite slot.
    """
    palette = ui_state.get("palette", [])
    if not palette:
        return

    idx = int(ui_state.get("palette_index", 0)) % len(palette)
    template = palette[idx]
    spr_path = template.get("sprite")
    sprite = getCachedSprite(spr_path) if spr_path else None

    w, h = slot_size
    padding = 8
    panel_w = w + padding * 2 + 120
    panel_h = h + padding * 2

    # panel background and border
    pygame.draw.rect(surface, PALETTE_BG, pygame.Rect(x, y, panel_w, panel_h))
    pygame.draw.rect(surface, PALETTE_BORDER, pygame.Rect(x, y, panel_w, panel_h), 1)

    # draw sprite area
    slot_x = x + padding
    slot_y = y + padding
    slot_rect = pygame.Rect(slot_x, slot_y, w, h)
    pygame.draw.rect(surface, (16, 16, 16), slot_rect)
    if sprite:
        # center sprite in slot; scale if larger
        sw, sh = sprite.get_size()
        if sw > w or sh > h:
            sprite = pygame.transform.smoothscale(sprite, (w, h))
            surface.blit(sprite, (slot_x, slot_y))
        else:
            sx = slot_x + (w - sw) // 2
            sy = slot_y + (h - sh) // 2
            surface.blit(sprite, (sx, sy))
    else:
        # placeholder
        pygame.draw.rect(surface, (80, 80, 80), slot_rect)
        surface.blit(font.render("N/A", True, (200, 200, 200)), (slot_x + 6, slot_y + 6))

    # draw info text: type, damage, index
    info_x = slot_x + w + 12
    surface.blit(font.render(f"{template.get('type','?')}", True, STAT_TEXT_COLOR), (info_x, slot_y))
    surface.blit(font.render(f"Damage: {template.get('damage', '?')}", True, STAT_TEXT_COLOR), (info_x, slot_y + 18))
    surface.blit(font.render(f"{idx+1} / {len(palette)}", True, STAT_TEXT_COLOR), (info_x, slot_y + 36))


def drawHUD(surface: pygame.Surface,
            engine,
            sprites: Dict[str, Optional[pygame.Surface]],
            rects: Dict[str, pygame.Rect],
            font: pygame.font.Font,
            ui_state: Dict,
            hud_height: int) -> None:
    """
    Draw the top HUD including background, stats, buttons area (buttons drawn elsewhere),
    and palette when in GOD_MODE.

    Args:
        surface: destination surface.
        engine: GameEngine instance.
        sprites: button sprites mapping.
        rects: button rects mapping.
        font: pygame Font for label rendering.
        ui_state: shared UI state dict (contains palette info).
        hud_height: height of the HUD in pixels.
    """
    # background strip
    pygame.draw.rect(surface, HUD_BG_COLOR, pygame.Rect(0, 0, surface.get_width(), hud_height))

    # stats block (left)
    drawGameStats(surface, engine, font, x=6, y=8)
    energy = getattr(engine.car, "energy", 0)
    max_energy = getattr(engine.car, "energy_max", 100)
    drawEnergyBar(surface, x=6, y=30, w=200, h=12, value=energy, max_value=max_energy)
    # palette (right) when in GOD_MODE
    if engine.state == "god_mode" or engine.state == GameState.GOD_MODE:
        # place palette centered at bottom with a margin
        panel_width = 200  # ajusta según el ancho real del panel
        panel_height = 100  # ajusta según el alto real del panel
        margin = 12

        panel_x = (surface.get_width() - panel_width) // 2
        panel_y = surface.get_height() - panel_height - margin

        drawPalette(surface, ui_state, font, panel_x, panel_y)
