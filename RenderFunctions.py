import string
import sys
import random

import tcod as libtcod
from tcod import color_lerp
from tcod.image import Image as TcodImage
import tcod

from enum import Enum

from GameStates import GameStates
from loader_functions.JsonReader import obtain_tile_set
from Menus import character_screen, debug_menu, inventory_menu, level_up_menu, map_screen


class RenderOrder(Enum):
    STAIRS = 1
    CORPSE = 2
    ITEM = 3
    ACTOR = 4


def get_info_under_mouse(mouse, game_map, entities, map_objects, fov_map, toggle_reveal, view_x_start, view_x_end, view_y_start,
                         view_y_end, viewport_width, viewport_height, viewport_width_start, viewport_height_start):

    (x, y) = (mouse.cx, mouse.cy)
    names = []
    for entity in entities + map_objects:

        # Mob Name
        if entity.x == x + view_x_start + viewport_width_start and entity.y == y + view_y_start + viewport_height_start and (libtcod.map_is_in_fov(fov_map, entity.x, entity.y) or toggle_reveal):
            if entity.fighter:
                names.append('%s: HP:%s|%s ATT:%s DEF:%s' %
                             (entity.name, entity.fighter.hp, entity.fighter.max_hp, entity.fighter.power,
                              entity.fighter.defense))
            # Items, Objects
            else:
                names.append(entity.name)
    names = ', '.join(names)

    # Room Type
    for room in game_map.rooms:
        if room.check_point_within_room(x + view_x_start + viewport_width_start,
                                        y + view_y_start + viewport_height_start):
            names = room.room_type + " " + names
            break


    # Obtain Coordinates under Mouse
    if -viewport_width_start <= x <= -viewport_width_start + viewport_width * 2 and \
            -viewport_height_start <= y <= -viewport_height_start + viewport_height * 2:
        names += ' (%s, %s)' % (x + view_x_start + viewport_width_start,
                                y + view_y_start + viewport_height_start)

    return names.title()


def obtain_viewport_dimensions(game_map, viewport_width, viewport_height):
    player_x, player_y = game_map.player.x, game_map.player.y

    if viewport_width == 0 or viewport_height == 0:
        return 0, game_map.width, 0, game_map.height

    if player_x - viewport_width < 0:
        view_x_start = 0
        view_x_end = 2 * viewport_width
    elif player_x + viewport_width >= game_map.width:
        view_x_start = game_map.width - (2 * viewport_width)
        view_x_end = game_map.width
    else:
        view_x_start = player_x - viewport_width
        view_x_end = player_x + viewport_width

    if player_y - viewport_height < 0:
        view_y_start = 0
        view_y_end = 2 * viewport_height
    elif player_y + viewport_height >= game_map.height:
        view_y_start = game_map.height - (2 * viewport_height)
        view_y_end = game_map.height
    else:
        view_y_start = player_y - viewport_height
        view_y_end = player_y + viewport_height

    return view_x_start, view_x_end, view_y_start, view_y_end


def render_tile(con, x, y, color, char):
    libtcod.console_set_char_background(con, x, y, color, libtcod.BKGND_SET)
    libtcod.console_set_default_foreground(con, libtcod.white)
    libtcod.console_put_char(con, x, y, char)


