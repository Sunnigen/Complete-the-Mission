import tcod as libtcod

from GameStates import GameStates


def handle_keys(key, game_state):
    if game_state == GameStates.DEBUG_MENU:
        return handle_debug_menu(key)
    elif game_state == GameStates.PLAYER_TURN:
        return handle_player_turn_keys(key)
    elif game_state == GameStates.PLAYER_DEAD:
        return handle_player_dead_keys(key)
    elif game_state == GameStates.TARGETING:
        return handle_targeting_keys(key)
    elif game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
        return handle_inventory_keys(key, game_state)
    elif game_state == GameStates.LEVEL_UP:
        return handle_level_up_menu(key)
    elif game_state == GameStates.CHARACTER_SCREEN or game_state == GameStates.READ:
        return handle_character_screen(key)
    return {}


def handle_inventory_keys(key, game_state):
    # Inventory Items are Selected by Keyboard Letter
    index = key.c - ord('a')

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle fullscreen
        return {'fullscreen': True}
        # User Actions
    elif str(key.c) == 'r':  # wait
        return {'wait': True}
    elif key.vk == libtcod.KEY_ESCAPE or \
            (key.c == ord('i') and game_state == GameStates.SHOW_INVENTORY) or \
            (key.c == ord('t') and game_state == GameStates.DROP_INVENTORY):
        return {'exit': True}

    if index >= 0:
        return {'inventory_index': index}

    return {}


def handle_main_menu(key):
    key_char = chr(key.c)

    if key.vk == libtcod.KEY_ENTER or key_char == '1':
        return {'new_game': True}
    elif key.vk == libtcod.KEY_SHIFT  or key_char == '2':
        return {'load_game': True}
    elif key.vk == libtcod.KEY_ESCAPE:
        return {'exit': True}

    return {}


def handle_level_select(key):
    key_char = chr(key.c)

    if key_char == '1':
        return {'overworld': True}
    elif key_char == '2':
        return {'flamewood_prison': True}
    elif key_char == '3':
        return {'generic': True}
    elif key.vk == libtcod.KEY_ESCAPE:
        return {'exit': True}

    return {}


def handle_level_up_menu(key):
    if key:
        key_char = chr(key.c)

        if key_char == '1':
            return {'level_up': 'hp'}
        elif key_char == '2':
            return {'level_up': 'str'}
        elif key_char == '3':
            return {'level_up': 'def'}

    return {}


def handle_character_screen(key):
    if chr(key.c) == 'v' or key.vk == libtcod.KEY_ESCAPE:
        return {'exit': True}
    elif chr(key.c) == 'r':
        return {'wait': True}

    return {}


def handle_debug_menu(key):
    if key:
        key_char = chr(key.c)

        if key_char == '1':
            return {'god_mode': 1}
        elif key_char == '2':
            return {'reveal': 1}
        elif key_char == '3':
            return {'give_level_up': True}
        elif key_char == '4':
            return {'next_level': True}
        elif key_char == '5':
            return {'revive_player': True}
        elif key_char == '6':
            return {'show_spawn_table': True}
        elif key_char == '7':
            return {'size_8_font': True, 'exit': True}
        elif key_char == '8':
            return {'size_10_font': True, 'exit': True}
        elif key_char == '9':
            return {'size_16_font': True, 'exit': True}
        elif key.vk == libtcod.KEY_ESCAPE or key.vk == libtcod.KEY_HOME or key.vk == libtcod.KEY_KP7:
            return {'exit': True}
    return {}


def handle_player_turn_keys(key):
    # Movement Keys
    key_char = chr(key.c)

    if key_char == 'w':  # up
        return {'move': (0, -1)}
    elif key_char == 's':  # down
        return {'move': (0, 1)}
    elif key_char == 'a':  # left
        return {'move': (-1, 0)}
    elif key_char == 'd':  # right
        return {'move': (1, 0)}

    # Diagonal Movement
    elif key_char == 'c':  # down right
        return {'move': (1, 1)}
    elif key_char == 'z':  # down left
        return {'move': (-1, 1)}
    elif key_char == 'e':  # up right
        return {'move': (1, -1)}
    elif key_char == 'q':  # up left
        return {'move': (-1, -1)}

    # User Actions
    elif key_char == 'r':  # wait
        return {'wait': True}
    elif key_char == 'g':  # get key
        return {'pickup': True}
    elif key_char == 'v':  # show character stats
        return {'show_character_screen': True}
    elif key_char == 'i':  # display inventory
        return {'show_inventory': True}
    elif key_char == 't':  # drop inventory
        return {'drop_inventory': True}
    elif key.vk == libtcod.KEY_ENTER:  # take stairs
        return {'take_stairs': True}

    # Debug
    elif key.vk == libtcod.KEY_HOME or key.vk == libtcod.KEY_KP7:
        return {'debug_menu': True}

    elif key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle full screen
        return {'fullscreen': True}
    elif key.vk == libtcod.KEY_ESCAPE:
        # Exit the game
        return {'exit': True}

    return {}


def handle_targeting_keys(key):
    if key.vk == libtcod.KEY_ESCAPE:
        return {'exit': True}

    return {}


def handle_player_dead_keys(key):
    key_char = chr(key.c)

    if key_char == 'i':
        return {'show_inventory': True}
    elif key.vk == libtcod.KEY_HOME or key.vk == libtcod.KEY_KP7:
        return {'debug_menu': True}

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle full screen
        return {'fullscreen': True}
    elif key.vk == libtcod.KEY_ESCAPE:
        # Exit the menu
        return {'exit': True}

    return {}


def handle_mouse(mouse):
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
