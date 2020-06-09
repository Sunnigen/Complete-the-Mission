# https://github.com/marukrap/RoguelikeDevResources
# http://bfnightly.bracketproductions.com/rustbook/chapter_16.html
from functools import partial

import numpy as np
import tcod
import tcod.tileset

from GameMessages import Message
from DeathFunctions import kill_player, kill_monster
from Entity import get_blocking_entities_at_location, get_blocking_object_at_location
from FOVFunctions import definite_enemy_fov, initialize_fov, recompute_fov
from GameStates import GameStates
from InputHandlers import handle_debug_menu, handle_no_action, handle_player_turn_keys, \
    handle_player_dead_keys, handle_targeting_keys, handle_inventory_keys, handle_level_up_menu, \
    handle_character_screen, no_key_action
from loader_functions.InitializeNewGame import get_constants, get_game_variables
from loader_functions.DataLoaders import load_game, save_game
from Menus import character_screen, debug_menu, inventory_menu, level_up_menu, map_screen, menu, message_box, \
    select_level
from RenderFunctions import draw_entity, get_info_under_mouse, obtain_viewport_dimensions, render_bar, render_viewport

TITLE = 'Complete the Mission'
AUTHOR = 'Sunnigen'
CONSTANTS = get_constants()
tcod.console_set_custom_font('assets/dejavu_wide16x16_gs_tc.png', tcod.FONT_TYPE_GREYSCALE | tcod.FONT_LAYOUT_TCOD)
ROOT_CONSOLE = tcod.console_init_root(w=CONSTANTS['screen_width'], h=CONSTANTS['screen_height'],
                                      title=CONSTANTS['window_title'], fullscreen=False,
                                      renderer=tcod.RENDERER_OPENGL2, vsync=True)
current_screen = None
NUM_KEYS = [tcod.event.K_1, tcod.event.K_2, tcod.event.K_3, tcod.event.K_4, tcod.event.K_5, tcod.event.K_6,
            tcod.event.K_7, tcod.event.K_8, tcod.event.K_9]


class Controller(tcod.event.EventDispatch):
    """
    State based Meta-class that converts user inputs(events) into commands.
    """
    def __init__(self, name, **kwargs):
        self.name = name
        super(Controller, self).__init__(**kwargs)

    def on_enter(self):
        pass

    def on_draw(self):
        pass

    def ev_keydown(self, event: tcod.event.KeyDown):
        pass

    def ev_quit(self, event: tcod.event.Quit) -> None:
        print('Terminating program.')
        self.exit_program()

    def exit_program(self):
        raise SystemExit()


class Title(Controller):
    """
    Title Screen
    """
    cursor_position = 0
    menu_options = ['New Game', 'Continue', 'Quit']

    def __init__(self, **kwargs):
        super(Title, self).__init__(**kwargs)
        self.background_image = tcod.image_load('assets/menu_background.png')

        # Check if Existing Game Exists
        try:
            a,b,c,d,e = load_game()
        except FileNotFoundError:
            print('TODO: Blank out "Continue"')

    def on_enter(self):
        self.cursor_position = 0

    def move_cursor(self, inc):
        self.cursor_position = (self.cursor_position + inc) % len(self.menu_options)

    def ev_keydown(self, event: tcod.event.KeyDown):
        actions = {
            tcod.event.K_DOWN: partial(self.move_cursor, 1),
            tcod.event.K_UP: partial(self.move_cursor, -1),
            tcod.event.K_KP_ENTER: partial(change_screen, self.menu_options[self.cursor_position]),
            tcod.event.K_RETURN: partial(change_screen, self.menu_options[self.cursor_position]),
            tcod.event.K_ESCAPE: partial(self.ev_quit, event)
        }

        for i, option in enumerate(self.menu_options):
            actions[i + 97] = partial(change_screen, self.menu_options[i])

        # elif event.sym in NUM_KEYS:
        #     try:
        #         change_screen(self.menu_options[NUM_KEYS.index(event.sym)])
        #     except IndexError:
        #         print('Menu does not go up to %s' % NUM_KEYS.index(event.sym))
        actions.get(event.sym, no_key_action)()

    def ev_mousemotion(self, event: tcod.event.MouseMotion):
        # print(self.name, event.type)
        pass

    def on_draw(self):
        global ROOT_CONSOLE
        # Display the Main Menu
        screen_width, screen_height = CONSTANTS['screen_width'], CONSTANTS['screen_height']
        self.background_image.blit(ROOT_CONSOLE, 0, 0, 0, scale_x=1, scale_y=1, angle=0)

        text_color = tcod.yellow
        ROOT_CONSOLE.print(int(screen_width / 2), int(screen_height / 2) - 4, TITLE,
                           fg=text_color,
                           bg_blend=tcod.BKGND_DEFAULT,
                           alignment=tcod.CENTER)
        ROOT_CONSOLE.print(int(screen_width / 2), int(screen_height - 2), 'By: %s' % AUTHOR,
                           fg=text_color,
                           bg_blend=tcod.BKGND_DEFAULT,
                           alignment=tcod.CENTER)

        menu(ROOT_CONSOLE, '', self.menu_options, 24, screen_width, screen_height, self.cursor_position)


