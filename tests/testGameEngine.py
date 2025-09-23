# testGameEngine.py  -- headless script
import time
import sys
from src.game.gameEngine import GameEngine

# Try to avoid initializing pygame display if pygame is present
try:
    import pygame
    # only init the parts we need (no display)
    pygame.init()
    pygame.display.init()
    pygame.display.quit()
except Exception:
    pygame = None


FRAMES = 300
FPS = 60
JUMP_AT_FRAME = 30
PRINT_EVERY = 10

def run_headless():
    delta_time = 1.0 / FPS

    # Create engine but avoid sprite loading by passing None if your ctor supports it
    engine = GameEngine(config_path="config/config.json",
                        car_sprite_path=None,
                        start_x=0,
                        start_y=31,
                        screen_width=800)

    print("Headless test start")
    print("Initial obstacles:", len(engine._active_obstacles))
    print("Initial energy:", getattr(engine.car, "energy", None))

    for frame in range(1, FRAMES + 1):
        if JUMP_AT_FRAME and frame == JUMP_AT_FRAME and hasattr(engine.car, "jump"):
            print(f"[frame {frame}] car.jump()")
            engine.car.jump()

        # prefer update with delta_time, fallback to no-arg update
        try:
            engine.update(delta_time)
        except TypeError:
            engine.update()

        if frame % PRINT_EVERY == 0 or engine.is_game_over():
            print(f"[frame {frame}] x={getattr(engine.car,'x',None):.1f} energy={getattr(engine.car,'energy',None)} visible={len(engine.get_visible_obstacles())} remaining={len(engine._active_obstacles)} state={engine.state}")

        if engine.is_game_over():
            print("Game over detected.")
            break

    print("Final energy:", getattr(engine.car, "energy", None))
    print("Obstacles remaining:", len(engine._active_obstacles))
    for i, obs in enumerate(engine._active_obstacles[:10]):
        print(f"  remaining[{i}] type={obs.get('type')} x={obs.get('x')} y={obs.get('y')}")

if __name__ == "__main__":
    run_headless()
    sys.exit(0)
