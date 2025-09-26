# src/main.py

import pygame
from gui.mainWindow import main
def main():
    pygame.init()
    try:
        main()
    except Exception as e:
        print(f"[Error] El juego encontró un problema: {e}")
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()