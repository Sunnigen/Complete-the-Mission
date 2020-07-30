import string
import sys
from random import choice

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
    PARTICLE = 5


def obtain_viewport_dimensions(game_map, viewport_width, viewport_height):
    player_x, player_y = game_map.player.position.x, game_map.player.position.y

    # Transition to a "static" viewport if game_map width/height is less than viewport width/height
    # TODO: Center the viewport
    if game_map.width < viewport_width * 2 or game_map.height < viewport_height * 2:
        # print('static viewport', game_map.width, viewport_width, game_map.height, viewport_height)
        return 0, game_map.width + 2, 0, game_map.height + 2

    view_x_start = player_x - viewport_width
    view_x_end = player_x + viewport_width
    view_y_start = player_y - viewport_height + 1
    view_y_end = player_y + viewport_height + 1


    # # Left or Right of Screen
    # if player_x - viewport_width < 0:
    #     view_x_start = 0
    #     view_x_end = (2 * viewport_width)
    # elif player_x + viewport_width >= game_map.width + 2:
    #     view_x_start = game_map.width - (2 * viewport_width) + 2
    #     view_x_end = game_map.width + 2
    # else:
    #     view_x_start = player_x - viewport_width
    #     view_x_end = player_x + viewport_width
    #
    # # Top or Bottom of Screen
    # if player_y - viewport_height < 0:
    #     view_y_start = 0
    #     view_y_end = 2 * viewport_height
    # elif player_y + viewport_height >= game_map.height + 2:
    #     view_y_start = game_map.height - (2 * viewport_height) + 2
    #     view_y_end = game_map.height + 2
    # else:
    #     view_y_start = player_y - viewport_height + 1
    #     view_y_end = player_y + viewport_height + 1

    return view_x_start, view_x_end, view_y_start, view_y_end


def render_tile(con, x, y, color, char, fg_color=tcod.white):
    tcod.console_set_char_background(con, x, y, color, tcod.BKGND_SET)
    tcod.console_set_default_foreground(con, fg_color)
    tcod.console_put_char(con, x, y, char)


def render_viewport(con, mouse_pos, mouse_targets, game_map, entities, fov_map, enemy_fov_map, fov_recompute, toggle_reveal_all,
                    view_x_start, view_x_end, view_y_start, view_y_end, viewport_width_start, viewport_height_start):
    # print('render_viewport', fov_recompute)
    # if fov_recompute:
    # Obtain all Center Coordinates

    # Render Walls and Floors
    lerp_color = (128, 64, 64)

    for y in range(view_y_start, view_y_end):
        for x in range(view_x_start, view_x_end):
            try:
                1 // (abs(y + 1) + y + 1)
                1 // (abs(x + 1) + x + 1)
                tile = game_map.tileset_tiles[y][x]
                visible = fov_map.fov[y][x]  # Check if tile is visible at (x, y)
                enemy_fov = enemy_fov_map[y][x]  # Check if tile is visible to enemy at (x, y)
                walkable = not game_map.walkable[y][x]
                explored = game_map.explored[y][x]
            except:
            # except IndexError or ZeroDivisionError:
            #     print('IndexError!')
                # print(view_x_start, view_x_end)
                # print(view_y_start, view_y_end)
                # print(game_map.width, game_map.height)
                # print('x/y:', x, y)
                # print(len(game_map.tileset_tiles), len(game_map.tileset_tiles))
                tile = 1
                visible = False
                enemy_fov = False
                walkable = False
                explored = False

                # sys.exit()


            # wall = not game_map.walkable[y][x]  # Check if tile is a wall at (x, y)

            # Add Highlight to Entity and Entity's FOV
            lerp_val = 0.05 * toggle_reveal_all * enemy_fov * walkable
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
            elif explored or toggle_reveal_all == 1:
                # Darken Color
                tile_color = color_lerp(game_map.tile_set[str(tile)].get('color'), (0, 0, 0), 0.75)
                tile_char = game_map.tile_set[str(tile)].get('fov_char')
                tile_fg_color = color_lerp(tile_fg_color, (0, 0, 0), 0.75)

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
            # TODO: Area of affect or mouse path highlighting
            # print("mouse_targets:", mouse_targets)

            is_mouse_pos = (x, y) in mouse_targets
            # is_mouse_pos = ((x, y) == mouse_pos) * ((x, y) in mouse_targets)
            color_val = color_lerp(tuple(tile_color), lerp_color, lerp_val)  # highlight if within monster FOV
            color_val = color_lerp(color_val, tcod.white, is_mouse_pos * 0.4)  # highlight if under mouse

            render_tile(con, correct_x, correct_y, color_val, tile_char, fg_color=tile_fg_color)
            # if not game_map.tileset_tiles[y][x] == 0 and game_map.explored[y][x]:
            #     tile_char = game_map.tile_set[str(tile)].get('char')


