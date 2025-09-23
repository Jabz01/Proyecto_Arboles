from model.avlTree import avlTree

def testAVL():
    tree = avlTree()

    print("\n=== INSERT TEST ===")
    nodes_to_insert = [
        # LL case (Right Rotation triggered)
        (30, 1), (20, 2), (10, 3),

        # RR case (Left Rotation triggered)
        (40, 4), (50, 5),

        # LR case (Left-Right Rotation triggered)
        (25, 6),

        # RL case (Right-Left Rotation triggered)
        (45, 7), (8, 20), (9, 10)
    ]

    for x, y in nodes_to_insert:
        print(f"\nInserting ({x}, {y})")
        tree.insert(x, y, obstacle=False)
        print("Tree structure:")
        tree.print_tree()
        print("Inorder: ", end="")
        tree.inorderTraversal()
        print("\nPreorder:", end=" ")
        tree.preorderTraversal()
        print("\nPostOrder:", end=" ")
        tree.postorderTraversal()
        print("\n---")

    print("\n=== DELETE TEST ===")
    nodes_to_delete = [(8, 20), (45, 7), (20, 2)]
    for x, y in nodes_to_delete:
        print(f"\nDeleting ({x}, {y})")
        tree.delete(x, y)
        print("Tree structure:")
        tree.print_tree()
        print("Inorder: ", end="")
        tree.inorderTraversal()
        print("\nPreorder:", end=" ")
        tree.preorderTraversal()
        print("\nLevelOrder:", end=" ")
        tree.levelOrderTraversal()
        print("\n---")


if __name__ == "__main__":
    testAVL()
