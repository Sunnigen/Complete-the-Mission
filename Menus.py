import tcod as libtcod
from tcod.image import Image as TcodImage


def picture(con, game_map, dungeon_map, header, map_width, map_height, screen_width, screen_height, panel_height):
    # create an off-screen console that represents the menu's window
    window = libtcod.console_new(screen_width, screen_height)

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

    libtcod.console_blit(window, true_width, true_height, map_width, map_height, 1, 0, 0, 1.0, 1.0)
    # libtcod.console_blit(window, -map_width // 4, -map_height // 4, map_width, map_height, 1, 0, 0, 1.0, 1.0)


def menu(con, header, options, width, screen_width, screen_height):
    # Main Function to Display a Generic Menu
    if len(options) > 26:
        raise ValueError("Cannot have a menu with more than 26 options!")

    # Calculate total height for the header (after auto-wrap) and one line per option
    header_height = libtcod.console_get_height_rect(con, 0, 0, width, screen_height, header)
    height = len(options) + header_height

    # create an off-screen console that represents the menu's window
    window = libtcod.console_new(width, height)

    # print the header, with auto-wrap
    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)

    # print all the options is a letter-bullet-list format
    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(%s) %s' % (chr(letter_index), option_text)
        libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
        y += 1
        letter_index += 1

    # blit the contents of "window" to the root console
    x = int(screen_width / 2 - width / 2)
    y = int(screen_height / 2 - height / 2)
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)


def inventory_menu(con, header, player, inventory_width, screen_width, screen_height):
    # show a menu with each item of the inventory as an option
    if len(player.inventory.items) == 0:
        options = ['Inventory is empty.']
    else:
        # options = [item.name for item in inventory.items]
        options = []

        for item in player.inventory.items:
            if player.equipment.main_hand == item:
                options.append('%s (on main hand)' % item.name)
            elif player.equipment.off_hand == item:
                options.append('%s (on off hand)' % item.name)
            else:
                options.append(item.name)

    menu(con, header, options, inventory_width, screen_width, screen_height)


def main_menu(con, background_image, screen_width, screen_height):
    # Display the Main Menu
    # libtcod.image_blit_2x(background_image, 0, 0, 0)

    libtcod.console_set_default_foreground(0, libtcod.yellow)
    libtcod.console_print_ex(0, int(screen_width / 2), int(screen_height / 2) - 4, libtcod.BKGND_DEFAULT, libtcod.CENTER,
                             'TOMBS OF THE ANCIENT KINGS')
    libtcod.console_print_ex(0, int(screen_width / 2), int(screen_height - 2), libtcod.BKGND_DEFAULT, libtcod.CENTER,
                             'By ********')

    menu(con, '', ['New Game', 'Continue', 'Quit'], 24, screen_width, screen_height)


def level_up_menu(con, header, player, menu_width, screen_width, screen_height):
    options = ['Constitution (+20 HP, from %s).' % player.fighter.max_hp,
               'Strength (+1 attack, from %s).' % player.fighter.power,
               'Defense (+1 defense, from %s).' % player.fighter.defense]

    menu(con, header, options, menu_width, screen_width, screen_height)


def map_screen(con, entities, game_map, header, map_width, map_height, screen_width, screen_height, panel_height):
    # TODO: Save processing time by keeping base map as image file and modify add entities before blitting?
    dungeon_map = TcodImage(width=game_map.width, height=game_map.height)
    color = [0, 0, 100]
    for x in range(game_map.width):
        for y in range(game_map.height):
            if game_map.walkable[y][x]:
                color = [50, 50, 150]
            elif not game_map.walkable[y][x]:
                color = [0, 0, 100]
            else:
                print('no color :(')

            dungeon_map.put_pixel(x, y, color)

    for entity in entities:
        if entity.stairs:
            dungeon_map.put_pixel(entity.x, entity.y, entity.color)
            continue
        if entity.fighter and not entity.ai:
            dungeon_map.put_pixel(entity.x, entity.y, entity.color)
        elif entity.ai:
            dungeon_map.put_pixel(entity.x, entity.y, entity.color)

    picture(con, game_map, dungeon_map, header, map_width, map_height, screen_width, screen_height, panel_height)


def debug_menu(con, header, menu_width, screen_width, screen_height):
    options = ['Toggle God Mode',
               'Toggle Reveal Map',
               'Level Up',
               'Go to Next Level',
               'Revive Player',
               'Show Spawn Table']
    menu(con, header, options, menu_width, screen_width, screen_height)


def character_screen(player, character_screen_width, character_screen_height, screen_width, screen_height):
    window = libtcod.console_new(character_screen_width, character_screen_height)

    libtcod.console_set_default_foreground(window, libtcod.white)

    libtcod.console_print_rect_ex(window, 0, 1, character_screen_width, character_screen_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Character Information')

    libtcod.console_print_rect_ex(window, 0, 1, character_screen_width, character_screen_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Character Information')

    libtcod.console_print_rect_ex(window, 0, 2, character_screen_width, character_screen_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Level: {0}'.format(player.level.current_level))

    libtcod.console_print_rect_ex(window, 0, 3, character_screen_width, character_screen_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Experience: {0}'.format(player.level.current_xp))

    libtcod.console_print_rect_ex(window, 0, 4, character_screen_width, character_screen_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Experience to Level: {0}'.format(player.level.experience_to_next_level))

    libtcod.console_print_rect_ex(window, 0, 6, character_screen_width, character_screen_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Maximum HP: {0}'.format(player.fighter.max_hp))

    libtcod.console_print_rect_ex(window, 0, 7, character_screen_width, character_screen_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Attack: {0}'.format(player.fighter.power))

    libtcod.console_print_rect_ex(window, 0, 8, character_screen_width, character_screen_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Defense: {0}'.format(player.fighter.defense))

    x = screen_width // 2 - character_screen_width // 2
    y = screen_height // 2 - character_screen_height // 2
    libtcod.console_blit(window, 0, 0, character_screen_width, character_screen_height, 0, x, y, 1.0, 0.7)


def message_box(con, header, width, screen_width, screen_height):
    # Return a 'simple' Message Box
    menu(con, header, [], width, screen_width, screen_height)