def render_bar(panel, x, y, total_width, name, value, maximum, bar_color, back_color):
    # Render Bar(Current Value) Over Dark Bar(Max Value)
    bar_width = int(float(value) / maximum * total_width)

    # Current Bar, Dynamically Increases/Decreases
    panel.draw_rect(x, y, total_width, 1, 127, bg=back_color, bg_blend=tcod.BKGND_SCREEN)

    # Max Bar, Never Decreases
    if bar_width > 0:
        panel.draw_rect(x, y, bar_width, 1, 127, bg=bar_color, bg_blend=tcod.BKGND_SCREEN)

    # Display Text
    panel.print(int(x + total_width / 2), y, '%s: %s/%s' % (name, value, maximum), fg=tcod.white, bg_blend=tcod.BKGND_NONE,
                alignment=tcod.CENTER)


def draw_entity(con, entity, fov_map, game_map, toggle_reveal_all, view_x_start, view_x_end, view_y_start, view_y_end,
                viewport_width_start, viewport_height_start):
    # TODO: Handle drawing entities, not within FOV
    # Draw Console to Screen
    # Normalize Position
    entity_x = entity.position.x - view_x_start - viewport_width_start
    entity_y = entity.position.y - view_y_start - viewport_height_start

    # Render Entity if Within FOV or Stairs
    if fov_map.fov[entity.position.y][entity.position.x] or toggle_reveal_all == 1:
        con.put_char(entity_x, entity_y, entity.char)
        con.fg[entity_y, entity_x] = entity.color

    # # Render Entity although Not in FOV
    # elif entity.fov_color and game_map.explored[entity.position.y][entity.position.x] and toggle_reveal_all < 1:
    #     con.put_char(entity_x, entity_y, entity.char)
    #     con.fg[entity_y, entity_x] = entity.fov_color


def draw_particle_entity(con, entity, fov_map, reveal_all, view_x_start, view_y_start, viewport_width_start,
                         viewport_height_start):
    entity_x = entity.position.x - view_x_start - viewport_width_start
    entity_y = entity.position.y - view_y_start - viewport_height_start

    particle = entity.particle
    if fov_map.fov[entity.position.y][entity.position.x] or reveal_all:

        if particle.char:
            # print('placing particle char')
            con.put_char(entity_x, entity_y, particle.char)

        if particle.fg:
            # print('placing particle fg')
            con.fg[entity_y, entity_x] = particle.fg
            # tcod.console_set_default_foreground(con, particle)

        if particle.bg:
            # print('placing particle bg')
            con.bg[entity_y, entity_x] = choice(particle.bg)
            # tcod.console_set_default_background(con, particle)


def clear_entity(con, entity, view_x_start, view_x_end, view_y_start, view_y_end):
    # Erase the character that represents this object
    entity_x = entity.position.x - view_x_start
    entity_y = entity.position.y - view_y_start
    tcod.console_put_char(con, entity_x, entity_y, " ", tcod.BKGND_NONE)
