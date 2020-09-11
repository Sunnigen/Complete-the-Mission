import tcod
from tcod.image import Image as TcodImage

from EquipmentSlots import EQUIPMENT_SLOT_NAME
from loader_functions.JsonReader import obtain_tile_set

TILE_SET = obtain_tile_set()


def picture(console, game_map, dungeon_map, header, map_width, map_height, screen_width, screen_height, panel_height):
    # create an off-screen console that represents the menu's window
    window = tcod.console_new(screen_width, screen_height)

    dungeon_map.blit_2x(window, 0, 0, 0, 0, -1, -1)

    # blit the contents of "window" to the root console
    # (-map_width // 2) - (screen_width // 2)
    # (-map_height // 2) - (screen_height // 2)
    true_width, true_height = 0, 0

    if map_width >= screen_width:
        true_width = 0
    else:
        true_width = -map_width // 4

    if map_height >= screen_height:
        true_height = 0
    else:
        true_height = -map_height // 4
    window.blit(dest=console, dest_x=0, dest_y=0, src_x=0, src_y=0,width=map_width, height=map_height)
    # tcod.console_blit(window, true_width, true_height, map_width, map_height, 1, 0, 0, 1.0, 1.0)
    # tcod.console_blit(window, -map_width // 4, -map_height // 4, map_width, map_height, 1, 0, 0, 1.0, 1.0)


def menu(console, header, options, width, screen_width, screen_height, cursor_position=0):
    # Main Function to Display a Generic Menu
    if len(options) > 26:
        raise ValueError("Cannot have a menu with more than 26 options!")

    # Calculate total height for the header (after auto-wrap) and one line per option
    header_height = console.get_height_rect(0, 0, width, screen_height, header)
    height = len(options) + header_height

    # create an off-screen console that represents the menu's window
    window = tcod.console.Console(width, height)

    # print the header, with auto-wrap
    # tcod.console_set_default_foreground(window, tcod.white)
    window.print_box(0, 0, width, height, header, alignment=tcod.LEFT)

    # print all the options is a letter-bullet-list format
    y = header_height
    letter_index = ord('a')
    for i, option_text in enumerate(options):
        text = '(%s) %s' % (chr(letter_index), option_text)
        if i == cursor_position:
            fg = tcod.white
            bg = tcod.light_blue
        else:
            fg = tcod.grey
            bg = tcod.black
        window.print(0, y, text,
                     fg=fg,
                     bg=bg,
                     bg_blend=tcod.BKGND_NONE,
                     alignment=tcod.LEFT)
        y += 1
        letter_index += 1

    # blit the contents of "window" to the root console
    x = int(screen_width / 2 - width / 2)
    y = int(screen_height / 2 - height / 2)
    window.blit(dest=console, dest_x=x, dest_y=y, src_x=0, src_y=0, width=width, height=height, fg_alpha=1.0,
                bg_alpha=0, key_color=None)


def inventory_menu(con, header, player, inventory_width, screen_width, screen_height):
    # show a menu with each item of the inventory as an option
    if len(player.inventory.items) == 0:
        options = ['Inventory is empty.']
    else:
        options = []

        temporary_equip_dict = {value:key for key, value in player.equipment.equipment_dict.items()}

        for item in player.inventory.items:

            equipment = temporary_equip_dict.get(item, None)
            if equipment:
                options.append('{} ({})'.format(item.name, EQUIPMENT_SLOT_NAME[equipment]))
            else:
                options.append(item.name)
            # for equipment_slot, equipment in player.equipment.equipment_dict.items():
            #     if equipment == item:
            #         options.append('{} (on {})'.format(item.name, EQUIPMENT_SLOT_NAME[equipment_slot]))
            #     else:
            #         options.append(item.name)

            # if player.equipment.main_hand == item:
            #     options.append('%s (on main hand)' % item.name)
            # elif player.equipment.off_hand == item:
            #     options.append('%s (on off hand)' % item.name)
            # else:
            #     options.append(item.name)

    menu(con, header, options, inventory_width, screen_width, screen_height)


