# https://github.com/marukrap/RoguelikeDevResources
# http://bfnightly.bracketproductions.com/rustbook/chapter_16.html
from collections import deque
from copy import copy
import collections
from functools import partial
from math import ceil
import os
from random import choice, randint
import string
import textwrap


import numpy as np
import tcod
import tcod.tileset

from AlertMode import AlertEnum
from components.AI import FollowAI
from components.Particle import Particle, ParticleSystem
from components.Position import Position
from GameMessages import Message
from DeathFunctions import kill_player, kill_mob
from Entity import Entity
from FOVFunctions import definite_enemy_fov, initialize_fov, recompute_fov
from GameStates import GameStates
from InputHandlers import handle_debug_menu, handle_no_action, handle_player_turn_keys, \
    handle_player_dead_keys, handle_targeting_keys, handle_inventory_keys, handle_level_up_menu, \
    handle_character_screen, no_key_action, handle_dialogue, handle_event_message
from loader_functions.InitializeNewGame import get_constants, get_game_variables
from loader_functions.DataLoaders import load_game, save_game
from loader_functions.JsonReader import obtain_particles, obtain_tile_set
from map_objects.GameMapUtils import get_blocking_entities_at_location, get_map_object_at_location
from Menus import character_screen, debug_menu, inventory_menu, level_up_menu, map_screen, menu, message_box, \
    select_level
from RenderFunctions import draw_entity, draw_particle_entity, obtain_viewport_dimensions, RenderOrder, render_bar, render_viewport, render_tileset

TITLE = 'Complete the Mission'
AUTHOR = 'Sunnigen'
CONSTANTS = get_constants()
TILESET = tcod.tileset.load_tilesheet('assets/dejavu_wide16x16_gs_tc.png', 32, 8, tcod.tileset.CHARMAP_TCOD)
ROOT_CONSOLE = tcod.Console(CONSTANTS['screen_width'], CONSTANTS['screen_height'])
current_screen = None
NUM_KEYS = [tcod.event.K_1, tcod.event.K_2, tcod.event.K_3, tcod.event.K_4, tcod.event.K_5, tcod.event.K_6,
            tcod.event.K_7, tcod.event.K_8, tcod.event.K_9]


