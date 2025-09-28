# src/gui/eventHandler.py
from typing import Dict, Callable, Tuple, Optional
import pygame
from gui.spriteUtils import getCachedSprite
from gui.treeVisualizer import show_tree
from game.gameEngine import GameEngine, GameState
from gui.preview import getSnappedPosition, validatePreview, screenToWorld


# en src/gui/eventHandler.py

def handleKeyEvent(event: pygame.event.Event, engine: GameEngine) -> None:
    if event.type != pygame.KEYDOWN:
        return

    lane_height = int((engine.road_y_max - engine.road_y_min) / 8)

    if event.key == pygame.K_UP:
        engine.car.move_up(lane_height, min_y=int(engine.road_y_min))
    elif event.key == pygame.K_DOWN:
        engine.car.move_down(lane_height, max_y=int(engine.road_y_max))
    elif event.key == pygame.K_SPACE:
        engine.car.jump()
    elif event.key == pygame.K_RETURN:
        if engine.state == GameState.GOD_MODE:
            engine.exit_god_mode()
        engine.start()
    elif event.key == pygame.K_ESCAPE:
        engine.pause()




def handleEvent(event: pygame.event.Event,
                engine: GameEngine,
                ui_state: Dict,
                rects: Dict[str, pygame.Rect]) -> None:
    """
    Generic event handler. Call this once per pygame event.

    Expected ui_state keys:
        - screenToWorld: callable(mouse_x, mouse_y, engine) -> ((wx, wy), in_game_bool)
        - palette: list of templates (each template is dict with keys 'type','damage','sprite')
        - palette_index: int
        - selected_template: current template dict
        - preview_visible: bool (updated here)
        - preview_world: (wx, wy) (updated here)
        - preview_valid: bool (updated here)
        - getSnappedPosition: optional callable to compute snapped pos (fallbacks to gui.preview.getSnappedPosition)
    """
    # Keyboard events
    if event.type == pygame.KEYDOWN:
        handleKeyEvent(event, engine)
        return

    # Mouse motion -> update preview state when in GOD_MODE
    if event.type == pygame.MOUSEMOTION:
        mx, my = event.pos
        if engine.state == GameState.GOD_MODE:
            screenToWorldFn = ui_state.get("screenToWorld", None)
            if callable(screenToWorldFn):
                world, in_game = screenToWorldFn(mx, my, engine)
                ui_state["preview_world"] = world
                ui_state["preview_visible"] = bool(in_game)
                # snapped and validation
                snappedFn = ui_state.get("getSnappedPosition", getSnappedPosition)
                snapped = snappedFn(world, engine)
                tpl = ui_state.get("selected_template", {})
                ui_state["preview_valid"] = engine.can_place_obstacle(float(snapped[0]), int(snapped[1]), obstacle_type=tpl.get("type", "cone"))
        return

    # Mouse wheel -> cycle palette when in GOD_MODE (wrap-around)
    if event.type == pygame.MOUSEWHEEL:
        if engine.state == GameState.GOD_MODE:
            palette = ui_state.get("palette", [])
            if not palette:
                return
            # pygame: event.y = +1 (up), -1 (down). Wheel up -> previous item
            delta = event.y
            idx = int(ui_state.get("palette_index", 0))
            idx = (idx - delta) % len(palette)
            ui_state["palette_index"] = idx
            ui_state["selected_template"] = palette[idx]
        return

    # Mouse button down (left click) -> buttons and placement
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        mx, my = event.pos

        start_rect = rects.get("START_BTN_RECT")
        pause_rect = rects.get("PAUSE_BTN_RECT")
        tree_rect = rects.get("TREE_BTN_RECT")
        god_rect = rects.get("GOD_BTN_RECT")
        reset_rect = rects.get("RESET_BTN_RECT")
        
        if reset_rect and reset_rect.collidepoint(mx, my):
            # Reiniciar motor y posicion del coche
            engine.reset()
            engine.car.x = float(engine.road_x_min)
            engine.car.y = int(engine.road_y_min)
            engine.start()
            return

        # START: exit GOD_MODE if active, then start
        if start_rect and start_rect.collidepoint(mx, my):
            if engine.state == GameState.GOD_MODE:
                engine.exit_god_mode()
            engine.start()
            return

        # PAUSE: exit GOD_MODE if active, then toggle pause
        if pause_rect and pause_rect.collidepoint(mx, my):
            if engine.state == GameState.GOD_MODE:
                engine.exit_god_mode()
            engine.toggle_pause()
            return

        # TREE: exit GOD_MODE if active, then notify (UI-level)
        if tree_rect and tree_rect.collidepoint(mx, my):
            if engine.state == GameState.GOD_MODE:
                engine.exit_god_mode()
            # Try to display the tree using the tree visualizer.
            try:
                # engine.obstacle_manager holds the AVL tree as .tree
                show_tree(engine.obstacle_manager.tree)
            except Exception as e:
                print(f"[Error] Could not show tree: {e}")
            return

        # GOD: enter god mode if not already; if already in GOD_MODE do nothing (persist)
        if god_rect and god_rect.collidepoint(mx, my):
            if engine.state != GameState.GOD_MODE:
                engine.enter_god_mode()
            else:
                # explicitly persist; do nothing
                pass
            return

        # Otherwise: click inside game area -> attempt placement when in GOD_MODE
        screenToWorldFn = ui_state.get("screenToWorld", None)
        if not callable(screenToWorldFn):
            return
        world, in_game = screenToWorldFn(mx, my, engine)
        if engine.state == GameState.GOD_MODE and in_game:
            # compute snapped pos and validate
            snappedFn = ui_state.get("getSnappedPosition", getSnappedPosition)
            snapped = snappedFn(world, engine)
            tpl = ui_state.get("selected_template", {})
            valid = engine.can_place_obstacle(float(snapped[0]), int(snapped[1]), obstacle_type=tpl.get("type", "cone"))
            if valid:
                obs = {
                    "x": float(snapped[0]),
                    "y": int(snapped[1]),
                    "type": tpl.get("type", "cone"),
                    "sprite": tpl.get("sprite"),
                    "damage": tpl.get("damage", 1)
                }
                inserted = engine.place_obstacle(obs)
                if inserted:
                    print("[UI] obstacle placed:", obs)
                    # IMPORTANT: per rules, do NOT exit GOD_MODE when placement occurs
                    ui_state["preview_visible"] = False
                    ui_state["preview_valid"] = False
            else:
                # invalid placement feedback is left to UI rendering (preview_valid False)
                ui_state["preview_valid"] = False
        return