def select_level(con, levels, width, screen_width, screen_height):
    # Level Selection
    # menu(con, header, options, width, screen_width, screen_height):
    #
    tcod.console_set_default_foreground(0, tcod.yellow)
    tcod.console_print_ex(0, int(screen_width / 2), int(screen_height / 2) - 4, tcod.BKGND_DEFAULT,
                             tcod.CENTER,
                             'LEVEL SELECT')
    menu(con, '', levels, width, screen_width, screen_height)


def level_up_menu(con, header, player, menu_width, screen_width, screen_height):
    options = ['Constitution (+20 HP, from %s).' % player.fighter.max_hp,
               'Strength (+1 attack, from %s).' % player.fighter.power,
               'Defense (+1 defense, from %s).' % player.fighter.defense]

    menu(con, header, options, menu_width, screen_width, screen_height)


def map_screen(console, entities, game_map, header, map_width, map_height, screen_width, screen_height, panel_height):
    # TODO: Save processing time by keeping base map as image file and modify add entities before blitting?
    dungeon_map = TcodImage(width=game_map.width, height=game_map.height)

    for x in range(game_map.width):
        for y in range(game_map.height):
            tile = TILE_SET.get("%s" % (game_map.tileset_tiles[y][x]))
            color = tile.get("fg_color", tile["color"])
            dungeon_map.put_pixel(x, y, color)

    for entity in entities:
        if entity.stairs:
            dungeon_map.put_pixel(entity.position.x, entity.position.y, entity.color)
            continue
        if entity.fighter and not entity.ai:
            dungeon_map.put_pixel(entity.position.x, entity.position.y, entity.color)
        elif entity.ai:
            dungeon_map.put_pixel(entity.position.x, entity.position.y, entity.color)

    picture(console, game_map, dungeon_map, header, map_width, map_height, screen_width, screen_height, panel_height)


def debug_menu(con, header, menu_width, screen_width, screen_height):
    options = ['Toggle God Mode',
               'Toggle Reveal Map',
               'Level Up',
               'Go to Next Level',
               'Revive Player',
               'Show Spawn Table',
               'font size 8',
               'font size 10',
               'font size 16']
    menu(con, header, options, menu_width, screen_width, screen_height)


def character_screen(player, character_screen_width, character_screen_height, screen_width, screen_height):
    window = tcod.console_new(character_screen_width, character_screen_height)

    tcod.console_set_default_foreground(window, tcod.white)

    tcod.console_print_rect_ex(window, 0, 1, character_screen_width, character_screen_height, tcod.BKGND_NONE,
                                  tcod.LEFT, 'Character Information')

    tcod.console_print_rect_ex(window, 0, 1, character_screen_width, character_screen_height, tcod.BKGND_NONE,
                                  tcod.LEFT, 'Character Information')

    tcod.console_print_rect_ex(window, 0, 2, character_screen_width, character_screen_height, tcod.BKGND_NONE,
                                  tcod.LEFT, 'Level: {0}'.format(player.level.current_level))

    tcod.console_print_rect_ex(window, 0, 3, character_screen_width, character_screen_height, tcod.BKGND_NONE,
                                  tcod.LEFT, 'Experience: {0}'.format(player.level.current_xp))

    tcod.console_print_rect_ex(window, 0, 4, character_screen_width, character_screen_height, tcod.BKGND_NONE,
                                  tcod.LEFT, 'Experience to Level: {0}'.format(player.level.experience_to_next_level))

    tcod.console_print_rect_ex(window, 0, 6, character_screen_width, character_screen_height, tcod.BKGND_NONE,
                                  tcod.LEFT, 'Maximum HP: {0}'.format(player.fighter.max_hp))

    tcod.console_print_rect_ex(window, 0, 7, character_screen_width, character_screen_height, tcod.BKGND_NONE,
                                  tcod.LEFT, 'Attack: {0}'.format(player.fighter.power))

    tcod.console_print_rect_ex(window, 0, 8, character_screen_width, character_screen_height, tcod.BKGND_NONE,
                                  tcod.LEFT, 'Defense: {0}'.format(player.fighter.defense))

    x = screen_width // 2 - character_screen_width // 2
    y = screen_height // 2 - character_screen_height // 2
    tcod.console_blit(window, 0, 0, character_screen_width, character_screen_height, 0, x, y, 1.0, 0.7)


def message_box(con, header, width, screen_width, screen_height):
    # Return a 'simple' Message Box
    menu(con, header, [], width, screen_width, screen_height)
