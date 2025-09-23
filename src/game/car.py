import pygame

class Car:
    """
    Represents the player's car in the game.
    Handles movement, jumping, collisions, and rendering.
    """

    def __init__(self, x: int, y: int, sprite_path: str, config: dict, energy_max: int = 100):
        """
        Initializes the Car object.

        Args:
            x (int): Initial horizontal position
            y (int): Initial vertical position
            sprite_path (str): path to car sprite
            config (dict): configuration dictionary loaded from config.json. have speed, jumpDistance and energy
            energy_max (int): max health of the car.
        """
        self.x = x
        self.y = y
        self.speed = config["speed"]
        self.jump_distance = config["jumpDistance"]
        self.color = config["carColor"]
        self.energy = energy_max
        self.energy_max = energy_max

        # Load normal and jump sprites
        self.normal_sprite = pygame.image.load(sprite_path).convert_alpha()
        self.jump_sprite = self._create_brighter_sprite(self.normal_sprite)
        self.sprite = self.normal_sprite
        self.rect = self.sprite.get_rect(topleft=(self.x, self.y))

        # Jump state
        self.is_jumping = False
        self.jump_remaining = 0

    def _create_brighter_sprite(self, base_sprite: pygame.Surface) -> pygame.Surface:
        """
        make the car brighter if is jumping

        Args:
            base_sprite (pygame.Surface): Original car sprite.

        Returns:
            pygame.Surface: Brightened sprite surface.
        """
        bright_sprite = base_sprite.copy()
        bright_overlay = pygame.Surface(bright_sprite.get_size(), flags=pygame.SRCALPHA)
        bright_overlay.fill((255, 255, 255, 80))  # White overlay with alpha
        bright_sprite.blit(bright_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
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
            step = min(self.jump_remaining, self.speed)
            self.x += step
            self.jump_remaining -= step
            if self.jump_remaining <= 0:
                self.is_jumping = False
        else:
            self.x += self.speed

        self.rect.x = self.x

    def collide(self, obstacle: dict):
        """
        Handles collision with an obstacle.

        Args:
            obstacle (dict): Obstacle data containing 'damage' and 'type'.
        """
        if not self.is_jumping:
            damage = obstacle.get("damage", 0)
            self.energy -= damage
            if self.energy < 0:
                self.energy = 0
            print(f"💥 Collision with {obstacle.get('type', 'unknown')}, energy left: {self.energy}")

    def draw(self, surface: pygame.Surface):
        """
        Draws the car sprite on the given surface.
        Uses bright sprite if jumping.

        Args:
            surface (pygame.Surface): The surface to draw the car on.
        """
        current_sprite = self.jump_sprite if self.is_jumping else self.normal_sprite
        surface.blit(current_sprite, (self.x, self.y))

    def is_alive(self) -> bool:
        """Returns True if the car still has energy."""
        return self.energy > 0
