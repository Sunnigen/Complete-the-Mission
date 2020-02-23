# https://github.com/marukrap/RoguelikeDevResources

import numpy as np

import tcod as libtcod
import tcod.event as tcod_event

from GameMessages import Message
from DeathFunctions import kill_player, kill_monster
from Entity import get_blocking_entities_at_location
from FOVFunctions import definite_enemy_fov, initialize_fov, recompute_fov
from GameStates import GameStates
from InputHandlers import handle_keys, handle_main_menu, handle_mouse
from loader_functions.InitializeNewGame import get_constants, get_game_variables
from loader_functions.DataLoaders import load_game, save_game
from Menus import main_menu, message_box
from RenderFunctions import clear_all, render_all

"""
 !"#$&'()*+,-./0123456789:;<=>? 
 @[\]^_'{|}~░▒▓│—┼┤┴├┬└╥┘▀▄

"""


def main():
    # Generation Variables and Intialization of Entities
    constants = get_constants()

    # Select Font and Font File Type
    # libtcod.console_set_custom_font('assets/arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
    # libtcod.console_set_custom_font('assets/prestige8x8_gs_tc.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
    libtcod.console_set_custom_font('assets/dejavu_wide16x16_gs_tc.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
    # libtcod.console_set_custom_font('assets/lucida12x12_gs_tc.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
    libtcod.console_init_root(w=constants['screen_width'], h=constants['screen_height'],
                              title=constants['window_title'], fullscreen=False,
                              renderer=libtcod.RENDERER_OPENGL2, vsync=True)

    # Initialize Consoles
    con = libtcod.console.Console(constants['screen_width'], constants['screen_height'])
    panel = libtcod.console.Console(constants['screen_width'], constants['panel_height'])

    # Initialize Game Variables
    player = None
    entities = []
    game_map = None
    message_log = None
    game_state = None

    # Menu Variables
    show_main_menu = True
    show_load_error_message = False

    main_menu_background_image = libtcod.image_load('assets/menu_background.png')

    # Connect Keyboard and Mouse
    key = libtcod.Key()
    mouse = libtcod.Mouse()

    # Start Game Loop
    while True:
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)

        # State to Show Main Menu or Game
        if show_main_menu:
            # Show Main Menu
            main_menu(con, main_menu_background_image, constants['screen_width'],
                      constants['screen_height'])

            # Cannot Load Saved Game
            if show_load_error_message:
                message_box(con, 'No save game to load', 50, constants['screen_width'], constants['screen_height'])

            libtcod.console_flush()  # Present everything onto the the screen

            # User Inputs
            action = handle_main_menu(key)
            # mouse_action = handle_mouse(mouse)

            new_game = action.get('new_game')
            load_saved_game = action.get('load_game')
            exit_game = action.get('exit')

            # Remove Error Message if Game has been found
            if show_load_error_message and (new_game or load_saved_game or exit_game):
                show_load_error_message = False

            # Start a New Game
            elif new_game:
                player, entities, game_map, message_log, game_state = get_game_variables(constants)
                game_state = GameStates.PLAYER_TURN

                show_main_menu = False

            # Reload Saved Game
            # Location: ./save_files
            elif load_saved_game:
                try:
                    player, entities, game_map, message_log, game_state = load_game()
                    show_main_menu = False

                except FileNotFoundError:
                    show_load_error_message = True

            elif exit_game:
                break

        # Do not Show Main Menu, Show Game
        else:
            clear_console(con)
            play_game(player, entities, game_map, message_log, game_state, con, panel, constants)

            show_main_menu = True


def clear_console(con):
    con.clear(fg=(0, 0, 100), bg=(0, 0, 100))
    # con.clear(fg=(0, 0, 0), bg=(0, 0, 0))


