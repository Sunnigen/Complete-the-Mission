import tcod as libtcod
from tcod import color_lerp

from enum import Enum

from GameStates import GameStates
from loader_functions.JsonReader import obtain_tile_set
from Menus import character_screen, debug_menu, inventory_menu, level_up_menu


class RenderOrder(Enum):
    STAIRS = 1
    CORPSE = 2
    ITEM = 3
    ACTOR = 4


def get_names_under_mouse(mouse, entities, fov_map, toggle_reveal):
    (x, y) = (mouse.cx, mouse.cy)
    names = []
    for entity in entities:
        if entity.x == x and entity.y == y and (libtcod.map_is_in_fov(fov_map, entity.x, entity.y) or toggle_reveal):
            if entity.fighter:
                names.append('%s: HP:%s|%s ATT:%s DEF:%s' %
                             (entity.name, entity.fighter.hp, entity.fighter.max_hp, entity.fighter.power,
                              entity.fighter.defense))

            else:
                names.append(entity.name)
    names = ', '.join(names)

    return names.title()


def render_tiles(con, game_map, fov_map, enemy_fov_map, fov_recompute, toggle_reveal_all):
    tile_set = obtain_tile_set()
    # Render Walls and Floors
    lerp_color = (128, 64, 64)

    # TODO: Combine the (2) tile render loops below, one for view all and for player vision only. This is based on
    #  "toggle_reveal_all".
    # if (fov_recompute and toggle_reveal_all != 1) or (toggle_reveal_all == 1):
    #     pass

    if fov_recompute and toggle_reveal_all != 1:

        # Obtain all Center Coordinates
        # TODO: Room center call out is for debugging
        room_centers = []
        # room_centers = [room.center for room in game_map.rooms]

        for y in range(game_map.height):
            for x in range(game_map.width):
                visible = fov_map.fov[y][x]  # Check if tile is visible at (x, y)
                wall = not game_map.walkable[y][x]  # Check if tile is a wall at (x, y)

                # Add Highlight to Enemy Character
                lerp_val = 0

                # Select Tile
                if visible:
                    if (x, y) in room_centers:
                        tile_name = "light_center"
                    elif wall:
                        tile_name = "light_wall"
                    else:
                        tile_name = "light_ground"
                    game_map.explored[y][x] = True
                    if enemy_fov_map[y][x]:  # Check if tile is visible to enemy at (x, y):
                        # TODO: Lerp the value based on distance from entity
                        lerp_val = 0.5

                elif game_map.explored[y][x]:
                    if (x, y) in room_centers:
                        tile_name = "dark_center"
                    elif wall:
                        tile_name = "dark_wall"
                    else:
                        tile_name = "dark_ground"
                else:
                    tile_name = 'default'

                # Set Tile Characteristics
                tile_color = tile_set[tile_name].get('color')
                tile_char = tile_set[tile_name].get('char')

                color_val = color_lerp(tuple(tile_color), lerp_color, lerp_val)
                libtcod.console_set_char_background(con, x, y, color_val, libtcod.BKGND_SET)
                libtcod.console_set_default_foreground(con, libtcod.white)
                libtcod.console_put_char(con, x, y, tile_char)

    # Reveal Entire Map
    elif toggle_reveal_all == 1:

        # Obtain all Center Coordinates
        # room_centers = []
        room_centers = [room.center for room in game_map.rooms]
        # monster_locations = [(e.x, e.y) for e in entities if e.fighter]

        for y in range(game_map.height):
            for x in range(game_map.width):
                wall = not game_map.walkable[y][x]
                visible = fov_map.fov[y][x]  # Check if tile is visible at (x, y)
                enemy_fov = enemy_fov_map[y][x]  # Check if tile is visible to enemy at (x, y)
                lerp_val = 0
                lerp_color = (128, 64, 64)
                if enemy_fov:
                    # TODO: Lerp the value based on distance from entity
                    lerp_val = 0.5

                if visible:
                    if (x, y) in room_centers:
                        tile_name = "light_center"
                    elif wall:
                        tile_name = "light_wall"
                    else:
                        tile_name = "light_ground"
                    game_map.explored[y][x] = True
                else:
                    if (x, y) in room_centers:
                        tile_name = "dark_center"
                    elif wall:
                        tile_name = "dark_wall"
                    else:
                        tile_name = "dark_ground"

                tile_color = tile_set[tile_name].get('color')
                tile_char = tile_set[tile_name].get('char')
                # libtcod.console_set_char_background(con, x, y, color_lerp(tuple(tile_color), lerp_color, lerp_val),
                #                                     libtcod.BKGND_SET)
                # libtcod.console_put_char(con, x, y, tile_char)
                color_val = color_lerp(tuple(tile_color), lerp_color, lerp_val)
                libtcod.console_set_char_background(con, x, y, color_val, libtcod.BKGND_SET)
                libtcod.console_set_default_foreground(con, libtcod.white)
                libtcod.console_put_char(con, x, y, tile_char)


