from random import choice

from tcod import color_lerp
import tcod

from enum import Enum


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

    return view_x_start, view_x_end, view_y_start, view_y_end


def render_tile(console, x, y, bg_color, char, fg_color=tcod.white):
    console.print(x=x, y=y, string="%s" % char, fg=fg_color, bg=bg_color, alignment=tcod.CENTER)


def render_viewport(console, mouse_pos, mouse_targets, game_map, entities, fov_map, enemy_fov_map, fov_recompute, toggle_reveal_all,
                    view_x_start, view_x_end, view_y_start, view_y_end, viewport_width_start, viewport_height_start, default_tile=1):
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
                visible = fov_map.fov[x][y]  # Check if tile is visible at (x, y)
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
                tile = default_tile
                visible = False
                enemy_fov = False
                walkable = False
                explored = True

                # sys.exit()


            # wall = not game_map.walkable[y][x]  # Check if tile is a wall at (x, y)
            enemy_fov = False
            # Add Highlight to Entity and Entity's FOV
            lerp_val = 0.5 * toggle_reveal_all * enemy_fov * walkable
            # print('lerp_val:', lerp_val)
                # if (x, y) in room_centers:
                #     tile = 3
            tile_fg_color = game_map.tile_set[str(tile)].get('fg_color', tcod.white)

            # Select Tile
            # visible = True
            if visible:
                tile_color = game_map.tile_set[str(tile)].get('color')
                tile_char = game_map.tile_set[str(tile)].get('glyph')

                game_map.explored[y][x] = True

                # if enemy_fov:  # Check if tile is visible to enemy at (x, y):
                # TODO: Lerp the value based on distance from entity
                lerp_val = 0.25 * enemy_fov * (not walkable)
                # print('lerp_val', lerp_val, enemy_fov, walkable)
                # lerp_val = 0.5

            # Tile Has Been Seen Before, but not in Current FOV
            elif explored or toggle_reveal_all == 1:
                # Darken Color
                tile_color = color_lerp(game_map.tile_set[str(tile)].get('color'), (0, 0, 0), 0.75)
                tile_char = game_map.tile_set[str(tile)].get('glyph')
                tile_fg_color = color_lerp(tile_fg_color, (0, 0, 0), 0.75)

            # Unexplored Area
            else:
                tile = 0
                tile_color = game_map.tile_set[str(tile)].get('color')
                tile_char = game_map.tile_set[str(tile)].get('glyph')



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

            render_tile(console, correct_x, correct_y, color_val, tile_char, fg_color=tile_fg_color)
            # if not game_map.tileset_tiles[y][x] == 0 and game_map.explored[y][x]:
            #     tile_char = game_map.tile_set[str(tile)].get('char')


