import matplotlib.pyplot as plt
import networkx as nx
from model.avlTree import avlTree, avlNode

def _add_edges(G, node: avlNode):
    """Recursive helper to add edges of the AVL tree into the graph G."""
    if node is None:
        return
    if node.left:
        G.add_edge(node.key, node.left.key)
        _add_edges(G, node.left)
    if node.right:
        G.add_edge(node.key, node.right.key)
        _add_edges(G, node.right)

def _build_graph(tree: avlTree):
    """Builds a NetworkX graph from the AVL tree structure."""
    G = nx.DiGraph()
    if tree.root:
        _add_edges(G, tree.root)
    return G

def _get_traversals(tree: avlTree):
    """Return traversals as strings (pre, in, post, level)."""
    # Collect results instead of printing
    def preorder(node, acc):
        if node:
            acc.append(str(node.key))
            preorder(node.left, acc)
            preorder(node.right, acc)

    def inorder(node, acc):
        if node:
            inorder(node.left, acc)
            acc.append(str(node.key))
            inorder(node.right, acc)

    def postorder(node, acc):
        if node:
            postorder(node.left, acc)
            postorder(node.right, acc)
            acc.append(str(node.key))

    def levelorder(root, acc):
        if root is None: return
        q = [root]
        while q:
            cur = q.pop(0)
            acc.append(str(cur.key))
            if cur.left: q.append(cur.left)
            if cur.right: q.append(cur.right)

    pre, ino, post, lvl = [], [], [], []
    preorder(tree.root, pre)
    inorder(tree.root, ino)
    postorder(tree.root, post)
    levelorder(tree.root, lvl)
    return pre, ino, post, lvl

def show_tree(tree: avlTree):
    """
    Visualize the AVL tree and its traversals using matplotlib and networkx.
    """
    if not tree.root:
        print("Tree is empty. Nothing to visualize.")
        return

    G = _build_graph(tree)
    pos = nx.spring_layout(G)
    plt.figure(figsize=(10, 8))
    nx.draw(G, pos, with_labels=True, arrows=False, node_size=2000, 
            node_color="lightblue", font_size=10, font_weight="bold")

    # Traversals
    pre, ino, post, lvl = _get_traversals(tree)
    traversals_text = (
        f"Preorder: {' - '.join(pre)}\n"
        f"Inorder: {' - '.join(ino)}\n"
        f"Postorder: {' - '.join(post)}\n"
        f"Levelorder: {' - '.join(lvl)}"
    )

    # Add traversals text under the plot
    plt.gcf().text(0.1, 0.02, traversals_text, fontsize=10, va="bottom", ha="left",
                   bbox=dict(facecolor="white", alpha=0.7, edgecolor="black"))

    plt.title("AVL Tree Visualization")
    plt.tight_layout()
    plt.show()
