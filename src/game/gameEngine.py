from model.avlTree import AvlTree
from game.car import Car
from utils.configLoader import loadConfig

class GameEngine:
    """
    Core game logic controller.
    Manages car movement, obstacle collisions, and game progression.
    """

    def __init__(self, configPath="config.json", spritePath="assets/sprites/car.png", startX=0, startY=31):
        """
        Initializes the game engine with configuration, car, and obstacle tree.

        Args:
            configPath (str): Path to the JSON config file.
            spritePath (str): Path to the car sprite image.
            startX (int): Initial X position of the car.
            startY (int): Initial Y position of the car.
        """
        self.config, self.obstaclesData = loadConfig(configPath)
        self.car = Car(startX, startY, spritePath, self.config)
        self.tree = AvlTree()
        self.totalDistance = self.config["totalDistance"]
        self.screenWidth = 1000

        self._loadObstacles()

    def _loadObstacles(self):
        """
        Inserts all obstacles from config into the AVL tree.
        """
        for obs in self.obstaclesData:
            self.tree.insert(obs["x"], obs["y"], obs)

    def update(self):
        """
        Updates the game state for the current frame.
        Moves the car forward and checks for collisions.
        """
        self.car.update()
        self._checkCollision()

    def _checkCollision(self):
        """
        Checks if the car collides with any obstacle at its current position.
        """
        node = self.tree.search(self.car.x, self.car.y)
        if node and node.obstacle:
            self.car.collide(node.obstacle)
            self.tree.delete(node.key[0], node.key[1])  # Remove obstacle after collision

    def getVisibleObstacles(self):
        """
        Returns a list of obstacles within the visible screen range.

        Returns:
            list: Obstacles with x <= car.x + screenWidth
        """
        visible = []
        maxX = self.car.x + self.screenWidth
        for obs in self.obstaclesData:
            if self.car.x <= obs["x"] <= maxX:
                visible.append(obs)
        return visible

    def isGameOver(self):
        """
        Checks if the game has ended due to energy depletion or reaching the goal.

        Returns:
            bool: True if game is over, False otherwise.
        """
        return not self.car.isAlive() or self.car.x >= self.totalDistance
