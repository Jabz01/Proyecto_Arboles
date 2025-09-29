from typing import Dict, Optional, Tuple
import math
import pygame
from gui.spriteUtils import getCachedSprite
from game.gameEngine import GameState
from gui.buttons import drawButton, RESET_BTN_RECT_NAME, START_BTN_RECT_NAME

HUD_BG_COLOR = (36, 40, 60)
STAT_TEXT_COLOR = (230, 230, 230)
PALETTE_BG = (28, 28, 36)
PALETTE_BORDER = (200, 200, 200)


def drawEnergyBar(surface: pygame.Surface, x: int, y: int, w: int, h: int, value: float, max_value: float) -> None:
    pygame.draw.rect(surface, (80, 80, 80), pygame.Rect(x, y, w, h))
    pct = max(0.0, min(1.0, (value / float(max_value) if max_value else 0.0)))
    fill_w = int(round(w * pct))
    if pct >= 0.7:
        fill_color = (60, 220, 100)
    elif pct >= 0.4:
        fill_color = (240, 200, 40)
    else:
        fill_color = (220, 60, 60)
    pygame.draw.rect(surface, fill_color, pygame.Rect(x, y, fill_w, h))
    pygame.draw.rect(surface, (0, 0, 0), pygame.Rect(x, y, w, h), 1)


def drawGameStats(surface: pygame.Surface, engine, font: pygame.font.Font, x: int, y: int) -> None:
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
    pygame.draw.rect(surface, PALETTE_BG, pygame.Rect(x, y, panel_w, panel_h))
    pygame.draw.rect(surface, PALETTE_BORDER, pygame.Rect(x, y, panel_w, panel_h), 1)
    slot_x = x + padding
    slot_y = y + padding
    slot_rect = pygame.Rect(slot_x, slot_y, w, h)
    pygame.draw.rect(surface, (16, 16, 16), slot_rect)
    if sprite:
        sw, sh = sprite.get_size()
        if sw > w or sh > h:
            sprite = pygame.transform.smoothscale(sprite, (w, h))
            surface.blit(sprite, (slot_x, slot_y))
        else:
            sx = slot_x + (w - sw) // 2
            sy = slot_y + (h - sh) // 2
            surface.blit(sprite, (sx, sy))
    else:
        pygame.draw.rect(surface, (80, 80, 80), slot_rect)
        surface.blit(font.render("N/A", True, (200, 200, 200)), (slot_x + 6, slot_y + 6))
    info_x = slot_x + w + 12
    surface.blit(font.render(f"{template.get('type','?')}", True, STAT_TEXT_COLOR), (info_x, slot_y))
    surface.blit(font.render(f"Damage: {template.get('damage', '?')}", True, STAT_TEXT_COLOR), (info_x, slot_y + 18))
    surface.blit(font.render(f"{idx+1} / {len(palette)}", True, STAT_TEXT_COLOR), (info_x, slot_y + 36))


# ---------------------------------------------------------------------
# Helper: pixel font
# ---------------------------------------------------------------------
def load_pixel_font(size: int) -> pygame.font.Font:
    try:
        return pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", size)
    except Exception:
        return pygame.font.SysFont("Arial", size, bold=True)