class Game(Controller):
    """
    Game screen that houses GUI, level, message logs, etc.
    """
    player = None
    entities = []
    game_map = []
    message_log = None
    game_state = None
    fov_recompute = True
    fov_map = None
    enemy_fov_map = None
    reveal_all = 0
    previous_game_state = None
    targeting_item = None
    key = None
    mouse = None
    action = None
    mouse_action = None
    player_turn_results = []
    mouse_pos = None  # mouse position relative to game map
    normal_mouse_pos = None  # mouse position relative to screen

    panel = None
    top_panel = None
    event_panel = None
    side_panel = None
    popup_panel = None

    def __init__(self, **kwargs):
        super(Game, self).__init__(**kwargs)
        # Preload Existing Game
        try:
            self.player, self.entities, self.game_map, self.message_log, self.game_state = load_game()
            self.game_map.player = self.player  # connect player from screen to player from game_map
            self.game_map.transparent[self.player.y][self.player.x] = True  # unblock current position
            self.initialize_loaded_game()  # perform checks to ensure game is "truly" loaded
        except FileNotFoundError:
            pass

    def on_enter(self):
        pass

    def exit_current_game(self, parameter):
        # Save and Exit Current Game
        save_game(self.player, self.entities, self.game_map, self.message_log, self.game_state)
        change_screen(parameter)

    def ev_keydown(self, event: tcod.event.KeyDown):
        """
        Perform Key Actions as Follows:
        1. Look at the Game State
        2. Look at which input function is pair with the game state
        3. Enact functions connected to that input
        """
        action = MENU_HANDLING[self.game_state](engine=self, key=event, game_state=self.game_state, player=self.player)
        try:
            action()
        except TypeError as error:
            print('action:', action)
            print('game state:', self.game_state)
            print('previous game state', self.previous_game_state)
            print('error:', error)
            self.exit_program()

        super(Game, self).ev_keydown(event)

    def move(self, dx, dy):
        destination_x = self.player.x + dx
        destination_y = self.player.y + dy

        # Block Player from Moving Through Obstacle
        if self.game_map.is_within_map(destination_x, destination_y):

            # Check if Map is Walkable
            if not self.game_map.is_blocked(destination_x, destination_y):
                target = get_blocking_entities_at_location(self.entities, destination_x, destination_y)

                # Attack Entity or Move
                if target:

                    # Check if Entity Faction
                    if self.player.faction.check_enemy(target.faction.faction_name):
                        # Enemy
                        attack_results = self.player.fighter.attack(target)
                        self.player_turn_results.extend(attack_results)
                    elif self.player.faction.check_ally(target.faction.faction_name):
                        # Ally
                        self.player_turn_results.extend([{'message': Message('You bump into a friendly %s.' %
                                                                             target.name)}])
                    else:
                        # Neutral
                        self.player_turn_results.extend([{'message': Message('You bump into a %s.' % target.name)}])

                else:
                    self.game_map.transparent[self.player.y][self.player.x] = True  # unblock previous position
                    self.game_map.transparent[self.player.y + dy][self.player.x + dx] = False  # block new position
                    self.update_mouse_pos(dx, dy)
                    self.player.move(dx, dy)
                    self.fov_recompute = True

                self.game_state = GameStates.ENEMY_TURN

            # Check if Location has a Map Object by "Bumping" Into it
            elif self.game_map.transparent[destination_y][destination_x]:
                map_object_entity = \
                    get_blocking_object_at_location(self.game_map.map_objects, destination_x, destination_y)

                # Interaction with Map Object Entity
                if map_object_entity:
                    interact_results = self.player.fighter.interact(map_object_entity,
                                                                    target_inventory=self.player.inventory)
                    self.player_turn_results.extend(interact_results)


                self.game_state = GameStates.ENEMY_TURN

    def wait(self):
        # Player Character Does Nothing for a Turn
        self.fov_recompute = True
        self.game_state = GameStates.ENEMY_TURN

    def pickup(self):
        # Player is Attempting to Pick Up Item
        # Loop through each entity, check if same tile as player and is an item
        for entity in self.entities:
            if entity.item and entity.x == self.player.x and entity.y == self.player.y:
                pickup_results = self.player.inventory.add_item(entity)
                self.player_turn_results.extend(pickup_results)
                break
        else:
            self.message_log.add_message(Message('There is nothing here to pick up.', tcod.yellow))

    def show_character_screen(self):
        # Toggle Character Screen
        if self.game_state != GameStates.CHARACTER_SCREEN:
            self.previous_game_state = self.game_state
            self.game_state = GameStates.CHARACTER_SCREEN
        else:
            self.game_state = GameStates.PLAYER_TURN

    def show_inventory(self):
        # Open Inventory to Use Items
        if self.game_state != GameStates.SHOW_INVENTORY:
            self.previous_game_state = self.game_state
            self.game_state = GameStates.SHOW_INVENTORY
        else:
            self.game_state = GameStates.PLAYER_TURN

    def drop_inventory(self):
        # Open Inventory to Drop Items
        if self.game_state != GameStates.DROP_INVENTORY:
            self.previous_game_state = self.game_state
            self.game_state = GameStates.DROP_INVENTORY
        else:
            self.game_state = GameStates.PLAYER_TURN

    def toggle_debug_menu(self):
        # Toggle Debug Menu
        if self.game_state != GameStates.DEBUG_MENU:
            self.previous_game_state = self.game_state
            self.game_state = GameStates.DEBUG_MENU
        else:
            self.game_state = GameStates.PLAYER_TURN

    def take_stairs(self):
        # Player Found Goal and Advances to Next Level
        # if self.game_state == GameStates.PLAYER_TURN:
        for entity in self.entities:
            if entity.stairs and entity.x == self.player.x and entity.y == self.player.y:
                self.entities = self.game_map.next_floor(self.player, self.message_log, CONSTANTS)
                self.fov_map = initialize_fov(self.game_map)
                self.enemy_fov_map = np.zeros(self.fov_map.transparent.shape, dtype=bool)
                self.fov_recompute = True
                # clear_console(root)
                break
        else:
            self.message_log.add_message(Message('There are no stairs here.', tcod.yellow))

    def level_up(self, stat):
        # Player Levels Up
        if stat == 'hp':
            self.player.fighter.base_max_hp += 20
            self.player.fighter.hp += 20
        elif stat == 'str':
            self.player.fighter.base_power += 1
        elif stat == 'def':
            self.player.fighter.base_defense += 1

        self.game_state = self.previous_game_state

    def handle_item(self, inventory_index):
        # Use/Drop Item if Selected Through Inventory
        if self.previous_game_state != GameStates.PLAYER_DEAD and inventory_index < len(self.player.inventory.items):
            item = self.player.inventory.items[inventory_index]
            if self.game_state == GameStates.SHOW_INVENTORY:
                self.player_turn_results.extend(self.player.inventory.use(item, entities=self.entities, fov_map=self.fov_map))
            elif self.game_state == GameStates.DROP_INVENTORY:
                self.player_turn_results.extend(self.player.inventory.drop_item(item))

    def targetting(self, mouse_click):
        # Handle Targeting for Ranged Attacks
        if mouse_click.button == tcod.event.BUTTON_LEFT:
            target_x = self.mouse_pos[0]
            target_y = self.mouse_pos[1]
            item_use_results = self.player.inventory.use(self.targeting_item, entities=self.entities,
                                                         fov_map=self.fov_map, target_x=target_x, target_y=target_y)
            self.player_turn_results.extend(item_use_results)

        elif mouse_click.button == tcod.event.BUTTON_RIGHT:
            self.player_turn_results.append({'targeting_cancelled': True})

    def exit_state(self):
        # print('exit state! current game state is:', self.game_state)
        if self.game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY, GameStates.CHARACTER_SCREEN,
                               GameStates.DEBUG_MENU, GameStates.READ):
            self.game_state = self.previous_game_state
        elif self.game_state == GameStates.TARGETING:
            self.player_turn_results.append({'targeting_cancelled': True})
        else:
            self.exit_current_game('title')

    @staticmethod
    def toggle_full_screen():
        pass
        # print('TODO: actually toggle full screen or not ...')

    # PLAYER_TURN_RESULTS = {
    #     'message': Game.display_message,
    #     'item_added': Game.item_added,
    #     'consumed': Game.item_consumed,
    #     'reuseable': Game.item_reuseable,
    #     'item_dropped': Game.item_dropped,
    #     'equip:': Game.equip,
    #     'targeting': Game.targetting,
    #     'map': Game.map,
    #     'targeting_cancelled': Game.targeting_cancelled,
    #     'xp': Game.xp,
    #     'chest': Game.chest
    # }

    def display_message(self, game_message):
        self.message_log.add_message(game_message)

    def item_added(self, item_added):
        """

        :param item_added: Entity.Entity
        :return:
        """
        # TODO: Deal with removing items that are not entities, not ValueError handling
        try:
            self.entities.remove(item_added)  # how to deal with items from chest that are not entities
        except ValueError:
            pass  # ignore entity since it doesn't exist on map

        self.game_state = GameStates.ENEMY_TURN

    def item_consumed(self, *args):
        self.game_state = GameStates.ENEMY_TURN

    def item_reuseable(self, *args):
        self.game_state = GameStates.ENEMY_TURN

    def item_dropped(self, item):
        # Add item to Map
        self.entities.append(item)
        self.game_state = GameStates.ENEMY_TURN

    def equip_player(self, equip):
        equip_results = self.player.equipment.toggle_equip(equip)
        for equip_result in equip_results:
            equipped = equip_result.get('equipped')
            dequipped = equip_result.get('dequipped')

            if equipped:
                self.display_message(Message('You equipped the %s.' % equipped.name))

            if dequipped:
                self.display_message(Message('You removed the %s.' % dequipped.name))

        self.game_state = GameStates.ENEMY_TURN

    def activate_targeting_mode(self, targeting):
        # Activate Targeting Game State to User to Mouse Select
        self.previous_game_state = GameStates.PLAYER_TURN
        self.game_state = GameStates.TARGETING
        self.targeting_item = targeting
        self.display_message(self.targeting_item.item.targeting_message)

    def deactivate_targeting_mode(self, *args):
        self.game_state = self.previous_game_state
        self.display_message(Message('Targeting cancelled.'))

    def activate_map(self, *args):
        # Allow Document to Read On Screen
        # TODO: Make modular to allow any other type of "reading" item
        self.previous_game_state = GameStates.PLAYER_TURN
        self.game_state = GameStates.READ

    def obtain_xp(self, xp):
        leveled_up = self.player.level.add_xp(xp)
        self.display_message(Message('You gained %s experience points.' % xp))

        if leveled_up:
            self.display_message(Message('Your battle skills grow stronger! You reached level %s!' %
                                         self.player.level.current_level, tcod.yellow))
            self.previous_game_state = self.game_state
            self.game_state = GameStates.LEVEL_UP

    def dead_entity(self, dead_entity):
        if dead_entity == self.player:
            message, self.game_state = kill_player(dead_entity)
        else:
            message = kill_monster(dead_entity)
        self.display_message(message)
            # self.message_log.add_message(message)

    def chest_interact(self, chest):
        if chest:
            if chest.inventory.empty:
                # Change from Close Chest to Open Chest
                self.game_map.tileset_tiles[chest.y][chest.x] = 9
                chest.change_map_object(self.game_map.tile_set.get("9"), 9)
        self.game_state = GameStates.ENEMY_TURN

    def toggle_god_mode(self):
        # Toggle God Mode
        if self.player.fighter.god_mode == 0:
            self.player.fighter.god_mode = 1
            self.message_log.add_message(Message('Toggle God Mode: ON.', tcod.white))
        else:
            self.player.fighter.god_mode = 0
            self.message_log.add_message(Message('Toggle God Mode: OFF.', tcod.white))

        # Revive Player if Dead
        if self.previous_game_state == GameStates.PLAYER_DEAD:
            self.game_state = self.previous_game_state
            self.revive_player()
        else:
            self.game_state = GameStates.PLAYER_TURN

    def toggle_reveal_map(self):
        # Debug Toggle Reveal All
        if self.reveal_all == 0:
            self.reveal_all = 1
            self.message_log.add_message(Message('Toggle Map Reveal: ON.', tcod.white))
        else:
            self.reveal_all = 0
            self.message_log.add_message(Message('Toggle Map Reveal: OFF.', tcod.white))

        self.fov_recompute = True

        if self.previous_game_state == GameStates.PLAYER_DEAD:
            self.game_state = self.previous_game_state
        else:
            self.game_state = GameStates.PLAYER_TURN

    def give_level_up(self):
        # Debug Level Up
        # player.level.current_xp += player.level.experience_needed_to_next_level
        self.message_log.add_message(
            Message('%s XP given to player.' % self.player.level.experience_needed_to_next_level, tcod.white))

        # player.level.current_xp = player.level.experience_to_next_level
        self.player_turn_results.append({'xp': self.player.level.experience_needed_to_next_level})

        if self.previous_game_state == GameStates.PLAYER_DEAD:
            self.game_state = self.previous_game_state
        else:
            self.game_state = GameStates.PLAYER_TURN

    def go_to_next_level(self):
        # Debug Go to Next Level
        self.entities = self.game_map.next_floor(self.player, self.message_log, CONSTANTS)
        self.fov_map = initialize_fov(self.game_map)
        self.fov_recompute = True
        self.game_state = GameStates.PLAYER_TURN
        # clear_console(root)
        self.revive_player()

    def change_font_size(self, font_size):
        # Debug Font
        global ROOT_CONSOLE
        ROOT_CONSOLE = change_font(ROOT_CONSOLE, font_size, CONSTANTS)
        self.message_log.add_message(Message('Font size change: %s.' % font_size, tcod.white))

    def show_spawn_table(self):
        # TODO: Show proper menu of spawn rates
        self.game_map.print_spawn_rates()
        self.game_state = GameStates.PLAYER_TURN

    def revive_player(self):
        # Debug Revive Player
        if self.player.fighter.hp == 0:
            self.message_log.add_message(Message('Player is revived!', tcod.white))
            self.player.char = '@'
            self.player.color = tcod.white
            self.player.fighter.hp = self.player.fighter.max_hp
            self.game_state = GameStates.PLAYER_TURN
        elif self.game_state == GameStates.DEBUG_MENU:
            self.game_state = GameStates.PLAYER_TURN


    def ev_mousebuttonup(self, event: tcod.event.MouseButtonUp):
        print(event.tile)
        if self.game_state == GameStates.TARGETING:
            self.targetting(event)


    def ev_mousemotion(self, event: tcod.event.MouseMotion):
        self.set_mouse_pos(event.tile.x, event.tile.y)


    def set_mouse_pos(self, x, y):
        view_x_start, view_x_end, view_y_start, view_y_end = obtain_viewport_dimensions(self.game_map,
                                                                                        CONSTANTS['viewport_width'],
                                                                                        CONSTANTS['viewport_height']
                                                                                        )
        viewport_width_start = -1
        viewport_height_start = -1

        if 0 < x < CONSTANTS['viewport_width'] * 2 - 1 and \
                0 < y < CONSTANTS['viewport_height'] * 2 - 1:
            self.mouse_pos = (view_x_start + x + viewport_width_start,
                              view_y_start + y + viewport_height_start)
            self.normal_mouse_pos = (x, y)
        else:
            self.normal_mouse_pos = None
            self.mouse_pos = None

    def update_mouse_pos(self, dx, dy):
        if self.mouse_pos:
            new_x, new_y = self.mouse_pos
            if CONSTANTS['viewport_width'] < self.player.x < CONSTANTS['map_width'] - CONSTANTS['viewport_width']:
                new_x += dx

            if CONSTANTS['viewport_height'] < self.player.y < CONSTANTS['map_height'] - CONSTANTS['viewport_height']:
                new_y += dy

            self.mouse_pos = new_x, new_y

    def initialize_game(self, level):
        # Initialize Game Variables
        self.player, self.entities, self.game_map, self.message_log, self.game_state = get_game_variables(CONSTANTS,
                                                                                                          level=level)
        self.panel = tcod.console.Console(CONSTANTS['screen_width'], CONSTANTS['panel_height'])
        self.top_panel = tcod.console.Console(CONSTANTS['screen_width'], CONSTANTS['top_gui_height'])
        self.event_panel = tcod.console.Console(CONSTANTS['viewport_width'] * 2, CONSTANTS['viewport_height'] * 2)
        self.side_panel = tcod.console.Console(CONSTANTS['side_panel_width'], CONSTANTS['side_panel_height'] * 2)

        self.fov_recompute = True
        self.fov_map = initialize_fov(self.game_map)
        self.enemy_fov_map = np.zeros(self.fov_map.transparent.shape, dtype=bool)
        self.reveal_all = 0
        self.previous_game_state = self.game_state
        self.targeting_item = None

    def initialize_loaded_game(self):
        self.panel = tcod.console.Console(CONSTANTS['screen_width'], CONSTANTS['panel_height'])
        self.top_panel = tcod.console.Console(CONSTANTS['screen_width'], CONSTANTS['top_gui_height'])
        self.fov_map = initialize_fov(self.game_map)
        self.enemy_fov_map = np.zeros(self.fov_map.transparent.shape, dtype=bool)

    def on_draw(self):
        global ROOT_CONSOLE, PLAYER_TURN_RESULTS
        # """
        #  !"#$&'()*+,-./0123456789:;<=>?
        #  @[\]^_'{|}~░▒▓│—┼┤┴├┬└╥┘▀▄
        # """
        #
        # j = 1
        # x = 0
        # har = 48
        # for i in range(250):
        #     if x >= 50:
        #         j += 2
        #         x -= 50
        #
        #     tcod.console_put_char(root, x, j, i, tcod.BKGND_NONE)
        #     tcod.console_put_char(root, x, j + 1, har, tcod.BKGND_NONE)
        #     x += 1
        #     har += 1
        #     if har > 57:
        #         har = 48ds
        #
        # # Debugging Only!
        #
        # for x, c in enumerate([]):
        #     tcod.console_put_char(root, x, 1, c, tcod.BKGND_NONE)
        #
        # """
        #              ○  ◙  ►  ◄   ↕   ↑    ↓   →   ←  ↔   ▲  ▼   !   "   #   $   y   &   '   (   )   *   +   ,   -   .
        # """
        # char_list = [9, 10, 16, 17, 18, 24, 25, 26, 27, 29, 30, 31, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46]
        # """
        #              /   0   1   2   3   4   5   6   7   8   9   :   ;   <   -   >   ?   @
        # """
        # char_list = [47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64]
        #
        # """
        #              A   B   C   D   E   F   G   H   J   K   L   M
        # """
        # char_list = [65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76]
        # """
        #              d    e    f    g    h    i    j    k    l    m    n    o    p    q    r    s    t
        # """
        # char_list = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116]
        #
        # """
        #                   ░    ▒    ▓    │    ┤    ╣    ║    ╗    ╝    ╜    ≈    └    ╔    ┬    ╣    ─    ┼
        # """
        # char_list.extend([176, 177, 178, 179, 180, 185, 186, 187, 188, 189, 191, 192, 193, 194, 195, 196, 197])
        #
        # """
        #                   ╚    ╤    ╩    ╦    ╠    ═    ╬    ┘    ┌    open clo
        #                                                                box  box
        # """
        # char_list.extend([200, 201, 202, 203, 204, 205, 206, 217, 218, 224, 225, 226, 227, 228, 229, 230, 231, 232])
        #
        # for x, c in enumerate(char_list):
        #     tcod.console_put_char(root, x, 13, c, tcod.BKGND_NONE)
        #
        # """
        # let mut mask : u8 = 0;
        #
        # if is_revealed_and_wall(map, x, y - 1) { mask +=1; }
        # if is_revealed_and_wall(map, x, y + 1) { mask +=2; }
        # if is_revealed_and_wall(map, x - 1, y) { mask +=4; }
        # if is_revealed_and_wall(map, x + 1, y) { mask +=8; }
        #
        # walls:
        #  0 => { 9 } // Pillar because we can't see neighbors        ○
        #     1 => { 186 } // Wall only to the north                   ║
        #     2 => { 186 } // Wall only to the south                  ║
        #     3 => { 186 } // Wall to the north and south              ║
        #     4 => { 205 } // Wall only to the west                   ═
        #     5 => { 188 } // Wall to the north and west               ╝
        #     6 => { 187 } // Wall to the south and west              ╗
        #     7 => { 185 } // Wall to the north, south and west        ╣
        #     8 => { 205 } // Wall only to the east                   ═
        #     9 => { 200 } // Wall to the north and east               ╚
        #     10 => { 201 } // Wall to the south and east             ╤
        #     11 => { 204 } // Wall to the north, south and east       ╠
        #     12 => { 205 } // Wall to the east and west              ═
        #     13 => { 202 } // Wall to the east, west, and south       ╩
        #     14 => { 203 } // Wall to the east, west, and north      ╦
        # """
        # return
        # FOV Update

        # Log Events that Occured During Player Turn
        # Analyze Actions User Results and Propagate Resulting Events
        for player_turn_result_dict in self.player_turn_results:
            for result_key, result_val in player_turn_result_dict.items():
                result_event = PLAYER_TURN_RESULTS.get(result_key, no_key_action)
                result_event(self, result_val)  # pass dict.values()

        self.player_turn_results = []

        # Enemy Turn to Act
        if self.game_state == GameStates.ENEMY_TURN:
            self.fov_recompute = True
            for entity in self.entities:
                if entity.ai:

                    # Pick Closest Enemy Entity and Attack
                    # Note: This doesn't take into account, if obstacles block FOV to see entity as all entities are
                    #       sharing the same FOV map.

                    # Check if Current Target is Dead
                    if entity.ai.current_target:
                        if not entity.ai.current_target.fighter:
                            entity.ai.current_target = None

                    if not entity.ai.current_target:
                        close_entities = {}
                        for other_entity in self.entities:
                            if other_entity.ai or other_entity is self.player:  # Check if AI

                                distance = entity.distance_to(other_entity.x, other_entity.y)
                                if distance < entity.fighter.fov:  # Check within FOV distance
                                    if entity.faction.check_enemy(other_entity.faction.faction_name):

                                        close_entities[distance] = other_entity

                        if close_entities:
                            entity.ai.current_target = close_entities[min(close_entities.keys())]
                        else:
                            entity.ai.path = []
                            entity.ai.current_target = None

                    enemy_turn_results = entity.ai.take_turn(self.enemy_fov_map, self.game_map, self.entities)

                    for enemy_turn_result in enemy_turn_results:
                        message = enemy_turn_result.get('message')
                        dead_entity = enemy_turn_result.get('dead')

                        if message:
                            self.message_log.add_message(message)

                        # Check if Target Dead or Monster Dead
                        if dead_entity:
                            if dead_entity == self.player:
                                message, self.game_state = kill_player(dead_entity)
                            else:
                                print('%s has perished!' % dead_entity.name)
                                message = kill_monster(dead_entity)
                                self.game_map.walkable[dead_entity.y][dead_entity.x] = True
                                self.game_map.transparent[dead_entity.y][dead_entity.x] = True

                            self.message_log.add_message(message)

                    # Check if Player is Dead as a Result
                    if self.game_state == GameStates.PLAYER_DEAD:
                        break
            else:
                self.game_state = GameStates.PLAYER_TURN

        # TODO: Does the game need to be saved every turn?
        # save_game(player, entities, game_map, message_log, game_state)    

        if self.fov_recompute:
            # Update FOV for Player
            recompute_fov(self.fov_map, self.player.x, self.player.y, self.player.fighter.fov, self.game_map.entrances,
                          CONSTANTS['fov_light_walls'], CONSTANTS['fov_algorithm'])
            
            # Update and Combine FOV for Entities
            self.enemy_fov_map = definite_enemy_fov(self.game_map, self.fov_map, self.game_map.entrances, self.entities,
                                               CONSTANTS['fov_light_walls'],
                                               CONSTANTS['fov_algorithm'])

        # Actual Drawing
        clear_console(self.event_panel)
        view_x_start, view_x_end, view_y_start, view_y_end = obtain_viewport_dimensions(self.game_map,
                                                                                        CONSTANTS['viewport_width'],
                                                                                        CONSTANTS['viewport_height']
                                                                                        )
        # Make Viewport Smaller than Frame
        viewport_width_start = -1
        viewport_height_start = -1
        view_x_end -= 2
        view_y_end -= 2
        # viewport_width_start = (((screen_width // 2) - viewport_width) * -1)
        # viewport_height_start = (((screen_height // 2) - (viewport_height // 2)) // -2) + 5

        # Background, Tiles, Etc.
        render_viewport(self.event_panel, self.mouse_pos, self.game_map, self.entities, self.fov_map, self.enemy_fov_map,
                        self.fov_recompute, self.reveal_all, view_x_start, view_x_end, view_y_start, view_y_end,
                        viewport_width_start, viewport_height_start)

        # Sort Draw Order to Sort by Render Order Enum Value
        entities_under_mouse = []
        entities_in_render_order = sorted(
            [entity for entity in self.entities if view_x_start <= entity.x < view_x_end and view_y_start <= entity.y < view_y_end],
            key=lambda x: x.render_order.value
        )
        # Draw all entities in the list
        for entity in entities_in_render_order:
            # if :

            # Find Entity Under Mouse since we're looping :D
            if self.mouse_pos:
                # if entity.x == view_x_start + self.mouse_pos[0] + viewport_width_start and \
                #         entity.y == view_y_start + self.mouse_pos[1] + viewport_height_start and \
                #         self.fov_map.fov[view_y_start + self.mouse_pos[1] + viewport_height_start][view_x_start + self.mouse_pos[0] + viewport_width_start]:
                if entity.x == self.mouse_pos[0] and entity.y == self.mouse_pos[1] and \
                        self.fov_map.fov[self.mouse_pos[1]][self.mouse_pos[0]]:
                    entities_under_mouse.append(entity)

            draw_entity(self.event_panel, entity, self.fov_map, self.game_map, self.reveal_all, view_x_start, view_x_end,
                        view_y_start, view_y_end, viewport_width_start, viewport_height_start)

        # Create Frame around near pos
        info = ''
        line_count = 0
        for entity in entities_under_mouse:
            if entity.fighter:
                info += '\n\n%s\n\nLv: %s\nHP: %s\nStr: %s\nDef: %s' % (entity.name, entity.fighter.mob_level, entity.fighter.hp, entity.fighter.power, entity.fighter.defense)
                line_count += 8

            elif entity.equippable:
                info += '\n\n%s\n\n%s\n\n+HP: %s\n+STR: %s\nDEF: %s' % (entity.name, entity.equippable.description,
                                                entity.equippable.max_hp_bonus,
                                                entity.equippable.power_bonus,
                                                entity.equippable.defense_bonus)
                line_count += 18
            elif entity.item:
                info += '\n\n%s\n\n%s' % (entity.name, entity.item.description)
                line_count += 18

        if entities_under_mouse:
            info_pane_width = 16

            # Check left or right
            frame_x = self.normal_mouse_pos[0] + 1  # display right
            if self.normal_mouse_pos[0] >= CONSTANTS.get('viewport_width'):
                frame_x = self.normal_mouse_pos[0] - info_pane_width  # display left

            # Check top or bottom
            frame_y = self.normal_mouse_pos[1]
            if self.normal_mouse_pos[1] > CONSTANTS.get('viewport_height'):
                frame_y = self.normal_mouse_pos[1] + 1 - line_count
            popup_panel = tcod.console.Console(info_pane_width, line_count+1)

            popup_panel.draw_frame(x=0, y=0, width=info_pane_width, height=line_count+1, title='', fg=tcod.light_gray,
                                   bg=tcod.black, clear=True, bg_blend=tcod.BKGND_SCREEN)

            popup_panel.print_box(x=1, y=1, width=info_pane_width - 2,
                                       height=line_count+1, string=info[2:])

            popup_panel.blit(dest=self.event_panel, dest_x=frame_x, dest_y=frame_y, src_x=0, src_y=0,
                                  width=info_pane_width, height=line_count+1)

        # # Mouse Over Display
        # mouse_info = get_info_under_mouse(self.mouse_pos, self.game_map, self.entities, self.game_map.map_objects,
        #                                   self.fov_map, self.reveal_all, view_x_start, view_x_end, view_y_start,
        #                                   view_y_end, CONSTANTS['viewport_width'], CONSTANTS['viewport_height'],
        #                                   viewport_width_start, viewport_height_start)
        #
        # self.side_panel.print(1, 1, mouse_info, fg=tcod.light_gray, bg_blend=tcod.BKGND_NONE, alignment=tcod.LEFT)


        # Frame
        self.event_panel.draw_frame(0, 0, self.event_panel.width, self.event_panel.height,
                                    title='%s Level: %s' % (self.game_map.level, self.game_map.dungeon_level),
                                    fg=tcod.white, bg=tcod.black, clear=False, bg_blend=tcod.BKGND_DEFAULT)

        # Actual Game Screen
        self.event_panel.blit(dest=ROOT_CONSOLE, dest_x=0, dest_y=0, src_x=0, src_y=0,
                              width=self.event_panel.width, height=self.event_panel.height)
        # Draw Console to Screen


        # tcod.console_blit(con, viewport_width_start, viewport_height_start, screen_width, screen_height, 0, 0, 0)
        # print('\nCentering Viewport')
        # print(screen_width // 2, viewport_width // 2, viewport_width_start)
        # print(screen_height // 2, viewport_height // 2, viewport_height_start)

        # Player UI Panel
        # clear_console(self.panel)
        self.panel.clear()
        self.panel.draw_frame(0, 0, CONSTANTS['screen_width'], CONSTANTS['panel_height'],
                              clear=False, bg_blend=tcod.BKGND_NONE)

        # Print the game Messages, one line at a time
        y = 1
        for message in self.message_log.messages:
            self.panel.print(self.message_log.x, y, message.text, fg=message.color)
            y += 1

        self.panel.blit(dest=ROOT_CONSOLE, dest_x=0, dest_y=CONSTANTS['panel_y'], src_x=0, src_y=0,
                        width=CONSTANTS['screen_width'], height=CONSTANTS['panel_height'],)

        # Side Panel for Enemy Display Status Effects etc.
        self.side_panel.clear()
        self.side_panel.draw_frame(0, 0, CONSTANTS['side_panel_width'], CONSTANTS['side_panel_height'], clear=False,
                                   bg_blend=tcod.BKGND_DEFAULT)

        # Display Character Level
        self.side_panel.print(CONSTANTS['bar_width'] // 2 + 1, 1, 'Fighter Lv: %s ' % self.player.level.current_level,
                              fg=tcod.light_gray, bg_blend=tcod.BKGND_NONE, alignment=tcod.CENTER)
        # Render HP Bar
        render_bar(self.side_panel, 1, 2, CONSTANTS['bar_width'], 'HP', self.player.fighter.hp,
                   self.player.fighter.max_hp, tcod.light_red, tcod.darker_red)

        # Render XP Bar
        render_bar(self.side_panel, 1, 3, CONSTANTS['bar_width'], 'XP', self.player.level.current_xp,
                   self.player.level.experience_to_next_level, tcod.darker_yellow, tcod.darkest_yellow)

        # Display ATT/DEF
        self.side_panel.print(1, 5, 'STR: %s\nDEF: %s' % (self.player.fighter.power, self.player.fighter.defense),
                              fg=tcod.light_gray, bg_blend=tcod.BKGND_NONE, alignment=tcod.LEFT)

        # Terrain Under Mouse Display
        if self.mouse_pos:
            mouse_x, mouse_y = self.mouse_pos
            tile = self.game_map.tileset_tiles[mouse_y][mouse_x]
            _tile = self.game_map.tile_set.get("%s" % tile)
            name = "%s\nCost: %s\n(%s, %s)" % (_tile.get("name"), self.game_map.tile_cost[mouse_y][mouse_x],
                                                   mouse_x, mouse_y)
            # else:
            #     name = "(%s, %s)" % (mouse_x, mouse_y)
            self.side_panel.print(1, CONSTANTS['side_panel_height'] - 4, string=name, fg=tcod.light_gray,
                                  bg_blend=tcod.BKGND_NONE, alignment=tcod.LEFT)

        self.side_panel.blit(dest=ROOT_CONSOLE, dest_x=CONSTANTS['viewport_width'] * 2, dest_y=0, src_x=0, src_y=0,
                             width=CONSTANTS['side_panel_width'], height=CONSTANTS['side_panel_height'], )




       # Entity Display
        # # tcod.console_clear(top_panel)
        # top_panel.clear()
        # tcod.console_set_default_foreground(top_panel, tcod.light_gray)
        # test = ''
        #
        # for i in range(1, 1000):
        #     test += "%c%c%c%c " % (tcod.COLCTRL_FORE_RGB, random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) + \
        #        random.choice(string.ascii_letters) + "%c" % tcod.COLCTRL_STOP
        #     if i % screen_width == 0:
        #         test += " \n"
        # # x: int, y: int, string: str, fg: Optional[Tuple[int, int, int]] = None, bg: Optional[
        #     # Tuple[int, int, int]] = None, bg_blend: int = 1, alignment: int =
        # top_panel.print(x=0, y=0, string=test, fg=tcod.light_gray)
        #
        # tcod.console_blit(top_panel, 0, 0, screen_width, top_gui_height, 0, 0, top_gui_y)

        IN_GAME_MENU = {GameStates.SHOW_INVENTORY:
                            partial(inventory_menu, ROOT_CONSOLE,
                                    'Press the key next to an item to use it, or Esc to cancel.\n',
                                    self.player, 50, CONSTANTS['screen_width'], CONSTANTS['screen_height']),
                        GameStates.DROP_INVENTORY:
                            partial(inventory_menu, ROOT_CONSOLE,
                                    'Press the key next to an item to drop it, or Esc to cancel.\n',
                                    self.player, 50, CONSTANTS['screen_width'], CONSTANTS['screen_height']),
                        GameStates.DEBUG_MENU:
                            partial(debug_menu, ROOT_CONSOLE, 'Debug Menu\n', 30, CONSTANTS['screen_width'],
                                    CONSTANTS['screen_height']),
                        GameStates.LEVEL_UP:
                            partial(level_up_menu, ROOT_CONSOLE, 'Level up! Choose a stat to raise:', self.player, 30,
                                    CONSTANTS['screen_width'], CONSTANTS['screen_height']),
                        GameStates.CHARACTER_SCREEN:
                            partial(character_screen, self.player, 30, 10, CONSTANTS['screen_width'],
                                    CONSTANTS['screen_height']),
                        GameStates.READ:
                            partial(map_screen, ROOT_CONSOLE, self.entities, self.game_map, "Dungeon Map",
                                    int(self.game_map.width * 0.75), int(self.game_map.height * 0.75),
                                    CONSTANTS['screen_width'], CONSTANTS['screen_height'], CONSTANTS['panel_height'])
        }

        IN_GAME_MENU.get(self.game_state, no_key_action)()
        self.fov_recompute = False


