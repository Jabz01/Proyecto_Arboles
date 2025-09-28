## Proyecto_Arboles

An educational project focused on practicing and applying knowledge of **AVL Trees** and their integration into a **game environment** built with `pygame`.

---

## Project Overview

This project combines **data structures** (AVL Trees) with a **2D game** where the player drives along a road while avoiding obstacles.  
The **AVL Tree** is used to store and manage the obstacles efficiently, and you can visualize the tree at runtime.

Key features:
- Interactive game built with **pygame**.
- Obstacles managed and stored in an **AVL Tree**.
- **Tree visualization** with traversals using **matplotlib**, **networkx**, and **Graphviz**.
- Support for different game modes (e.g., GOD_MODE for manual obstacle placement).

---

## Project Structure

Proyecto_Arboles/
├── src/
│   ├── game/              # Game engine and obstacle management
│   ├── gui/               # GUI components (HUD, buttons, preview, event handler)
│   ├── model/             # AVL Tree implementation (avlNode, avlTree)
│   ├── utils/             # Config loader and helper utils
│   ├── main.py            # Entry point for the game
│   └── ...
├── assets/                # Sprites and graphical assets
├── config/                # Game configuration (JSON files)
├── tests/                 # Game development tests
├── requirements.txt
└── README.md

---

## Requirements

Python 3.10+ is recommended.  
Install dependencies with:

```bash
pip install -r requirements.txt
```

⚠️ Important: You also need to install Graphviz on your system and add it to the PATH environment variable.

Download Graphviz here:
https://graphviz.gitlab.io/download/
On Windows, make sure "dot.exe" is accessible from the terminal.

---

## How to Run

1. Clone the repository:

git clone https://github.com/Jabz01/Proyecto_Arboles.git
cd Proyecto_Arboles

2. Run the game:

python src/main.py

--- 

## Controls

- Arrow Up / Arrow Down → Move the car between lanes.
- Space → Jump.
- Enter → Start the game.
- Escape → Pause the game.
- Mouse Click (in GOD_MODE) → Place obstacles manually.
- Buttons on screen:
    - Start → Start the game.
    - Pause → Pause/unpause the game.
    - Tree → Visualize the AVL Tree with traversals.
    - God → Enter GOD_MODE to place obstacles.
    - Reset → Restart the game.

---

## Tree Visualization

When you press the Tree button, a window will open showing:
The AVL Tree structure (drawn with Graphviz).
Traversals (Preorder, Inorder, Postorder, Level order).
This allows you to see how the AVL Tree is storing obstacles at that point in the game.