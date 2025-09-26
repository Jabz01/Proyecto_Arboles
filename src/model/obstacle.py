import pygame
from typing import Optional, Dict

class Obstacle:
    """
    Represents an obstacle loaded from config.json.
    Coordinates x, y are given in screen pixels.
    """
    def __init__(self, x: int, y: int, type: str, damage: int, sprite: Optional[str]):
        # Screen coordinates (pixels)
        self.x = x
        self.y = y
        self.type = type
        self.damage = int(damage)
        self.sprite_path = sprite

        # Runtime fields
        self.image: Optional[pygame.Surface] = None # Will be loaded when drawing
        self.rect: Optional[pygame.Rect] = None # Pygame.Rect for collisions

    @classmethod
    def from_dict(cls, d: Dict):
        """
        Factory to build an Obstacle from a JSON/dict entry.
        Accepts keys: x, y, type, damage, sprite.
        """
        return cls(int(d["x"]), int(d["y"]), d.get("type"), int(d.get("damage", 0)), d.get("sprite"))

    def to_dict(self) -> Dict:
        """Return a serializable dict similar to original JSON format."""
        return {"x": self.x, "y": self.y, "type": self.type, "damage": self.damage, "sprite": self.sprite_path}

    def get_key(self) -> tuple:
        """
        Returns the unique key for the AVL tree (x first, then y).
        """
        return (self.x, self.y)

    def load_image(self, sprite_cache: Optional[Dict[str, pygame.Surface]] = None):
        """
        Load sprite if available. Uses sprite_cache if provided to avoid reloading.
        Must be called after pygame.init() to succeed.
        """
        if not self.sprite_path:
            return

        # Use cache if provided
        if sprite_cache is not None and self.sprite_path in sprite_cache:
            self.image = sprite_cache[self.sprite_path]
            self.rect = self.image.get_rect(topleft=(self.x, self.y))
            return

        try:
            surf = pygame.image.load(self.sprite_path).convert_alpha()
            self.image = surf
            self.rect = surf.get_rect(topleft=(self.x, self.y))
            if sprite_cache is not None:
                sprite_cache[self.sprite_path] = surf
        except Exception as e:
            # Fallback to rectangle box if sprite missing
            print(f"[WARN] Could not load sprite '{self.sprite_path}': {e}")
            self.image = None
            self.rect = pygame.Rect(self.x, self.y, 40, 40)

    def get_rect(self, camera_x: int = 0) -> pygame.Rect:
        """
        Returns the obstacle Rect **in screen coordinates**, applying camera_x offset.
        camera_x: scroll offset in pixels (how far the world scrolled left).
        """
        if self.image:
            w, h = self.image.get_size()
        else:
            w, h = (40, 40)
        return pygame.Rect(int(self.x - camera_x), int(self.y), int(w), int(h))

    def draw(self, surface: pygame.Surface, camera_x: int = 0):
        """
        Draw the obstacle on the Pygame surface using its sprite or fallback rectangle.
        """
        # Load image if not loaded and pygame available
        if self.image is None and self.sprite_path and pygame.get_init():
            # Not passing a cache here; loader will try load directly
            self.load_image()

        rect = self.get_rect(camera_x)
        if self.image:
            surface.blit(self.image, rect)
        else:
            pygame.draw.rect(surface, (200, 50, 50), rect)

        # Save last rect (useful for collision checks)
        self.rect = rect

    def collides_with(self, other_rect: pygame.Rect, camera_x: int = 0) -> bool:
        """
        Check collision between this obstacle (screen position) and other_rect.
        other_rect is expected to be a pygame.Rect in screen coords.
        """
        return other_rect.colliderect(self.get_rect(camera_x))