class GameMode(Controller):
    """
    Menu to select:
    - New Game
        - Complete the Mission
        - Go to Overworld
        - Go to Undergrave Prison
        - Go to Resinfaire Forest
        - Go to Generic Dungeon
    - Load Existing Game

    Include making new character/selecting game parameters/etc.
    """
    cursor_position = 0
    game_modes = ['New Game', 'Load Game']
    current_mode = game_modes[cursor_position]
    menu_names = ['Complete the Mission', 'Go to Overworld', 'Go to Undergrave Prison', 'Go to Resinfaire Forest',
                  'Go to Generic Dungeon']
    menu_options = ['ctm', 'overworld', 'undergrave', 'resinfaire', 'generic']
    # initialize_game

    def on_enter(self):
        self.cursor_position = 0

    def move_cursor(self, inc):
        self.cursor_position = (self.cursor_position + inc) % len(self.menu_options)

    def ev_keydown(self, event: tcod.event.KeyDown):
        actions = {
            tcod.event.K_DOWN: partial(self.move_cursor, 1),
            tcod.event.K_UP: partial(self.move_cursor, -1),
            tcod.event.K_KP_ENTER: partial(change_screen, self.menu_options[self.cursor_position]),
            tcod.event.K_RETURN: partial(change_screen, self.menu_options[self.cursor_position]),
            tcod.event.K_ESCAPE: partial(change_screen, 'title')
        }

        for i, option in enumerate(self.menu_options):
            actions[i + 97] = partial(change_screen, self.menu_options[i])

        actions.get(event.sym, no_key_action)()

    def ev_mousemotion(self, event: tcod.event.MouseMotion):
        # print(self.name, event.type)
        pass

    def on_draw(self):
        global ROOT_CONSOLE
        screen_width, screen_height = CONSTANTS['screen_width'], CONSTANTS['screen_height']
        menu(ROOT_CONSOLE, 'Select Level', self.menu_names, 40, screen_width, screen_height, self.cursor_position)


