class avlNodo:
    def __init__(self, x: float, y: int, obstacle):
        self.x = x
        self.y = y
        self.key = (x, y)
        self.obstacle = obstacle
        self.left = None
        self.right = None
        self.parent = None
        self.height = 1