import sys
import pygame
from game.gameEngine import GameEngine, GameState

# --- Layout / constants ---
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
FPS = 60

HUD_HEIGHT = 100
GAME_AREA_HEIGHT = 500
BOTTOM_HEIGHT = 168

CAR_SCREEN_X = 100            # camera X where the car is drawn on screen
BUTTON_PADDING = 12

# Button positions in HUD (x, y, w, h)
BTN_W, BTN_H = 96, 48
START_BTN_RECT = pygame.Rect(20, 20, BTN_W, BTN_H)
PAUSE_BTN_RECT = pygame.Rect(20 + BTN_W + BUTTON_PADDING, 20, BTN_W, BTN_H)
TREE_BTN_RECT  = pygame.Rect(20 + 2*(BTN_W + BUTTON_PADDING), 20, BTN_W, BTN_H)
GOD_BTN_RECT   = pygame.Rect(20 + 3*(BTN_W + BUTTON_PADDING), 20, BTN_W, BTN_H)

# Preview obstacle visual size (fallback)
PREVIEW_SIZE = (48, 48)

# --- Helpers ---
def draw_text(surface, text, pos, font, color=(255,255,255)):
    surface.blit(font.render(text, True, color), pos)

def load_sprite(path, fallback_size=None):
    try:
        surf = pygame.image.load(path).convert_alpha()
        return surf
    except Exception:
        if fallback_size:
            s = pygame.Surface(fallback_size, pygame.SRCALPHA)
            s.fill((255, 255, 255, 100))
            return s
        return None

def screen_to_world(mouse_x, mouse_y, engine):
    """
    Convert mouse screen coords to world coords.
    Returns (world_x, world_y) and a bool indicating if mouse is inside game area.
    """
    # reject if in HUD or bottom bar
    if mouse_y < HUD_HEIGHT or mouse_y >= HUD_HEIGHT + GAME_AREA_HEIGHT:
        return (0.0, 0), False
    # world_x: car.x + (mouse_x - CAR_SCREEN_X)
    world_x = engine.car.x + (mouse_x - CAR_SCREEN_X)
    world_y = mouse_y - HUD_HEIGHT
    return (world_x, world_y), True

