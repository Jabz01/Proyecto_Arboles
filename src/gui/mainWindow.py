# src/mainWindow.py
import pygame
from typing import Dict, Optional, List
from game.gameEngine import GameEngine
from gui.buttons import loadButtonSprites, buildButtonRects, drawButtons
from gui.hud import drawHUD
from gui.preview import drawPreview, screenToWorld, getSnappedPosition
from gui.eventHandler import handleEvent
from gui.spriteUtils import loadSprite, getCachedSprite
from gui.treeVisualizer import show_tree
from utils.configLoader import load_config

# Layout constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
HUD_HEIGHT = 100
GAME_AREA_HEIGHT = 500
FPS = 60
CAR_SCREEN_X = 1

def mainWindow():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Chiva killer")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 16)

    # Load config and palette
    config, _ = load_config("config/config.json")
    palette = config.get("obstaclePalette", [])

    # Preload palette sprites (reduces hitches when entering GOD_MODE)
    for tpl in palette:
        loadSprite(tpl.get("sprite", ""), fallbackSize=(48, 48))

    # Preload button and world sprites
    button_paths = {
        "start": "assets/sprites/startButton.png",
        "pause": "assets/sprites/pauseButton.png",
        "tree": "assets/sprites/treeButton.png",
        "god": "assets/sprites/godButton.png",
        "reset": "assets/sprites/resetButton.png"
    }
    for p in button_paths.values():
        loadSprite(p, fallbackSize=(70, 70))

    background = loadSprite("assets/sprites/road.png", fallbackSize=(SCREEN_WIDTH, GAME_AREA_HEIGHT))

    # Initialize engine with camera_offset (anchor on screen)
    engine = GameEngine(config_path="config/config.json", screen_width=SCREEN_WIDTH, camera_offset=CAR_SCREEN_X)
    engine.reset()                        
    engine.car.x = float(engine.road_x_min)
    engine.car.y = int(engine.road_y_min)        

    # Anchor used by UI/preview/drawing (read from engine so both agree)
    car_screen_x = engine.camera_offset

    # Force car to start exactly at road start
    engine.car.x = float(engine.road_x_min)
    engine.car.y = int(engine.road_y_min)




    # Load button sprites and place them aligned to the right
    button_sprites = loadButtonSprites(button_paths)
    keys_order = ["start", "pause", "tree", "god", "reset"]
    # measure total width of the buttons (use fallback if sprite missing)
    button_w_list = []
    for k in keys_order:
        s = button_sprites.get(k)
        button_w_list.append(s.get_width() if s else 70)
    BUTTON_PADDING = 12
    total_buttons_w = sum(button_w_list) + (len(button_w_list) - 1) * BUTTON_PADDING
    start_x = SCREEN_WIDTH - 20 - total_buttons_w
    button_rects = buildButtonRects(button_sprites, start_pos=(start_x, 20), padding=BUTTON_PADDING)

    # UI state that other modules read/write
    ui_state: Dict = {
        "screenToWorld": lambda mx, my, eng: screenToWorld(mx, my, eng, HUD_HEIGHT, car_screen_x),
        "getSnappedPosition": getSnappedPosition,
        "palette": palette,
        "palette_index": 0,
        "selected_template": palette[0] if palette else {},
        "preview_visible": False,
        "preview_world": (0.0, 0),
        "preview_valid": False,
    }

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # seconds
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                tree_btn = button_rects.get("tree")
                if tree_btn and tree_btn.collidepoint(ev.pos):
                    show_tree(engine.obstacle_manager.tree)
                else:
                    handleEvent(ev, engine, ui_state, button_rects)
            else:
                handleEvent(ev, engine, ui_state, button_rects)

        # Update engine with delta-time
        engine.update(dt)
        # Clear and draw background
        screen.fill((0, 0, 0))
        if background:
            screen.blit(background, (0, HUD_HEIGHT))
        else:
            pygame.draw.rect(screen, (50, 50, 50), pygame.Rect(0, HUD_HEIGHT, SCREEN_WIDTH, GAME_AREA_HEIGHT))

              # Draw visible obstacles using baseline -> top = baseline - sprite_h,
        # then convert world top to screen y using road_y_min and HUD_HEIGHT.
        world_left = float(engine.car.x) - float(engine.camera_offset)
        visible: List[Dict] = engine.obstacle_manager.get_visible(world_left, SCREEN_WIDTH)
        cache = engine.get_sprite_cache()
        for obs in visible:
            sprite_path = obs.get("sprite")
            sprite = cache.get(sprite_path) if sprite_path else None
            sx = int(obs["x"] - engine.car.x + car_screen_x)

            obs_baseline = float(obs["y"])
            if sprite:
                sh = sprite.get_height()
                # top in world coords (baseline -> top)
                top_world = obs_baseline - sh
            else:
                sh = 24
                top_world = obs_baseline - sh

            # Convert world top to screen y
            sy = int(top_world - engine.road_y_min + HUD_HEIGHT)

            # Clamp so sprite does not render above HUD or off-screen
            min_sy = HUD_HEIGHT  # top of game area
            sy = max(min_sy, sy)

            if sprite:
                screen.blit(sprite, (sx, sy))
            else:
                pygame.draw.rect(screen, (200, 100, 100), pygame.Rect(sx, sy, 24, sh))

        # Draw car anchored at car_screen_x using baseline semantics and clamp top
        if getattr(engine.car, 'is_jumping', False) and getattr(engine.car, 'jump_remaining', 0) > 0:
            car_sprite = getattr(engine.car, "jump_sprite", None)
        else:
            car_sprite = getattr(engine.car, "normal_sprite", None)

        car_baseline = float(getattr(engine.car, "y", 0))
        if car_sprite:
            ch = car_sprite.get_height()
            car_top_world = car_baseline - ch
            car_draw_y = int(car_top_world - engine.road_y_min + HUD_HEIGHT)
            car_draw_y = max(HUD_HEIGHT, car_draw_y)
            screen.blit(car_sprite, (car_screen_x, car_draw_y))
        else:
            rect_h = 32
            car_top_world = car_baseline - rect_h
            car_draw_y = int(car_top_world - engine.road_y_min + HUD_HEIGHT)
            car_draw_y = max(HUD_HEIGHT, car_draw_y)
            pygame.draw.rect(screen, (0, 120, 200), pygame.Rect(car_screen_x, car_draw_y, 64, rect_h))

        # Draw preview ghost when visible
        if ui_state.get("preview_visible", False):
            tpl = ui_state.get("selected_template", {})
            preview_sprite = None
            if tpl:
                preview_sprite = getCachedSprite(tpl.get("sprite"))
            drawPreview(screen,
                        ui_state.get("preview_world", (0.0, 0)),
                        engine,
                        preview_sprite,
                        ui_state.get("preview_valid", False),
                        HUD_HEIGHT,
                        car_screen_x)

        # Draw HUD (stats + palette when in GOD_MODE) and buttons
        drawHUD(screen, engine, button_sprites, button_rects, font, ui_state, HUD_HEIGHT)
        drawButtons(screen, button_sprites, button_rects, font)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    mainWindow()