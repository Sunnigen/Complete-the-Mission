import string
import sys
import random

import tcod
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


def get_info_under_mouse(mouse_pos, game_map, entities, map_objects, fov_map, toggle_reveal, view_x_start, view_x_end, view_y_start,
                         view_y_end, viewport_width, viewport_height, viewport_width_start, viewport_height_start):

    (x, y) = mouse_pos
    names = []
    for entity in entities + map_objects:

        # Mob Name
        if entity.x == x + view_x_start + viewport_width_start and entity.y == y + view_y_start + viewport_height_start and (tcod.map_is_in_fov(fov_map, entity.x, entity.y) or toggle_reveal):
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

    # Transition to a "static" viewport if game_map width/height is less than viewport width/height
    # TODO: Center the viewport
    if game_map.width < viewport_width * 2 or game_map.height < viewport_height * 2:
        # print('static viewport', game_map.width, viewport_width, game_map.height, viewport_height)
        return 0, game_map.width + 2, 0, game_map.height + 2
    # if game_map.width

    # Left or Right of Screen
    if player_x - viewport_width < 0:
        view_x_start = 0
        view_x_end = (2 * viewport_width)
    elif player_x + viewport_width >= game_map.width + 2:
        view_x_start = game_map.width - (2 * viewport_width) + 2
        view_x_end = game_map.width + 2
    else:
        view_x_start = player_x - viewport_width
        view_x_end = player_x + viewport_width

    # Top or Bottom of Screen
    if player_y - viewport_height < 0:
        view_y_start = 0
        view_y_end = 2 * viewport_height
    elif player_y + viewport_height >= game_map.height + 2:
        view_y_start = game_map.height - (2 * viewport_height) + 2
        view_y_end = game_map.height + 2
    else:
        view_y_start = player_y - viewport_height + 1
        view_y_end = player_y + viewport_height + 1

    return view_x_start, view_x_end, view_y_start, view_y_end


def render_tile(con, x, y, color, char, fg_color=tcod.white):
    tcod.console_set_char_background(con, x, y, color, tcod.BKGND_SET)
    tcod.console_set_default_foreground(con, fg_color)
    tcod.console_put_char(con, x, y, char)


def render_viewport(con, mouse_pos, game_map, entities, fov_map, enemy_fov_map, fov_recompute, toggle_reveal_all,
                    view_x_start, view_x_end, view_y_start, view_y_end, viewport_width_start, viewport_height_start):
    # print('render_viewport', fov_recompute)
    # if fov_recompute:
    # Obtain all Center Coordinates
    room_centers = []
    monster_locations = []
    if toggle_reveal_all > 0:
        # room_centers = [room.center for room in game_map.rooms]
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

                # if (x, y) in room_centers:
                #     tile = 3
            tile_fg_color = game_map.tile_set[str(tile)].get('fg_color', tcod.white)

            # Select Tile
            if visible:
                tile_color = game_map.tile_set[str(tile)].get('color')
                tile_char = game_map.tile_set[str(tile)].get('char')

                game_map.explored[y][x] = True
                if enemy_fov_map[y][x]:  # Check if tile is visible to enemy at (x, y):
                    # TODO: Lerp the value based on distance from entity
                    lerp_val = 0.5

            # Tile Has Been Seen Before, but not in Current FOV
            elif game_map.explored[y][x] or toggle_reveal_all == 1:
                # Darken Color
                tile_color = color_lerp(game_map.tile_set[str(tile)].get('color'), (0, 0, 0), 0.5)
                tile_char = game_map.tile_set[str(tile)].get('fov_char')
                tile_fg_color = color_lerp(tile_fg_color, (0, 0, 0), 0.5)

            # Unexplored Area
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

            # Normalize Position
            correct_x = x - view_x_start - viewport_width_start
            correct_y = y - view_y_start - viewport_height_start

            # Highlight Mouse Position
            is_mouse_pos = (x, y) == mouse_pos
            color_val = color_lerp(tuple(tile_color), lerp_color, lerp_val)  # highlight if within monster FOV
            color_val = color_lerp(color_val, tcod.white, is_mouse_pos * 0.4)  # highlight if under mouse

            render_tile(con, correct_x, correct_y, color_val, tile_char, fg_color=tile_fg_color)
            # if not game_map.tileset_tiles[y][x] == 0 and game_map.explored[y][x]:
            #     tile_char = game_map.tile_set[str(tile)].get('char')


def render_bar(panel, x, y, total_width, name, value, maximum, bar_color, back_color):
    # Render Bar(Current Value) Over Dark Bar(Max Value)
    bar_width = int(float(value) / maximum * total_width)

    # Current Bar, Dynamically Increases/Decreases
    # tcod.console_set_default_background(panel, back_color)
    # tcod.console_rect(panel, x, y, total_width, 1, False, tcod.BKGND_SCREEN)


    # draw_rect(x: int, y: int, width: int, height: int, ch: int, fg: Optional[Tuple[int, int, int]] = None,
    # bg: Optional[Tuple[int, int, int]] = None, bg_blend: int = 1)

    panel.draw_rect(x, y, total_width, 1, 127, bg=back_color, bg_blend=tcod.BKGND_SCREEN)

    # Max Bar, Never Decreases
    # tcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        # tcod.console_rect(panel, x, y, bar_width, 1, False, tcod.BKGND_SCREEN)

        panel.draw_rect(x, y, bar_width, 1, 127, bg=bar_color, bg_blend=tcod.BKGND_SCREEN)

    # Display Text
    # tcod.console_set_default_foreground(panel, tcod.white)
    # tcod.console_print_ex(panel, int(x + total_width / 2), y, tcod.BKGND_NONE, tcod.CENTER, )

    panel.print(int(x + total_width / 2), y, '%s: %s/%s' % (name, value, maximum), fg=tcod.white, bg_blend=tcod.BKGND_NONE,
                alignment=tcod.CENTER)


def draw_entity(con, entity, fov_map, game_map, toggle_reveal_all, view_x_start, view_x_end, view_y_start, view_y_end,
                viewport_width_start, viewport_height_start):
    # TODO: Handle drawing entities, not within FOV
    # Draw Console to Screen
    # Normalize Position
    entity_x = entity.x - view_x_start - viewport_width_start
    entity_y = entity.y - view_y_start - viewport_height_start

    # Render Entity if Within FOV or Stairs
    if fov_map.fov[entity.y][entity.x] or toggle_reveal_all == 1:
        tcod.console_set_default_foreground(con, entity.color)
        tcod.console_put_char(con, entity_x, entity_y, entity.char, tcod.BKGND_NONE)

    # Render Entity although Not in FOV
    elif entity.fov_color and game_map.explored[entity.y][entity.x] and toggle_reveal_all < 1:
        tcod.console_set_default_foreground(con, entity.fov_color)
        tcod.console_put_char(con, entity_x, entity_y, entity.char, tcod.BKGND_NONE)


def clear_entity(con, entity, view_x_start, view_x_end, view_y_start, view_y_end):
    # Erase the character that represents this object
    entity_x = entity.x - view_x_start
    entity_y = entity.y - view_y_start
    tcod.console_put_char(con, entity_x, entity_y, " ", tcod.BKGND_NONE)