SCREENS = {
    'title': Title(name='title_screen'),
    'gamemode': GameMode(name='game_mode_screen'),
    'game': Game(name='game_screen')
}


def change_screen(parameter):
    global current_screen
    print('change_screen', parameter)
    if parameter == 'New Game':
        current_screen = SCREENS.get('gamemode')
        current_screen.on_enter()
    elif parameter == 'Continue':
        current_screen = SCREENS.get('game')
    elif parameter == 'Quit':
        current_screen.exit_program()
    elif parameter == 'title':
        current_screen = SCREENS.get(parameter)
        current_screen.on_enter()
    elif parameter == 'ctm':
        print('NOT READY YET!!!')
    elif parameter == 'generic':
        SCREENS.get('game').initialize_game(parameter)
        current_screen = SCREENS.get('game')
    elif parameter == 'overworld':
        SCREENS.get('game').initialize_game(parameter)
        current_screen = SCREENS.get('game')
    elif parameter == 'undergrave':
        SCREENS.get('game').initialize_game(parameter)
        current_screen = SCREENS.get('game')
    elif parameter == 'resinfaire':
        SCREENS.get('game').initialize_game(parameter)
        current_screen = SCREENS.get('game')
    else:
        print('doing nothing :|')


# ===============================================================
#                         MAIN LOOP
# ===============================================================
MENU_HANDLING = {
    GameStates.DEBUG_MENU: handle_debug_menu,
    GameStates.PLAYER_TURN: handle_player_turn_keys,
    GameStates.PLAYER_DEAD: handle_player_dead_keys,
    GameStates.TARGETING: handle_targeting_keys,
    GameStates.SHOW_INVENTORY: handle_inventory_keys,
    GameStates.DROP_INVENTORY: handle_inventory_keys,
    GameStates.LEVEL_UP: handle_level_up_menu,
    GameStates.CHARACTER_SCREEN: handle_character_screen,
    GameStates.READ: handle_character_screen,
    GameStates.ENEMY_TURN: handle_no_action
}