def render_viewport(con, game_map, entities, fov_map, enemy_fov_map, fov_recompute, toggle_reveal_all, view_x_start, view_x_end,
                    view_y_start, view_y_end):

    if fov_recompute:
        # Obtain all Center Coordinates
        room_centers = []
        monster_locations = []
        if toggle_reveal_all > 0:
            room_centers = [room.center for room in game_map.rooms]
            monster_locations = [(e.x, e.y) for e in entities if e.fighter]

        # Render Walls and Floors
        lerp_color = (128, 64, 64)

        correct_x, correct_y = 0, 0
        for y in range(view_y_start, view_y_end):
            for x in range(view_x_start, view_x_end):
                try:
                    tile = game_map.tileset_tiles[y][x]
                except IndexError:
                    print('IndexError!')
                    print(view_x_start, view_x_end)
                    print(view_y_start, view_y_end)
                    print(game_map.width, game_map.height)
                    print('x/y:', x, y)
                    print(len(game_map.tileset_tiles), len(game_map.tileset_tiles))

                    sys.exit()

                visible = fov_map.fov[y][x]  # Check if tile is visible at (x, y)
                enemy_fov = enemy_fov_map[y][x]  # Check if tile is visible to enemy at (x, y)
                # wall = not game_map.walkable[y][x]  # Check if tile is a wall at (x, y)

                # Add Highlight to Enemy Character
                lerp_val = 0

                if toggle_reveal_all == 1:
                    if enemy_fov:
                        # TODO: Lerp the value based on distance from entity
                        lerp_val = 0.05

                    if (x, y) in room_centers:
                        tile = 3

                # Select Tile
                if visible:
                    tile_color = game_map.tile_set[str(tile)].get('color')
                    tile_char = game_map.tile_set[str(tile)].get('char')

                    game_map.explored[y][x] = True
                    if enemy_fov_map[y][x]:  # Check if tile is visible to enemy at (x, y):
                        # TODO: Lerp the value based on distance from entity
                        lerp_val = 0.5

                elif game_map.explored[y][x] or toggle_reveal_all == 1:
                    tile_color = game_map.tile_set[str(tile)].get('fov_color')
                    tile_char = game_map.tile_set[str(tile)].get('fov_char')

                else:
                    tile = 0
                    tile_color = game_map.tile_set[str(tile)].get('color')
                    tile_char = game_map.tile_set[str(tile)].get('char')


                # if 'wall' in tile_name:
                #     mask_char_list = [35, 186, 186, 186, 205, 188, 187, 185, 205, 200, 201, 204, 205, 202, 203, 35]
                #     tile_char = game_map.tile_set[tile_name].get(tile)
                #     mask = 0
                #     for c in [(x, y - 1, 1), (x, y + 1, 2), (x - 1, y, 4), (x + 1, y, 8)]:
                #         c1, c2, c_ind = c[0], c[1], c[2]
                #         if game_map.is_within_map(c1, c2):
                #             if not game_map.walkable[c2][c1]:
                #                 mask += c_ind
                #
                #     # let mut mask : u8 = 0;
                #     #
                #     #     if is_revealed_and_wall(map, x, y - 1) { mask +=1; }
                #     #     if is_revealed_and_wall(map, x, y + 1) { mask +=2; }
                #     #     if is_revealed_and_wall(map, x - 1, y) { mask +=4; }
                #     #     if is_revealed_and_wall(map, x + 1, y) { mask +=7; }
                #     #
                #     #     walls:
                #     #      0 => { 9 } // Pillar because no walls                      ○
                #     #         1 => { 186 } // Wall only to the north                   ║
                #     #         2 => { 186 } // Wall only to the south                  ║
                #     #         3 => { 186 } // Wall to the north and south              ║
                #     #         4 => { 205 } // Wall only to the west                   ═
                #     #         5 => { 188 } // Wall to the north and west               ╝
                #     #         6 => { 187 } // Wall to the south and west              ╗
                #     #         7 => { 185 } // Wall to the north, south and west        ╣
                #     #         8 => { 205 } // Wall only to the east                   ═
                #     #         9 => { 200 } // Wall to the north and east               ╚
                #     #         10 => { 201 } // Wall to the south and east             ╤
                #     #         11 => { 204 } // Wall to the north, south and east       ╠
                #     #         12 => { 205 } // Wall to the east and west              ═
                #     #         13 => { 202 } // Wall to the east, west, and south       ╩
                #     #         14 => { 203 } // Wall to the east, west, and north      ╦
                #     try:
                #         tile_char = mask_char_list[mask]
                #     except:
                #         print('mask:', mask)
                # else:
                #     tile_char = game_map.tile_set[tile_name].get('char')

                color_val = color_lerp(tuple(tile_color), lerp_color, lerp_val)

                # Normalize Position
                correct_x = x - view_x_start
                correct_y = y - view_y_start
                # if not game_map.tileset_tiles[y][x] == 0 and game_map.explored[y][x]:
                #     tile_char = game_map.tile_set[str(tile)].get('char')

                render_tile(con, correct_x, correct_y, color_val, tile_char)

    # Reveal Entire Map
    # elif toggle_reveal_all == 1:
    #
    #     # Obtain all Center Coordinates
    #     room_centers = []
    #     entrances = []
    #     room_centers = [room.center for room in game_map.rooms]
    #     entrances = [r for r in game_map.entrances]
    #     monster_locations = [(e.x, e.y) for e in entities if e.fighter]
    #
    #     for y in range(view_y_start, view_y_end):
    #         for x in range(view_x_start, view_x_end):
    #             wall = not game_map.walkable[y][x]
    #             visible = fov_map.fov[y][x]  # Check if tile is visible at (x, y)
    #             enemy_fov = enemy_fov_map[y][x]  # Check if tile is visible to enemy at (x, y)
    #             lerp_val = 0
    #             lerp_color = (128, 64, 64)
    #             if enemy_fov:
    #                 # TODO: Lerp the value based on distance from entity
    #                 lerp_val = 0.5
    #
    #             if visible:
    #                 if (x, y) in room_centers:
    #                     tile_name = "light_center"
    #                 elif wall:
    #                     tile_name = "light_wall"
    #                 else:
    #                     tile_name = "light_ground"
    #
    #                 if (x, y) in entrances:
    #                     tile_name = "light_door"
    #
    #                 game_map.explored[y][x] = True
    #             else:
    #                 if (x, y) in room_centers:
    #                     tile_name = "dark_center"
    #                 elif wall:
    #                     tile_name = "dark_wall"
    #                 else:
    #                     tile_name = "dark_ground"
    #
    #                 if (x, y) in entrances:
    #                     tile_name = "dark_door"
    #
    #             tile_color = game_map.tile_set[tile_name].get('color')
    #             tile_char = game_map.tile_set[tile_name].get('char')
    #
    #             # TODO: How to handle wall calculations for straight walls
    #             # if 'wall' in tile_name:
    #             #     mask_char_list = [9, 186, 186, 186, 205, 188, 187, 185, 205, 200, 201, 204, 205, 202, 203, 35]
    #             #     mask = 0
    #             #     for c in [(x, y - 1, 1), (x, y + 1, 2), (x - 1, y, 4), (x + 1, y, 8)]:
    #             #         c1, c2, c_ind = c[0], c[1], c[2]
    #             #         if game_map.is_within_map(c1, c2):
    #             #             if not game_map.walkable[c2][c1]:
    #             #                 mask += c_ind
    #             #
    #             #     # let mut mask : u8 = 0;
    #             #     #
    #             #     #     if is_revealed_and_wall(map, x, y - 1) { mask +=1; }
    #             #     #     if is_revealed_and_wall(map, x, y + 1) { mask +=2; }
    #             #     #     if is_revealed_and_wall(map, x - 1, y) { mask +=4; }
    #             #     #     if is_revealed_and_wall(map, x + 1, y) { mask +=7; }
    #             #     #
    #             #     #     walls:
    #             #     #      0 => { 9 } // Pillar because no walls                      ○
    #             #     #         1 => { 186 } // Wall only to the north                   ║
    #             #     #         2 => { 186 } // Wall only to the south                  ║
    #             #     #         3 => { 186 } // Wall to the north and south              ║
    #             #     #         4 => { 205 } // Wall only to the west                   ═
    #             #     #         5 => { 188 } // Wall to the north and west               ╝
    #             #     #         6 => { 187 } // Wall to the south and west              ╗
    #             #     #         7 => { 185 } // Wall to the north, south and west        ╣
    #             #     #         8 => { 205 } // Wall only to the east                   ═
    #             #     #         9 => { 200 } // Wall to the north and east               ╚
    #             #     #         10 => { 201 } // Wall to the south and east             ╤
    #             #     #         11 => { 204 } // Wall to the north, south and east       ╠
    #             #     #         12 => { 205 } // Wall to the east and west              ═
    #             #     #         13 => { 202 } // Wall to the east, west, and south       ╩
    #             #     #         14 => { 203 } // Wall to the east, west, and north      ╦
    #             #     try:
    #             #         tile_char = mask_char_list[mask]
    #             #     except:
    #             #         print('mask:', mask)
    #             # else:
    #             #     tile_char = tile_set[tile_name].get('char')
    #             color_val = color_lerp(tuple(tile_color), lerp_color, lerp_val)
    #
    #             # Normalize Position
    #             correct_x = x - view_x_start
    #             correct_y = y - view_y_start
    #
    #             render_tile(con, correct_x, correct_y, color_val, tile_char)


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


