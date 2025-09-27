import pygame   
import time     

class Car:
    """
    Represents the player's car in the game.
    Handles movement, jumping, collisions, and rendering.
    """
    INVULNERABILITY_SECONDS = 0.5  
    def __init__(self, x: int, y: int, sprite_path: str, config: dict, energy_max: int = 100):
        """
        Initializes the Car object.
        """
        self.x = x
        self.y = y
        self.speed = config["speed"]
        self.jump_distance = config["jumpDistance"]
        self.color = config["carColor"]
        self.energy = energy_max
        self.energy_max = energy_max

        # Load normal and jump sprites
        self.normal_sprite = pygame.image.load(sprite_path).convert_alpha()  # load(): loads image, convert_alpha(): keeps transparency returning a surface type that works to pygame 
        self.jump_sprite = self._create_brighter_sprite(self.normal_sprite)
        self.sprite = self.normal_sprite
        self.rect = self.sprite.get_rect(topleft=(self.x, self.y))  # get_rect(): give a rectangle of the sprite taking in the top left the positión in x and y

        # Jump state
        self.is_jumping = False
        self.jump_remaining = 0

    def _create_brighter_sprite(self, base_sprite: pygame.Surface) -> pygame.Surface:
        """
        Make the car brighter if it is jumping
        """
        bright_sprite = base_sprite.copy()  # copy(): duplicates surface
        bright_overlay = pygame.Surface(bright_sprite.get_size(), flags=pygame.SRCALPHA)  # Surface(): create new surface, SRCALPHA: allows transparency
        bright_overlay.fill((255, 255, 255, 80))  # fill(): fill with color RGBA
        bright_sprite.blit(bright_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)  # blit(): draw one surface over another
        return bright_sprite

    def move_up(self, lane_height: int):
        """Moves the car up by one lane."""
        self.y -= lane_height
        self.rect.y = self.y

    def move_down(self, lane_height: int):
        """Moves the car down by one lane."""
        self.y += lane_height
        self.rect.y = self.y

    def jump(self):
        """Initiates a jump with temporary invulnerability."""
        self.is_jumping = True
        self.jump_remaining = self.jump_distance

    def update(self):
        """
        Updates the car's position.
        Handles jump movement and resets jump state when complete.
        """
        if self.is_jumping:
            step = min(self.jump_remaining, self.speed)  # min(): returns the smaller of two values
            self.x += step
            self.jump_remaining -= step
            if self.jump_remaining <= 0:
                self.is_jumping = False
        else:
            self.x += self.speed

        self.rect.x = self.x
        
    def collide(self, obstacle: dict) -> bool:
        """
        Handle collision with an obstacle, applying damage only if not jumping
        and not within an invulnerability window.
        """
        now = time.time()  # time(): current time in seconds since epoch
        if self.is_jumping:
            return False

        # still invulnerable after previous hit
        if now - getattr(self, "_last_hit_time", 0.0) < self.INVULNERABILITY_SECONDS:  # getattr(): get attribute with default value
            return False

        damage = obstacle.get("damage", 0)  # get(): returns dict value with default
        energy_before = self.energy
        self.energy = max(0, self.energy - damage)  # max(): ensures energy doesn’t go below 0
        damaged = self.energy < energy_before
        if damaged:
            self._last_hit_time = now
            print(f"💥 Collision with {obstacle.get('type', 'unknown')}, energy left: {self.energy}")  
        return damaged

    def draw(self, surface: pygame.Surface):
        """
        Draws the car sprite on the given surface.
        Uses bright sprite if jumping.
        """
        current_sprite = self.jump_sprite if self.is_jumping else self.normal_sprite
        surface.blit(current_sprite, (self.x, self.y))  # blit(): draw sprite onto another surface

    def is_alive(self) -> bool:
        """Returns True if the car still has energy."""
        return self.energy > 0