def render_bar(panel, x, y, total_width, name, value, maximum, bar_color, back_color):
    # Render Bar(Current Value) Over Dark Bar(Max Value)
    bar_width = int(float(value) / maximum * total_width)

    # Current Bar, Dynamically Increases/Decreases
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

    # Max Bar, Never Decreases
    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

    # Display Text
    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, int(x + total_width / 2), y, libtcod.BKGND_NONE, libtcod.CENTER, '%s: %s/%s' %
                             (name, value, maximum))


def render_all(con, panel, entities, player, game_map, fov_map, enemy_fov_map, fov_recompute, message_log, screen_width, screen_height,
               bar_width, panel_height, panel_y, mouse, game_state, toggle_reveal_all=0):

    # Background, Tiles, Etc.
    render_tiles(con, game_map, fov_map, enemy_fov_map, fov_recompute, toggle_reveal_all)

    # Sort Draw Order to Sort by Render Order Enum Value
    entities_in_render_order = sorted(entities, key=lambda x: x.render_order.value)
    # Draw all entities in the list
    for entity in entities_in_render_order:
        draw_entity(con, entity, fov_map, game_map, toggle_reveal_all)

    # Draw Console to Screen
    libtcod.console_blit(con, 0, 0, screen_width, screen_height, 0, 0, 0)

    # Player UI Panel
    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)

    # Print the game Messages, one line at a time
    y = 1
    for message in message_log.messages:
        libtcod.console_set_default_foreground(panel, message.color)
        libtcod.console_print_ex(panel, message_log.x, y, libtcod.BKGND_NONE, libtcod.LEFT, message.text)
        y += 1

    # Render HP Bar
    render_bar(panel, 1, 1, bar_width, 'HP', player.fighter.hp, player.fighter.max_hp,
               libtcod.light_red, libtcod.darker_red)

    # Render XP Bar
    render_bar(panel, 1, 2, bar_width, 'XP', player.level.current_xp, player.level.experience_to_next_level,
               libtcod.darker_yellow, libtcod.darkest_yellow)

    # Display ATT/DEF
    libtcod.console_print_ex(panel, 1, 4, libtcod.BKGND_NONE, libtcod.LEFT, 'LV: %s ATT: %s DEF: %s' %
                             (player.level.current_level, player.fighter.power, player.fighter.defense))

    # Display Current Dungeon Level
    libtcod.console_print_ex(panel, 1, 5, libtcod.BKGND_NONE, libtcod.LEFT, 'Dungeon Level: %s' %
                             game_map.dungeon_level)

    # Mouse Over Display
    libtcod.console_set_default_foreground(panel, libtcod.light_gray)
    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT,
                             get_names_under_mouse(mouse, entities, fov_map, toggle_reveal_all))

    libtcod.console_blit(panel, 0, 0, screen_width, panel_height, 0, 0, panel_y)

    if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
        if game_state == GameStates.SHOW_INVENTORY:
            inventory_title = 'Press the key next to an item to use it, or Esc to cancel.\n'
        else:
            inventory_title = 'Press the key next to an item to drop it, or Esc to cancel.\n'

        inventory_menu(con, inventory_title, player, 50, screen_width, screen_height)

    elif game_state == GameStates.DEBUG_MENU:
        menu_title = 'Debug Menu\n'
        debug_menu(con, menu_title, 50, screen_width, screen_height)

    elif game_state == GameStates.LEVEL_UP:
        level_up_menu(con, 'Level up! Choose a stat to raise:', player, 40, screen_width, screen_height)

    elif game_state == GameStates.CHARACTER_SCREEN:
        character_screen(player, 30, 10, screen_width, screen_height)


def clear_all(con, entities):
    for entity in entities:
        clear_entity(con, entity)


def draw_entity(con, entity, fov_map, game_map, toggle_reveal_all):
    # TODO: Handle drawing entities, not within FOV
    # Render Entity if Within FOV or Stairs
    if libtcod.map_is_in_fov(fov_map, entity.x, entity.y) or toggle_reveal_all == 1:
        libtcod.console_set_default_foreground(con, entity.color)
        libtcod.console_put_char(con, entity.x, entity.y, entity.char, libtcod.BKGND_NONE)

    # Render Entity although Not in FOV
    elif entity.fov_color and game_map.explored[entity.y][entity.x] and toggle_reveal_all < 1:
        libtcod.console_set_default_foreground(con, entity.fov_color)
        libtcod.console_put_char(con, entity.x, entity.y, entity.char, libtcod.BKGND_NONE)


def clear_entity(con, entity):
    # Erase the character that represents this object
    libtcod.console_put_char(con, entity.x, entity.y, " ", libtcod.BKGND_NONE)
