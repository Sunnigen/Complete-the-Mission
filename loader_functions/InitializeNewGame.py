import tcod as libtcod

from components.Faction import Faction
from components.Fighter import Fighter
from components.Level import Level
from components.Item import Item
from components.Inventory import Inventory
from components.Equippable import Equippable
from components.Equipment import Equipment
from components.Position import Position
from loader_functions.JsonReader import obtain_item_table
from Entity import Entity
from level_generation.GenerationUtils import create_item_entity
from GameMessages import Message, MessageLog

from GameStates import GameStates
import ItemFunctions
from map_objects.GameMap import GameMap
from RenderFunctions import RenderOrder


ITEMS = obtain_item_table()


def get_constants():
    window_title = 'Complete The Mission'

    # Size of Window
    screen_width = 50
    screen_height = 40

    # Size of Map Render
    viewport_width = 16
    viewport_height = 16

    # Map Size
    map_width = 100
    map_height = 100

    panel_height = 8
    panel_y = screen_height - panel_height

    # Side Panel
    side_panel_height = viewport_height * 2
    side_panel_width = screen_width - (screen_width - viewport_width) + 2
    bar_width = side_panel_width - 2
    # panel_y = 0
    top_gui_height = 5
    top_gui_y = 0

    message_x = 1
    message_width = screen_width - 2
    message_height = panel_height - 2

    room_max_size = min(map_height // 5, map_width // 5)
    room_min_size = min(map_height // 7, map_width // 7)
    max_rooms = 50

    fov_algorithm = libtcod.FOV_BASIC
    fov_light_walls = True
    fov_radius = 10
    enemy_fov_radius = 5

    constants = {
        'window_title': window_title,
        'screen_width': screen_width,
        'screen_height': screen_height,
        'bar_width': bar_width,
        'panel_height': panel_height,
        'panel_y': panel_y,
        'message_x': message_x,
        'message_width': message_width,
        'message_height': message_height,
        'map_width': map_width,
        'map_height': map_height,
        'room_max_size': room_max_size,
        'room_min_size': room_min_size,
        'max_rooms': max_rooms,
        'fov_algorithm': fov_algorithm,
        'fov_light_walls': fov_light_walls,
        'fov_radius': fov_radius,
        'enemy_fov_radius': enemy_fov_radius,
        'viewport_width': viewport_width,
        'viewport_height': viewport_height,
        'top_gui_height': top_gui_height,
        'top_gui_y': top_gui_y,
        'side_panel_height': side_panel_height,
        'side_panel_width': side_panel_width
    }

    return constants


def get_game_variables(constants, level=None):
    # Player Variables
    fighter_component = Fighter(hp=30, defense=0, power=1, is_player=True, fov_range=constants.get('fov_radius'))
    inventory_component = Inventory(26)
    level_component = Level()
    equipment_component = Equipment()
    faction_component = Faction(faction_name='Player')
    position_component = Position(0, 0)
    player = Entity("@", (95, 75, 47), 'Player', "player", blocks=True, render_order=RenderOrder.ACTOR, position=position_component,
                    fighter=fighter_component, inventory=inventory_component, level=level_component,
                    equipment=equipment_component, faction=faction_component)
    entities = [player]
    particles = []
    particle_systems = []
    encounters = []

    # Generate Starting Equipment
    if not player.inventory.items:
        # starting_equipment = ['map', 'imperial_longsword', 'imperial_chainmail_leggings', 'imperial_chainmail_coif',
        #                       'imperial_chainmail_hauberk', 'imperial_battle_shield', 'teleport_crystal', 'blind_powder', 'confusion_scroll', 'lightning_scroll', 'fireball_scroll', 'poison_vial']
        # starting_equipment = ['map', 'dagger', 'fireball_scroll','fireball_scroll', 'lightning_scroll', 'lightning_scroll', 'lightning_scroll', 'lightning_scroll', 'master_key']
        starting_equipment = ['map','short_sword', 'healing_potion', 'healing_potion']
        for item_index in starting_equipment:
            item_entity = create_item_entity(item_index)
            player.inventory.add_item(item_entity)
            if item_entity.equippable:
                player.equipment.toggle_equip(item_entity)

    # Initiatize Map
    # TODO: Change game_map into a Map variable containing all the entities and tiles. All tiles are not transparent
    game_map = GameMap(constants['map_width'], constants['map_height'], dungeon_level=4)
    game_map.make_map(constants['max_rooms'], constants['room_min_size'], constants['room_max_size'],
                      constants['map_width'], constants['map_height'], player, entities, particles, particle_systems,
                      encounters=encounters, level=level)

    # Initialize Message Log
    message_log = MessageLog(constants['message_x'], constants['message_width'], constants['message_height'])

    # Initialize Game State
    game_state = GameStates.EVENT_MESSAGE

    return player, entities, particles, particle_systems, game_map, message_log, game_state
