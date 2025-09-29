import pygame   
import time     

class Car:
    """
    Represents the player's car in the game.
    Handles movement, jumping, collisions, and rendering.
    """
    INVULNERABILITY_SECONDS = 0.5  
    
    def __init__(self, x: int, y: int, sprite_path: str, config: dict, energy_max: int = 100):
        self.x = x
        self.y = y
        self.speed = config["speed"]
        self.jump_distance = config["jumpDistance"]
        self.color = config["carColor"]
        self.energy = energy_max
        self.energy_max = energy_max

        # Load normal and jump sprites
        self.normal_sprite = pygame.image.load(sprite_path).convert_alpha()
        self.jump_sprite = self._create_brighter_sprite_subtle(self.normal_sprite)
        self.sprite = self.normal_sprite
        self.rect = self.sprite.get_rect(topleft=(self.x, self.y))

        # Jump state
        self.is_jumping = False
        self.jump_remaining = 0

    def _create_brighter_sprite_subtle(self, base_sprite: pygame.Surface) -> pygame.Surface:
        """
        Crear sprite brillante sutil que solo afecte el contenido, no el fondo transparente
        """
        bright_sprite = base_sprite.copy()
        w, h = bright_sprite.get_size()
        
        # Método 1: Overlay blanco suave solo en píxeles no transparentes
        bright_overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        
        # Obtener los datos de píxeles para trabajar solo con píxeles visibles
        for x in range(w):
            for y in range(h):
                pixel = base_sprite.get_at((x, y))
                if pixel[3] > 0:  # Si el pixel no es completamente transparente
                    # Aplicar brillo suave
                    r, g, b, a = pixel
                    # Aumentar brillo sin saturar
                    new_r = min(255, r + 40)
                    new_g = min(255, g + 40) 
                    new_b = min(255, b + 40)
                    bright_overlay.set_at((x, y), (new_r, new_g, new_b, a))
        
        return bright_overlay

    def move_up(self, lane_height: int, min_y: int = 0):
        self.y = max(min_y, self.y - lane_height)
        if hasattr(self, "rect"):
            self.rect.y = int(self.y)

    def move_down(self, lane_height: int, max_y: int = 500):
        self.y = min(max_y, self.y + lane_height)
        if hasattr(self, "rect"):
            self.rect.y = int(self.y)

    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.jump_remaining = self.jump_distance

    def update(self, delta_time: float = 0.0):
        if self.is_jumping:
            step = self.speed * delta_time if delta_time > 0 else min(self.jump_remaining, self.speed)
            self.x += step
            self.jump_remaining -= step
            if self.jump_remaining <= 0:
                self.is_jumping = False
        else:
            movement = self.speed * delta_time if delta_time > 0 else self.speed
            self.x += movement

        self.rect.x = self.x
        
    def collide(self, obstacle: dict) -> bool:
        now = time.time()

        if self.is_jumping and self.jump_remaining > 0:
            return False

        if now - getattr(self, "_last_hit_time", 0.0) < self.INVULNERABILITY_SECONDS:
            return False

        damage = obstacle.get("damage", 0)
        energy_before = self.energy
        self.energy = max(0, self.energy - damage)
        damaged = self.energy < energy_before
        
        if damaged:
            self._last_hit_time = now
            print(f"💥 Collision with {obstacle.get('type', 'unknown')}, energy left: {self.energy}")
        
        return damaged
    
    def draw(self, surface: pygame.Surface):
        """
        Draws the car sprite with dynamic brightness during jump
        """
        if self.is_jumping and self.jump_remaining > 0:
            current_sprite = self.jump_sprite
        else:
            current_sprite = self.normal_sprite
            
        surface.blit(current_sprite, (self.x, self.y))

    def is_alive(self) -> bool:
        return self.energy > 0