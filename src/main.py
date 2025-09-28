import pygame
from gui.mainWindow import mainWindow
def main():
    pygame.init()
    try:
        mainWindow()
    except Exception as e:
        print(f"[Error] El juego encontró un problema: {e}")
    finally: 
        pygame.quit()

if __name__ == "__main__":
    main()