PLAYER_TURN_RESULTS = {
    'message': Game.display_message,
    'item_added': Game.item_added,
    'consumed': Game.item_consumed,
    'reuseable': Game.item_reuseable,
    'item_dropped': Game.item_dropped,
    'equip:': Game.equip_player,
    'targeting': Game.activate_targeting_mode,
    'map': Game.activate_map,
    'targeting_cancelled': Game.deactivate_targeting_mode,
    'xp': Game.obtain_xp,
    'chest': Game.chest_interact,
    'dead': Game.dead_entity
}


def main():
    global current_screen
    # Initialize Consoles
    # font = 'assets/arial10x10.png'
    # font = 'assets/prestige8x8_gs_tc.png'
    # font = 'assets/lucida12x12_gs_tc.png'
    font = 'assets/dejavu_wide16x16_gs_tc.png'
    tcod.console_set_custom_font(font, tcod.FONT_TYPE_GREYSCALE | tcod.FONT_LAYOUT_TCOD)
    current_screen = SCREENS['title']

    # Game Loop
    while True:
        # User Events
        handle_events()

        # Rendering
        clear_console(ROOT_CONSOLE)
        current_screen.on_draw()
        tcod.console_flush(ROOT_CONSOLE)


def handle_events():
    global current_screen
    for event in tcod.event.get():
        current_screen.dispatch(event)


def clear_console(con):
    con.clear(fg=(0, 0, 0), bg=(0, 0, 0))


def change_font(con, font, constants):
    # clear_console(con)
    font_sizes = {
        8: partial(tcod.console_set_custom_font, 'assets/prestige8x8_gs_tc.png',
                   tcod.FONT_TYPE_GREYSCALE | tcod.FONT_LAYOUT_TCOD),
        10: partial(tcod.console_set_custom_font, 'assets/arial10x10.png',
                    tcod.FONT_TYPE_GREYSCALE | tcod.FONT_LAYOUT_TCOD),
        16: partial(tcod.console_set_custom_font, 'assets/dejavu_wide16x16_gs_tc.png',
                    tcod.FONT_TYPE_GREYSCALE | tcod.FONT_LAYOUT_TCOD)
    }
    font_sizes.get(font, no_key_action)()
    return tcod.console_init_root(w=constants['screen_width'], h=constants['screen_height'],
                                  title=constants['window_title'], fullscreen=False, renderer=tcod.RENDERER_OPENGL2,
                                  vsync=True)


if __name__ == '__main__':
    main()
