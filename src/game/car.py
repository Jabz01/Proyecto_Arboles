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
            x (int): Initial horizontal position of the car.
            y (int): Initial vertical position of the car.
            sprite_path (str): Path to the car's sprite image.
            config (dict): Configuration dictionary loaded from config.json.
                           Must contain 'speed', 'jumpDistance', and 'carColor'.
            energy_max (int): Maximum energy (health) of the car.
        """
        self.x = x
        self.y = y
        self.speed = config.get("speed", 5)
        self.jump_distance = config.get("jumpDistance", 50)
        self.color = config.get("carColor", "#FFFFFF")
        self.energy = energy_max
        self.energy_max = energy_max

        # Load sprite and set position
        self.sprite = pygame.image.load(sprite_path).convert_alpha()
        self.rect = self.sprite.get_rect(topleft=(self.x, self.y))

        # Jump state
        self.is_jumping = False
        self.jump_remaining = 0

    def move_up(self, lane_height: int):
        """
        Moves the car up by one lane.

        Args:
            lane_height (int): Height in pixels of each lane.
        """
        self.y -= lane_height
        self.rect.y = self.y

    def move_down(self, lane_height: int):
        """
        Moves the car down by one lane.

        Args:
            lane_height (int): Height in pixels of each lane.
        """
        self.y += lane_height
        self.rect.y = self.y

    def jump(self):
        """
        Initiates a jump.
        The car will move forward by jumpDistance and be invulnerable
        to obstacles during the jump.
        """
        self.is_jumping = True
        self.jump_remaining = self.jump_distance

    def update(self):
        """
        Updates the car's position.
        If jumping, moves forward by jumpDistance over time and
        disables collision detection until jump ends.
        Otherwise, moves forward at normal speed.
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

        Args:
            surface (pygame.Surface): The surface to draw the car on.
        """
        surface.blit(self.sprite, (self.x, self.y))

    def is_alive(self) -> bool:
        """
        Checks if the car still has energy.

        Returns:
            bool: True if energy > 0, False otherwise.
        """
        return self.energy > 0