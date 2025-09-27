import pygame
import unittest
from src.game.obstacleManager import ObstacleManager
from src.model.obstacle import Obstacle

class TestObstacle(unittest.TestCase):
    def setUp(self):
        # Initialize pygame in headless mode (no window)
        pygame.init()
        pygame.display.set_mode((1, 1))
        self.manager = ObstacleManager()

    def tearDown(self):
        pygame.quit()

    def test_spawn_and_remove_obstacle(self):
        obs_data = {"x": 100, "y": 50, "type": "cone", "damage": 10, "sprite": None}
        result = self.manager.spawn_obstacle(obs_data)
        self.assertTrue(result)
        self.assertEqual(len(self.manager.get_active_obstacles()), 1)

        removed = self.manager.remove_by_coords(100, 50)
        self.assertTrue(removed)
        self.assertEqual(len(self.manager.get_active_obstacles()), 0)

    def test_visible_obstacles(self):
        obs1 = {"x": 50, "y": 30, "type": "rock", "damage": 5, "sprite": None}
        obs2 = {"x": 300, "y": 60, "type": "hole", "damage": 8, "sprite": None}
        self.manager.spawn_obstacle(obs1)
        self.manager.spawn_obstacle(obs2)

        visible = self.manager.get_visible(camera_x=0, screen_width=200)
        self.assertIn(obs1, visible)
        self.assertNotIn(obs2, visible)

    def test_obstacle_collision(self):
        obs = Obstacle(120, 60, "rock", 10, None)
        player_rect = pygame.Rect(110, 55, 20, 20) # Player near the obstacle
        self.assertTrue(obs.collides_with(player_rect))

        player_rect_far = pygame.Rect(300, 300, 20, 20)
        self.assertFalse(obs.collides_with(player_rect_far))

if __name__ == "__main__":
    unittest.main()