# --- Main ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Main Window - Game Test")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 20)

    # --- Load button sprites (names provided) ---
    sprites = {}
    sprites['start'] = load_sprite("sprites/startButton.png", (BTN_W, BTN_H))
    sprites['pause'] = load_sprite("sprites/pauseButton.png", (BTN_W, BTN_H))
    sprites['tree'] = load_sprite("sprites/treeButton.png", (BTN_W, BTN_H))
    sprites['god'] = load_sprite("sprites/godButton.png", (BTN_W, BTN_H))

    # --- Engine ---
    engine = GameEngine(config_path="config/config.json",
                        car_sprite_path="assets/sprites/chiva.png",
                        start_x=0, start_y=31, screen_width=WINDOW_WIDTH)
    # start engine from INIT explicitly
    engine.start()

    # optional: UI hooks
    def on_state_change(new):
        print(f"[Engine] state -> {new}")
    engine.on_state_change = on_state_change

    # preview settings
    preview_type = "cone"  # default obstacle type when placing
    preview_sprite = load_sprite("sprites/preview_cone.png", PREVIEW_SIZE)
    preview_visible = False
    preview_valid = False
    preview_world = (0.0, 0)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False

                # Start button behavior: when pressed from PAUSED/GOD_MODE -> RUNNING
                elif ev.key == pygame.K_RETURN:
                    engine.start()

                # space still maps to car.jump if running
                elif ev.key == pygame.K_SPACE and engine.state == GameState.RUNNING:
                    if hasattr(engine.car, "jump"):
                        engine.car.jump()

            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                # HUD button clicks
                if START_BTN_RECT.collidepoint(mx, my):
                    # Start button: if in GOD_MODE or PAUSED, go to RUNNING
                    engine.start()
                    # exit god mode if accidentally left
                    if engine.state == GameState.GOD_MODE:
                        engine.exit_god_mode()
                elif PAUSE_BTN_RECT.collidepoint(mx, my):
                    engine.toggle_pause()
                elif TREE_BTN_RECT.collidepoint(mx, my):
                    # tree button placeholder: could toggle AVL view
                    print("[UI] Tree button pressed")
                elif GOD_BTN_RECT.collidepoint(mx, my):
                    # toggle god mode: if not in GOD_MODE, enter; if in GOD_MODE, exit to PAUSED
                    if engine.state != GameState.GOD_MODE:
                        engine.enter_god_mode()
                    else:
                        engine.exit_god_mode()
                else:
                    # If click inside game area while in GOD_MODE and preview valid -> place obstacle
                    (world, in_game) = screen_to_world(mx, my, engine)
                    if engine.state == GameState.GOD_MODE and in_game and preview_valid:
                        obs = {
                            "x": world[0] if isinstance(world, tuple) else world,
                            "y": int(world[1] if isinstance(world, tuple) else 0),
                            "type": preview_type,
                            "sprite": f"assets/sprites/{preview_type}.png",
                            "damage": 1
                        }
                        inserted = engine.place_obstacle(obs)
                        if inserted:
                            print("[UI] obstacle placed:", obs)
                            # exit god mode and leave engine paused; user must press Start to resume
                            engine.exit_god_mode()
                            preview_visible = False

            elif ev.type == pygame.MOUSEMOTION:
                mx, my = ev.pos
                (world, in_game) = screen_to_world(mx, my, engine)
                if in_game:
                    # world is a tuple (world_x, world_y)
                    world_x, world_y = world if isinstance(world, tuple) else (world, 0)
                    preview_world = (world_x, world_y)
                    preview_visible = True
                    # clamp to road bounds when validating
                    x_min, x_max, y_min, y_max = engine.get_road_bounds()
                    clamped_x = max(min(world_x, x_max), x_min)
                    clamped_y = max(min(world_y, y_max), y_min)
                    preview_valid = engine.can_place_obstacle(clamped_x, clamped_y)
                else:
                    preview_visible = False
                    preview_valid = False

        # --- Engine update ---
        # engine.update only when RUNNING (engine enforces this internally)
        engine.update(dt)

        # --- Rendering ---
        screen.fill((18, 18, 18))

        # HUD top
        pygame.draw.rect(screen, (36, 40, 60), pygame.Rect(0, 0, WINDOW_WIDTH, HUD_HEIGHT))
        # draw buttons
        if sprites['start']:
            screen.blit(sprites['start'], START_BTN_RECT.topleft)
        else:
            pygame.draw.rect(screen, (60,180,80), START_BTN_RECT)
            draw_text(screen, "Start", (START_BTN_RECT.x+10, START_BTN_RECT.y+12), font, (0,0,0))

        if sprites['pause']:
            screen.blit(sprites['pause'], PAUSE_BTN_RECT.topleft)
        else:
            pygame.draw.rect(screen, (200,180,60), PAUSE_BTN_RECT)
            draw_text(screen, "Pause", (PAUSE_BTN_RECT.x+10, PAUSE_BTN_RECT.y+12), font, (0,0,0))

        if sprites['tree']:
            screen.blit(sprites['tree'], TREE_BTN_RECT.topleft)
        else:
            pygame.draw.rect(screen, (120,160,200), TREE_BTN_RECT)
            draw_text(screen, "Tree", (TREE_BTN_RECT.x+10, TREE_BTN_RECT.y+12), font, (0,0,0))

        if sprites['god']:
            screen.blit(sprites['god'], GOD_BTN_RECT.topleft)
        else:
            pygame.draw.rect(screen, (200,100,160), GOD_BTN_RECT)
            draw_text(screen, "God", (GOD_BTN_RECT.x+10, GOD_BTN_RECT.y+12), font, (0,0,0))

        # HUD texts
        draw_text(screen, f"State: {engine.state}", (600, 12), font)
        draw_text(screen, f"Energy: {getattr(engine.car, 'energy', '?')}", (600, 32), font)
        draw_text(screen, f"Distance: {int(getattr(engine.car, 'x', 0))}/{engine.total_distance}", (600, 52), font)
        draw_text(screen, "Press Enter to Start; God toggles placement mode", (600, 72), font)

        # Game area background (draw road placeholder or background image if available)
        try:
            bg = pygame.image.load("assets/roda.png").convert()
            screen.blit(bg, (0, HUD_HEIGHT))
        except Exception:
            pygame.draw.rect(screen, (80,80,80), pygame.Rect(0, HUD_HEIGHT, WINDOW_WIDTH, GAME_AREA_HEIGHT))

        # Draw visible obstacles
        for obs in engine.get_visible_obstacles():
            sprite = None
            sprite_path = obs.get("sprite")
            if sprite_path and sprite_path in engine._sprite_cache:
                sprite = engine._sprite_cache[sprite_path]
            x_screen = int(obs["x"] - engine.car.x + CAR_SCREEN_X)
            y_screen = int(obs["y"]) + HUD_HEIGHT
            if sprite:
                screen.blit(sprite, (x_screen, y_screen))
            else:
                pygame.draw.rect(screen, (200,80,80), pygame.Rect(x_screen, y_screen, 48, 48))

        # Draw car at fixed screen x
        car_y_screen = int(engine.car.y) + HUD_HEIGHT
        if hasattr(engine.car, "sprite") and getattr(engine.car, "sprite", None):
            screen.blit(engine.car.sprite, (CAR_SCREEN_X, car_y_screen))
        else:
            pygame.draw.rect(screen, (100,200,100), pygame.Rect(CAR_SCREEN_X, car_y_screen, 64, 32))

        # Bottom area (tree button region)
        bottom_y = HUD_HEIGHT + GAME_AREA_HEIGHT
        pygame.draw.rect(screen, (40,40,100), pygame.Rect(0, bottom_y, WINDOW_WIDTH, BOTTOM_HEIGHT))
        pygame.draw.rect(screen, (70,90,160), pygame.Rect(20, bottom_y + 20, 220, 48))
        draw_text(screen, "Show AVL Tree", (36, bottom_y + 32), font)

        # Preview rendering when in GOD_MODE and mouse over game area
        if preview_visible:
            # compute preview screen position clamped to road bounds
            world_x, world_y = preview_world
            x_min, x_max, y_min, y_max = engine.get_road_bounds()
            clamped_x = max(min(world_x, x_max), x_min)
            clamped_y = max(min(world_y, y_max), y_min)
            preview_screen_x = int(clamped_x - engine.car.x + CAR_SCREEN_X)
            preview_screen_y = int(clamped_y) + HUD_HEIGHT

            # color by validity
            color = (40, 200, 40, 140) if preview_valid else (200, 40, 40, 100)
            # draw translucent rect as preview
            preview_surf = pygame.Surface(PREVIEW_SIZE, pygame.SRCALPHA)
            preview_surf.fill((*color[:3], 120))
            screen.blit(preview_surf, (preview_screen_x, preview_screen_y))
            # draw sprite if available
            if preview_sprite:
                screen.blit(preview_sprite, (preview_screen_x, preview_screen_y))

            # if inside GOD_MODE, render hint
            if engine.state == GameState.GOD_MODE:
                draw_text(screen, "GOD MODE: Click to place; Exit -> leaves PAUSED; Start to resume", (230, 12), font, (255, 220, 120))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()