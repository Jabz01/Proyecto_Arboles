import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import networkx as nx
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from networkx.drawing.nx_pydot import graphviz_layout
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

def _draw_with_sprites(G, pos, tree: avlTree):
    """
    Draw nodes using obstacle sprites instead of plain circles.
    """
    ax = plt.gca()

    def _traverse(node: avlNode):
        if not node:
            return
        obs = getattr(node, "obstacle", None)
        if obs:
            sprite_path = obs.get("sprite")
            try:
                img = mpimg.imread(sprite_path)
                imagebox = OffsetImage(img, zoom=1)  # Adjust zoom to scale sprite
                ab = AnnotationBbox(imagebox, pos[node.key], frameon=False)
                ax.add_artist(ab)
                # Add coordinates text under sprite
                x, y = node.key
                ax.text(
                    pos[node.key][0],
                    pos[node.key][1] - 30,
                    f"({int(x)}, {int(y)})",
                    ha="center",
                    va="top",
                    fontsize=8,
                    color="black",
                )
            except Exception as e:
                print(f"[Warn] Could not load sprite {sprite_path}: {e}")
                nx.draw_networkx_nodes(G, pos, nodelist=[node.key],
                                       node_color="lightblue", node_size=1200)
                nx.draw_networkx_labels(G, pos, labels={node.key: str(node.key)}, font_size=8)

        _traverse(node.left)
        _traverse(node.right)

    _traverse(tree.root)

def show_tree(tree: avlTree):
    """
    Visualize the AVL tree and its traversals using matplotlib and networkx.
    """
    if not tree.root:
        print("Tree is empty. Nothing to visualize.")
        return

    G = _build_graph(tree)
    pos = graphviz_layout(G, prog="dot")
    plt.figure(figsize=(10, 8))

    # Draw only edges, nodes will be custom-drawn with sprites
    nx.draw_networkx_edges(G, pos, arrows=False)
    _draw_with_sprites(G, pos, tree)

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