PARTICLES = obtain_particles()
TILE_SET = obtain_tile_set()


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
            a,b,c,d,e,f,g = load_game()
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
        # render_tileset(ROOT_CONSOLE)


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

    particles = []
    particle_systems = []

    # Dialogue Panel
    dialogue_panel = None
    event_message_panel = None
    current_dialogue = ''
    total_dialogue = []
    entity_dialogue = None
    dialogue_pane_width = 16
    dialogue_line_count = 0

    # Mouse Selection for Targetting
    mouse_target_type = None
    mouse_targets = []
    mouse_target_range = 0
    mouse_target_radius = 0

    # Alert Mode
    alert_mode = None
    alert_lerp_value = 0
    alert_lerp_mod = 0.01
    alert_counter = 0
    activate_alert = False


    def __init__(self, **kwargs):
        super(Game, self).__init__(**kwargs)
        # Preload Existing Game
        try:
            self.player, self.entities, self.particles, self.particle_systems, self.game_map, self.message_log, self.game_state = load_game()
            self.game_map.player = self.player  # connect player from screen to player from game_map
            self.game_map.transparent[self.player.position.y][self.player.position.x] = True  # unblock current position
            self.initialize_loaded_game()  # perform checks to ensure game is "truly" loaded
        except FileNotFoundError:
            pass

        # self.dialogue_panel =

    def reset_mouse_targets(self):
        self.mouse_target_type = None
        self.mouse_targets = [self.mouse_pos]
        self.mouse_target_range = 0
        self.mouse_target_radius = 0

    def on_enter(self):
        pass

    def exit_current_game(self, parameter):
        # Save and Exit Current Game
        save_game(self.player, self.entities, self.particles, self.particle_systems, self.game_map, self.message_log, self.game_state)
        change_screen(parameter)

    def ev_keydown(self, event: tcod.event.KeyDown):
        """
        Perform Key Actions as Follows:
        1. Look at the Game State
        2. Look at which input function is pair with the game state
        3. Enact functions connected to that input
        """
        action = MENU_HANDLING[self.game_state](engine=self, key=event, game_state=self.game_state, player=self.player)
        action()
        # try:
        #     action()
        # except TypeError as error:
        #     print('action:', action)
        #     print('game state:', self.game_state)
        #     print('previous game state', self.previous_game_state)
        #     print('error:', error)
        #     self.exit_program()

        super(Game, self).ev_keydown(event)

    def move(self, dx, dy):
        destination_x = self.player.position.x + dx
        destination_y = self.player.position.y + dy

        # Block Player from Moving Through Obstacle
        if self.game_map.is_within_map(destination_x, destination_y):

            map_object_entity = get_map_object_at_location(self.game_map.map_objects, destination_x, destination_y)

            # Check if Map is Walkable
            if not self.game_map.is_blocked(destination_x, destination_y):
                # print(self.entities, destination_x,destination_y, self.player.position.x, self.player.position.y)

                tech = "side_impact"
                # tech = choice(["side_impact", "spin_impact", "far_impact", "blast_impact","dragons_breath_impact", None])
                targets, targetted_spaces = get_blocking_entities_at_location(
                    self.entities, destination_x, destination_y, self.player.position.x, self.player.position.y,
                    technique_name=tech)

                # print("# Attack Entity or Move")
                # print("targets: ", targets)
                # Attack Entity or Move
                if targets:

                    # Check if Non Attackable Entity

                    # elif not self.player.faction.check_ally(target.faction.faction_name):


                    main_target = targets[0]
                    if not self.player.faction.check_enemy(main_target.faction.faction_name):
                        # Ally
                        # Switch Player with Entity, if Entity is Following Player
                        if isinstance(main_target.ai, FollowAI):
                            if main_target.ai.follow_entity == self.player:
                                old_x, old_y = self.player.position.x, self.player.position.y
                                new_x, new_y = main_target.position.x, main_target.position.y
                                self.player.position.x, self.player.position.y = new_x, new_y
                                main_target.position.x, main_target.position.y = old_x, old_y
                                self.game_state = GameStates.ENEMY_TURN

                        else:
                            self.dialogue(main_target)

                    # Attack Enemies
                    for target in targets:
                        # Check if Entity Faction
                        if self.player.faction.check_enemy(target.faction.faction_name):
                            # Enemy
                            attack_results = self.player.fighter.attack(target)
                            self.player_turn_results.extend(attack_results)
                            self.game_state = GameStates.ENEMY_TURN

                    # else:
                        # Neutral
                        # self.player_turn_results.extend([{'message': Message('You bump into a %s.' % target.name)}])
                        # self.game_state = GameStates.ENEMY_TURN
                    # Spawn Hit Particles for Non-Target Spaces
                    for (x, y) in targetted_spaces:
                        if not self.game_map.is_blocked(x, y) and (x, y) in self.player.fighter.curr_fov_map:
                            self.player_turn_results.append({"spawn_particle": ["hit_blank", x, y, None]})

                else:
                    # Check for Strafe Slashes
                    # print('# Check for Strafe Slashes')
                    # tech = "side_impact"
                    # side_x, side_y = None, None
                    # if dy == 0:
                    #     side_x = self.player.position.x + 1
                    #     side_y = destination_y + 1
                    # elif dx == 0:
                    #     side_x = destination_x + 1
                    #     side_y = self.player.position.y + 1
                    # print('\ndx/dy : ', dx, dy)
                    # print("side : ", side_x, side_y)

                    """
                    # Move downright
                    dx = 1
                    dy = 1
                    
                    # Move downleft
                    dx = -1
                    dy = 1
                                        
                    # Move Topleft
                    dx = -1
                    dy = -1
                    
                                                            
                    # Move Topright
                    dx = 1
                    dy = -1
                    """


                    # if side_x or side_y:
                    #     # tech = choice(["side_impact", "spin_impact", "far_impact", "blast_impact","dragons_breath_impact", None])
                    #     targets, targetted_spaces = get_blocking_entities_at_location(
                    #         self.entities, destination_x, destination_y, side_x, side_y, technique_name=tech)
                    #
                    #     if targets:
                    #
                    #         # Check if Non Attackable Entity
                    #
                    #         # elif not self.player.faction.check_ally(target.faction.faction_name):
                    #
                    #         main_target = targets[0]
                    #         if not self.player.faction.check_enemy(main_target.faction.faction_name):
                    #             # Ally
                    #             # Switch Player with Entity, if Entity is Following Player
                    #             if isinstance(main_target.ai, FollowAI):
                    #                 if main_target.ai.follow_entity == self.player:
                    #                     old_x, old_y = self.player.position.x, self.player.position.y
                    #                     new_x, new_y = main_target.position.x, main_target.position.y
                    #                     self.player.position.x, self.player.position.y = new_x, new_y
                    #                     main_target.position.x, main_target.position.y = old_x, old_y
                    #                     self.game_state = GameStates.ENEMY_TURN
                    #
                    #             else:
                    #                 self.dialogue(main_target)
                    #
                    #         # Attack Enemies
                    #         for target in targets:
                    #             # Check if Entity Faction
                    #             if self.player.faction.check_enemy(target.faction.faction_name):
                    #                 # Enemy
                    #                 attack_results = self.player.fighter.attack(target)
                    #                 self.player_turn_results.extend(attack_results)
                    #                 # self.game_state = GameStates.ENEMY_TURN
                    #
                    #         # else:
                    #         # Neutral
                    #         # self.player_turn_results.extend([{'message': Message('You bump into a %s.' % target.name)}])
                    #         # self.game_state = GameStates.ENEMY_TURN
                    #         # Spawn Hit Particles for Non-Target Spaces
                    #     print("targetted_spaces : ", targetted_spaces)
                    #     for (x, y) in targetted_spaces:
                    #         if not self.game_map.is_blocked(x, y) and (x, y) in self.player.fighter.curr_fov_map:
                    #             self.player_turn_results.append({"spawn_particle": ["hit_blank", x, y, None]})













                    self.game_map.tile_cost[self.player.position.y][self.player.position.x] = TILE_SET.get("%s" % self.game_map.tileset_tiles[self.player.position.y][self.player.position.x]).get('tile_cost')
                    # self.update_mouse_pos(dx, dy)
                    self.player.position.move(dx, dy)
                    self.fov_recompute = True
                    self.game_map.tile_cost[destination_y][destination_x] = 99
                    self.game_state = GameStates.ENEMY_TURN

                    # Reset Mouse
                    self.mouse_pos = None
                    self.mouse_targets = []

            # Check if Location has a Map Object by "Bumping" Into it or "Waiting" next to it
            elif map_object_entity:
                interact_results = self.player.fighter.interact(map_object_entity, interact_type='move',
                                                                target_inventory=self.player.inventory,
                                                                entities=self.entities, reveal_all=self.reveal_all,
                                                                game_map=self.game_map, player=self.player)
                self.player_turn_results.extend(interact_results)
                self.game_state = GameStates.ENEMY_TURN

            elif self.game_map.transparent[destination_y][destination_x] and self.game_map.tile_cost[destination_y][destination_x] == 0:
                pass
                # print('interact with entity other side of transparent object')
                # target = get_blocking_entities_at_location(self.entities, destination_x, destination_y)

                # Attempt to talk to Prisoner on Other Side of Jail Cell Wall
                # if not self.player.faction.check_enemy(target.faction.faction_name):
                #     self.dialogue(target)

    def wait(self):
        # Player Character Does Nothing for a Turn
        self.fov_recompute = True
        self.game_state = GameStates.ENEMY_TURN

        # Check Tiles Around for Wait Function
        tiles_to_check = [(self.player.position.x + 1, self.player.position.y), (self.player.position.x - 1, self.player.position.y),
                          (self.player.position.x, self.player.position.y + 1), (self.player.position.x, self.player.position.y - 1)]

        for map_object_entity in self.game_map.map_objects:
            if (map_object_entity.position.x, map_object_entity.position.y) in tiles_to_check:
                # "Wait" Interaction with Map Object Entity
                wait_results = self.player.fighter.interact(map_object_entity, interact_type='wait',
                                                            target_inventory=self.player.inventory,
                                                            entities=self.entities, reveal_all=self.reveal_all,
                                                            game_map=self.game_map, player=self.player)
                self.player_turn_results.extend(wait_results)
                self.game_state = GameStates.ENEMY_TURN

    def game_message(self):
        self.previous_game_state = self.game_state
        self.game_state = GameStates.EVENT_MESSAGE
        print('game_message', self.game_state)


    def close_game_message(self):
        print('close_game_message')
        self.game_state = GameStates.PLAYER_TURN


    def dialogue(self, entity=None):
        if entity:

            if entity.dialogue:

                self.previous_game_state = self.game_state
                self.game_state = GameStates.DIALOGUE
                self.entity_dialogue = entity
                dialogue = entity.dialogue.initiate_dialogue()
                if dialogue:
                    self.total_dialogue = collections.deque(dialogue.split(' '))
                    self.dialogue_line_count = 4 + ceil(len(dialogue) / (self.dialogue_pane_width - 2))
                else:
                    self.total_dialogue = []

                if not self.total_dialogue:
                    self.game_state = GameStates.PLAYER_TURN
                    self.current_dialogue = ''
                    self.dialogue_line_count = 0
            else:
                self.player_turn_results.extend(
                    [{'message': Message('You bump into a friendly {}.'.format(entity.name))}])

        elif self.entity_dialogue:
            dialogue = self.entity_dialogue.dialogue.continue_dialogue()
            self.current_dialogue = ''
            if dialogue:
                self.total_dialogue = collections.deque(dialogue.split(' '))
                self.dialogue_line_count = 4 + ceil(len(dialogue) / (self.dialogue_pane_width - 2))
            else:
                self.total_dialogue = []

            if not self.total_dialogue:
                self.game_state = GameStates.PLAYER_TURN
                self.current_dialogue = ''
                self.dialogue_line_count = 0
        else:
            self.player_turn_results.extend([{'message': Message('You bump into a friendly {}.'.format(entity.name))}])

    def change_faction(self, entity, new_faction_name):
        entity.faction.faction_name = new_faction_name

    def pickup(self):
        # Player is Attempting to Pick Up Item
        # Loop through each entity, check if same tile as player and is an item

        for entity in self.entities:
            if entity.position.x == self.player.position.x and entity.position.y == self.player.position.y and entity.item:
                pickup_results = self.player.inventory.add_item(entity)
                self.player_turn_results.extend(pickup_results)
                break
        else:
            self.player_turn_results.append({'message': Message('There is nothing here to pick up.', tcod.yellow)})

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
        # TODO: Incorporate "Stairs" as a Map Object Entity with Interact/Wait functions
        for entity in self.game_map.map_objects:
            if entity.stairs and entity.position.x == self.player.position.x and entity.position.y == self.player.position.y:
                self.entities, self.particles, self.particle_systems = self.game_map.next_floor(self.player, self.message_log, CONSTANTS)
                self.fov_map = initialize_fov(self.game_map)
                self.enemy_fov_map = np.zeros(self.fov_map.transparent.shape, dtype=bool)
                self.fov_recompute = True
                self.game_message()  # start message
                break
        self.player_turn_results.append({'message': Message('There are no stairs here.', tcod.yellow)})

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
                self.player_turn_results.extend(self.player.inventory.use(item, entities=self.entities, fov_map=self.fov_map, reveal_all=self.reveal_all, game_map=self.game_map))

            elif self.game_state == GameStates.DROP_INVENTORY:
                self.player_turn_results.extend(self.player.inventory.drop_item(item, self.player))

    def targetting(self, mouse_click):
        # Handle Targeting for Ranged Attacks
        if mouse_click.button == tcod.event.BUTTON_LEFT:
            target_x = self.mouse_pos[0]
            target_y = self.mouse_pos[1]
            item_use_results = self.player.inventory.use(self.targeting_item, entities=self.entities,
                                                         game_map=self.game_map,  fov_map=self.fov_map,
                                                         target_x=target_x, target_y=target_y, reveal_all=self.reveal_all)
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

    def spawn_particle(self, particle_request):
        # print('\nspawn particle:', particle_request)

        p_index, p_x, p_y, particle_system = particle_request

        p_stats = PARTICLES.get(p_index)
        p_name = p_stats.get("name")
        p_lifetime = p_stats.get("lifetime")
        p_char = p_stats.get("glyph")
        p_fg = p_stats.get("fg")
        p_bg = p_stats.get("bg")
        p_within_fov = p_stats.get("within_fov")
        p_propagate = p_stats.get("propagate", False)
        p_propagate_property = p_stats.get("propagate_property", None)
        p_forever = p_stats.get("forever", False)

        # if particle_system:
        #     print('\tparticle_system:')
        #     print(particle_system.particle_list, particle_system.coordinates)

        if not particle_system:
            particle_system = ParticleSystem()
            # print('Creating new particle there are %s particles and %s coordinates:' % (
            #     len(particle_system.particle_list), len(particle_system.coordinates)))

        if particle_system not in self.particle_systems:
            # print('\nnew particle system there are %s particles and %s coordinates:' % (
            #     len(particle_system.particle_list), len(particle_system.coordinates)))
            self.particle_systems.append(particle_system)

        position_component = Position(x=p_x, y=p_y)
        particle_component = Particle(lifetime=p_lifetime, char=p_char, fg=p_fg, bg=p_bg, forever=p_forever,
                                      propagate=p_propagate, propagate_property=p_propagate_property,
                                      within_fov=p_within_fov, particle_system=particle_system)
        particle_entity = Entity(char=p_char, color=p_fg, name=p_name, json_index=p_index, position=position_component,
                                 particle=particle_component, render_order=RenderOrder.PARTICLE)
        particle_system.particle_list.append(particle_component)
        particle_system.coordinates.append((p_x, p_y))
        self.particles.append(particle_entity)

    def propagate_particle(self, particle_dict):
        # print('\npropagate_particle', particle_dict)
        for particle, val_list in particle_dict.items():
            # print(val_list[0])
            if val_list[0]:
                center_x, center_y = particle.owner.position.x, particle.owner.position.y
                directions = [(center_x - 1, center_y),
                              (center_x + 1, center_y),
                              (center_x, center_y + 1),
                              (center_x, center_y - 1)]

                # Propagate in all (4) Cardinal Directions
                # print('# Propagate in all (4) Cardinal Directions')
                for dx, dy in directions:

                    # Check if Particle System Doesn't Already Have a Particle at Location
                    # print('# Check if Particle System Doesn\'t Already Have a Particle at Location')
                    particle_system = particle.particle_system
                    # if particle_system:
                    if (dx, dy) in particle_system.coordinates:
                        continue

                    tile = self.game_map.tileset_tiles[dy][dx]
                    tile_stats = TILE_SET.get("{}".format(tile))
                    tile_property = tile_stats.get('properties')
                    # tile_name = tile_stats.get('name')
                    if [val_list[1]] == tile_property:
                        # print('spawning fire particle at (%s, %s)' % (dx, dy))
                        # print('tile:', tile_name)
                        # print('tile_property:', tile_property)

                        if val_list[1] == 'flammable':

                            # Check if Entity Exists on tile
                            for entity in self.entities:
                                if entity.position and entity.fighter:
                                    if (entity.position.x, entity.position.y) == (dx, dy):
                                        entity.fighter.take_damage(25)
                                        break

                            self.spawn_particle(('fire', dx, dy, particle_system))

                            map_object = self.game_map.obtain_map_objects(dx, dy)

                            new_tile = 4
                            if map_object:
                                if map_object.inventory:
                                    for item in map_object.inventory.items:
                                        self.entities.append(item)

                                    map_object.inventory.drop_all_items()

                                self.change_map_object([map_object, new_tile])
                            else:
                                new_tile_stats = TILE_SET.get('{}'.format(new_tile))
                                scorched_ground = new_tile_stats.get("glyph")
                                self.game_map.tileset_tiles[dy][dx] = new_tile
                                self.game_map.tile_cost[dy][dx] = new_tile_stats.get("tile_cost")
                                self.game_map.walkable[dy][dx] = new_tile_stats.get("walkable")
                                self.game_map.transparent[dy][dx] = new_tile_stats.get("transparent")
                                self.fov_map.transparent[dy][dx] = new_tile_stats.get("fov")
                                self.enemy_fov_map[dy][dx] = new_tile_stats.get("fov")

                        elif val_list[1] == 'conductor':
                            for entity in self.entities:
                                if entity.position and entity.fighter:
                                    if (entity.position.x, entity.position.y) == (dx, dy):
                                        entity.fighter.take_damage(40)
                                        break
                            self.spawn_particle(('lightning', dx, dy, particle_system))


    @staticmethod
    def toggle_full_screen():
        # print('TODO: actually toggle full screen or not ...')
        pass

    def display_message(self, game_message):
        self.message_log.add_message(game_message)

    def item_added(self, item_added):
        # TODO: Deal with removing items that are not entities, not ValueError handling
        try:
            self.entities.remove(item_added)  # how to deal with items from chest that are not entities
        except ValueError:
            pass  # ignore entity since it doesn't exist on map

        self.game_state = GameStates.ENEMY_TURN

    def item_consumed(self, *args):
        self.reset_mouse_targets()
        self.game_state = GameStates.ENEMY_TURN

    def item_reuseable(self, *args):
        self.reset_mouse_targets()
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
        # print('activate_targeting_mode', targeting)
        # print('range:', targeting.item.function_kwargs.get('maximum_range'))
        # Activate Targeting Game State to User to Mouse Select
        self.mouse_target_type = targeting.item.function_kwargs.get('targeting_type')
        self.mouse_target_radius = targeting.item.function_kwargs.get('radius')
        self.mouse_target_range = targeting.item.function_kwargs.get('maximum_range')
        self.previous_game_state = GameStates.PLAYER_TURN
        self.game_state = GameStates.TARGETING
        self.targeting_item = targeting
        self.display_message(self.targeting_item.item.targeting_message)
        if self.mouse_pos:
            self.set_mouse_pos(self.mouse_pos[0] + 1, self.mouse_pos[1] + 1)

    def deactivate_targeting_mode(self, *args):
        self.game_state = self.previous_game_state
        self.display_message(Message('Targeting cancelled.'))
        self.reset_mouse_targets()

    def activate_map(self, *args):
        # Allow Document to Read On Screen
        # TODO: Make modular to allow any other type of "reading" item
        self.previous_game_state = GameStates.PLAYER_TURN
        self.game_state = GameStates.READ

    def obtain_xp(self, xp_args):
        # Only Allow Player to Receive XP
        xp = xp_args[0]
        entity = xp_args[1]
        # TODO: Separate XP component from Fighter Component
        if entity == self.player:
            leveled_up = self.player.level.add_xp(xp)
            self.display_message(Message('You gained %s experience points.' % xp))

            if leveled_up:
                self.display_message(Message('Your battle skills grow stronger! You reached level %s!' %
                                             self.player.level.current_level, tcod.yellow))
                self.previous_game_state = self.game_state
                self.game_state = GameStates.LEVEL_UP

    def dead_entity(self, entity):
        if entity == self.player:
            message, self.game_state = kill_player(entity)
        else:
            # Remove Encounter or Reference to Encounter
            entity.ai.remove_encounter()

            message = kill_mob(entity)

            # Drop All Items on Floor
            if entity.inventory:
                # message = Message('You see {} drop items is dead!'.format(entity.name.capitalize()), tcod.orange)
                items_to_drop = copy(entity.inventory.items)

                for item_entity in items_to_drop:
                    entity.inventory.drop_item(item_entity, entity)
                    self.entities.append(item_entity)

            self.game_map.walkable[entity.position.y][entity.position.x] = True
            self.game_map.transparent[entity.position.y][entity.position.x] = True
            self.game_map.tile_cost[entity.position.y][entity.position.x] = self.game_map.tile_set.get(
                "%s" % self.game_map.tileset_tiles[entity.position.y][entity.position.x]).get('tile_cost')

        # Display Message if Within Player FOV
        if self.fov_map.fov[entity.position.x][entity.position.y]:
            self.display_message(message)

    def change_map_object(self, map_object_entity_args):
        map_object_entity = map_object_entity_args[0]
        new_json_index = map_object_entity_args[1]

        y, x = map_object_entity.position.y, map_object_entity.position.x

        # Change Map Object Entity
        map_object_entity.change_entity(self.game_map.tile_set.get("%s" % new_json_index), new_json_index)

        # Update Game Map
        self.game_map.tileset_tiles[y][x] = new_json_index
        tile_stats = TILE_SET.get('%s' % new_json_index)
        self.game_map.tile_cost[y][x] = tile_stats.get("tile_cost")
        self.game_map.walkable[y][x] = tile_stats.get("walkable")
        self.game_map.transparent[y][x] = tile_stats.get("transparent")
        self.fov_map.transparent[y][x] = tile_stats.get("fov")
        self.enemy_fov_map[y][x] = tile_stats.get("fov")
        self.game_state = GameStates.ENEMY_TURN

    def temporary_vision(self, door_entity):
        self.game_map.temporary_vision.append((door_entity.position.x, door_entity.position.y))
        self.fov_recompute = True
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
        self.player_turn_results.append({'xp': [self.player, self.player.level.experience_needed_to_next_level]})

        if self.previous_game_state == GameStates.PLAYER_DEAD:
            self.game_state = self.previous_game_state
        else:
            self.game_state = GameStates.PLAYER_TURN

    def go_to_next_level(self):
        # Debug Go to Next Level
        self.entities, self.particles, self.particle_systems = self.game_map.next_floor(self.player, self.message_log, CONSTANTS)
        self.fov_map = initialize_fov(self.game_map)
        self.fov_recompute = True
        self.game_state = GameStates.PLAYER_TURN
        self.revive_player()
        self.game_message()  # start message

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
            self.player.char = "@"
            self.player.color = [191, 171, 143]
            self.player.fighter.hp = self.player.fighter.max_hp
            self.game_state = GameStates.PLAYER_TURN
        elif self.game_state == GameStates.DEBUG_MENU:
            self.game_state = GameStates.PLAYER_TURN

    def ev_mousebuttonup(self, event: tcod.event.MouseButtonUp):
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
            self.mouse_targets = []

            mouse_x = self.clamp(view_x_start + x + viewport_width_start, 0, self.game_map.width - 1)
            mouse_y = self.clamp(view_y_start + y + viewport_height_start, 0, self.game_map.height - 1)
            if self.mouse_target_type == 'area':
                # radius = self.mouse_target_range mouse_target_range // 2
                radius = self.mouse_target_radius
                for dx in range(mouse_x - radius, mouse_x + radius + 1):
                    for dy in range(mouse_y - radius, mouse_y + radius + 1):

                        radius_x = mouse_x - dx
                        radius_y = mouse_y - dy

                        distance_squared = radius_x * radius_x + radius_y * radius_y

                        if distance_squared <= self.mouse_target_range:
                        # if distance_squared <= radius * radius:
                        # if self.game_map.tile_cost[dy][dx] != 0 and distance_squared <= radius * radius:
                            self.mouse_targets.append((dx, dy))
                print('mouse_targets:', self.mouse_targets)

            elif self.mouse_target_type == 'path':
                self.mouse_targets = self.player.position.move_astar(mouse_x, mouse_y, self.game_map, diagonal_cost=1.00)

            self.mouse_targets.append((mouse_x, mouse_y))
            self.mouse_pos = (mouse_x, mouse_y)
            self.normal_mouse_pos = (x, y)
        else:
            self.normal_mouse_pos = None
            self.mouse_pos = None
            self.mouse_targets = []

    @staticmethod
    def clamp(num, min_value, max_value):
        return max(min(num, max_value), min_value)

    def update_mouse_pos(self, dx, dy):
        if self.mouse_pos:
            new_x, new_y = self.mouse_pos
            if CONSTANTS['viewport_width'] < self.player.position.x + dx < CONSTANTS['map_width'] - CONSTANTS['viewport_width']:
                new_x += dx

            if CONSTANTS['viewport_height'] < self.player.position.y + dy < CONSTANTS['map_height'] - CONSTANTS['viewport_height']:
                new_y += dy

            # Clamp Values
            new_x = self.clamp(new_x, 0, self.game_map.width - 1)
            new_y = self.clamp(new_y, 0, self.game_map.height - 1)


            # if self.game_map.width >= new_x:
            #     new_x = self.game_map.width
            # elif new_x < 0:
            #     new_x = 0
            #
            # if self.game_map.height >= new_y:
            #     new_y = self.game_map.height
            # elif new_y < 0:
            #     new_y = 0

            self.mouse_pos = new_x, new_y

    def initialize_game(self, level):
        print('initialize_game : ', level)
        # Initialize Game Variables
        self.player, self.entities, self.particles, self.particle_systems, self.game_map, self.message_log, \
            self.game_state, dungeon_level = get_game_variables(CONSTANTS, level=level)
        self.panel = tcod.console.Console(CONSTANTS['screen_width'], CONSTANTS['panel_height'])
        self.top_panel = tcod.console.Console(CONSTANTS['screen_width'], CONSTANTS['top_gui_height'])
        self.event_panel = tcod.console.Console(CONSTANTS['viewport_width'] * 2, CONSTANTS['viewport_height'] * 2)
        self.side_panel = tcod.console.Console(CONSTANTS['side_panel_width'], CONSTANTS['side_panel_height'] * 2)

        self.fov_recompute = True
        self.fov_map = initialize_fov(self.game_map)
        self.enemy_fov_map = np.zeros(self.fov_map.transparent.shape, dtype=bool)
        print("level : ", level)
        if dungeon_level == 0:  # arena level
            self.reveal_all = 1
        else:
            self.reveal_all = 0
        self.previous_game_state = self.game_state
        self.targeting_item = None
        self.alert_mode = AlertEnum.NORMAL

    def initialize_loaded_game(self):
        self.panel = tcod.console.Console(CONSTANTS['screen_width'], CONSTANTS['panel_height'])
        self.top_panel = tcod.console.Console(CONSTANTS['screen_width'], CONSTANTS['top_gui_height'])
        self.fov_map = initialize_fov(self.game_map)
        self.enemy_fov_map = np.zeros(self.fov_map.transparent.shape, dtype=bool)

    def on_draw(self):
        global ROOT_CONSOLE, TURN_RESULTS
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
        #              ○  ◙  ►  ◄   ↕   ↑    ↓   →   ←  ↔   ▲  ▼   !   "   #   $   y   %   '   (   )   *   +   ,   -   .
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
        #              d    e    f    g    h    i    j    k    l    m    n    o    p    q    r    s    t    z
        # """
        # char_list = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 122] v
        #
        # """
        #              {    |    }    ~    ⌂    Ç    ü    é    â    ä    à    å    ç    ê    ë    R    ï    î    ì
        # char_list = [123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141]
        #
        # """
        #                   ░    ▒    ▓    │    ┤    ╣    ║    ╗    ╝    ╜    ≈    └    ╔    ┬    ╣    ─    ┼
        # """
        # char_list.extend([176, 177, 178, 179, 180, 185, 186, 187, 188, 189, 191, 192, 193, 194, 195, 196, 197])
        #╡╢╖╕╣║╗╝╜╛┐└┴┬├─┼╞╟╚╔╩
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

        # Log Events that Occured During Player Turn
        # Analyze Actions User Results and Propagate Resulting Events
        for player_turn_result_dict in self.player_turn_results:
            for result_key, result_val in player_turn_result_dict.items():
                result_event = TURN_RESULTS.get(result_key, no_key_action)
                result_event(self, result_val)  # pass dict.values()
        self.player_turn_results = []

        # # Elevate to Alert Mode
        # if self.alert_mode == AlertEnum.WARNING and entity.ai.current_target == self.player:
        #     self.alert_mode = AlertEnum.SPOTTED

        # Enemy Turn to Act
        bool_spotted = -1
        if self.game_state == GameStates.ENEMY_TURN:
            self.fov_recompute = True
            for entity in self.entities:
                if entity.ai:

                    # Pick Closest Enemy Entity and Attack
                    # Note: This doesn't take into account, if obstacles block FOV to see entity as all entities are
                    #       sharing the same FOV map. Entities will be able to target through walls if ally target on
                    #       other side has that entity in its FOV.

                    # Check if Current Target is Dead
                    if entity.ai.current_target:
                        # if hasattr(entity.ai.current_target, "fighter"):
                        if hasattr(entity.ai.current_target, "render_order"):
                            if entity.ai.current_target.render_order == RenderOrder.CORPSE:
                                entity.ai.current_target = None

                    # If Entity doesn't have a Current Target
                    # TODO: Condense this disgusting IF structure:
                    #       1. Check if no current target
                    #       2. AI exist or is Player
                    #       3. Within Distance
                    #       4. Within FOV
                    #       5. Add Target and Dist Val to Dictionary
                    #       6. Pick min distance value
                    # if not entity.ai.current_target:
                    close_entities = {}
                    for other_entity in self.entities:

                        # Check if AI
                        if other_entity.ai or other_entity is self.player:

                            # Check if Enemy Faction
                            if entity.faction.check_enemy(other_entity.faction.faction_name):

                                # Check within Distance and Entity's FOV
                                distance = int(entity.position.distance_to(other_entity.position.x, other_entity.position.y)) + 1
                                if distance <= entity.fighter.fov_range and \
                                        (other_entity.position.y, other_entity.position.x) in entity.fighter.curr_fov_map:
                                        # self.enemy_fov_map[other_entity.position.y][other_entity.position.x]:

                                    # Add Target to Dict of Possible Targets by Distance
                                    close_entities[distance] = other_entity

                    # close_entities = {int(entity.position.distance_to(other_entity.position.x, other_entity.position.y)) + 1:other_entity for other_entity in self.entities \
                    #                   if (other_entity.ai or other_entity is self.player) and }
                    # If Possible Targets, Finally Select The Closest Target
                    if close_entities:
                        min_distance = min(close_entities.keys())
                        entity_target = close_entities[min_distance]
                        entity.ai.target_not_within_fov_max = min_distance + min_distance
                        entity.ai.current_target = entity_target
                        entity.ai.encounter.target_list.add(entity_target)

                    # Elevate to Alert Mode
                    # if self.alert_counter > 6 and entity.ai.current_target == self.player:
                    #     self.alert_mode = AlertEnum.SPOTTED
                    #     self.alert_counter = 10
                    #
                    # # Check if Player is Spotted
                    # if (self.player.position.y, self.player.position.x) in entity.fighter.curr_fov_map and \
                    #         entity.faction.check_enemy(self.player.faction.faction_name):
                    #     bool_spotted = 1
                    #
                    # # Seek Player if Alert Mode is Escalated
                    # if self.alert_mode == AlertEnum.SPOTTED and self.alert_counter == 11:
                    #     if not entity.ai.current_target and entity.faction.check_enemy(self.player.faction.faction_name):
                    #         entity.ai.current_target = self.player
                    #         entity.ai.path = []

                    # Free/Retreat AI
                    enemy_turn_results = entity.ai.take_turn(entity.fighter.curr_fov_map, self.game_map, self.entities)

                    # Activate Actions/Events from Enemy Turn
                    for enemy_turn_result_dict in enemy_turn_results:
                        for result_key, result_val in enemy_turn_result_dict.items():

                            # Don't Dislay Messages if Entity not Within Player FOV
                            # TODO: FOV should depend on action position, not the entity position itself.
                            if result_key == 'message':
                                if (entity.position.y, entity.position.x) in self.player.fighter.curr_fov_map:

                                    result_event = TURN_RESULTS.get(result_key, no_key_action)
                                    result_event(self, result_val)  # pass dict.values()
                            else:
                                result_event = TURN_RESULTS.get(result_key, no_key_action)
                                result_event(self, result_val)  # pass dict.values()

                    # Check if Player is Dead as a Result
                    if self.game_state == GameStates.PLAYER_DEAD:
                        break
            else:
                self.game_state = GameStates.PLAYER_TURN

            # Iterate through Encounters
            for e in self.game_map.encounters:
                e.unite()

            # Update Turn Count
            self.game_map.turn_count += 1

            # Decrement Alert Counter if Not Spotted
            self.alert_counter += bool_spotted

            if self.alert_counter < 1:
                self.alert_counter = 0

        if self.alert_counter < 1:
            if self.alert_mode == AlertEnum.SPOTTED:
                self.alert_mode = AlertEnum.WARNING

            elif self.alert_mode == AlertEnum.WARNING:
                self.alert_mode = AlertEnum.NORMAL

        elif 0 < self.alert_counter < 6:
            self.alert_mode = AlertEnum.WARNING

        # elif self.alert_counter > 5:
        #     self.alert_mode = AlertEnum.SPOTTED

        # Update Particles Life Time Counter
        particle_results = []
        for p in self.particles:
            particle_results.append(p.particle.update(1))

        for result in particle_results:
            self.propagate_particle(result)

        # Remove Particles Past their lifetime
        self.particles = [p for p in self.particles if p.particle.lifetime > 0]

        # Remove Particle Systems if No Particles
        self.particle_systems = [p_sys for p_sys in self.particle_systems if len(p_sys.particle_list) > 0]

        # Check for Game Events Activations
        for game_event in self.game_map.game_events:

            if game_event.check_conditions():
                print('\n', game_event)
                game_event_results = game_event.activate_event(self.entities, self.particles)

                for game_event_result_dict in game_event_results:

                    for result_key, result_val in game_event_result_dict.items():
                        result_event = TURN_RESULTS.get(result_key, no_key_action)
                        result_event(self, result_val)  # pass dict.values()

        # Remove Game Events if Conditions All Conditions Are True
        self.game_map.game_events = [g for g in self.game_map.game_events if not g.check_conditions()]

        if self.fov_recompute:
            # Update FOV for Player
            self.fov_map.fov[:] = recompute_fov(self.fov_map, self.player, self.game_map.temporary_vision,
                                                        CONSTANTS['fov_light_walls'], CONSTANTS['fov_algorithm'])

            # Obtain all True Coordinates from fov_map and assign to Player
            curr_fov_map = np.where(self.fov_map.fov==True)
            self.player.fighter.curr_fov_map = list(zip(curr_fov_map[0], curr_fov_map[1]))

            # Remove Temporary Vision for Next Turn
            for x, y in self.game_map.temporary_vision:
                fov_boolean = TILE_SET.get('%s' % self.game_map.tileset_tiles[y][x]).get('transparent')
                self.fov_map.transparent[y][x] = fov_boolean

            self.game_map.temporary_vision = []
            
            # Update and Combine FOV for Entities
            self.enemy_fov_map = definite_enemy_fov(self.game_map, self.fov_map, self.game_map.entrances, self.entities,
                                               CONSTANTS['fov_light_walls'], CONSTANTS['fov_algorithm'])

        # Actual Drawing
        self.event_panel.clear()
        view_x_start, view_x_end, view_y_start, view_y_end = \
            obtain_viewport_dimensions(self.game_map, CONSTANTS['viewport_width'], CONSTANTS['viewport_height'])

        # Make Viewport Smaller than Frame
        viewport_width_start = -1
        viewport_height_start = -1
        view_x_end -= 2
        view_y_end -= 2

        # Background, Tiles, Etc.
        render_viewport(self.event_panel, self.mouse_pos, self.mouse_targets, self.game_map, self.entities, self.fov_map, self.enemy_fov_map,
                        self.fov_recompute, self.reveal_all, view_x_start, view_x_end, view_y_start, view_y_end,
                        viewport_width_start, viewport_height_start, self.game_map.default_tile)

        # Render Reference Tiles

        # Sort Draw Order to Sort by Render Order Enum Value and if Within Screen,
        entities_under_mouse = []
        # _entities_in_render_order = [entity for entity in self.entities + self.particles if entity.position]
        entities_in_render_order = sorted(
            [entity for entity in self.entities + self.particles if view_x_start <= entity.position.x < view_x_end and view_y_start <= entity.position.y < view_y_end and entity.position],
            key=lambda x: x.render_order.value
        )
        # Draw all entities in the list
        for entity in entities_in_render_order:

            # Find Entity Under Mouse since we're looping :D
            if self.mouse_pos:
                if entity.position.x == self.mouse_pos[0] and entity.position.y == self.mouse_pos[1] and \
                        self.fov_map.fov[self.mouse_pos[0]][self.mouse_pos[1]] and not entity.particle:
                    entities_under_mouse.append(entity)

            if entity.particle:
                draw_particle_entity(self.event_panel, entity, self.fov_map, self.reveal_all, view_x_start,
                                     view_y_start, viewport_width_start, viewport_height_start)
            else:
                draw_entity(self.event_panel, entity, self.fov_map, self.game_map, self.reveal_all, view_x_start, view_x_end,
                            view_y_start, view_y_end, viewport_width_start, viewport_height_start)

        # Alert Mode GUI
        if self.alert_mode != AlertEnum.NORMAL:

            if self.alert_mode == AlertEnum.SPOTTED:
                alert_color = tcod.red
            elif self.alert_mode == AlertEnum.WARNING:
                alert_color = tcod.yellow

            if self.alert_lerp_value > 0.90:
                self.alert_lerp_mod = -1
            elif self.alert_lerp_value < 0.10:
                self.alert_lerp_mod = 1
            self.alert_lerp_value += self.alert_lerp_mod * 0.075
            frame_color = tcod.color_lerp(alert_color, tcod.white, self.alert_lerp_value)
        else:
            frame_color = tcod.white

        # Create Frame around near pos
        info = ''
        line_count = 0
        info_pane_width = 16
        for entity in entities_under_mouse:

            # info += '\n\n%s' % entity.name
            # line_count += 3
            if entity.render_order == RenderOrder.CORPSE:
                info += '\n\n{}'.format(entity.name)
                line_count += 3 + ceil(len(entity.name) / info_pane_width - 2)

            elif entity.fighter:
                info += '\n\n%s\nLv: %s\nHP: %s\nStr: %s\nDef: %s' % (entity.name, entity.fighter.mob_level, entity.fighter.hp, entity.fighter.power, entity.fighter.defense)
                line_count += 6 + ceil(len(entity.name) / (info_pane_width - 2))

            elif entity.equippable:
                info += '\n\n%s\n\n+HP: %s\n+STR: %s\nDEF: %s' % (entity.name,
                                                entity.equippable.max_hp_bonus,
                                                entity.equippable.power_bonus,
                                                entity.equippable.defense_bonus)
                line_count += 5 + ceil(len(entity.name) / info_pane_width)

            elif entity.item:
                info += '\n\n{}'.format(entity.name)
                line_count += 2

        if entities_under_mouse:
            # Check left or right
            frame_x = self.normal_mouse_pos[0] + 1  # display right
            if self.normal_mouse_pos[0] >= CONSTANTS.get('viewport_width'):
                frame_x = self.normal_mouse_pos[0] - info_pane_width  # display left
                if frame_x < 1:
                    frame_x = 1

            # Check top or bottom
            frame_y = self.normal_mouse_pos[1]
            if self.normal_mouse_pos[1] > CONSTANTS.get('viewport_height'):
                frame_y = self.normal_mouse_pos[1] + 1 - line_count

                if frame_y < 1:
                    frame_y = 1

            popup_panel = tcod.console.Console(info_pane_width, line_count+1)
            popup_panel.print_box(x=1, y=1, width=info_pane_width - 2, height=line_count+1, string=info[2:])

            popup_panel.draw_frame(x=0, y=0, width=info_pane_width, height=line_count+1, title='', fg=frame_color,
                                   bg=tcod.black, clear=False, bg_blend=tcod.BKGND_SCREEN)

            popup_panel.blit(dest=self.event_panel, dest_x=frame_x, dest_y=frame_y, src_x=0, src_y=0,
                             width=info_pane_width, height=line_count+1)

        # Frame
        self.event_panel.draw_frame(0, 0, self.event_panel.width, self.event_panel.height,
                                    title='%s Level: %s' % (self.game_map.level, self.game_map.dungeon_level),
                                    fg=frame_color, bg=tcod.black, clear=False, bg_blend=tcod.BKGND_DEFAULT)

        # Continue Dialogue Options
        if self.game_state == GameStates.DIALOGUE:

            # self.dialogue_panel.update()
            # print(self.entity_dialogue.name, self.total_dialogue)
            dialogue_name = self.entity_dialogue.name

            if self.total_dialogue:
                self.current_dialogue += self.total_dialogue.popleft() + ' '

            # frame_x = (self.event_panel.width // 2) - pane_width // 2
            # frame_y = (self.event_panel.height // 2) - pane_height // 2
            frame_x = 2
            frame_y = 2
            self.dialogue_panel = tcod.console.Console(self.dialogue_pane_width, self.dialogue_line_count)
            self.dialogue_panel.clear()

            self.dialogue_panel.draw_frame(x=0, y=0, width=self.dialogue_pane_width, height=self.dialogue_line_count,
                                           title='', fg=frame_color, bg=tcod.black, clear=True, bg_blend=tcod.BKGND_SCREEN)
            self.dialogue_panel.print_box(x=1, y=1, width=self.dialogue_pane_width - 2,
                                          height=self.dialogue_line_count,
                                          string='{}\n\n{}'.format(dialogue_name, self.current_dialogue))

            self.dialogue_panel.blit(dest=self.event_panel, dest_x=frame_x, dest_y=frame_y, src_x=0, src_y=0,
                                     width=self.dialogue_pane_width, height=self.dialogue_line_count)
            # self.end_dialogue()

        if self.game_state == GameStates.EVENT_MESSAGE:
            msg = self.game_map.level_message
            new_lines = msg.count('\n\n')
            event_message_panel_width = ceil(CONSTANTS.get("viewport_width") * 1.5)
            event_message_panel_height = CONSTANTS.get("viewport_height")
            # event_message_panel_height = ceil(len(msg) / event_message_panel_width) + new_lines

            self.event_message_panel = tcod.console.Console(event_message_panel_width, event_message_panel_height)
            self.event_message_panel.clear()

            # msg = "".join(choice(string.ascii_letters) for _ in range(randint(25, 50)))



            self.event_message_panel.draw_frame(x=0, y=0, width=event_message_panel_width,
                                                height=event_message_panel_height
                                                , title='', fg=frame_color, bg=tcod.black,
                                                clear=True, bg_blend=tcod.BKGND_SCREEN)
            self.event_message_panel.print_box(x=1, y=1, width=event_message_panel_width-2,
                                               height=event_message_panel_height-2, string=msg,
                                               alignment=tcod.CENTER)
            self.event_message_panel.blit(dest=self.event_panel, dest_x=CONSTANTS.get("viewport_width") - event_message_panel_width//2,
                                          dest_y=CONSTANTS.get("viewport_height") - (event_message_panel_height//2),
                                          src_x=0, src_y=0, width=event_message_panel_width, height=event_message_panel_height)

        # Actual Game Screen
        self.event_panel.blit(dest=ROOT_CONSOLE, dest_x=0, dest_y=0, src_x=0, src_y=0,
                              width=self.event_panel.width, height=self.event_panel.height)
        # Draw Console to Screen
        # Player UI Panel
        self.panel.clear()
        self.panel.draw_frame(0, 0, CONSTANTS['screen_width'], CONSTANTS['panel_height'], fg=frame_color, clear=False,
                              bg_blend=tcod.BKGND_NONE)

        # Print the game Messages, one line at a time
        y = 1
        for message in self.message_log.messages:
            self.panel.print(self.message_log.x, y, message.text, fg=message.color)
            y += 1

        self.panel.blit(dest=ROOT_CONSOLE, dest_x=0, dest_y=CONSTANTS['panel_y'], src_x=0, src_y=0,
                        width=CONSTANTS['screen_width'], height=CONSTANTS['panel_height'],)

        # Side Panel for Enemy Display Status Effects etc.
        self.side_panel.clear()
        self.side_panel.draw_frame(0, 0, CONSTANTS['side_panel_width'], CONSTANTS['side_panel_height'], fg=frame_color,
                                   clear=False, bg_blend=tcod.BKGND_DEFAULT)

        # Display Character Level
        # self.side_panel.print(CONSTANTS['bar_width'] // 2 + 1, 1, "{}".format(self.alert_mode),
        #                       fg=tcod.light_gray, bg_blend=tcod.BKGND_NONE, alignment=tcod.CENTER)
        # Render HP Bar
        render_bar(self.side_panel, 1, 2, CONSTANTS['bar_width'], 'HP', self.player.fighter.hp,
                   self.player.fighter.max_hp, tcod.light_red, tcod.darker_red)

        # Render XP Bar
        render_bar(self.side_panel, 1, 3, CONSTANTS['bar_width'], 'XP', self.player.level.current_xp,
                   self.player.level.experience_to_next_level, tcod.darker_yellow, tcod.darkest_yellow)

        # Display ATT/DEF
        self.side_panel.print(1, 5, 'STR: %s\nDEF: %s' % (self.player.fighter.power, self.player.fighter.defense),
                              fg=tcod.light_gray, bg_blend=tcod.BKGND_NONE, alignment=tcod.LEFT)

        # Display Turn Count
        self.side_panel.print(1, 6, 'CurrentTurn:{}'.format(self.game_map.turn_count), fg=tcod.light_gray,
                              bg_blend=tcod.BKGND_NONE, alignment=tcod.LEFT)
        # Display Alert Counter
        # self.side_panel.print(1, 7, 'AlertCounter:{}'.format(self.alert_counter), fg=tcod.light_gray,
        #                       bg_blend=tcod.BKGND_NONE, alignment=tcod.LEFT)

        # Dislay Technique Slots
        self.side_panel.print(2, 11, "1", fg=tcod.white,
                              bg_blend=tcod.BKGND_NONE, alignment=tcod.CENTER)

        self.side_panel.draw_frame(1, 10, 3, 3, fg=tcod.pink,
                                   clear=False, bg_blend=tcod.BKGND_DEFAULT)


        # Terrain Under Mouse Display
        if self.mouse_pos:
            mouse_x, mouse_y = self.mouse_pos

            # Tile Data
            tile = self.game_map.tileset_tiles[mouse_y][mouse_x]
            _tile = self.game_map.tile_set.get("%s" % tile)
            name = "%s\nCost: %s\n(%s, %s)" % (_tile.get("name"), self.game_map.tile_cost[mouse_y][mouse_x],
                                                   mouse_x, mouse_y)
            # Room Type
            for room in self.game_map.mouse_rooms:
                # if room.check_point_within_room(mouse_x + view_x_start + viewport_width_start,
                #                                 mouse_y + view_y_start + viewport_height_start):
                if room.check_point_within_room(mouse_x, mouse_y):
                    name += "\nRoom: %s" % room.room_type
            self.side_panel.print(1, CONSTANTS['side_panel_height'] - 5, string=name, fg=tcod.light_gray,
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

    if parameter == 'New Game':
        current_screen = SCREENS.get('gamemode')
        SCREENS.get('game').initialize_game('resinfaire')
        current_screen = SCREENS.get('game')
    elif parameter == 'Continue':
        current_screen = SCREENS.get('game')
    elif parameter == 'Quit':
        current_screen.exit_program()
    elif parameter == 'title':
        current_screen = SCREENS.get(parameter)
        current_screen.on_enter()
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
    GameStates.ENEMY_TURN: handle_no_action,
    GameStates.DIALOGUE: handle_dialogue,
    GameStates.EVENT_MESSAGE: handle_event_message,
}


TURN_RESULTS = {
    'message': Game.display_message,
    'spawn_particle': Game.spawn_particle,
    'item_added': Game.item_added,
    'consumed': Game.item_consumed,
    'reuseable': Game.item_reuseable,
    'item_dropped': Game.item_dropped,
    'equip': Game.equip_player,
    'targeting': Game.activate_targeting_mode,
    'map': Game.activate_map,
    'targeting_cancelled': Game.deactivate_targeting_mode,
    'xp': Game.obtain_xp,
    'change_map_object': Game.change_map_object,
    'dead': Game.dead_entity,
    "see_through_key_hole": Game.temporary_vision,
    # "npc_message": Game.
}


def main():
    global current_screen
    # Initialize Consoles
    current_screen = SCREENS['title']

    # Create Window based Around Console and Tileset
    with tcod.context.new_terminal(
            ROOT_CONSOLE.width, ROOT_CONSOLE.height, tileset=TILESET
    ) as context:

        # Game Loop
        while True:
            # User Events
            handle_events(context)

            # Rendering
            ROOT_CONSOLE.clear()
            current_screen.on_draw()
            context.present(ROOT_CONSOLE)


def handle_events(context):
    global current_screen
    for event in tcod.event.get():
        context.convert_event(event)
        current_screen.dispatch(event)


def clear_console(con):
    con.clear(fg=(0, 0, 0), bg=(0, 0, 0))


def change_font(con, font, constants):
    global TILESET
    font_sizes = {
        8: tcod.tileset.load_tilesheet('assets/prestige8x8_gs_tc.png', 32, 8, tcod.tileset.CHARMAP_TCOD),
        10: tcod.tileset.load_tilesheet('assets/arial10x10.png', 32, 8, tcod.tileset.CHARMAP_TCOD),
        16: tcod.tileset.load_tilesheet('assets/dejavu_wide16x16_gs_tc.png', 32, 8, tcod.tileset.CHARMAP_TCOD)
    }
    TILESET = font_sizes.get(font)

    return tcod.Console(constants['screen_width'], constants['screen_height'])


if __name__ == '__main__':
    main()
