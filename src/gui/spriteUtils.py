# src/gui/spriteUtils.py
import os
from typing import Dict, Optional, Tuple
import pygame

# Constants
SPRITE_CACHE: Dict[str, pygame.Surface] = {}
DEFAULT_FALLBACK_COLOR: Tuple[int, int, int] = (255, 255, 255)
DEFAULT_FALLBACK_ALPHA: int = 120


def _normalizePath(path: str) -> str:
    """
    Normalize a filesystem path for consistent cache keys.

    Args:
        path: original filesystem path.

    Returns:
        Normalized path string.
    """
    return os.path.normpath(path) if path else path


def loadSprite(path: str,
               fallbackSize: Optional[Tuple[int, int]] = None,
               scaleTo: Optional[Tuple[int, int]] = None,
               convertAlpha: bool = True) -> Optional[pygame.Surface]:
    """
    Load a sprite from disk and cache it. If loading fails and fallbackSize is provided,
    return a translucent fallback surface of that size.

    Args:
        path: filesystem path to the image.
        fallbackSize: optional (width, height) for a placeholder surface when load fails.
        scaleTo: optional (width, height) to scale the loaded surface to (preserves original if None).
        convertAlpha: if True, call convert_alpha() on the loaded surface; otherwise convert().

    Returns:
        pygame.Surface loaded or created, or None if loading failed and no fallbackSize given.
    """
    key = _normalizePath(path)
    if key in SPRITE_CACHE:
        return SPRITE_CACHE[key]

    if not path:
        if fallbackSize:
            surf = pygame.Surface(fallbackSize, pygame.SRCALPHA)
            surf.fill((*DEFAULT_FALLBACK_COLOR, DEFAULT_FALLBACK_ALPHA))
            SPRITE_CACHE[key] = surf
            return surf
        return None

    try:
        img = pygame.image.load(path)
        surf = img.convert_alpha() if convertAlpha else img.convert()
        if scaleTo:
            surf = pygame.transform.smoothscale(surf, scaleTo)
        SPRITE_CACHE[key] = surf
        return surf
    except Exception:
        if fallbackSize:
            s = pygame.Surface(fallbackSize, pygame.SRCALPHA)
            s.fill((*DEFAULT_FALLBACK_COLOR, DEFAULT_FALLBACK_ALPHA))
            SPRITE_CACHE[key] = s
            return s
        return None


def getCachedSprite(path: str) -> Optional[pygame.Surface]:
    """
    Return a cached sprite if previously loaded.

    Args:
        path: filesystem path used to load the sprite.

    Returns:
        pygame.Surface if present in cache, otherwise None.
    """
    key = _normalizePath(path)
    return SPRITE_CACHE.get(key)


def clearSpriteCache() -> None:
    """
    Clear the sprite cache. Useful during development or when reloading assets.
    """
    SPRITE_CACHE.clear()


def preloadSprites(pathMap: Dict[str, str],
                   fallbackSize: Optional[Tuple[int, int]] = None) -> Dict[str, Optional[pygame.Surface]]:
    """
    Preload multiple sprites given a mapping of keys to filesystem paths.

    Args:
        pathMap: dict mapping arbitrary keys to sprite paths (e.g., {'start': 'sprites/start.png'}).
        fallbackSize: fallback size for missing sprites.

    Returns:
        dict mapping the same keys to loaded pygame.Surface or fallback/None.
    """
    loaded: Dict[str, Optional[pygame.Surface]] = {}
    for k, p in pathMap.items():
        loaded[k] = loadSprite(p, fallbackSize=fallbackSize)
    return loaded


def getSpriteSize(path: str) -> Tuple[int, int]:
    """
    Return width and height for a sprite. If not cached, attempt to load it (without scaling).
    If loading fails, return (0,0) or the fallbackSize if it was created earlier.

    Args:
        path: filesystem path to the image.

    Returns:
        (width, height) in pixels.
    """
    surf = getCachedSprite(path)
    if surf:
        return surf.get_width(), surf.get_height()
    # try to load without scaling and without fallback
    surf = loadSprite(path, fallbackSize=None)
    if surf:
        return surf.get_width(), surf.get_height()
    return 0, 0