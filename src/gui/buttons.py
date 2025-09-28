# src/gui/buttons.py
from typing import Dict, Optional, Tuple
import pygame
from gui.spriteUtils import loadSprite, preloadSprites, getSpriteSize

# Constants (UPPER_SNAKE_CASE)
BUTTON_PADDING: int = 12
DEFAULT_BUTTON_POS: Tuple[int, int] = (20, 20)
FALLBACK_BTN_SIZE: Tuple[int, int] = (70, 70)

# Exported rect name constants so callers (eventHandler/mainWindow) can reference keys safely
START_BTN_RECT_NAME = "START_BTN_RECT"
PAUSE_BTN_RECT_NAME = "PAUSE_BTN_RECT"
TREE_BTN_RECT_NAME = "TREE_BTN_RECT"
GOD_BTN_RECT_NAME = "GOD_BTN_RECT"
RESET_BTN_RECT_NAME = "RESET_BTN_RECT"

# Button keys (camelCase)
START_KEY = "start"
PAUSE_KEY = "pause"
TREE_KEY = "tree"
GOD_KEY = "god"
RESET_KEY = "reset"


def loadButtonSprites(path_map: Dict[str, str],
                      fallback_size: Optional[Tuple[int, int]] = FALLBACK_BTN_SIZE) -> Dict[str, Optional[pygame.Surface]]:
    """
    Load button sprites using spriteUtils and return a mapping from keys to surfaces.

    Args:
        path_map: dict mapping button keys ('start','pause','tree','god') to filesystem paths.
        fallback_size: size for placeholder surfaces when load fails.

    Returns:
        dict mapping the same keys to pygame.Surface or None.
    """
    # Use preloadSprites to centralize loading and caching
    return preloadSprites(path_map, fallbackSize=fallback_size)


def buildButtonRects(sprites: Dict[str, Optional[pygame.Surface]],
                     start_pos: Tuple[int, int] = DEFAULT_BUTTON_POS,
                     padding: int = BUTTON_PADDING) -> Dict[str, pygame.Rect]:
    """
    Build button rects using each sprite's actual width and height. If a sprite is missing
    the function uses FALLBACK_BTN_SIZE for that button.

    Args:
        sprites: dict mapping 'start','pause','tree','god' to pygame.Surface or None.
        start_pos: top-left position for the first button.
        padding: horizontal padding in pixels between buttons.

    Returns:
        dict mapping UPPER_SNAKE_CASE names to pygame.Rect objects:
        'START_BTN_RECT', 'PAUSE_BTN_RECT', 'TREE_BTN_RECT', 'GOD_BTN_RECT'.
    """
    x, y = start_pos
    rects: Dict[str, pygame.Rect] = {}
    keys = [START_KEY, PAUSE_KEY, TREE_KEY, GOD_KEY, RESET_KEY]

    for key in keys:
        surf = sprites.get(key)
        if surf:
            w, h = surf.get_width(), surf.get_height()
        else:
            # if sprite is not present, try to query cached size by path convention
            # otherwise fallback to constant
            w, h = FALLBACK_BTN_SIZE

        rect = pygame.Rect(x, y, w, h)
        name = f"{key.upper()}_BTN_RECT"
        rects[name] = rect

        # advance x by this button width + padding (sizes are sprite-based)
        x += w + padding

    return rects


def drawButton(surface: pygame.Surface,
               rect: pygame.Rect,
               sprite: Optional[pygame.Surface],
               label: str,
               font: pygame.font.Font,
               fallback_color: Tuple[int, int, int] = (120, 160, 200)) -> None:
    """
    Draw a single button using a sprite when available, otherwise draw a fallback rect and label.

    Args:
        surface: destination pygame Surface.
        rect: pygame.Rect where the button is drawn.
        sprite: optional sprite surface to blit.
        label: text label used when sprite is missing.
        font: pygame Font used for fallback label rendering.
        fallback_color: RGB color for the fallback rectangle.
    """
    if sprite:
        surface.blit(sprite, rect.topleft)
    else:
        pygame.draw.rect(surface, fallback_color, rect)
        text = font.render(label, True, (0, 0, 0))
        tx = rect.x + max(8, (rect.width - text.get_width()) // 2)
        ty = rect.y + max(2, (rect.height - text.get_height()) // 2)
        surface.blit(text, (tx, ty))


def drawButtons(surface: pygame.Surface,
                sprites: Dict[str, Optional[pygame.Surface]],
                rects: Dict[str, pygame.Rect],
                font: pygame.font.Font) -> None:
    """
    Draw all HUD buttons. Uses the rects returned by buildButtonRects and the sprites loaded
    by loadButtonSprites (which uses spriteUtils).

    Args:
        surface: destination pygame Surface.
        sprites: mapping 'start','pause','tree','god' to pygame.Surface or None.
        rects: mapping UPPER_SNAKE_CASE rect names to pygame.Rect.
        font: pygame Font for fallback labels.
    """
    mapping = {
        START_KEY: (START_BTN_RECT_NAME, (60, 180, 80), "Start"),
        PAUSE_KEY: (PAUSE_BTN_RECT_NAME, (200, 180, 60), "Pause"),
        TREE_KEY: (TREE_BTN_RECT_NAME, (120, 160, 200), "Tree"),
        GOD_KEY: (GOD_BTN_RECT_NAME, (200, 100, 160), "God"),
        RESET_KEY: (RESET_BTN_RECT_NAME, (200, 160, 80), "Reset")
    }

    for key, (rect_name, color, label) in mapping.items():
        rect = rects.get(rect_name)
        if rect is None:
            continue
        sprite = sprites.get(key)
        drawButton(surface, rect, sprite, label, font, fallback_color=color)