# ---------------------------------------------------------------------
# Helper: centered overlay text with optional bounce
# ---------------------------------------------------------------------
def draw_overlay_text(surface, text, font, color, y_offset=0, bounce=False):
    if bounce:
        bounce_offset = int(6 * math.sin(pygame.time.get_ticks() * 0.005))
    else:
        bounce_offset = 0
    label = font.render(text, True, color)
    lx = (surface.get_width() - label.get_width()) // 2
    ly = (surface.get_height() // 2 - label.get_height() // 2) + y_offset + bounce_offset
    surface.blit(label, (lx, ly))
    return lx, ly, label


def _make_overlay_button_rect(surface, surf, top_y, margin=12):
    if surf:
        sw, sh = surf.get_size()
    else:
        sw, sh = 120, 40
    bx = int((surface.get_width() - sw) // 2)
    by = int(top_y + margin)
    return pygame.Rect(bx, by, sw, sh)


# ---------------------------------------------------------------------
# Pause / Instructions overlay (engine.state == INIT shows this)
# ---------------------------------------------------------------------
def draw_pause_overlay(surface, rects, sprites, font, ui_state: Dict):
    # dark full-screen overlay
    overlay = pygame.Surface(surface.get_size(), flags=pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surface.blit(overlay, (0, 0))

    # Title
    title_font = load_pixel_font(28)
    draw_overlay_text(surface, "CHIVA KILLER", title_font, (255, 215, 0), y_offset=-120, bounce=True)

    # Instructions block (pixel font smaller)
    txt_font = load_pixel_font(12)
    lines = [
        "CONTROLES: Arrow Up/Down = Cambiar carril, Space = Saltar",
        "COMO SE PIERDE: Si la energia llega a 0 al chocar con obstaculos",
        "COMO SE GANA: Llegar a la distancia total (ver config -> totalDistance)",
        "GOD MODE: Activa para colocar obstaculos; pulsa el boton GOD y usa el raton",
        "ARBOL AVL: Obstaculos gestionados en un AVL (ver Tree button para visualizar)",
        "Pulsa Start para comenzar"
    ]
    start_y = surface.get_height() // 2 - 60
    for i, line in enumerate(lines):
        lbl = txt_font.render(line, True, (220, 220, 220))
        lx = (surface.get_width() - lbl.get_width()) // 2
        surface.blit(lbl, (lx, start_y + i * (lbl.get_height() + 6)))

    # Create temporary Start button rect and publish in ui_state
    start_surf = sprites.get("start")
    btn_top = start_y + len(lines) * (txt_font.get_height() + 6) + 8
    btn_rect = _make_overlay_button_rect(surface, start_surf, btn_top, margin=6)
    drawButton(surface, btn_rect, start_surf, "Start", font)
    ov = ui_state.setdefault("overlay_buttons", {})
    ov["start"] = btn_rect


# ---------------------------------------------------------------------
# Lose overlay
# ---------------------------------------------------------------------
def draw_lose_overlay(surface, rects, sprites, font, ui_state: Dict):
    overlay = pygame.Surface(surface.get_size(), flags=pygame.SRCALPHA)
    overlay.fill((30, 0, 0, 220))
    surface.blit(overlay, (0, 0))

    title_font = load_pixel_font(26)
    lx, ly, label = draw_overlay_text(surface, "PERDISTE", title_font, (220, 40, 40), y_offset=-70, bounce=True)

    # skulls
    skull_surf = title_font.render("💀", True, (255, 255, 255))
    surface.blit(skull_surf, (lx - 48, ly))
    surface.blit(skull_surf, (lx + label.get_width() + 20, ly))

    # Reset button
    reset_surf = sprites.get("reset")
    btn_top = ly + label.get_height() + 18
    reset_rect = _make_overlay_button_rect(surface, reset_surf, btn_top, margin=6)
    drawButton(surface, reset_rect, reset_surf, "Reset", font)
    ov = ui_state.setdefault("overlay_buttons", {})
    ov["reset"] = reset_rect


# ---------------------------------------------------------------------
# Win overlay
# ---------------------------------------------------------------------
def draw_win_overlay(surface, rects, sprites, font, ui_state: Dict):
    overlay = pygame.Surface(surface.get_size(), flags=pygame.SRCALPHA)
    overlay.fill((60, 60, 60, 200))
    surface.blit(overlay, (0, 0))

    title_font = load_pixel_font(22)
    lx, ly, label = draw_overlay_text(surface, "¡GANASTE!", title_font, (60, 220, 100), y_offset=-80, bounce=True)

    msg_font = load_pixel_font(12)
    msg = "Eres la mejor chiva fiestera de Paracolombia 🎉"
    msg_label = msg_font.render(msg, True, (255, 255, 255))
    msg_x = (surface.get_width() - msg_label.get_width()) // 2
    msg_y = ly + label.get_height() + 12
    surface.blit(msg_label, (msg_x, msg_y))

    # Continue button
    start_surf = sprites.get("start")
    btn_top = msg_y + msg_label.get_height() + 12
    start_rect = _make_overlay_button_rect(surface, start_surf, btn_top, margin=6)
    drawButton(surface, start_rect, start_surf, "Continue", font)
    ov = ui_state.setdefault("overlay_buttons", {})
    ov["start"] = start_rect


# ---------- HUD principal (NO dibuja Start por defecto) ----------
def drawHUD(surface: pygame.Surface,
            engine,
            sprites: Dict[str, Optional[pygame.Surface]],
            rects: Dict[str, pygame.Rect],
            font: pygame.font.Font,
            ui_state: Dict,
            hud_height: int) -> None:

    # clear overlay buttons when no overlay is visible
    overlay_exists = (engine.state == GameState.PAUSED or engine.state == GameState.INIT) or (not engine.car.is_alive()) or (getattr(engine.car, "x", 0) >= engine.total_distance and engine.car.is_alive())
    if not overlay_exists:
        ui_state.pop("overlay_buttons", None)

    pygame.draw.rect(surface, HUD_BG_COLOR, pygame.Rect(0, 0, surface.get_width(), hud_height))

    # stats
    surface.blit(font.render(f"Estado: {engine.state}", True, STAT_TEXT_COLOR), (6, 8))
    surface.blit(font.render(f"Distancia: {int(getattr(engine.car, 'x', 0))}/{engine.total_distance}", True, STAT_TEXT_COLOR), (206, 8))

    # energy bar
    energy = getattr(engine.car, "energy", 0)
    max_energy = getattr(engine.car, "energy_max", 100)
    drawEnergyBar(surface, x=6, y=30, w=200, h=12, value=energy, max_value=max_energy)

    # palette when in GOD_MODE
    if engine.state == "god_mode" or engine.state == GameState.GOD_MODE:
        panel_width = 200
        panel_height = 100
        margin = 12
        panel_x = (surface.get_width() - panel_width) // 2
        panel_y = surface.get_height() - panel_height - margin
        drawPalette(surface, ui_state, font, panel_x, panel_y)

    # overlays: show INIT instructions, lose, win
    if engine.state == GameState.INIT or engine.state == GameState.PAUSED:
        draw_pause_overlay(surface, rects, sprites, font, ui_state)
    elif not engine.car.is_alive():
        draw_lose_overlay(surface, rects, sprites, font, ui_state)
    elif getattr(engine.car, "x", 0) >= engine.total_distance and engine.car.is_alive():
        draw_win_overlay(surface, rects, sprites, font, ui_state)