def play_game(player, entities, game_map, message_log, game_state, con, panel, constants):
    # Initialize FOV
    fov_recompute = True
    fov_map = initialize_fov(game_map)
    enemy_fov_map = np.zeros(fov_map.transparent.shape, dtype=bool)
    # enemy_fov_map = initialize_fov(game_map)
    toggle_reveal_all = 0

    # Connect Keyboard and Mouse
    key = libtcod.Key()
    mouse = libtcod.Mouse()

    # Initialize GameStates
    game_state = GameStates.PLAYER_TURN
    previous_game_state = game_state

    # Initialize Targeting Item
    targeting_item = None
    # j = 1
    # x = 1
    # for i in range(255):
    #     x += 1
    #     if x % 50 == 0:
    #         j += 1
    #         x -= 30
    #     libtcod.console_put_char(con, x, j, i, libtcod.BKGND_NONE)
    #
    # libtcod.console_save_xp(con, filename='file')
    # libtcod.console_save_asc(con, filename='file')
    # Start Game Loop
    while True:
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)

        # User Inputs
        action = handle_keys(key, game_state)
        mouse_action = handle_mouse(mouse)

        # Obtain All Actions
        move = action.get('move')
        wait = action.get('wait')
        pickup = action.get('pickup')
        show_inventory = action.get('show_inventory')
        drop_inventory = action.get('drop_inventory')
        inventory_index = action.get('inventory_index')
        take_stairs = action.get('take_stairs')
        level_up = action.get('level_up')
        show_character_screen = action.get('show_character_screen')
        exit = action.get('exit')
        fullscreen = action.get('fullscreen')

        # Debug Actions
        debug_menu = action.get('debug_menu')
        give_level_up = action.get('give_level_up')
        next_level = action.get('next_level')
        reveal = action.get('reveal')
        toggle_god_mode = action.get('god_mode')
        revive = action.get('revive_player')
        spawn_table = action.get('show_spawn_table')

        left_click = mouse_action.get('left_click')
        right_click = mouse_action.get('right_click')

        player_turn_results = []

        # FOV Update
        if fov_recompute:
            # Update FOV for Player
            recompute_fov(fov_map, player.x, player.y, constants['fov_radius'], constants['fov_light_walls'],
                          constants['fov_algorithm'])
            # Update FOV for Entities
            # Note: Doesn't do as expected, fov_map gets overwritten multiple times per entity.
            # TODO: Combine fov calculations for all entities, that it only happens once.
            enemy_fov_map = definite_enemy_fov(fov_map, entities, constants['enemy_fov_radius'],
                                               constants['fov_light_walls'], constants['fov_algorithm'])

        # Toggle Debug Menu
        if debug_menu:
            previous_game_state = game_state
            game_state = GameStates.DEBUG_MENU

        # Debug Toggle Reveal All
        if reveal:
            toggle_reveal_all = abs(toggle_reveal_all - reveal)
            if toggle_reveal_all == 0:
                fov_recompute = True
                message_log.add_message(Message('Toggle Map Reveal: ON.', libtcod.white))
            else:
                message_log.add_message(Message('Toggle Map Reveal: OFF.', libtcod.white))
            if previous_game_state == GameStates.PLAYER_DEAD:
                game_state = previous_game_state
            else:
                game_state = GameStates.PLAYER_TURN

        # Drawing
        render_all(con, panel, entities, player, game_map, fov_map, enemy_fov_map, fov_recompute, message_log,
                   constants['screen_width'], constants['screen_height'], constants['bar_width'],
                   constants['panel_height'], constants['panel_y'], mouse,
                   game_state, toggle_reveal_all=toggle_reveal_all)

        fov_recompute = False
        clear_all(con, entities)
        libtcod.console_flush()  # Present everything onto the the screen

        # Debug Level Up
        if give_level_up:
            # player.level.current_xp += player.level.experience_needed_to_next_level
            message_log.add_message(Message('%s XP given to player.' % player.level.experience_needed_to_next_level,
                                            libtcod.white))

            # player.level.current_xp = player.level.experience_to_next_level
            player_turn_results.append({'xp': player.level.experience_needed_to_next_level})

            if previous_game_state == GameStates.PLAYER_DEAD:
                game_state = previous_game_state
            else:
                game_state = GameStates.PLAYER_TURN

        # Debug God Mode
        if toggle_god_mode:
            player.fighter.god_mode = abs(player.fighter.god_mode - toggle_god_mode)
            if player.fighter.god_mode == 1:
                message_log.add_message(Message('Toggle God Mode: ON.', libtcod.white))
            else:
                message_log.add_message(Message('Toggle God Mode: OFF.', libtcod.white))
            if previous_game_state == GameStates.PLAYER_DEAD:
                game_state = previous_game_state
                revive = True
            else:
                game_state = GameStates.PLAYER_TURN

        # Debug Go to Next Level
        if next_level:
            entities = game_map.next_floor(player, message_log, constants)
            fov_map = initialize_fov(game_map)
            fov_recompute = True
            game_state = GameStates.PLAYER_TURN
            clear_console(con)
            revive = True

        # Debug Revive Player
        if revive and player.fighter.hp == 0:
            message_log.add_message(Message('Player is revived!', libtcod.white))
            player.char = '@'
            player.color = libtcod.white
            player.fighter.hp = player.fighter.max_hp
            game_state = GameStates.PLAYER_TURN
        elif revive and game_state == GameStates.DEBUG_MENU:
            game_state = GameStates.PLAYER_TURN

        # Debug Revive Player
        if spawn_table:
            # TODO: Show proper menu of spawn rates
            game_map.print_spawn_rates()
            game_state = GameStates.PLAYER_TURN

        # Player is Moving
        if move and game_state == GameStates.PLAYER_TURN:
            dx, dy = move

            destination_x = player.x + dx
            destination_y = player.y + dy

            # Block Player from Moving Through Obstacle
            if game_map.is_within_map(destination_x, destination_y):
                if not game_map.is_blocked(destination_x, destination_y):
                    target = get_blocking_entities_at_location(entities, destination_x, destination_y)

                    # Attack Entity or Move
                    if target:
                        attack_results = player.fighter.attack(target)
                        player_turn_results.extend(attack_results)
                    else:
                        game_map.transparent[player.y][player.x] = True  # unblock previous position
                        game_map.transparent[player.y + dy][player.x + dx] = False  # block new position
                        player.move(dx, dy)
                        fov_recompute = True

                    game_state = GameStates.ENEMY_TURN

        # Player Character "Waits"
        elif wait:
            fov_recompute = True
            game_state = GameStates.ENEMY_TURN

        # Player is Attempting to Pick Up Item
        elif pickup and game_state == GameStates.PLAYER_TURN:

            # Loop through each entity, check if same tile as player and is an item
            for entity in entities:
                if entity.item and entity.x == player.x and entity.y == player.y:
                    pickup_results = player.inventory.add_item(entity)
                    player_turn_results.extend(pickup_results)

                    break
            else:
                message_log.add_message(Message('There is nothing here to pick up.', libtcod.yellow))

        # Trigger Game States to Show Inventory
        if show_inventory:
            previous_game_state = game_state
            game_state = GameStates.SHOW_INVENTORY

        # Trigger Game State to Allow Dropping Items:
        if drop_inventory:
            previous_game_state = game_state
            game_state = GameStates.DROP_INVENTORY

        # Use/Drop Item if Selected Through Inventory
        if inventory_index is not None and previous_game_state != GameStates.PLAYER_DEAD and inventory_index < len(
                player.inventory.items):
            item = player.inventory.items[inventory_index]
            if game_state == GameStates.SHOW_INVENTORY:
                player_turn_results.extend(player.inventory.use(item, entities=entities, fov_map=fov_map))
            elif game_state == GameStates.DROP_INVENTORY:
                player_turn_results.extend(player.inventory.drop_item(item))

        # Player Found Goal and Advances to Next Level
        if take_stairs and game_state == GameStates.PLAYER_TURN:
            for entity in entities:
                if entity.stairs and entity.x == player.x and entity.y == player.y:
                    entities = game_map.next_floor(player, message_log, constants)
                    fov_map = initialize_fov(game_map)
                    enemy_fov_map = np.zeros(fov_map.transparent.shape, dtype=bool)
                    fov_recompute = True
                    clear_console(con)
                    break
            else:
                message_log.add_message(Message('There are no stairs here.', libtcod.yellow))

        # Player Levels Up
        if level_up:
            if level_up == 'hp':
                player.fighter.base_max_hp += 20
                player.fighter.hp += 20
            elif level_up == 'str':
                player.fighter.base_power += 1
            elif level_up == 'def':
                player.fighter.base_defense += 1

            game_state = previous_game_state

        # Toggle Character Screen
        if show_character_screen:
            previous_game_state = game_state
            game_state = GameStates.CHARACTER_SCREEN

        # Handle Targeting for Ranged Attacks
        if game_state == GameStates.TARGETING:
            if left_click:
                target_x, target_y = left_click

                item_use_results = player.inventory.use(targeting_item, entities=entities, fov_map=fov_map,
                                                        target_x=target_x, target_y=target_y)
                player_turn_results.extend(item_use_results)
            elif right_click:
                player_turn_results.append({'targeting_cancelled': True})

        # Exit Game or Menu OR Exit Targeting Game State
        if exit:
            if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY, GameStates.CHARACTER_SCREEN,
                              GameStates.DEBUG_MENU):
                game_state = previous_game_state
            elif game_state == GameStates.TARGETING:
                player_turn_results.append({'targeting_cancelled': True})
            else:
                # Exit the Game
                save_game(player, entities, game_map, message_log, game_state)
                return True

        # Toggle Full Screen
        if fullscreen:
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

        # Log Events that Occured During Player Turn
        for player_turn_result in player_turn_results:
            message = player_turn_result.get('message')
            dead_entity = player_turn_result.get('dead')
            item_added = player_turn_result.get('item_added')
            item_consumed = player_turn_result.get('consumed')
            item_dropped = player_turn_result.get('item_dropped')
            equip = player_turn_result.get('equip')
            targeting = player_turn_result.get('targeting')
            targeting_cancelled = player_turn_result.get('targeting_cancelled')
            xp = player_turn_result.get('xp')

            if message:
                message_log.add_message(message)

            if targeting_cancelled:
                game_state = previous_game_state

                message_log.\
                    add_message(Message('Targeting cancelled.'))

            if xp:
                leveled_up = player.level.add_xp(xp)
                message_log.add_message(Message('You gained %s experience points.' % xp))

                if leveled_up:
                    message_log.add_message(Message(
                        'Your battle skills grow stronger! You reached level %s!' %
                        player.level.current_level, libtcod.yellow)
                    )
                    previous_game_state = game_state
                    game_state = GameStates.LEVEL_UP

            if dead_entity:
                if dead_entity == player:
                    message, game_state = kill_player(dead_entity)
                else:
                    message = kill_monster(dead_entity)

                message_log.add_message(message)

            if item_added:
                entities.remove(item_added)
                game_state = GameStates.ENEMY_TURN

            if item_consumed:
                game_state = GameStates.ENEMY_TURN

            if targeting:
                previous_game_state = GameStates.PLAYER_TURN
                game_state = GameStates.TARGETING

                targeting_item = targeting

                message_log.add_message(targeting_item.item.targeting_message)

            if item_dropped:
                entities.append(item_dropped)
                game_state = GameStates.ENEMY_TURN

            if equip:
                equip_results = player.equipment.toggle_equip(equip)
                for equip_result in equip_results:
                    equipped = equip_result.get('equipped')
                    dequipped = equip_result.get('dequipped')

                    if equipped:
                        message_log.add_message(Message('You equipped the %s.' % equipped.name))

                    if dequipped:
                        message_log.add_message(Message('You removed the %s.' % dequipped.name))

                game_state = GameStates.ENEMY_TURN

        # Enemy Turn to Act
        if game_state == GameStates.ENEMY_TURN:
            for entity in entities:
                if entity.ai:
                    # enemy_turn_results = entity.ai.take_turn(player, fov_map, game_map, entities)
                    enemy_turn_results = entity.ai.take_turn(player, enemy_fov_map, game_map, entities,
                                                             constants['enemy_fov_radius'])

                    for enemy_turn_result in enemy_turn_results:
                        message = enemy_turn_result.get('message')
                        dead_entity = enemy_turn_result.get('dead')

                        if message:
                            message_log.add_message(message)

                        if dead_entity:
                            if dead_entity == player:
                                message, game_state = kill_player(dead_entity)
                            else:
                                message = kill_monster(dead_entity)

                            message_log.add_message(message)

                    if game_state == GameStates.PLAYER_DEAD:
                        break

            else:
                game_state = GameStates.PLAYER_TURN


if __name__ == '__main__':
    main()
