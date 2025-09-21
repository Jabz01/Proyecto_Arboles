from model.avlNode import avlNode

class avlTree:
    def __init__(self):
        self.root = None

    # Implementation of AVL tree insertion
    def insert(self, x: float, y: int, obstacle):
        node = self.search(x, y)
        if node is not None:
            print(f"Node with coordinates ({x}, {y}) already exists.")
        else:
            if self.root is None:
                self.root = avlNode(x,y, obstacle)
            else:
                self.root = self._insert(self.root, x,y, obstacle)

    def _insert(self, node, x, y, obstacle):
        if not node:
            return avlNode(x,y, obstacle)
        
        if (x,y) < node.key:
            node.left = self._insert(node.left, x,y,obstacle)
            if node.left:
                node.left.parent = node #Keep parent references for new nodes

        else:
            node.right = self._insert(node.right, x,y,obstacle)
            if node.right:
                node.right.parent = node

        #AVL Balance
        
        #Height for the new node
        node.height = 1 + max(self.getHeight(node.left), self.getHeight(node.right))
        
        #Balance for the new node
        balance = self.getBalance(node)

        node = self.imbalanceCases(node)
        return node
    
    # Implementation of search for a node with given coordinates
    def search(self, x: float, y: int):
        if self.root is None:
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
        # Case 1: Leaf, no children
        if nodeToDelete.left is None and nodeToDelete.right is None:
            parent = nodeToDelete.parent
            self._replaceNode(nodeToDelete, None)
            if parent:  # avoid empty tree case 
                self._rebalanceUp(parent)
            return
        
        # Case 2: two children
        if nodeToDelete.left is not None and nodeToDelete.right is not None:
            predecessor = self._findPredecessor(nodeToDelete)
            if predecessor.parent != nodeToDelete: # If predecessor is not the direct child of nodeToDelete
                self._replaceNode(predecessor, predecessor.left)
                predecessor.left = nodeToDelete.left
                predecessor.left.parent = predecessor
            self._replaceNode(nodeToDelete, predecessor)
            predecessor.right = nodeToDelete.right
            predecessor.right.parent = predecessor
            self._rebalanceUp(predecessor)
            return
        
        # Case 3: one child  
        #Child, verifies if exist a left child if not, takes the right one
        #yes or yes there will be a child 
        child = nodeToDelete.left if nodeToDelete.left else nodeToDelete.right
        self._replaceNode(nodeToDelete, child)
        self._rebalanceUp(child)
    
            
    def getHeight(self, node):
        if not node:
            return 0
        return node.height
    
    def getBalance(self, node):
        if not node:
            return 0
        return self.getHeight(node.left) - self.getHeight(node.right)
    
    def _rebalanceUp(self, node):
        """
        Walk up from `node` to root, updating heights and rebalancing.
        Ensures the parent's child pointer is updated after a rotation.
        """
        while node:
            # update height
            node.height = 1 + max(self.getHeight(node.left), self.getHeight(node.right))

            # store parent BEFORE rebalance (because rebalance may change node.parent)
            parent = node.parent

            # rebalance this subtree; imbalanceCases returns the new root of this subtree
            new_subroot = self.imbalanceCases(node)

            # attach new_subroot to parent (or set as tree root)
            if parent is None:
                # this subtree is at top level -> update global root
                self.root = new_subroot
                if new_subroot:
                    new_subroot.parent = None
            else:
                # attach to the correct side of parent
                if parent.left is node:
                    parent.left = new_subroot
                else:
                    parent.right = new_subroot
                if new_subroot:
                    new_subroot.parent = parent

            # move up
            node = parent
      
    # Cases for imbalance
    def imbalanceCases(self, node):
        """
        Rebalance this subtree rooted at `node` and return the new root of the subtree.
        Uses child balances (standard AVL logic), so it is safe tanto para insert como delete.
        """
        if node is None:
            return node

        balance = self.getBalance(node)

        # LEFT heavy
        if balance > 1:
            # if left child is left-heavy or balanced -> LL
            if self.getBalance(node.left) >= 0:
                print(f"LL Rotation at node {node.key}")
                return self.rightRotation(node)
            else:
                # LR case
                print(f"LR Rotation at node {node.key}")
                node.left = self.leftRotation(node.left)
                if node.left:
                    node.left.parent = node
                return self.rightRotation(node)

        # RIGHT heavy
        if balance < -1:
            # if right child is right-heavy or balanced -> RR
            if self.getBalance(node.right) <= 0:
                print(f"RR Rotation at node {node.key}")
                return self.leftRotation(node)
            else:
                # RL case
                print(f"RL Rotation at node {node.key}")
                node.right = self.rightRotation(node.right)
                if node.right:
                    node.right.parent = node
                return self.leftRotation(node)

        # no change needed
        return node

        
    
    def rightRotation(self, node):
        newRoot = node.left
        temp = newRoot.right
                                                        
        # Rotate
        newRoot.right = node
        node.left = temp

        # Update parents
        if temp:
            temp.parent = node
        newRoot.parent = node.parent
        node.parent = newRoot

        # Update heights
        node.height = 1 + max(self.getHeight(node.left), self.getHeight(node.right))
        newRoot.height = 1 + max(self.getHeight(newRoot.left), self.getHeight(newRoot.right))

        return newRoot
    
    def leftRotation(self, node):
        newRoot = node.right
        temp = newRoot.left

        # Rotate
        newRoot.left = node
        node.right = temp

        # Update parents
        if temp:
            temp.parent = node
        newRoot.parent = node.parent
        node.parent = newRoot

        # Update heights
        node.height = 1 + max(self.getHeight(node.left), self.getHeight(node.right))
        newRoot.height = 1 + max(self.getHeight(newRoot.left), self.getHeight(newRoot.right))

        return newRoot
      
    # Preorder traversal of the tree
    def preorderTraversal(self, node=None):
        if node is None:
            node = self.root
        if node is  not None:
            print(node.key, end=' ')
            if node.left:
                self.preorderTraversal(node.left)
            if node.right:
                self.preorderTraversal(node.right)

    # Inorder traversal of the tree
    def inorderTraversal(self, node=None):
        if node is None:
            node = self.root
        if node is not None:
            if node.left:
                self.inorderTraversal(node.left)
            print(node.key, end=' ')
            if node.right:
                self.inorderTraversal(node.right)

    # Postorder traversal of the tree
    def postorderTraversal(self, node=None):
        if node is None:
            node = self.root
        if node is not None:
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

    def print_tree(self, node=None, prefix="", is_left=True):
        if node is None:
            node = self.root
        if node is None:  # Empty tree
            print("Tree is empty")
            return

        # Print right subtree
        if node.right:
            new_prefix = prefix + ("│   " if is_left else "    ")
            self.print_tree(node.right, new_prefix, False)

        # Print current node (show key instead of value)
        connector = "└── " if is_left else "┌── "
        print(prefix + connector + str(node.key))

        # Print left subtree
        if node.left:
            new_prefix = prefix + ("    " if is_left else "│   ")
            self.print_tree(node.left, new_prefix, True)


