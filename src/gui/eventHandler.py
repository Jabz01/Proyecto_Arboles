# src/gui/eventHandler.py
from typing import Dict, Callable, Tuple, Optional
import pygame
from game.gameEngine import GameEngine, GameState

# Note: rect names expected are UPPER_SNAKE_CASE strings as produced by build_button_rects
# Example keys in rects dict: 'START_BTN_RECT','PAUSE_BTN_RECT','TREE_BTN_RECT','GOD_BTN_RECT'


def handle_key_event(event: pygame.event.Event, engine: GameEngine) -> None:
    """
    Handle keyboard events that affect engine state or the car.

    Args:
        event: pygame Event (expecting KEYDOWN).
        engine: GameEngine instance to control.
    """
    if event.type != pygame.KEYDOWN:
        return

    if event.key == pygame.K_RETURN:
        # Start from INIT or PAUSED -> RUNNING
        engine.start()
    elif event.key == pygame.K_ESCAPE:
        # Quit handling is left to caller/main loop
        pass
    elif event.key == pygame.K_SPACE and engine.state == GameState.RUNNING:
        if hasattr(engine.car, "jump"):
            engine.car.jump()


def handle_mouse_event(event: pygame.event.Event,
                       engine: GameEngine,
                       ui_state: Dict,
                       rects: Dict[str, pygame.Rect]) -> None:
    """
    Handle mouse clicks for HUD buttons and obstacle placement.

    Args:
        event: pygame Event (expecting MOUSEBUTTONDOWN with button 1).
        engine: GameEngine instance to modify (start, pause, place obstacles).
        ui_state: mutable dict with keys expected by this handler:
            - preview_valid: bool
            - preview_type: str
            - preview_visible: bool
            - preview_world: (x, y)
            - screenToWorld: callable(mouse_x, mouse_y, engine) -> ((wx, wy), in_game_bool)
        rects: dict mapping UPPER_SNAKE_CASE rect names to pygame.Rect (from build_button_rects).
    """
    if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
        return

    mx, my = event.pos

    start_rect = rects.get("START_BTN_RECT")
    pause_rect = rects.get("PAUSE_BTN_RECT")
    tree_rect = rects.get("TREE_BTN_RECT")
    god_rect = rects.get("GOD_BTN_RECT")

    # Button clicks
    if start_rect and start_rect.collidepoint(mx, my):
        engine.start()
        # If currently in GOD_MODE, exit god mode (policy: Start resumes running)
        if engine.state == GameState.GOD_MODE:
            engine.exit_god_mode()
        return

    if pause_rect and pause_rect.collidepoint(mx, my):
        engine.toggle_pause()
        return

    if tree_rect and tree_rect.collidepoint(mx, my):
        # UI-level handling for AVL view should be triggered here (caller can subscribe)
        print("[UI] Tree button pressed")
        return

    if god_rect and god_rect.collidepoint(mx, my):
        if engine.state != GameState.GOD_MODE:
            engine.enter_god_mode()
        else:
            engine.exit_god_mode()
        return

    # Click inside game area -> placement attempt when in GOD_MODE
    screenToWorld = ui_state.get("screenToWorld")
    if not callable(screenToWorld):
        return

    (world, in_game) = screenToWorld(mx, my, engine)
    if engine.state == GameState.GOD_MODE and in_game and ui_state.get("preview_valid", False):
        world_x, world_y = world if isinstance(world, tuple) else (world, 0)
        obs = {
            "x": float(world_x),
            "y": int(world_y),
            "type": ui_state.get("preview_type", "cone"),
            "sprite": f"assets/sprites/{ui_state.get('preview_type','cone')}.png",
            "damage": 1
        }
        inserted = engine.place_obstacle(obs)
        if inserted:
            print("[UI] obstacle placed:", obs)
            # exit god mode and remain paused; user must press Start to resume
            engine.exit_god_mode()
            ui_state["preview_visible"] = False
            ui_state["preview_valid"] = False