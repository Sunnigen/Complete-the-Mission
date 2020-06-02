from math import sqrt
from random import choice, choices, randint

import tcod as libtcod

from components.AI import BasicMob, PatrolMob
from components.Encounter import Encounter
from components.Equippable import Equippable
from components.Fighter import Fighter
from components.Furniture import Furniture
from components.Inventory import Inventory
from components.Item import Item
from components.Stairs import Stairs
from Entity import Entity
from GameMessages import Message
# Do not remove ItemFunctions! There are called out in json and eval()'ed
from ItemFunctions import *
# from ItemFunctions import cast_confuse, cast_fireball, cast_lightning, heal,
from loader_functions.JsonReader import obtain_item_table, obtain_mob_table, obtain_tile_set
from MapObjectFunctions import *
from RandomUtils import random_choice_from_dict, spawn_chance
from RenderFunctions import RenderOrder


TILE_SET = obtain_tile_set()


def calculate_distance(x1, y1, x2, y2):
    return sqrt((x2 - x1)**2 + (y2 - y1)**2)


def close_room(game_map, room):
    # Sets Tiles in to Become Passable
    for x in range(room.x1, room.x2):
        for y in range(room.y1, room.y2):
            create_wall(game_map, x, y)


def create_walled_room(game_map, room, buffer=0):
    # Sets Tiles in to Become Passable, but add walls around
    for x in range(room.x1, room.x2):
        for y in range(room.y1, room.y2):
            if x == room.x1 or x == room.x2 - buffer or y == room.y1 or y == room.y2 - buffer:
                create_wall(game_map, x, y)
            else:
                create_floor(game_map, x, y)


def create_room(game_map, room):
    # Sets Tiles in to Become Passable
    for x in range(int(room.x1) + 1, int(room.x2) - 1):
        for y in range(int(room.y1) + 1, int(room.y2) - 1):
            create_floor(game_map, x, y)


def create_hall(game_map, room1, room2):
    x1, y1 = room1.center
    x2, y2 = room2.center
    # x1, y1 = room1.x + room1.width // 2, room1.y + room1.height // 2
    # x2, y2 = room1.x + room1.width // 2, room2.y + room2.height // 2

    # Note: Unless the Rooms are physically touching, they overlap either Horizontally or Vertically, not both.

    # Check if Room 1 Overlaps Room 2 Horizontally
    # print('Check if Room 1 Overlaps Room 2 Horizontally')
    # for x in range(room1.x1, room1.x2 - 1):
    #     if room2.x1 < x < room2.x2:
    #         create_v_tunnel(game_map, y1, y2, x1)
    #         return None

    # Check if Room 1 Overlaps Room 2 Vertically
    # print('Check if Room 1 Overlaps Room 2 Vertically')
    # for y in range(room1.y1 + 1, room1.y2 - 1):
    #     if room2.y1 < y < room2.y2:
    #         create_h_tunnel(game_map, x1, x2, y1)
    #         return None

    if randint(0, 1) == 1:
        create_h_tunnel(game_map, x1, x2, y1)
        create_v_tunnel(game_map, y1, y2, x2)
    else:  # else it starts vertically
        create_v_tunnel(game_map, y1, y2, x1)
        create_h_tunnel(game_map, x1, x2, y2)