def render_all(con, panel, top_panel, entities, player, game_map, fov_map, enemy_fov_map, fov_recompute, message_log, screen_width, screen_height,
               bar_width, panel_height, panel_y, top_gui_height, top_gui_y, mouse, game_state, viewport_width, viewport_height, toggle_reveal_all=0):
    # Draw Console to Screen
    view_x_start, view_x_end, view_y_start, view_y_end = obtain_viewport_dimensions(game_map, viewport_width,
                                                                                    viewport_height)

    # Background, Tiles, Etc.
    render_viewport(con, game_map, entities, fov_map, enemy_fov_map, fov_recompute, toggle_reveal_all, view_x_start, view_x_end,
                    view_y_start, view_y_end)

    # Sort Draw Order to Sort by Render Order Enum Value
    entities_in_render_order = sorted(entities, key=lambda x: x.render_order.value)
    # Draw all entities in the list
    # print('# Draw all entities in the list')
    for entity in entities_in_render_order:

        if view_x_start <= entity.x < view_x_end and view_y_start <= entity.y < view_y_end:
            # print('drawing %s entity' % entity.name)
            draw_entity(con, entity, fov_map, game_map, toggle_reveal_all, view_x_start, view_x_end, view_y_start,
                        view_y_end)

    # Draw Console to Screen
    # TODO: Create a "map" console to render game_map not directly onto root(con) console.

    viewport_width_start = ((screen_width // 2) - viewport_width) * -1
    viewport_height_start = ((screen_height // 2) - (viewport_height // 2)) // -2
    libtcod.console_blit(con, viewport_width_start, viewport_height_start, screen_width, screen_height, 0, 0, 0)
    # print('\nCentering Viewport')
    # print(screen_width // 2, viewport_width // 2, viewport_width_start)
    # print(screen_height // 2, viewport_height // 2, viewport_height_start)

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
                             get_info_under_mouse(mouse, game_map, entities, game_map.map_objects, fov_map,
                                                  toggle_reveal_all, view_x_start, view_x_end, view_y_start, view_y_end,
                                                  viewport_width, viewport_height, viewport_width_start,
                                                  viewport_height_start))
    libtcod.console_blit(panel, 0, 0, screen_width, panel_height, 0, 0, panel_y)

    # # Enemy Display
    # # libtcod.console_clear(top_panel)
    # top_panel.clear()
    # libtcod.console_set_default_foreground(top_panel, libtcod.light_gray)
    # test = ''
    #
    # for i in range(1, 1000):
    #     test += "%c%c%c%c " % (libtcod.COLCTRL_FORE_RGB, random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) + \
    #        random.choice(string.ascii_letters) + "%c" % libtcod.COLCTRL_STOP
    #     if i % screen_width == 0:
    #         test += " \n"
    # # x: int, y: int, string: str, fg: Optional[Tuple[int, int, int]] = None, bg: Optional[
    #     # Tuple[int, int, int]] = None, bg_blend: int = 1, alignment: int =
    # top_panel.print(x=0, y=0, string=test, fg=libtcod.light_gray)
    #
    # libtcod.console_blit(top_panel, 0, 0, screen_width, top_gui_height, 0, 0, top_gui_y)

    if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
        if game_state == GameStates.SHOW_INVENTORY:
            inventory_title = 'Press the key next to an item to use it, or Esc to cancel.\n'
        else:
            inventory_title = 'Press the key next to an item to drop it, or Esc to cancel.\n'

        inventory_menu(con, inventory_title, player, 50, screen_width, screen_height)

    elif game_state == GameStates.DEBUG_MENU:
        menu_title = 'Debug Menu\n'
        debug_menu(con, menu_title, 30, screen_width, screen_height)

    elif game_state == GameStates.LEVEL_UP:
        level_up_menu(con, 'Level up! Choose a stat to raise:', player, 30, screen_width, screen_height)

    elif game_state == GameStates.CHARACTER_SCREEN:
        character_screen(player, 30, 10, screen_width, screen_height)

    elif game_state == GameStates.READ:
        map_screen(con, entities, game_map, "Dungeon Map", int(game_map.width * 0.75), int(game_map.height * 0.75), screen_width,
                   screen_height, panel_height)


# def clear_all(con, entities, view_x_start, view_x_end, view_y_start, view_y_end):
#     for entity in entities:
#         if view_x_start < entity.x < view_x_end and view_y_start < entity.y < view_y_end:
#             clear_entity(con, entity, view_x_start, view_x_end, view_y_start, view_y_end)


def draw_entity(con, entity, fov_map, game_map, toggle_reveal_all, view_x_start, view_x_end, view_y_start, view_y_end):
    # TODO: Handle drawing entities, not within FOV
    # Draw Console to Screen
    # Normalize Position
    entity_x = entity.x - view_x_start
    entity_y = entity.y - view_y_start

    # Render Entity if Within FOV or Stairs
    if fov_map.fov[entity.y][entity.x] or toggle_reveal_all == 1:
        libtcod.console_set_default_foreground(con, entity.color)
        libtcod.console_put_char(con, entity_x, entity_y, entity.char, libtcod.BKGND_NONE)

    # Render Entity although Not in FOV
    elif entity.fov_color and game_map.explored[entity.y][entity.x] and toggle_reveal_all < 1:
        libtcod.console_set_default_foreground(con, entity.fov_color)
        libtcod.console_put_char(con, entity_x, entity_y, entity.char, libtcod.BKGND_NONE)


def clear_entity(con, entity, view_x_start, view_x_end, view_y_start, view_y_end):
    # Erase the character that represents this object
    entity_x = entity.x - view_x_start
    entity_y = entity.y - view_y_start
    libtcod.console_put_char(con, entity_x, entity_y, " ", libtcod.BKGND_NONE)
