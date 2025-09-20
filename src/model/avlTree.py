from model import avlNodo

class avlTree:
    def __init__(self):
        self.root = None

    # Implementation of AVL tree insertion
    def insert(self, x: float, y: int, obstacle):
        node = self.search(x, y)
        if node is not None:
            print(f"Node with coordinates ({x}, {y}) already exists.")
        else:
            newNode = avlNodo(x, y, obstacle)
            if self.root is None:
                self.root = newNode
            else:
                self._insert(self.root, newNode)

    def _insert(self, currentNode, newNode):
        if newNode.key < currentNode.key:
            if currentNode.left is None:
                currentNode.left = newNode
                newNode.parent = currentNode
            else:
                self._insert(currentNode.left, newNode)
        else:
            if currentNode.right is None:
                currentNode.right = newNode
                newNode.parent = currentNode
            else:
                self._insert(currentNode.right, newNode)

    # Implementation of search for a node with given coordinates
    def search(self, x: float, y: int):
        if self.root is None:
            print("The tree is empty.")
            return None
        else:
            return self._search(self.root, x, y)
    
    def _search(self, currentNode, x: float, y: int):
        if currentNode is None or currentNode.key == (x, y):
            return currentNode
        if (x, y) < currentNode.key:
            return self._search(currentNode.left, x, y)
        else:
            return self._search(currentNode.right, x, y)
        
    # Find the inorder predecessor of a given node (the maximum node in its left subtree)
    def _findPredecessor(self, node):
        if node.left is not None:
            current = node.left
            while current.right is not None:
                current = current.right
            return current
        return None
    
    # Replace one subtree as a child of its parent with another subtree
    def _replaceNode(self, oldNode, newNode):
        if oldNode.parent is None: # If oldNode is the tree root
            self.root = newNode
        else:
            if oldNode == oldNode.parent.left:
                oldNode.parent.left = newNode
            else:
                oldNode.parent.right = newNode
        if newNode is not None:
            newNode.parent = oldNode.parent

    # Implementation of AVL tree deletion
    def delete(self, x: float, y: int):
        nodeToDelete = self.search(x, y)
        if nodeToDelete is None:
            print(f"Node with coordinates ({x}, {y}) not found.")
        else:
            self._delete(nodeToDelete)
    
    def _delete(self, nodeToDelete):
        # Case 1: Node to delete has no children (leaf node)
        if nodeToDelete.left is None and nodeToDelete.right is None:
            self._replaceNode(nodeToDelete, None)
            return
        
        # Case 2: Node to delete has two children
        if nodeToDelete.left is not None and nodeToDelete.right is not None:
            predecessor = self._findPredecessor(nodeToDelete)
            if predecessor.parent != nodeToDelete: # If predecessor is not the direct child of nodeToDelete
                self._replaceNode(predecessor, predecessor.left)
                predecessor.left = nodeToDelete.left
                predecessor.left.parent = predecessor
            self._replaceNode(nodeToDelete, predecessor)
            predecessor.right = nodeToDelete.right
            predecessor.right.parent = predecessor
            return
        
        # Case 3: Node to delete has one child
        if nodeToDelete.left is not None:
            self._replaceNode(nodeToDelete, nodeToDelete.left)
        else:
            self._replaceNode(nodeToDelete, nodeToDelete.right)

    # Implementation of AVL balancing
    def _detectImbalance(self, node):
        if node is None:
            return 0
        if balanceFactor > 1 or balanceFactor < -1:
            print(f"Imbalance detected at node {node.key} with balance factor {balanceFactor}")
            return node
        self.detectImbalance(node.left)
        self.detectImbalance(node.right)
        node.height = 1 + max(node.left.height, node.right.height)
        balanceFactor = node.left.height - node.right.height
        return balanceFactor

    # Preorder traversal of the tree
    def preorderTraversal(self, node=None):
        if node is None:
            node = self.root
        print(node.key, end=' ')
        if node.left:
            self.preorderTraversal(node.left)
        if node.right:
            self.preorderTraversal(node.right)

    # Inorder traversal of the tree
    def inorderTraversal(self, node=None):
        if node is None:
            node = self.root
        if node.left:
            self.inorderTraversal(node.left)
        print(node.key, end=' ')
        if node.right:
            self.inorderTraversal(node.right)

    # Postorder traversal of the tree
    def postorderTraversal(self, node=None):
        if node is None:
            node = self.root
        if node.left:
            self.postorderTraversal(node.left)
        if node.right:
            self.postorderTraversal(node.right)
        print(node.key, end=' ')

    # Level order traversal of the tree
    def levelOrderTraversal(self):
        if self.root is None:
            return
        queue = [self.root]
        while queue:
            current = queue.pop(0)
            print(current.key, end=' ')
            if current.left:
                queue.append(current.left)
            if current.right:
                queue.append(current.right)