def create_h_tunnel(game_map, x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        create_floor(game_map, x, y)


def create_v_tunnel(game_map, y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        create_floor(game_map, x, y)


def create_floor(game_map, x, y):
    # Open (1) Tile
    # floor = TILE_SET['2']
    # game_map.transparent[y][x] = floor.get("transparent")
    # game_map.walkable[y][x] = floor.get("walkable")
    # game_map.tiles[y][x] = floor.get("char")  # "."
    place_tile(game_map, x, y, '2')


def create_wall(game_map, x, y):
    # close (1) Tile
    # wall = TILE_SET['1']
    # game_map.transparent[y][x] = wall.get('transparent')
    # game_map.walkable[y][x] = wall.get('walkable')
    # game_map.tiles[y][x] = wall.get('char')  # "#"
    place_tile(game_map, x, y, '1')


def place_tile(game_map, x, y, obj):
    # Places Tile
    tile = TILE_SET.get(str(obj))
    game_map.transparent[y][x] = tile.get('transparent')
    game_map.fov[y][x] = tile.get('fov')
    game_map.walkable[y][x] = tile.get('walkable')
    game_map.char_tiles[y][x] = tile.get('char')
    game_map.tileset_tiles[y][x] = int(obj)


def find_wall_direction(room_from, room_to):
    directions = []
    x1, y1 = room_from.center
    x2, y2 = room_to.center

    if x1 < x2:
        directions.append('west')
    elif x1 > x2:
        directions.append('east')

    if y1 < y2:
        directions.append('north')
    elif y1 > y2:
        directions.append('south')

    if not directions:
        return None
    return choice(directions)


def create_door(game_map, sub_room, main_room):
    # Create a Single Opening at a Select Rectangle Wall
    direction = find_wall_direction(sub_room, main_room)
    x_door, y_door = sub_room.center
    if direction == 'south':
        x_door = (sub_room.x1 + 1 + sub_room.x2) // 2
        y_door = sub_room.y1 + 1
    elif direction == 'north':
        x_door = (sub_room.x1 - 1 + sub_room.x2) // 2
        y_door = sub_room.y2 - 1
    elif direction == 'east':
        x_door = sub_room.x1 + 1
        y_door = (sub_room.y1 + 1 + sub_room.y2) // 2
    elif direction == 'west':
        x_door = sub_room.x2 - 1
        y_door = (sub_room.y1 - 1 + sub_room.y2) // 2
    else:
        print('\n\nno door was created???')
        print('main_room:', main_room.center)
        print('sub_room:', sub_room.center)
    # create_hall(game_map, sub_room, main_room)
    # create_floor(game_map, x_door, y_door)
    return x_door, y_door


def place_entities(game_map, dungeon_level, room, entities, item_table, mob_table, object_table):

    # Get a Random Number of Monsters
    max_monsters_per_room = spawn_chance([[2, 1], [3, 4], [5, 6]], dungeon_level)
    max_items_per_room = spawn_chance([[1, 1], [2, 4]], dungeon_level)

    # number_of_mobs = randint(0, max_monsters_per_room)
    number_of_mobs = 4
    number_of_items = randint(1, max_items_per_room)
    # number_of_mobs = randint(0, 1)
    # number_of_items = randint(0, 1)

    monster_chances = {mob: spawn_chance([stats for stats in mob_stats.get('spawn_chance')], dungeon_level)
                       for mob, mob_stats in mob_table.items()
                       }
    # object_chances = {object: spawn_chance([[object_stats.get('spawn_chance'), object_stats.get('item_level')]],
    #                                    dungeon_level) for object, object_stats in object_table.items()
    #                 }

    item_chances = {item: spawn_chance([[item_stats.get('spawn_chance'), item_stats.get('item_level')]],
                                       dungeon_level) for item, item_stats in item_table.items()
                    }

    # print('Number of Items:', number_of_items)
    # print('Number of Monsters:', number_of_mobs)
    # For debug use, view loot table
    game_map.spawn_chances = {'mobs': monster_chances, 'items': item_chances}

    # Initiate Encounter
    pop = [BasicMob, PatrolMob]
    # pop = [BasicMob]
    # pop = [PatrolMob]
    # weights = [100]
    weights = [50, 50]
    encounter_type = choices(population=pop,
                             weights=weights,
                             k=1)[0]
    encounter = Encounter(room, len(game_map.encounters) + 1)

    # Generate Furniture
    # furniture_list = generate_objects(entities, game_map.map_objects, game_map, room, 5, object_chances, object_table)

    # Generate Monsters
    monster_list = generate_mobs(entities, game_map, number_of_mobs, monster_chances, mob_table,
                                 encounter_type, encounter, room=room)
    encounter.monster_list = monster_list

    # Generate Items
    item_list = generate_items(entities, game_map, room, number_of_items, item_chances, item_table)
    encounter.item_list = item_list

    # Group Created Monsters and Items into a Single Encounter
    # game_map.encounters.append(Encounter(monster_list, item_list, room, len(game_map.encounters) + 1))
    game_map.encounters.append(encounter)


def generate_mobs(entities, game_map, number_of_mobs, monster_chances, mob_table, encounter_type, encounter, room=None, x=None, y=None):
    # return []
    # for e in entities:
    #     if e.ai:
    #         return []
    # print('generate_mobs', number_of_mobs)
    # game_map.player.x, game_map.player.y = room.x, room.y
    monster_list = []
    # for i in range(1):
    for i in range(number_of_mobs):
        # Choose A Random Location Within the Room
        if room:
            x, y = room.obtain_point_within(2)

        # print('placing monster at', x, y)
        # Check if Another Entity already Exists in [x][y] Position
        if not any([entity for entity in entities if entity.x == x and entity.y == y]) and \
                game_map.is_within_map(x, y) and game_map.walkable[y][x]:
                # game_map.is_within_map(x, y) and game_map.is_blocked(x, y):

            mob_index = random_choice_from_dict(monster_chances)
            mob_stats = mob_table[mob_index]

            fighter_component = Fighter(hp=mob_stats.get('hp'), defense=mob_stats.get('def'),
                                        power=mob_stats.get('att'), xp=mob_stats.get('xp'), fov=mob_stats.get('fov'),
                                        mob_level=mob_stats.get('mob_level'))
            ai_component = encounter_type(encounter=encounter, origin_x=x, origin_y=y)
            mob_entity = Entity(x, y, mob_stats.get('char'), mob_stats.get('color'), mob_stats.get('name'), mob_index,
                                blocks=True, fighter=fighter_component, render_order=RenderOrder.ACTOR,
                                ai=ai_component)

            entities.append(mob_entity)
            monster_list.append(mob_entity)
        # print('monster_list:', monster_list)
    return monster_list


def generate_mob(x, y, mob_stats, mob_index, encounter_group, pop=BasicMob):
    pop = [pop]
    weights = [100]
    # weights = [50, 50]
    encounter_type = choices(population=pop,
                             weights=weights,
                             k=1)[0]

    fighter_component = Fighter(hp=mob_stats.get('hp'), defense=mob_stats.get('def'),
                                power=mob_stats.get('att'), xp=mob_stats.get('xp'), fov=mob_stats.get('fov'),
                                mob_level=mob_stats.get('mob_level'))
    ai_component = encounter_type(encounter=encounter_group, origin_x=x, origin_y=y)
    mob_entity = Entity(x, y, mob_stats.get('char'), mob_stats.get('color'), mob_stats.get('name'), mob_index,
                        blocks=True, fighter=fighter_component, render_order=RenderOrder.ACTOR,
                        ai=ai_component)
    if isinstance(ai_component, PatrolMob):
        mob_entity.ai.goal_x = x
        mob_entity.ai.goal_y = y

    return mob_entity


def generate_objects(entities, map_objects, game_map, room, number_of_objects, object_chances, object_table):
    object_list = []
    for i in range(number_of_objects):
        x, y = room.obtain_point_within(2)

        if not any([entity for entity in entities + map_objects if entity.x == x and entity.y == y]) and \
                game_map.is_within_map(x, y) and not game_map.is_blocked(x, y):

            # Randomly Select an Object to Spawn
            object_index = random_choice_from_dict(object_chances)
            object_stats = object_table[object_index]

            # Inventory/Items Contained Within
            inventory = object_stats.get('inventory')
            inventory_component = None
            if inventory:
                inventory_component = Inventory(26)
                inventory_component.items = generate_random_items()

                for item in inventory_component.items:
                    entities.append(item)


            # Interactable
            movable = object_stats.get('moveable')
            breakable = object_stats.get('breakable')
            walkable = object_stats.get('walkable')
             # items=[], movable=False, breakable=False, walkable=False, interact_function
            furniture_component = Furniture(name=object_stats.get('name'), movable=movable,
                                            breakable=breakable, walkable=walkable,
                                            interact_function=eval(object_stats.get('interact_function')))
            object_entity = Entity(x, y, object_stats.get('char'), object_stats.get('color'), object_stats.get('name'),
                                   object_index, render_order=RenderOrder.ITEM, furniture=furniture_component,
                                   inventory=inventory_component)
            map_objects.append(object_entity)
            object_list.append(object_entity)

    return object_list


def generate_random_items(number_of_items=3, item_chances={}, item_table={}):
    items = []

    """
    "healing_potion": {
    "name": "Healing Potion",
    "char": 33,
    "glyph": "!",
    "color": [127, 0, 255],
    "type": "consumable",
    "equippable": false,
    "amount": 40,
    "use_function": "heal",
    "spawn_chance": 35,
    "item_level": 1,
    "unique": false
    """
    # Generate Random Number of Items
    for i in range(number_of_items):
        item_component = Item(use_function=eval('heal'),
                              amount=40,
                              radius=None,
                              damage=None,
                              targeting_message=None,
                              targeting=None,
                              maximum_range=None,
                              description="A potion containing green liquid. Most likely a healing potion."
                              )

        item_entity = Entity(0, 0, 33, [127, 0, 255], "Healing Potion",
                             "healing_potion", render_order=RenderOrder.ITEM, item=item_component)
        items.append(item_entity)
    return items


def generate_items(entities, game_map, room, number_of_items, item_chances, item_table):
    item_list = []
    for i in range(number_of_items):
        x, y = room.obtain_point_within(2)

        # Ensure another Entity doesn't already Exist in same coordinates
        if not any([entity for entity in entities if entity.x == x and entity.y == y]) and \
                game_map.is_within_map(x, y) and not game_map.is_blocked(x, y):

            # Randomly Select an Item to Spawn
            item_index = random_choice_from_dict(item_chances)
            item_stats = item_table[item_index]

            if item_stats.get('type') == 'consumable':
                item_component = Item(use_function=eval(item_stats.get('use_function')),
                                      amount=item_stats.get('amount'),
                                      radius=item_stats.get('radius'),
                                      damage=item_stats.get('damage'),
                                      targeting_message=Message(item_stats.get('targeting_message')),
                                      targeting=item_stats.get('targeting'),
                                      maximum_range=item_stats.get('range'),
                                      description=item_stats.get('description')
                                      )

                item_entity = Entity(x, y, item_stats.get('char'), item_stats.get('color'), item_stats.get('name'),
                                     item_index, render_order=RenderOrder.ITEM, item=item_component)

            elif item_stats.get('type') == 'reuseable':
                item_component = Item(use_function=eval(item_stats.get('use_function')), name=item_stats.get('name'),
                                      text=item_stats.get('text'), description=item_stats.get('description'))

                item_entity = Entity(x, y, item_stats.get('char'), item_stats.get('color'), item_stats.get('name'),
                                     item_index, render_order=RenderOrder.ITEM, item=item_component,
                                     )

            elif item_stats.get('type') == 'equip':
                equippable_component = Equippable(item_stats.get('slot'), power_bonus=item_stats.get('attack'),
                                                  defense_bonus=item_stats.get('defense'), description=item_stats.get('description'))

                item_entity = Entity(x, y, item_stats.get('char'), item_stats.get('color'), item_stats.get('name'),
                                     item_index, equippable=equippable_component)
            else:
                print('Item Name: %s, Item type: %s isn\'t a suitable item type! Double check ./assets/item.json' %
                      (item_stats.get('name'), item_stats.get('type')))
                raise ValueError
            item_list.append(item_entity)
            entities.append(item_entity)
    return item_list


def place_stairs(dungeon_level, x, y):
    return Entity(x, y, '>', (255, 191, 0), 'Stairs', "11", render_order=RenderOrder.STAIRS,
                  stairs=Stairs(dungeon_level + 1), fov_color=(128, 112, 64))
