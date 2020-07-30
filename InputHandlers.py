from functools import partial

import tcod.event

DEBUG_MENU_ACTIONS = {

}


def no_key_action(*args, **kwargs):
    # Place Holder to Output Empty Key Presses
    # print('no action')
    pass


def handle_no_action(*args, **kwargs):
    # Dummy function handler that does nothing
    return no_key_action


def handle_inventory_keys(engine, key, game_state=None, player=None):
    # print('handle_inventory_keys', key)
    # Inventory Items are Selected by Keyboard Letter

    # Note: ord('a') = 97 and key.sym of "a" is 97
    # inventory_index = key.sym - ord('a')
    actions = {tcod.event.K_ESCAPE: engine.exit_state}

    # Add Extra Actions Based on Amount of Items in Player's Inventory
    for i in range(len(player.inventory.items)):
        actions[i + 97] = partial(engine.handle_item, i)

    # elif key.vk == tcod.KEY_ESCAPE or \
    #         (key.c == ord('i') and game_state == GameStates.SHOW_INVENTORY) or \
    #         (key.c == ord('t') and game_state == GameStates.DROP_INVENTORY):
    #     return {'exit': True}

    return actions.get(key.sym, no_key_action)


def handle_level_up_menu(engine, key, game_state=None, player=None):
    # print('handle_level_up_menu', key)
    actions = {
        tcod.event.K_1: partial(engine.level_up, 'hp'),
        tcod.event.K_2: partial(engine.level_up, 'str'),
        tcod.event.K_3: partial(engine.level_up, 'def'),
    }
    return actions.get(key.sym, no_key_action)


def handle_character_screen(engine, key, game_state=None, player=None):
    # print('handle_character_screen', key)
    actions = {
        tcod.event.K_ESCAPE: engine.exit_state,
        tcod.event.K_r: engine.wait
    }

    return actions.get(key.sym, no_key_action)


def handle_debug_menu(engine, key, game_state=None, player=None):
    # print('handle_debug_menu', key)
    actions = {
        tcod.event.K_1: engine.toggle_god_mode,  # player cannot be damaged
        tcod.event.K_2: engine.toggle_reveal_map,  # removes FOV
        tcod.event.K_3: engine.give_level_up,  # automatic player level up
        tcod.event.K_4: engine.go_to_next_level,  # advances player to next floor(level)
        tcod.event.K_5: engine.revive_player,  # revives player if dead
        tcod.event.K_6: engine.show_spawn_table,  # prints spawn table and location of each item (x, y)
        tcod.event.K_7: partial(engine.change_font_size, 8),  # changes console font to size 8
        tcod.event.K_8: partial(engine.change_font_size, 10),  # changes console font to size 10
        tcod.event.K_9: partial(engine.change_font_size, 16),  # changes console font to size 16
        tcod.event.K_SLASH: engine.toggle_debug_menu,  # exit debug menu
        tcod.event.K_ESCAPE: engine.toggle_debug_menu  # exit debug menu
    }

    return actions.get(key.sym, no_key_action)


def handle_dialogue(engine, key, game_state=None, player=None):
    # print('handle_dialogue', key)
    actions = {
        tcod.event.K_r: engine.dialogue,  # continue dialogue
        tcod.event.K_KP_5: engine.dialogue  # continue dialogue
    }

    return actions.get(key.sym, no_key_action)


def handle_player_turn_keys(engine, key, game_state=None, player=None):
    # print('handle_player_turn_keys', key)
    actions = {
        # Movement
        tcod.event.K_a: partial(engine.move, -1, 0),  # left
        tcod.event.K_w: partial(engine.move, 0, -1),  # up
        tcod.event.K_s: partial(engine.move, 0, 1),  # down
        tcod.event.K_d: partial(engine.move, 1, 0),  # right
        tcod.event.K_KP_4: partial(engine.move, -1, 0),  # left
        tcod.event.K_KP_8: partial(engine.move, 0, -1),  # up
        tcod.event.K_KP_2: partial(engine.move, 0, 1),  # down
        tcod.event.K_KP_6: partial(engine.move, 1, 0),  # right
        # Diagonal Movement
        tcod.event.K_c: partial(engine.move, 1, 1),  # down right
        tcod.event.K_z: partial(engine.move, -1, 1),  # down left
        tcod.event.K_e: partial(engine.move, 1, -1),  # up right
        tcod.event.K_q: partial(engine.move, -1, -1),  # up left
        tcod.event.K_KP_3: partial(engine.move, 1, 1),  # down right
        tcod.event.K_KP_1: partial(engine.move, -1, 1),  # down left
        tcod.event.K_KP_9: partial(engine.move, 1, -1),  # up right
        tcod.event.K_KP_7: partial(engine.move, -1, -1),  # up left
        # User Actions
        tcod.event.K_r: engine.wait,  # do nothing/wait turn
        tcod.event.K_KP_5: engine.wait,  # do nothing/wait turn
        tcod.event.K_g: engine.pickup,  # pick up item
        tcod.event.K_v: engine.show_character_screen,  # open character screen
        tcod.event.K_i: engine.show_inventory,  # display inventory
        tcod.event.K_t: engine.drop_inventory,  # display drop inventory
        tcod.event.K_KP_ENTER: engine.take_stairs,  # display drop inventory
        tcod.event.K_RETURN: engine.take_stairs,  # display drop inventory
        # Debug
        tcod.event.K_SLASH: engine.toggle_debug_menu,  # toggle debug menu
        # Main Menu
        tcod.event.K_ESCAPE: partial(engine.exit_current_game, 'title'),
        # Full Screen
        tcod.event.K_LALT: engine.toggle_full_screen,
        tcod.event.K_RALT: engine.toggle_full_screen,
    }

    return actions.get(key.sym, no_key_action)


def handle_targeting_keys(engine, key, game_state=None, player=None):
    actions = {tcod.event.K_ESCAPE: engine.exit_state}
    return actions.get(key.sym, no_key_action)


def handle_player_dead_keys(engine, key, game_state=None, player=None):
    # print('handle_player_dead_keys', key)
    actions = {
        tcod.event.K_i: engine.show_inventory,
        tcod.event.K_SLASH: engine.toggle_debug_menu,
        tcod.event.K_LALT: engine.toggle_full_screen,
        tcod.event.K_RALT: engine.toggle_full_screen,
        tcod.event.K_ESCAPE: engine.exit_state
    }

    return actions.get(key.sym, no_key_action)


def handle_mouse(mouse, game_state=None):
    # print('mouse', mouse)
    (x, y) = (mouse.cx, mouse.cy)
    # (x, y) = (mouse.pixel.x, mouse.pixel.y)
    # mouse_state = mouse.state
    # print(mouse_state)
    # Check if Left/Right Mouse Button is Pressed
    if mouse.lbutton_pressed:
        return {'left_click': (x, y)}
    if mouse.rbutton_pressed:
        return {'right_click': (x, y)}

    return {}