def render_tileset(console):

    # tiles = [160, 9632, 178, 8319, 8730, 183, 8729, 176, 8776, 247, 8993, 8992, 8804, 8805, 177, 8801, 8745, 949, 966,
    #          8734, 948, 937, 920, 934, 964, 181, 963, 931, 960, 915, 223, 945, 9600, 9616, 9612, 9604, 9608, 9484, 9496,
    #          9578, 9579, 9555, 9554, 9560, 9561, 9573, 9572, 9576, 9575, 9580, 9552, 9568, 9574, 9577, 9556, 9562, 9567,
    #          9566, 9532, 9472, 9500, 9516, 9524, 9492, 9488, 9563, 9564, 9565, 9559, 9553, 9571, 9557, 9558, 9570, 9569,
    #          9508, 9474, 9619, 9618, 9617, 187, 171, 161, 188, 189, 172, 8976, 191, 186, 170, 209, 241, 250, 243, 237,
    #          225, 402, 8359, 165, 163, 162, 220, 214, 255, 249, 251, 242, 246, 244, 198, 230, 201, 197, 196, 236, 238,
    #          239, 232, 235, 234, 231, 229, 224, 228, 226, 233, 252, 199, 127, 126, 125, 124, 123, 122, 121, 120, 119,
    #          118, 117, 116, 115, 114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100, 99, 98, 97,
    #          96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80, 79, 78, 77, 76, 75, 74, 73, 72, 71, 70,
    #          69, 68, 67, 66, 65, 64, 63, 62, 61, 60, 59, 58, 57, 56, 55, 54, 53, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43,
    #          42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 9660, 9650, 8596, 8735, 8592, 8594, 8595, 8593, 8616, 9644,
    #          167, 182, 8252, 8597, 9668, 9658, 9788, 9835, 9834, 9792, 9794, 9689, 9675, 9688, 8226, 9824, 9827, 9830,
    #          9829, 9787, 9786, 0]

    #                          z    y    x    w    v    u    t    s    r    q    p    o    n    m    l    k    j    i
    tiles = [0, 0, 0, 0, 0, 0, 122, 121, 120, 119, 118, 117, 116, 115, 114, 113, 112, 111, 110, 109, 108, 107, 106, 105,

             # h    g    f    e    d   c   b   a                     Z   Y   X   W   V   U   T   S   R   Q   P   O   N
             104, 103, 102, 101, 100, 99, 98, 97, 0, 0, 0, 0, 0, 0, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80, 79, 78,

             # M  L   K   J   I   H   G   F   E   D   C   B   A                          ]     W     T     Z     f
             77, 76, 75, 74, 73, 72, 71, 70, 69, 68, 67, 66, 65, 0, 0, 0, 0, 0, 0, 0, 9565, 9559, 9556, 9562, 9574,

             #  `     i     c     l     P     Q     ╔     ╦     ◄     ►     ö     ò     ║     ─     ╝     ▓     Æ     É
             9568, 9577, 9571, 9580, 9552, 9553, 9673, 9675, 9745, 9744, 8596, 8597, 9658, 9668, 9660, 9650, 8594, 8592,

             #  ô     æ     ù     É     Ü     û     Ç     ¥     ÿ     ↑     ►     ♀     ¶     ,     ∟     4     $     <
             8595, 8593, 9623, 9616, 9626, 9622, 9600, 9629, 9624, 9496, 9488, 9484, 9492, 9516, 9500, 9524, 9508, 9532,

             #  #     ☻     ô     Æ     æ    ~    }    |   {    `   _   ^   ]   \   [   @   ?   >   =   <   ;   :   9
             9472, 9474, 9619, 9618, 9617, 126, 125, 124, 123, 96, 95, 94, 93, 92, 91, 64, 63, 62, 61, 60, 59, 58, 57,

             # 8  7   6   5   4   3   2   1   0   /   .   -   ,   +   *   )   (   '   &   %   $   #   "   !
             56, 55, 54, 53, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32]

    x, y = 0, 0
    while tiles:
        c = tiles.pop()
        tile_char = chr(c)
        render_tile(console, x, y, tcod.white, tile_char, fg_color=tcod.white)

        x += 1
        if x > 31:
            y += 1
            x = 0


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


def draw_entity(console, entity, fov_map, game_map, toggle_reveal_all, view_x_start, view_x_end, view_y_start, view_y_end,
                viewport_width_start, viewport_height_start):
    # Normalize Position
    entity_x = entity.position.x - view_x_start - viewport_width_start
    entity_y = entity.position.y - view_y_start - viewport_height_start

    # Render Entity if Within FOV or Stairs
    if fov_map.fov[entity.position.x][entity.position.y] or toggle_reveal_all == 1:
        console.print(x=entity_x, y=entity_y, string="%s"%entity.char, fg=entity.color)


def draw_particle_entity(console, particle_entity, fov_map, reveal_all, view_x_start, view_y_start, viewport_width_start,
                         viewport_height_start):

    # Obtain Coordinates Relative to Map Screen
    entity_x = particle_entity.position.x - view_x_start - viewport_width_start
    entity_y = particle_entity.position.y - view_y_start - viewport_height_start
    particle = particle_entity.particle

    # Print Particle BG, FG and Char on Map
    if fov_map.fov[particle_entity.position.x][particle_entity.position.y] or reveal_all or not particle.within_fov:
        c = ' '
        if particle.char:
            c = particle.char

        bg = None
        if particle.bg:
            bg = choice(particle.bg)

        console.print(x=entity_x, y=entity_y, string=c, fg=particle.fg, bg=bg)


def clear_entity(con, entity, view_x_start, view_x_end, view_y_start, view_y_end):
    # Erase the character that represents this object
    entity_x = entity.position.x - view_x_start
    entity_y = entity.position.y - view_y_start
    tcod.console_put_char(con, entity_x, entity_y, " ", tcod.BKGND_NONE)
